#!/usr/bin/env python3
"""Certification report for judge_set_v1 against README section 4 criteria.

Two input modes, one output: a markdown verdict table.

  --json out_c/judge_calibration/cert.json   completed-run schema written by
                                             scripts/quinn/judge_calibration.py
  --log  out_c/judge_calibration/cert.log    the log; REQUIRED for partial runs,
                                             because cert.json is written only
                                             after the last row — an interrupted
                                             run leaves rows recoverable here.

The log parser reads only anchor lines, so multi-line ANSWER / JUDGE reasoning
blocks are skipped safely:
    === cert_de01 [de] stability=True repeats=3 ===
      --- cert_de01/good rep1 ---
      JUDGE finish=stop attempts=1 tokens=2048 usage={...}
      JUDGE score=4 | latency 221.7s

Criteria mirror README section 4 exactly (separation >=0.8 gap and >=80% good
at >=4; brevity >=80% long_wrong <=2 and mean <=2.5; fact-check >=80% planted
<=3 with 0% at 5; constraint >=80% audience_violation <=3; floor >=70% bad ==1
and mean <=1.5; per-item ordinal order; stability >=70% exact / >=95% within
+/-1 over the repeats of the stability subslice) and are computed for the
overall pass (repeat 1 only, harness parity) AND per language slice — README
row 8 requires every criterion to hold on en/de/zh separately, including
stability.

Read-only over the run artifacts; no endpoint calls.

Usage:
    python3 scripts/judge_cert_report.py --log out_c/judge_calibration/cert.log \
        --set data/evals/judge_set_v1/cert_items.json
"""

import argparse
import json
import re
from collections import defaultdict

ROW_HEAD = re.compile(r"^  --- ([a-z]+_[a-z]{2}\d+)/([a-z_]+) rep(\d+) ---")
ITEM_HEAD = re.compile(r"^=== ([a-z]+_[a-z]{2}\d+) \[([a-z]{2})\] stability=(\w+) repeats=(\d+) ===")
ROW_TAIL = re.compile(r"^  JUDGE score=(\d+|None) \| latency ([\d.]+)s")
ROW_FINISH = re.compile(r"^  JUDGE finish=(\w+) attempts=(\d+) tokens=(\d+) usage=(.*)$")
STAB_META = re.compile(r"stability (\w+).*pairs (\d+)")


def rows_from_json(path):
    doc = json.load(open(path, encoding="utf-8"))
    rows = doc["rows"]
    return rows


def rows_from_log(path, set_path=None):
    item_lang, stability_map = {}, {}

    if set_path:
        try:
            data = json.load(open(set_path, encoding="utf-8"))
            for it in data["items"]:
                item_lang[it["item_id"]] = it["lang"]
                stability_map[it["item_id"]] = bool(it.get("stability"))
        except OSError:
            pass

    rows = []
    cur = None
    for line in open(path, encoding="utf-8"):
        m = ITEM_HEAD.match(line)
        if m:
            item_lang.setdefault(m.group(1), m.group(2))
            stability_map.setdefault(m.group(1), m.group(3) == "True")
            continue

        m = ROW_HEAD.match(line)
        if m:
            cur = {"item_id": m.group(1), "variant": m.group(2), "repeat": int(m.group(3)),
                   "lang": item_lang.get(m.group(1), ""), "stability": stability_map.get(m.group(1), False),
                   "score": None, "finish_reason": None, "attempts": None,
                   "latency_s": None, "usage": None}
            continue

        m = ROW_FINISH.match(line)
        if m and cur:
            cur["finish_reason"] = m.group(1)
            cur["attempts"] = int(m.group(2))
            cur["usage"] = m.group(4)
            continue

        m = ROW_TAIL.match(line)
        if m and cur:
            cur["score"] = None if m.group(1) == "None" else int(m.group(1))
            cur["latency_s"] = float(m.group(2))
            rows.append(cur)
            cur = None
    return rows


def criteria(rows):
    """README section 4, over one row list (repeat 1 = harness parity)."""
    def scores(label):
        return [r["score"] for r in rows
                if r["variant"] == label and r["score"] is not None]

    out = {"n_rows": len(rows), "n_scored": sum(1 for r in rows if r["score"] is not None)}
    good, short = scores("good"), scores("short_correct")
    if good and short:
        gap = sum(good) / len(good) - sum(short) / len(short)
        ge4 = 100 * sum(1 for s in good if s >= 4) / len(good)
        out["sep_gap"] = round(gap, 2)
        out["sep"] = f"PASS ({gap:.2f} gap, {ge4:.0f}% good>=4)" if gap >= 0.8 and ge4 >= 80 \
            else f"FAIL ({gap:.2f} gap, {ge4:.0f}% good>=4)"
    lw, planted, audience, bad = scores("long_wrong"), scores("planted_error"), \
        scores("audience_violation"), scores("bad")
    if lw:
        le2 = 100 * sum(1 for s in lw if s <= 2) / len(lw)
        mean = sum(lw) / len(lw)
        out["brevity"] = f"PASS ({le2:.0f}%<=2, mean {mean:.2f})" if le2 >= 80 and mean <= 2.5 \
            else f"FAIL ({le2:.0f}%<=2, mean {mean:.2f})"
    if planted:
        le3 = 100 * sum(1 for s in planted if s <= 3) / len(planted)
        eq5 = 100 * sum(1 for s in planted if s == 5) / len(planted)
        out["fact"] = f"PASS ({le3:.0f}%<=3, {eq5:.0f}%==5)" if le3 >= 80 and eq5 == 0 \
            else f"FAIL ({le3:.0f}%<=3, {eq5:.0f}%==5)"
    if audience:
        le3 = 100 * sum(1 for s in audience if s <= 3) / len(audience)
        out["constraint"] = f"PASS ({le3:.0f}%<=3)" if le3 >= 80 else f"FAIL ({le3:.0f}%<=3)"
    if bad:
        eq1 = 100 * sum(1 for s in bad if s == 1) / len(bad)
        mean = sum(bad) / len(bad)
        out["floor"] = f"PASS ({eq1:.0f}%==1, mean {mean:.2f})" if eq1 >= 70 and mean <= 1.5 \
            else f"FAIL ({eq1:.0f}%==1, mean {mean:.2f})"

    by_item = defaultdict(dict)
    for r in rows:
        if r["score"] is not None:
            # keep the first repeat-1 score per (item, variant); repeat-1 = criteria basis
            if r["repeat"] == 1 or (r["item_id"], r["variant"]) not in by_item:
                by_item[(r["item_id"], r["variant"])] = r["score"]
    per_item = defaultdict(dict)
    for (iid, var), score in by_item.items():
        per_item[iid][var] = score
    ok = total = 0
    for var in per_item.values():
        if "good" in var and "short_correct" in var and "bad" in var:
            total += 1
            ok += var["good"] >= var["short_correct"] >= var["bad"]
    if total:
        out["ordinal"] = f"PASS ({ok}/{total})" if ok == total else f"FAIL ({ok}/{total})"

    # variant means for diagnosis
    for label in ("good", "short_correct", "long_wrong", "planted_error",
                  "audience_violation", "bad"):
        s = scores(label)
        if s:
            out[f"mean_{label}"] = round(sum(s) / len(s), 2)
    return out


def stability(rows):
    """Pairs (item, variant) with >=2 non-null scores, harness semantics."""
    seqs = defaultdict(list)
    for r in rows:
        if r["score"] is not None and r.get("stability"):
            seqs[(r["item_id"], r["variant"])].append((r["repeat"], r["score"]))
    pairs = exact = within1 = 0
    for (_, _), seq in seqs.items():
        if len(seq) < 2:
            continue
        seq = [s for _, s in sorted(seq)]
        pairs += 1
        exact += max(seq) == min(seq)
        within1 += max(seq) - min(seq) <= 1
    if not pairs:
        return {"pairs": 0, "stability": "n/a"}
    e, w = 100 * exact / pairs, 100 * within1 / pairs
    ok = e >= 70 and w >= 95
    return {"pairs": pairs,
            "stability": (f"PASS ({e:.0f}% exact, {w:.0f}% +-1, {pairs} pairs)" if ok
                          else f"FAIL ({e:.0f}% exact, {w:.0f}% +-1, {pairs} pairs)")}


def expected_calls(set_path):
    total, rep1_only = 0, 0
    try:
        data = json.load(open(set_path, encoding="utf-8"))
    except OSError:
        return None, None
    for it in data["items"]:
        reps = 3 if it.get("stability") else 1
        total += len(it["variants"]) * reps
        rep1_only += len(it["variants"])
    return total, rep1_only


def report(rows, exp, exp1):
    out = []
    out.append("# Judge cert report (draft — verdict for the cert run, not a freeze)\n")
    if exp:
        done = len(rows)
        out.append(f"**Coverage:** {done}/{exp} calls ({'COMPLETE' if done == exp else 'PARTIAL'}); "
                   f"expected row-1 basis: {exp1}\n")

    langs = ("all", "en", "de", "zh")
    out.append("| criterion | " + " | ".join(langs) + " |")
    out.append("|---|" + "---|" * len(langs))
    slices = {}
    for lang in langs:
        rs = rows if lang == "all" else [r for r in rows if r["lang"] == lang]
        # criteria basis: repeat-1 rows (harness parity)
        c = criteria([r for r in rs if r["repeat"] == 1])
        slices[lang] = (c, stability(rs))
    keys = ("sep", "brevity", "fact", "constraint", "floor", "ordinal")
    nice = {"sep": "separation", "brevity": "brevity bias", "fact": "fact-checking",
            "constraint": "constraint awareness", "floor": "floor", "ordinal": "ordinal order"}
    for k in keys:
        cells = []
        for lang in langs:
            v = slices[lang][0].get(k)
            cells.append(v if v else "n-a")
        out.append(f"| {nice[k]} | " + " | ".join(cells) + " |")
    st_cells = []
    for lang in langs:
        st = slices[lang][1]
        st_cells.append(st["stability"] if st["pairs"] else "n-a")
    out.append(f"| stability | " + " | ".join(st_cells) + " |")

    out.append("\n## Variant means (repeat 1, all langs)\n")
    labels = ("good", "short_correct", "long_wrong", "planted_error", "audience_violation", "bad")
    header = "| variant | all | " + " | ".join(("en", "de", "zh")) + " |"
    out.append(header)
    out.append("|---|" + "---|" * 4)
    for label in labels:
        cells = []
        for lang in ("all", "en", "de", "zh"):
            rs = [r for r in rows if r["lang"] == lang] if lang != "all" else rows
            rs = [r for r in rs if r["repeat"] == 1 and r["variant"] == label and r["score"] is not None]
            cells.append(f"{sum(r['score'] for r in rs) / len(rs):.2f} (n={len(rs)})" if rs else "n-a")
        out.append(f"| {label} | " + " | ".join(cells) + " |")

    nulls = [r for r in rows if r["score"] is None]
    if nulls:
        out.append(f"\n**NULLS (n={len(nulls)}):**\n")
        for r in nulls:
            out.append(f"- {r['item_id']}/{r['variant']} rep{r['repeat']}: finish="
                       f"{r['finish_reason']} attempts={r['attempts']} usage={r['usage']}")
    slow = sorted((r for r in rows if r["latency_s"]), key=lambda x: -x["latency_s"])[:5]
    if slow:
        out.append("\n**Slowest calls:**\n")
        for r in slow:
            out.append(f"- {r['item_id']}/{r['variant']} rep{r['repeat']}: {r['latency_s']:.0f}s "
                       f"finish={r['finish_reason']}")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--log")
    ap.add_argument("--set", default="data/evals/judge_set_v1/cert_items.json")
    args = ap.parse_args()
    if bool(args.json) == bool(args.log):
        ap.error("exactly one of --json or --log")

    if args.json:
        rows = rows_from_json(args.json)
    else:
        rows = rows_from_log(args.log, args.set)

    rows = sorted(rows, key=lambda r: (r["item_id"], r["variant"], r["repeat"]))
    exp, exp1 = expected_calls(args.set)
    print(report(rows, exp, exp1))


if __name__ == "__main__":
    main()
