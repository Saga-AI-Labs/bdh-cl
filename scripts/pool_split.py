#!/usr/bin/env python3
"""Register the pool A/B cohort split (deterministic, stratified).

Rule (README section 6 / prereg section 4.4b):
- stratify by lang x difficulty (9 strata) over the FROZEN pool file;
- within a stratum order items by
    rank = int(sha256("<SALT>|<item_id>").hexdigest()[:16], 16)   ascending;
- cohort B (40 %) takes the smallest ranks under a largest-remainder quota
  per language (56 of 140): floors floor(0.4*n) per stratum, remaining B slots
  go to the largest fractional remainders, ties alphabetical by difficulty.

The rule is registered BEFORE any cohort-A scoring. Any post-freeze item
change is set v2 and draws with its own salt ("..._split_v2").

Run:  python3 scripts/pool_split.py
Out:  data/evals/judge_set_v1/pool_split.json  (idempotent rewrite)
"""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data" / "evals" / "judge_set_v1"
POOL = BASE / "pool_instructions.json"
OUT = BASE / "pool_split.json"

LANGS = ("de", "zh", "en")
DIFFS = ("easy", "medium", "hard")
SALT = "judge_set_v1_pool_split_v1"
SOURCE_SHA = "07740b035e9a7245665d5c58df5c1f65d3e118e62d7356908b5b26e7d25d2dfe"

# Frozen-pool cell sizes the quota table was computed against; the source-hash
# assert below pins the bytes, these pin the arithmetic.
EXPECTED_CELLS = {
    "de": {"easy": 24, "medium": 66, "hard": 50},
    "zh": {"easy": 24, "medium": 67, "hard": 49},
    "en": {"easy": 24, "medium": 66, "hard": 50},
}


def rank(item_id: str) -> int:
    pre = f"{SALT}|{item_id}".encode("utf-8")
    return int(hashlib.sha256(pre).hexdigest()[:16], 16)


def strata_b_counts(lang: str, lang_cells: dict) -> dict:
    """quota 40 pct per language, floors + largest remainder, ties alphabetical."""
    quota = round(0.4 * sum(lang_cells.values()))  # 140 -> 56 exactly
    floors = {d: (2 * lang_cells[d]) // 5 for d in DIFFS}
    rems = sorted(((0.4 * lang_cells[d] - floors[d], d) for d in DIFFS),
                  key=lambda t: (-t[0], t[1]))
    pick = {d for _, d in rems[:quota - sum(floors.values())]}
    out = {d: floors[d] + (1 if d in pick else 0) for d in DIFFS}
    assert sum(out.values()) == quota, (lang, out, quota)
    return out


def main() -> None:
    raw = POOL.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == SOURCE_SHA, f"pool file is not the frozen set: {digest}"
    pool = json.loads(raw.decode("utf-8"))
    assert pool["status"] == "FROZEN", pool["status"]
    items = pool["items"]
    assert len(items) == 420, len(items)

    langs = tuple(dict.fromkeys(i["lang"] for i in items))
    assert langs == LANGS, langs
    cells = Counter((i["lang"], i["difficulty"]) for i in items)
    for lang in LANGS:
        for d in DIFFS:
            assert cells[(lang, d)] == EXPECTED_CELLS[lang][d], (lang, d)

    b_quotas = {lang: strata_b_counts(lang, {d: cells[(lang, d)] for d in DIFFS})
                for lang in LANGS}

    assignments: dict[str, str] = {}
    buckets = {(lang, d): [] for lang in LANGS for d in DIFFS}
    for it in items:
        buckets[(it["lang"], it["difficulty"])].append((rank(it["item_id"]), it["item_id"]))
    for key, rows in buckets.items():
        rows.sort()
        b = b_quotas[key[0]][key[1]]
        for _, iid in rows[:b]:
            assignments[iid] = "B"
        for _, iid in rows[b:]:
            assignments[iid] = "A"

    a_total = sum(1 for v in assignments.values() if v == "A")
    assert (a_total, len(assignments) - a_total) == (252, 168), (a_total, len(assignments))
    for lang in LANGS:
        a = sum(1 for iid, v in assignments.items()
                if v == "A" and iid[2:4] == lang)
        assert a == 84, (lang, a)

    manifest = {
        "schema": "judge_set_v1_pool_split",
        "status": "REGISTERED",
        "date": "2026-11-10",
        "source": {
            "file": "pool_instructions.json",
            "status": "FROZEN",
            "sha256": SOURCE_SHA,
        },
        "rule": {
            "name": "stratified hash-rank v1",
            "registered_before_scoring": True,
            "stratify": ["lang", "difficulty"],
            "preimage_template": SALT + "|{item_id}",
            "digest": "sha256, first 16 hex chars, parsed big-endian int",
            "quota": "cohort B = 40 pct per language (56 of 140); within a language "
                     "the strata quotas are floor(0.4*n) each plus one upgrade from "
                     "the largest fractional remainder, ties alphabetical by difficulty",
            "v2_salt": SALT.rsplit("_v1", 1)[0] + "_v2",
            "note": "IDs here are bookkeeping only; IDs never enter judge payloads "
                    "(README section 7). No judge run reads this file.",
        },
        "counts": {
            "total": 420, "A": 252, "B": 168,
            "per_language": {
                lang: {"A": 84, "B": 56, "B_per_stratum": b_quotas[lang]}
                for lang in LANGS
            },
        },
        "assignments": assignments,
    }

    payload = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    OUT.write_text(payload, encoding="utf-8")

    print("SPLIT:", f"A {a_total} / B {len(assignments) - a_total}",
          f"({a_total/420:.1%} / {(len(assignments)-a_total)/420:.1%})")
    for lang in LANGS:
        print(f"  {lang}: cells " + " / ".join(
            f"{d} {cells[(lang,d)]}" for d in DIFFS)
            + f"  ->  B " + "/".join(str(b_quotas[lang][d]) for d in DIFFS))

    # audits: report only, no repair
    dom = Counter()
    for it in items:
        dom[(assignments[it["item_id"]], it["lang"], it["domains"][0])] += 1
    print("  audit domains (first tag, A/B per language):")
    for lang in LANGS:
        row = {d: (dom[("A", lang, d)], dom[("B", lang, d)])
               for d in sorted({k[2] for k in dom if k[1] == lang})}
        print(f"    {lang}: " + "  ".join(f"{d} {a}/{b}" for d, (a, b) in row.items()))
    con = Counter()
    for it in items:
        if it["constraint"] is not None:
            con[assignments[it["item_id"]]] += 1
    print(f"  audit constrained: A {con['A']} / B {con['B']}",
          f"({con['A']/252:.1%} / {con['B']/168:.1%}; pool {sum(con.values())}/420 = {sum(con.values())/420:.1%})")
    ez = Counter()
    for it in items:
        if it["difficulty"] == "easy":
            ez[assignments[it["item_id"]]] += 1
    print(f"  audit easy floor in B: {ez['B']} ({ez['B']/168:.1%}) — floor kept in hold-out")

    print("manifest:", OUT)
    manifest_bytes = OUT.read_bytes()
    print("manifest sha256:", hashlib.sha256(manifest_bytes).hexdigest())


if __name__ == "__main__":
    main()
