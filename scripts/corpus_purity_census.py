"""Corpus purity census — per-crop script composition, free of model forwards.

Complements scripts/eval_router.py. Routing labels follow the corpus of origin,
but corpora contain foreign-script content (cf. RBC-1 v0.3: zh crop 91 is 95 %
ASCII English inside xscript_zh.txt and flips to the base route at window 384).
This census quantifies that contamination per corpus, per crop, so misroute
counts can be read against content-vs-label agreement instead of blind.

Two modes:
  protocol (default)  Replicates the eval_router crop protocol exactly:
                      torch.Generator().manual_seed(--seed),
                      read(--mb*1_000_000)[-2_000_000:],
                      randint(len-block-1, (--crops,)), block-byte crops.
                      Requires torch (in the venv). Comparable with stage runs
                      that invoke eval_router one domain per invocation.
  --scan              No RNG: --crops crops at even strides over the readable
                      slice. Use for corpus selection, where protocol crops are
                      irrelevant but whole-corpus coverage matters.

Per crop (character level, letters only) it reports the dominant Unicode script
and its share ("purity"), the foreign-letter share against the corpus-dominant
script, and byte-level ASCII share (comparable to territory_byte_census). Latin
ASCII and accented letters share one script class, so the foreign share against
a Latin corpus only fires on genuinely foreign scripts; same-script
contamination (English inside German) is invisible to it and caught by the
marker-word rates instead. Per corpus it reports quantiles, the anomaly rate
with a Wilson interval, and two function-word marker rates (English vs German).

Usage:
    .venv/bin/python scripts/corpus_purity_census.py PATH [PATH ...] \
        [--mb 30] [--crops 200] [--block 512] [--seed 1234] [--scan] \
        [--json PATH]

Interpretation guard: an anomaly rate above the Wilson floor is a corpus
property, not a routing result; crops are labelled by file of origin only.
"""
import argparse
import json
import math
import sys
from collections import Counter

import numpy as np

# Contiguous code-point ranges per script (letters the byte-level tokenizer
# actually meets; compact by design, not a full UCD table).
RANGES = [
    ("Han", [(0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF)]),
    ("Hiragana", [(0x3040, 0x309F)]),
    ("Katakana", [(0x30A0, 0x30FF)]),
    ("Hangul", [(0x1100, 0x11FF), (0xAC00, 0xD7A3)]),
    ("Cyrillic", [(0x0400, 0x052F)]),
    ("Greek", [(0x0370, 0x03FF), (0x1F00, 0x1FFF)]),
    ("Latin", [(0x0041, 0x005A), (0x0061, 0x007A), (0x00AA, 0x00AA),
               (0x00BA, 0x00BA), (0x00C0, 0x024F), (0x1E00, 0x1EFF)]),
    ("Arabic", [(0x0600, 0x06FF)]),
    ("Devanagari", [(0x0900, 0x097F)]),
    ("Syllabics", [(0x1400, 0x167F)]),
]

EN_MARKERS = ("the", "and", "of", "to", "in", "is", "that", "for", "with")
DE_MARKERS = ("der", "die", "und", "nicht", "ist", "dem", "ein", "eine", "mit")


def script_of(ch):
    # ASCII letters fall through to the Latin spans; Latin ASCII and accented
    # letters share one class on purpose -- same-script (Latin-on-Latin)
    # contamination is invisible here by construction and caught by the
    # marker-word rates instead. The byte-level ASCII share is reported
    # separately per crop.
    o = ord(ch)
    for name, spans in RANGES:
        if any(a <= o <= b for a, b in spans):
            return name
    return "other"


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def crop_offsets(mode, arr_len, block, crops, seed):
    hi = arr_len - block - 1
    if hi <= 0:
        raise SystemExit("readable slice is shorter than one block")
    if mode == "scan":
        return [int(i) for i in np.linspace(0, hi, crops).astype(int)]
    import torch  # protocol mode must match eval_router.py exactly
    g = torch.Generator().manual_seed(seed)
    return [int(i) for i in torch.randint(hi, (crops,), generator=g)]


def census(path, args):
    arr = np.frombuffer(open(path, "rb").read(args.mb * 1_000_000)[-2_000_000:],
                        dtype=np.uint8)
    offsets = crop_offsets("scan" if args.scan else "protocol", len(arr),
                           args.block, args.crops, args.seed)
    rows = []
    script_totals = Counter()
    for ci, off in enumerate(offsets):
        raw = arr[off:off + args.block]
        text = raw.tobytes().decode("utf-8", errors="replace")
        scripts = Counter()
        for ch in text:
            if ch.isalpha():
                scripts[script_of(ch)] += 1
        n_letters = sum(scripts.values())
        script_totals += scripts
        if n_letters:
            dom, dom_n = scripts.most_common(1)[0]
            purity = dom_n / n_letters
        else:
            dom, purity = "none", 0.0
        rows.append({
            "crop": ci, "offset": off,
            "ascii_byte_share": float((raw < 0x80).mean()),
            "n_letters": n_letters, "dominant_script": dom,
            "purity": round(purity, 4),
            "foreign_letter_share": round(1 - purity, 4) if n_letters else 1.0,
            "split_chars": text.count("\ufffd"),
        })
    dom_corpus = Counter(r["dominant_script"] for r in rows).most_common(1)[0][0]
    anomalies = [r for r in rows if r["dominant_script"] != dom_corpus]
    pures = sorted(r["purity"] for r in rows)
    q = lambda p: pures[min(len(pures) - 1, int(p * len(pures)))]
    words = 0
    en_hits = de_hits = 0
    for off in offsets[:: max(1, len(offsets) // 50)]:  # marker words: ~50 crops
        text = arr[off:off + args.block].tobytes().decode("utf-8", errors="replace").lower()
        toks = [t.strip(".,;:!?()\u300c\u300d\u300e\u300f\u201c\u201d") for t in text.split()]
        for t in toks:
            if t in EN_MARKERS:
                en_hits += 1
            if t in DE_MARKERS:
                de_hits += 1
            words += 1
    return {
        "path": path, "mode": "scan" if args.scan else "protocol",
        "crops": len(rows), "dominant_script": dom_corpus,
        "script_mix_letters": {k: v for k, v in script_totals.most_common()},
        "purity_p05": round(q(0.05), 4), "purity_p50": round(q(0.5), 4),
        "anomalous_crops": len(anomalies),
        "anomaly_rate": round(len(anomalies) / len(rows), 4),
        "anomaly_wilson95": [round(x, 4) for x in wilson(len(anomalies), len(rows))[1:]],
        "ascii_byte_share_mean": round(float(np.mean([r["ascii_byte_share"] for r in rows])), 4),
        "en_marker_per_1k": round(1000 * en_hits / max(words, 1), 2),
        "de_marker_per_1k": round(1000 * de_hits / max(words, 1), 2),
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpora", nargs="+")
    ap.add_argument("--mb", type=int, default=30)
    ap.add_argument("--crops", type=int, default=200)
    ap.add_argument("--block", type=int, default=512)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    results = [census(p, args) for p in args.corpora]

    hdr = ("| corpus | mode | crops | script | purity p5/p50 | anomalous (Wilson95) "
           "| ascii | EN mk/1k | DE mk/1k |")
    print(hdr)
    print("|" + "---|" * 9)
    for r in results:
        print(f"| {r['path'].split('/')[-1]} | {r['mode']} | {r['crops']} "
              f"| {r['dominant_script']} | {r['purity_p05']:.3f} / {r['purity_p50']:.3f} "
              f"| {r['anomalous_crops']} ({r['anomaly_wilson95'][0]:.3f}-{r['anomaly_wilson95'][1]:.3f}) "
              f"| {r['ascii_byte_share_mean']:.3f} | {r['en_marker_per_1k']} "
              f"| {r['de_marker_per_1k']} |")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(results, fh, indent=1)
        print(f"per-crop rows written: {args.json}", file=sys.stderr)


if __name__ == "__main__":
    main()
