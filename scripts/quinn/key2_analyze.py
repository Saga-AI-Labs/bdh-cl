#!/usr/bin/env python3
"""Key 2 calibration analysis: reference bands, M_d/F_d, agreement.

Reads judge outputs from `key2_judge.py` (one JSON per judge and band) and
computes the numbers section 8.3 needs before G0:

  - positive band (cert `good`@256) and the per-dimension negative bands
    (coherence: 3.62B salad; language: language-broken subset; relevance:
    off-topic control): mean, min, max, 10th percentile;
  - consensus per item = min of the two judges (the note's conservative rule);
  - F_d candidate = negative max + 1, strict alternative = positive min;
  - M_d candidate = positive mean - margin, with 0.3/0.5/0.7 sensitivities;
  - scale-set means per variant, to test that key 2 does not import 4.4b
    correctness (short_correct and fluent-wrong controls stay high on
    language/coherence);
  - inter-judge exact and +/-1 agreement per dimension;
  - NULL rate per judge against the registered 5 % cap;
  - sensitivity excluding the four format-constrained cert items.

This script does not freeze anything. It writes a candidate JSON; the operator
chooses the margin and signs off.

Usage:
    .venv/bin/python scripts/quinn/key2_analyze.py \
        --positive out/key2_calibration/qwen_positive.json \
        --positive out/key2_calibration/gemma_positive.json \
        --negative-coherence out/key2_calibration/qwen_negative.json \
        --negative-coherence out/key2_calibration/gemma_negative.json \
        --negative-language out/key2_calibration/qwen_langbroken.json \
        --negative-language out/key2_calibration/gemma_langbroken.json \
        --negative-relevance out/key2_calibration/qwen_offtopic.json \
        --negative-relevance out/key2_calibration/gemma_offtopic.json \
        --scale out/key2_calibration/qwen_scale.json \
        --scale out/key2_calibration/gemma_scale.json \
        --out out/key2_calibration/thresholds_candidate.json

If a dimension-specific band is omitted, --negative is used for it.
"""

import argparse
import hashlib
import json
import os
import statistics as st

DIMS = ("coherence", "relevance", "language")
FORMAT_IDS = ("cert_en05", "cert_en09", "cert_en10", "cert_en16")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    d = json.load(open(path))
    return {r["id"]: r for r in d.get("rows", [])}, d.get("meta", {})


def values(rows, dim, ids=None):
    out = []
    for rid, r in rows.items():
        if ids is not None and rid not in ids:
            continue
        v = r.get(dim)
        if isinstance(v, int) and 1 <= v <= 5:
            out.append(v)
    return out


def stats(vals):
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    return {
        "n": len(vals),
        "mean": round(st.mean(vals), 3),
        "min": min(vals),
        "max": max(vals),
        "p10": s[max(0, int(round(0.10 * (len(s) - 1))))],
        "median": st.median(vals),
    }


def consensus(files, ids=None):
    """Per-item min across judge files; requires the same ids in every file."""
    maps = []
    for path in files:
        m, _ = load(path)
        maps.append(m)
    common = set(maps[0])
    for m in maps[1:]:
        common &= set(m)
    if ids is not None:
        common &= set(ids)
    out = {}
    for rid in common:
        out[rid] = {}
        for dim in DIMS:
            vals = [m[rid][dim] for m in maps
                    if isinstance(m[rid].get(dim), int)]
            out[rid][dim] = min(vals) if vals else None
    return out


def agreement(files):
    """Pairwise exact and +/-1 agreement over the common scored ids."""
    if len(files) < 2:
        return {}
    maps = [load(p)[0] for p in files]
    common = set(maps[0])
    for m in maps[1:]:
        common &= set(m)
    out = {}
    for dim in DIMS:
        pairs = []
        for rid in common:
            vals = [m[rid].get(dim) for m in maps]
            if all(isinstance(v, int) for v in vals):
                pairs.append(vals)
        if not pairs:
            out[dim] = {"n": 0}
            continue
        exact = sum(1 for v in pairs if max(v) == min(v))
        within1 = sum(1 for v in pairs if max(v) - min(v) <= 1)
        out[dim] = {
            "n": len(pairs),
            "exact_pct": round(100.0 * exact / len(pairs), 1),
            "within_1_pct": round(100.0 * within1 / len(pairs), 1),
        }
    return out


def null_report(files):
    """NULL rate per judge and dimension against the registered 5 % cap."""
    per_judge = []
    worst = 0.0
    for path in files:
        m, _ = load(path)
        counts = {}
        pct = {}
        for dim in DIMS:
            k = sum(1 for r in m.values() if not isinstance(r.get(dim), int))
            counts[dim] = k
            p = 100.0 * k / len(m) if m else 100.0
            pct[dim] = round(p, 1)
            worst = max(worst, p)
        per_judge.append({"path": path, "rows": len(m),
                          "nulls": counts, "null_pct": pct})
    return {
        "threshold_pct": 5.0,
        "worst_pct": round(worst, 1),
        "status": ("not-scoreable-repeat" if worst > 5.0
                   else "nulls-not-evaluable"),
        "per_judge": per_judge,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--positive", action="append", required=True,
                    help="judge JSON for the positive band (repeat per judge)")
    ap.add_argument("--negative", action="append", default=[],
                    help="default negative band, used for every dimension that "
                         "has no specific override (repeat per judge)")
    ap.add_argument("--negative-coherence", action="append", default=[],
                    help="judge JSON for the coherence negative band")
    ap.add_argument("--negative-language", action="append", default=[],
                    help="judge JSON for the language negative band")
    ap.add_argument("--negative-relevance", action="append", default=[],
                    help="judge JSON for the relevance negative band")
    ap.add_argument("--scale", action="append", default=[],
                    help="judge JSON for the 108-row scale set (repeat per judge)")
    ap.add_argument("--coherence-seat-substr", default="",
                    help="restrict the coherence band to band files whose path "
                         "contains this substring, implementing per-dimension "
                         "seat authority (default: min of every supplied judge)")
    ap.add_argument("--out", default="out/key2_calibration/thresholds_candidate.json")
    ap.add_argument("--margin", type=float, default=0.5)
    ap.add_argument("--format-ids", default=",".join(FORMAT_IDS))
    args = ap.parse_args()

    format_ids = {x.strip() for x in args.format_ids.split(",") if x.strip()}
    neg_files = {
        "coherence": args.negative_coherence or args.negative,
        "language": args.negative_language or args.negative,
        "relevance": args.negative_relevance or args.negative,
    }
    missing = [d for d, files in neg_files.items() if not files]
    if missing:
        raise SystemExit("no negative band for %s; pass --negative or the "
                         "dimension-specific flag" % ", ".join(missing))
    def seat_files(files):
        """Per-dimension seat authority: keep only the authoritative seat."""
        if not args.coherence_seat_substr:
            return files
        keep = [f for f in files if args.coherence_seat_substr in f]
        if not keep:
            raise SystemExit("no coherence-band file matches %r"
                             % args.coherence_seat_substr)
        return keep

    pos = consensus(args.positive)
    pos_coh = consensus(seat_files(args.positive))
    neg_files["coherence"] = seat_files(neg_files["coherence"])
    neg_by_dim = {dim: consensus(files) for dim, files in neg_files.items()}
    pos_by_dim = {dim: pos for dim in DIMS}
    pos_by_dim["coherence"] = pos_coh

    bands = {}
    sensitivity = {}
    for dim in DIMS:
        neg = neg_by_dim[dim]
        pos_rows = pos_by_dim[dim]
        pv = [r[dim] for r in pos_rows.values() if isinstance(r.get(dim), int)]
        nv = [r[dim] for r in neg.values() if isinstance(r.get(dim), int)]
        p, n = stats(pv), stats(nv)
        if p["n"] and n["n"]:
            gap = p["min"] - n["max"]
            # lower separation: first integer above the negative band;
            # strict alternative: the positive minimum itself.
            floor = n["max"] + 1 if gap >= 1 else None
            floor_strict = p["min"] if gap >= 1 else None
            mean_candidates = {
                str(m): round(p["mean"] - m, 2) for m in (0.3, 0.5, 0.7)
            }
            bands[dim] = {
                "positive": p, "negative": n, "gap_min_minus_max": gap,
                "F_d_candidate": floor,
                "F_d_strict": floor_strict,
                "M_d_candidate": round(p["mean"] - args.margin, 2),
                "M_d_by_margin": mean_candidates,
                "overlap": gap < 1,
            }
        else:
            bands[dim] = {"positive": p, "negative": n,
                          "F_d_candidate": None, "M_d_candidate": None,
                          "overlap": True}

        # sensitivity: drop the format-constrained positive items
        pv2 = [r[dim] for rid, r in pos_by_dim[dim].items()
               if isinstance(r.get(dim), int)
               and not any(rid.endswith(x) or x in rid for x in format_ids)]
        p2 = stats(pv2)
        if p2.get("n") and n.get("n"):
            gap2 = p2["min"] - n["max"]
            sensitivity[dim] = {
                "positive_without_format": p2,
                "F_d_candidate": n["max"] + 1 if gap2 >= 1 else None,
                "F_d_strict": p2["min"] if gap2 >= 1 else None,
                "M_d_candidate": round(p2["mean"] - args.margin, 2),
                "gap_min_minus_max": gap2,
            }

    scale = {}
    if args.scale:
        smaps = [load(p)[0] for p in args.scale]
        common = set(smaps[0])
        for m in smaps[1:]:
            common &= set(m)
        by_variant = {}
        for rid in common:
            lab = smaps[0][rid].get("label")
            if not lab:
                continue
            by_variant.setdefault(lab, {d: [] for d in DIMS})
            for dim in DIMS:
                vals = [m[rid].get(dim) for m in smaps]
                if all(isinstance(v, int) for v in vals):
                    by_variant[lab][dim].append(min(vals))
        for lab, dims in by_variant.items():
            scale[lab] = {dim: stats(vals) for dim, vals in dims.items()}

    out = {
        "schema": "key2_thresholds",
        "status": "CANDIDATE",
        "date": "2026-11-20",
        "inputs": {
            "positive": [{"path": p, "sha256": sha256_file(p)} for p in args.positive],
            "negative": {dim: [{"path": p, "sha256": sha256_file(p)}
                               for p in files]
                         for dim, files in neg_files.items()},
            "scale": [{"path": p, "sha256": sha256_file(p)} for p in args.scale],
        },
        "rule": {
            "consensus": "min of the judges per item and dimension",
            "F_d": "negative max + 1 when positive min > negative max; null on overlap",
            "F_d_strict": "positive min only, when positive min > negative max",
            "M_d": "positive mean - margin; margin 0.5 default",
            "margin": args.margin,
        },
        "bands": bands,
        "sensitivity_excluding_format": sensitivity,
        "scale": scale,
        "seat_policy": {
            "coherence": {
                "mode": ("single-seat" if args.coherence_seat_substr
                         else "min-of-two"),
                "files": [{"path": p, "sha256": sha256_file(p)}
                          for p in seat_files(args.positive)],
                "deviation": (
                    "coherence has one effective seat; registered deviation per "
                    "docs/notes/2026-11-23_key2-instrument-gate-failure.md"
                    if args.coherence_seat_substr else None),
            },
            "relevance": {"mode": "min-of-two"},
            "language": {"mode": "min-of-two"},
        },
        "agreement": {
            "positive": agreement(args.positive),
            "negative": {dim: agreement(files)
                         for dim, files in neg_files.items()},
            "scale": agreement(args.scale) if args.scale else {},
        },
        "nulls": {
            "positive": {dim: sum(1 for r in pos.values()
                                   if not isinstance(r.get(dim), int))
                         for dim in DIMS},
            "negative": {dim: sum(1 for r in neg_by_dim[dim].values()
                                   if not isinstance(r.get(dim), int))
                         for dim in DIMS},
        },
        "null_cap": {
            "positive": null_report(args.positive),
            "negative": {dim: null_report(files)
                         for dim, files in neg_files.items()},
            "scale": null_report(args.scale) if args.scale else {},
        },
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({"out": args.out, "bands": bands,
                      "agreement": out["agreement"]}, indent=2))


if __name__ == "__main__":
    main()
