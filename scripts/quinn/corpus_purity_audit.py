#!/usr/bin/env python3
"""Audit the territory corpora for cross-script contamination.

Why this exists: crop 91 of the zh evaluation sample turned out to be English
UNCCD agenda text sitting inside xscript_zh.txt (0.0 % CJK, 100.0 % Latin).
A routing "error" on that crop was in fact a labelling error: the router sent
English prose to the prose route, which is correct once the label is read
against the content.

The first version of this script reported "0 contaminations" for that corpus.
It sampled twelve offsets spread over the whole 1.29 GB file, while the
evaluator only ever reads bytes 28-30 MB (read(mb*1e6)[-2e6:]). The nearest
sample sat 29.5 MB away from the contaminated region. A whole-file scan cannot
answer the question "are the evaluation crops clean".

This version reports two views per corpus:

  window -- offsets inside the 2 MB slice the evaluator actually draws from.
            This decides whether a routing label is trustworthy for a run.
  whole  -- offsets across the entire file. Shows whether a corpus is
            contaminated at scale; says nothing about the evaluation window.

It reads bytes only; no model, no GPU.

Usage:
    python3 scripts/quinn/corpus_purity_audit.py --data-root data \\
        --samples 12 --chunk 8192 --mb 30 --json-out audit.json

The exit code is 1 when any window-view region is off-script, so the script can
gate a run.
"""

import argparse
import json
import os
import re
import sys

# Coarse script classes. The question is "is this the script we expect", not
# "which language is this".
SCRIPT_PATTERNS = {
    "cjk": re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]"),
    "latin": re.compile(r"[A-Za-z\u00c0-\u024f]"),
    "cyrillic": re.compile(r"[\u0400-\u052f]"),
    "greek": re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]"),
    "arabic": re.compile(r"[\u0600-\u06ff]"),
    "devanagari": re.compile(r"[\u0900-\u097f]"),
}

# Expected script per territory. Unlisted territories default to latin, which
# is what every Europarl-derived corpus except bg, el and zh contains.
EXPECTED = {
    "zh": "cjk",
    "bg": "cyrillic",
    "el": "greek",
}

CORPORA = [
    ("prose", "textmix/wikitext-103-raw/wiki.train.raw"),
    ("es", "europarl/europarl-v7.es-en.es.txt"),
    ("pl", "europarl/europarl-v7.pl-en.pl.txt"),
    ("fr", "europarl/europarl-v7.fr-en.fr.txt"),
    ("de", "europarl/europarl-v7.de-en.de.txt"),
    ("cs", "europarl/europarl-v7.cs-en.cs.txt"),
    ("da", "europarl/europarl-v7.da-en.da.txt"),
    ("pt", "europarl/europarl-v7.pt-en.pt.txt"),
    ("fi", "europarl/europarl-v7.fi-en.fi.txt"),
    ("hu", "europarl/europarl-v7.hu-en.hu.txt"),
    ("bg", "europarl/europarl-v7.bg-en.bg.txt"),
    ("it", "europarl/europarl-v7.it-en.it.txt"),
    ("et", "europarl/europarl-v7.et-en.et.txt"),
    ("el", "europarl/europarl-v7.el-en.el.txt"),
    ("sk", "europarl/europarl-v7.sk-en.sk.txt"),
    ("sv", "europarl/europarl-v7.sv-en.sv.txt"),
    ("ro", "europarl/europarl-v7.ro-en.ro.txt"),
    ("nl", "europarl/europarl-v7.nl-en.nl.txt"),
    ("sl", "europarl/europarl-v7.sl-en.sl.txt"),
    ("lt", "europarl/europarl-v7.lt-en.lt.txt"),
    ("code", "textmix2/code.txt"),
    ("math", "textmix2/latex.txt"),
    ("legal", "textmix2/legal.txt"),
    ("ga", "europarl/DGT.en-ga.ga.txt"),
    ("zh", "europarl/xscript_zh.txt"),
]


def classify(text):
    """Return (dominant script, shares in percent, total letter-like chars)."""
    counts = {}
    for name, pat in SCRIPT_PATTERNS.items():
        n = len(pat.findall(text))
        if n:
            counts[name] = n
    total = sum(counts.values())
    if total == 0:
        return "none", {}, 0
    dominant = max(counts, key=counts.get)
    shares = {k: round(100.0 * v / total, 1) for k, v in counts.items()}
    return dominant, shares, total


def whole_offsets(size, samples):
    out = []
    for k in range(samples):
        o = int(size * k / samples)
        o -= o % 512
        out.append(o)
    return out


def window_offsets(window_len, samples, chunk):
    """Spread samples across the readable slice, aligned so a chunk fits.

    Note, measured 2026-11-04: twelve such samples cover 98 KB of a 2 MB
    window (4.9 %). A small foreign-language block of a few hundred bytes is
    missed. On xscript_zh.txt this view reported 12/12 clean while the
    protocol view found crop 91 at 100 % Latin. Use --mode protocol to decide
    whether the crops an evaluation actually draws are contaminated; this
    view only shows coarse composition.
    """
    hi = max(window_len - chunk, 0)
    if hi == 0:
        return [0]
    out = []
    for k in range(samples):
        o = int(hi * k / max(samples - 1, 1))
        o -= o % 2
        out.append(o)
    return out


def protocol_offsets(window_len, crops, block, seed):
    """Exactly the offsets eval_router.py draws for this corpus.

    Mirrors: generator seeded once with seed, hi = len(arr) - block - 1,
    then randint(hi, (crops,)) -- one domain per call, so no other corpus
    advances the generator.
    """
    import torch
    hi = window_len - block - 1
    if hi <= 0:
        raise SystemExit("readable slice is shorter than one block")
    g = torch.Generator().manual_seed(seed)
    return [int(x) for x in torch.randint(hi, (crops,), generator=g)]


def audit_corpus(path, samples, chunk, mb, mode, crops, block, seed):
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        head = fh.read(mb * 1_000_000)
    window_start = max(len(head) - 2_000_000, 0)
    window_len = len(head) - window_start
    window = head[window_start:]

    whole = []
    with open(path, "rb") as fh:
        for off in whole_offsets(size, samples):
            fh.seek(off)
            text = fh.read(chunk).decode("utf-8", errors="ignore")
            dominant, shares, total = classify(text)
            whole.append({"offset": off, "dominant": dominant, "shares": shares,
                          "total": total, "preview": text.replace("\n", " ")[:60]})

    win = []
    for rel in window_offsets(window_len, samples, chunk):
        text = window[rel:rel + chunk].decode("utf-8", errors="ignore")
        dominant, shares, total = classify(text)
        win.append({"offset": window_start + rel, "dominant": dominant,
                    "shares": shares, "total": total,
                    "preview": text.replace("\n", " ")[:60]})

    protocol = []
    if mode == "protocol":
        for ci, off in enumerate(protocol_offsets(window_len, crops, block, seed)):
            text = window[off:off + block].decode("utf-8", errors="ignore")
            dominant, shares, total = classify(text)
            protocol.append({"crop": ci, "offset": window_start + off,
                             "dominant": dominant, "shares": shares,
                             "total": total})

    return {"size_bytes": size, "window_start": window_start,
            "window_len": window_len, "whole": whole, "window": win,
            "protocol": protocol}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default="data")
    ap.add_argument("--samples", type=int, default=12)
    ap.add_argument("--chunk", type=int, default=8192)
    ap.add_argument("--mb", type=int, default=30)
    ap.add_argument("--json-out", default="")
    ap.add_argument("--mode", choices=["window", "protocol"], default="protocol",
                    help="protocol: sample exactly the crops eval_router draws "
                         "(the only view that decides label trust); "
                         "window: coarse composition of the 2 MB slice")
    ap.add_argument("--crops", type=int, default=200)
    ap.add_argument("--block", type=int, default=512)
    ap.add_argument("--seed", type=int, default=1234)
    args = ap.parse_args()

    results = []
    window_problems = []

    print("%8s %9s %7s %5s %5s  %s" %
          ("territory", "expect", "win.dom", "win", "whole", "window mismatches"))
    print("-" * 88)

    for name, rel in CORPORA:
        path = os.path.join(args.data_root, rel)
        if not os.path.exists(path):
            print("%8s   MISSING (%s)" % (name, rel))
            results.append({"territory": name, "path": rel, "missing": True})
            continue

        expected = EXPECTED.get(name, "latin")
        a = audit_corpus(path, args.samples, args.chunk, args.mb,
                        args.mode, args.crops, args.block, args.seed)

        win_dom = a["window"][0]["dominant"] if a["window"] else "none"
        win_bad = [r for r in a["window"] if r["dominant"] not in (expected, "none")]
        whole_bad = [r for r in a["whole"] if r["dominant"] not in (expected, "none")]
        if args.mode == "protocol":
            corpus_dom = max({r["dominant"] for r in a["protocol"] if r["dominant"] != "none"},
                             key=lambda d: sum(1 for r in a["protocol"] if r["dominant"] == d),
                             default=expected)
            win_bad = [r for r in a["protocol"] if r["dominant"] not in (corpus_dom, "none")]
            win_dom = corpus_dom

        note = ""
        if win_bad:
            note = "; ".join("off=%s %s" % (format(r["offset"], ","), r["shares"])
                             for r in win_bad[:2])

        print("%8s %9s %7s %4d/%d %4d/%d  %s" %
              (name, expected, win_dom, len(a["window"]) - len(win_bad),
               len(a["window"]), len(a["whole"]) - len(whole_bad),
               len(a["whole"]), note))

        entry = {"territory": name, "path": rel, "expected_script": expected,
                 "mode": args.mode,
                 "window": a["window"], "whole": a["whole"],
                 "protocol": a["protocol"],
                 "window_mismatches": len(win_bad),
                 "whole_mismatches": len(whole_bad),
                 "anomalies": win_bad}
        results.append(entry)
        if win_bad:
            window_problems.append(entry)

    print("")
    print("corpora with off-script regions inside the evaluation window: %d"
          % len(window_problems))
    for e in window_problems:
        print("  %-6s %d of %d window samples off-script"
              % (e["territory"], e["window_mismatches"], len(e["window"])))
        for r in e["window"]:
            if r["dominant"] not in (e["expected_script"], "none"):
                print("      offset %s: %s" % (format(r["offset"], ","), r["shares"]))
                print("      %r" % r["preview"])

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump({"data_root": args.data_root,
                       "samples_per_corpus": args.samples,
                       "chunk_bytes": args.chunk,
                       "mb_read": args.mb,
                       "corpora": results}, fh, indent=2)
        print("")
        print("json written: %s" % args.json_out)

    return 1 if window_problems else 0


if __name__ == "__main__":
    sys.exit(main())
