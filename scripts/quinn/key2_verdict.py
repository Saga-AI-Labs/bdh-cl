"""Apply the frozen key-2 G0 thresholds to a host verdict pass.

The verdict pass is a fresh judge pass over the host generations, scored under
the frozen rubric. This script does not score anything; it turns the judge
output into the section 8.2 gate result.

Gate rule (rubric section 8.2), per dimension d:
    mean_d over the 100 gate items >= M_d
    min_d  over the 100 gate items >= F_d
There is no mean across dimensions. The 33 argue items are reported separately
and are not gated.

Seat policy comes from the frozen thresholds record. Coherence has one effective
seat (registered deviation), so only the authoritative seat's file is used for
that dimension; relevance and language use the minimum of every supplied judge.

Usage:
    .venv/bin/python scripts/quinn/key2_verdict.py \
        --verdict out/key2_calibration/qwen_verdict_v2.json \
        --verdict out/key2_calibration/gemma_verdict_v2.json \
        --compare out/key2_calibration/qwen_negative_v2.json \
        --compare out/key2_calibration/gemma_negative_v2.json \
        --out out/key2_calibration/verdict_3.62b.json
"""

import argparse
import datetime
import hashlib
import json
import statistics as st

DIMS = ("coherence", "relevance", "language")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows(path):
    doc = json.load(open(path))
    rows = doc["rows"] if isinstance(doc, dict) and "rows" in doc else doc
    return {r["id"]: r for r in rows}, doc.get("meta", {}) if isinstance(doc, dict) else {}


def stats(values):
    v = sorted(values)
    return {
        "n": len(v),
        "mean": round(st.mean(v), 3),
        "min": v[0],
        "max": v[-1],
        "p10": v[int(0.1 * (len(v) - 1))],
        "median": round(st.median(v), 3),
    }


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(num / (dx * dy), 3) if dx and dy else None


def longest_repeated(data):
    """Length in bytes of the longest substring that occurs at least twice."""
    n = len(data)

    def has_repeat(length):
        seen = set()
        for i in range(n - length + 1):
            piece = data[i:i + length]
            if piece in seen:
                return True
            seen.add(piece)
        return False

    lo, hi = 0, n - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if has_repeat(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def distinct_n(data, n=4):
    if len(data) < n:
        return 0.0
    grams = {data[i:i + n] for i in range(len(data) - n + 1)}
    return round(len(grams) / (len(data) - n + 1), 3)


def generation_diagnostics(path, hard_fail_bytes=64):
    rows = [json.loads(line) for line in open(path)]
    repeats, distinct = [], []
    offenders = []
    for r in rows:
        data = bytes.fromhex(r["sample_hex"]) if "sample_hex" in r else r["sample_text"].encode()
        lr = longest_repeated(data)
        repeats.append(lr)
        distinct.append(distinct_n(data))
        if lr >= hard_fail_bytes:
            offenders.append({"id": r["id"], "longest_repeat_bytes": lr})
    return {
        "n": len(rows),
        "longest_repeat_bytes": {
            "max": max(repeats),
            "median": int(st.median(repeats)),
            "p90": sorted(repeats)[int(0.9 * (len(repeats) - 1))],
        },
        "rows_at_or_above_hard_fail": offenders,
        "hard_fail_threshold_bytes": hard_fail_bytes,
        "hard_fail": bool(offenders),
        "distinct_4": {
            "mean": round(st.mean(distinct), 3),
            "min": min(distinct),
            "median": round(st.median(distinct), 3),
        },
    }


def seat_filter(paths, substr, dim):
    if dim != "coherence" or not substr:
        return paths
    keep = [p for p in paths if substr in p]
    if not keep:
        raise SystemExit("no coherence seat file matches %r" % substr)
    return keep


def consensus(paths, dim, substr):
    """Per-item score for one dimension, min of the seated judges."""
    maps = [load_rows(p)[0] for p in seat_filter(paths, substr, dim)]
    common = set(maps[0])
    for m in maps[1:]:
        common &= set(m)
    out = {}
    for rid in common:
        vals = [m[rid].get(dim) for m in maps]
        if all(isinstance(x, int) for x in vals):
            out[rid] = min(vals)
    return out


def gate_map(path):
    doc = json.load(open(path))
    items = doc["prompts"] if isinstance(doc, dict) and "prompts" in doc else doc
    return {i["id"]: bool(i.get("gate")) for i in items}


def family_map(path):
    doc = json.load(open(path))
    items = doc["prompts"] if isinstance(doc, dict) and "prompts" in doc else doc
    return {i["id"]: i.get("family") for i in items}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thresholds", default="out/key2_calibration/thresholds_candidate_v2.json")
    ap.add_argument("--verdict", action="append", required=True,
                    help="judge JSON for the host verdict pass (repeat per seat)")
    ap.add_argument("--prompts", default="data/evals/key2_prompts_v1.json")
    ap.add_argument("--generations", default="out/key2_calibration/gen_3.62b.jsonl",
                    help="host generations, for the repetition diagnostics")
    ap.add_argument("--coherence-seat-substr", default="qwen",
                    help="path substring of the authoritative coherence seat")
    ap.add_argument("--compare", action="append", default=[],
                    help="judge JSON from the calibration pass, for a replication check")
    ap.add_argument("--out", default="out/key2_calibration/verdict_3.62b.json")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    args = ap.parse_args()

    th = json.load(open(args.thresholds))
    gates = gate_map(args.prompts)
    fams = family_map(args.prompts)
    seat_mode = th["seat_policy"]["coherence"]["mode"]
    if seat_mode == "single-seat" and not args.coherence_seat_substr:
        raise SystemExit("thresholds record a single coherence seat; pass "
                         "--coherence-seat-substr")

    # judge files must all describe the same input
    metas = [load_rows(p)[1] for p in args.verdict]
    inputs = {m.get("input_sha256") for m in metas}
    if len(inputs) > 1:
        raise SystemExit("verdict files were scored from different inputs: %s" % inputs)

    per_dim = {}
    gate = {}
    diagnostic = {}
    below_floor = {}
    nulls = {}
    gate_scores = {}
    for dim in DIMS:
        scores = consensus(args.verdict, dim, args.coherence_seat_substr)
        g = {i: v for i, v in scores.items() if gates.get(i) is True}
        d = {i: v for i, v in scores.items() if gates.get(i) is False}
        gate_scores[dim] = g
        unknown = set(scores) - set(gates)
        if unknown:
            raise SystemExit("verdict rows not in the prompt set: %s" % sorted(unknown)[:5])
        f_d = th["bands"][dim]["F_d_candidate"]
        m_d = th["bands"][dim]["M_d_candidate"]
        vals = list(g.values())
        gs = stats(vals)
        gs["F_d"] = f_d
        gs["M_d"] = m_d
        gs["mean_pass"] = gs["mean"] >= m_d
        gs["floor_pass"] = gs["min"] >= f_d
        gs["pass"] = gs["mean_pass"] and gs["floor_pass"]
        gs["second_worst"] = sorted(vals)[-2] if len(vals) > 1 else None
        gs["within_0_5_of_floor"] = sum(1 for v in vals if v <= f_d + 0.5)
        gs["leave_one_out_mean"] = {
            "min": round((sum(vals) - max(vals)) / (len(vals) - 1), 3) if len(vals) > 1 else None,
            "max": round((sum(vals) - min(vals)) / (len(vals) - 1), 3) if len(vals) > 1 else None,
        }
        gs["family_minima"] = {
            fam: min(v for i, v in g.items() if fams.get(i) == fam)
            for fam in sorted({fams.get(i) for i in g} - {None})
        }
        gate[dim] = gs
        diagnostic[dim] = stats(list(d.values()))
        below_floor[dim] = sorted(i for i, v in g.items() if v < f_d)
        nulls[dim] = {
            "gate_items": sum(1 for i in gates if gates[i]) - len(g),
            "diagnostic_items": sum(1 for i in gates if not gates[i]) - len(d),
        }

    corr = {}
    for a in DIMS:
        for b in DIMS:
            common = sorted(set(gate_scores[a]) & set(gate_scores[b]))
            corr["%s~%s" % (a, b)] = pearson(
                [gate_scores[a][i] for i in common],
                [gate_scores[b][i] for i in common])

    overall = all(gate[d]["pass"] for d in DIMS)

    replication = None
    if args.compare:
        replication = {}
        for dim in DIMS:
            a = consensus(args.verdict, dim, args.coherence_seat_substr)
            b = consensus(args.compare, dim, args.coherence_seat_substr)
            common = set(a) & set(b)
            if not common:
                continue
            diffs = {i: [a[i], b[i]] for i in common if a[i] != b[i]}
            replication[dim] = {
                "n": len(common),
                "exact_pct": round(100 * sum(a[i] == b[i] for i in common) / len(common), 1),
                "within_1_pct": round(100 * sum(abs(a[i] - b[i]) <= 1 for i in common) / len(common), 1),
                "changed_cells": len(diffs),
                "changed": dict(sorted(diffs.items())),
            }

    out = {
        "schema": "key2_verdict",
        "status": "VERDICT" if overall else "FAIL",
        "date": args.date,
        "gate_rule": "per dimension: mean_d >= M_d and min_d >= F_d; no cross-dimension mean",
        "thresholds": {
            "path": args.thresholds,
            "sha256": sha256_file(args.thresholds),
            "F_d": {d: th["bands"][d]["F_d_candidate"] for d in DIMS},
            "M_d": {d: th["bands"][d]["M_d_candidate"] for d in DIMS},
            "margin": th["rule"]["margin"],
            "seat_policy": th["seat_policy"],
        },
        "inputs": {
            "prompts": {"path": args.prompts, "sha256": sha256_file(args.prompts)},
            "verdict": [{"path": p, "sha256": sha256_file(p),
                         "model": load_rows(p)[1].get("model"),
                         "system_prompt_sha256": load_rows(p)[1].get("system_prompt_sha256")}
                        for p in args.verdict],
            "generation_input_sha256": sorted(inputs),
        },
        "gate": gate,
        "diagnostic": diagnostic,
        "correlation": corr,
        "generation_diagnostics": generation_diagnostics(args.generations),
        "below_floor": below_floor,
        "nulls": nulls,
        "overall": "pass" if overall else "fail",
        "replication_vs_calibration": replication,
        "note": ("Items listed in below_floor are re-scored blind per rubric 8.5 "
                 "before the floor breach counts. The 33 argue items are "
                 "diagnostic and are not gated."),
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")

    print("gate (100 items):")
    for dim in DIMS:
        g = gate[dim]
        print("  %-10s mean %5.2f >= %4.2f %s | min %d >= %d %s | %s"
              % (dim, g["mean"], g["M_d"], "ok" if g["mean_pass"] else "FAIL",
                 g["min"], g["F_d"], "ok" if g["floor_pass"] else "FAIL",
                 "pass" if g["pass"] else "FAIL"))
    print("diagnostic (33 items):")
    for dim in DIMS:
        d = diagnostic[dim]
        print("  %-10s mean %5.2f min %d" % (dim, d["mean"], d["min"]))
    print("overall:", out["overall"])
    if replication:
        print("replication vs calibration:")
        for dim, r in replication.items():
            print("  %-10s exact %5.1f%% within1 %5.1f%% changed %d"
                  % (dim, r["exact_pct"], r["within_1_pct"], r["changed_cells"]))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
