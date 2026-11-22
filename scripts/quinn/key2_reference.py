#!/usr/bin/env python3
"""Derive the key-2 reference bands from judge_set_v1.

The operator pointed at `data/evals/judge_set_v1/` as the reference
(2026-11-20). The certified set is instruction-response with gold labels, not
free generation. This script keeps the two uses separate:

  scale      18 English cert items x 6 variants, full length. Used to check the
             judges' 1-5 scale and the dimension separation; it is not a key-2
             prompt pool and its labels are not key-2 gold.
  positive   the 18 English `good` variants, truncated at a word boundary to
             256 B. This is the positive band for M_d/F_d; it is a proxy for
             on-prompt human answers, not a replacement in kind.
  negative   produced by `key2_generate.py` from the 3.62B checkpoint on the
             133-prompt set; section-16 salad is added at scoring time.

The script is read-only on `data/evals/judge_set_v1/`. It writes derived rows
and a manifest under `out/key2_calibration/` by default.

Usage:
    .venv/bin/python scripts/quinn/key2_reference.py
    .venv/bin/python scripts/quinn/key2_reference.py --out-dir out/key2_calibration
"""

import argparse
import hashlib
import json
import os
import statistics as st

CERT = "data/evals/judge_set_v1/cert_items_merged.json"
STAGE1 = "data/evals/judge_set_v1/cert_items.json"
STAGE2 = "data/evals/judge_set_v1/cert_items_stage2.json"
PROMPTS = "data/evals/key2_prompts_v1.json"
LABELS = ("good", "short_correct", "long_wrong", "planted_error",
          "audience_violation", "bad")
SAMPLE_BYTES = 256


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def truncate_words(text, limit=SAMPLE_BYTES):
    """Longest prefix <= limit bytes ending on a word boundary.

    ASCII reference text only; for non-ASCII this still cuts before the last
    space, and the caller records the exact bytes.
    """
    b = text.encode("utf-8")
    if len(b) <= limit:
        return b, False
    cut = b[:limit]
    k = cut.rfind(b" ")
    if k > 0:
        cut = cut[:k]
    return cut, True


def load_items(path):
    d = json.load(open(path))
    return d["items"], d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="out/key2_calibration")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    items, cert_doc = load_items(CERT)
    stage1, _ = load_items(STAGE1)
    stage2, _ = load_items(STAGE2)
    stage1_en = {i["item_id"] for i in stage1 if i["lang"] == "en"}
    stage2_en = {i["item_id"] for i in stage2 if i["lang"] == "en"}
    en = [i for i in items if i["lang"] == "en"]
    assert len(en) == 18, "expected 18 English cert items, got %d" % len(en)
    assert len(stage1_en) == 10 and len(stage2_en) == 8, "stage split changed"
    assert set(stage1_en) | set(stage2_en) == {i["item_id"] for i in en}

    scale_rows = []
    positive_rows = []
    per_item = []
    for it in en:
        by_label = {v["label"]: v for v in it["variants"]}
        missing = [lab for lab in LABELS if lab not in by_label]
        assert not missing, "%s missing variants %s" % (it["item_id"], missing)
        good = by_label["good"]["text"]
        good_b, truncated = truncate_words(good)
        positive_rows.append({
            "id": "cert_pos_" + it["item_id"],
            "item_id": it["item_id"],
            "stage": 1 if it["item_id"] in stage1_en else 2,
            "instruction": it["instruction"],
            "instruction_bytes": len(it["instruction"].encode("utf-8")),
            "constraint": it.get("constraint"),
            "prompt_sha256": sha256_text(it["instruction"]),
            "answer_full_bytes": len(good.encode("utf-8")),
            "answer": good_b.decode("utf-8"),
            "answer_bytes": len(good_b),
            "answer_sha256": hashlib.sha256(good_b).hexdigest(),
            "truncated": truncated,
            "label": "good",
        })
        for lab in LABELS:
            text = by_label[lab]["text"]
            b = text.encode("utf-8")
            scale_rows.append({
                "id": "%s_%s" % (it["item_id"], lab),
                "item_id": it["item_id"],
                "stage": 1 if it["item_id"] in stage1_en else 2,
                "instruction": it["instruction"],
                "prompt_sha256": sha256_text(it["instruction"]),
                "constraint": it.get("constraint"),
                "variant": lab,
                "answer": text,
                "answer_bytes": len(b),
                "answer_sha256": hashlib.sha256(b).hexdigest(),
            })
        per_item.append({
            "item_id": it["item_id"],
            "stage": 1 if it["item_id"] in stage1_en else 2,
            "good_full_bytes": len(good.encode("utf-8")),
            "good_256_bytes": len(good_b),
            "truncated": truncated,
            "constraint_type": (it.get("constraint") or {}).get("type"),
            "instruction_bytes": len(it["instruction"].encode("utf-8")),
        })

    def write_jsonl(path, rows):
        with open(path, "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    scale_path = os.path.join(args.out_dir, "reference_scale.jsonl")
    positive_path = os.path.join(args.out_dir, "reference_positive.jsonl")
    manifest_path = os.path.join(args.out_dir, "reference_manifest.json")
    write_jsonl(scale_path, scale_rows)
    write_jsonl(positive_path, positive_rows)

    lens_full = [r["good_full_bytes"] for r in per_item]
    lens_256 = [r["good_256_bytes"] for r in per_item]
    fmt = [r for r in per_item if r["constraint_type"] == "format"]
    manifest = {
        "schema": "key2_reference",
        "version": "v1-draft",
        "status": "DRAFT",
        "date": "2026-11-20",
        "source": {
            "cert": CERT,
            "cert_sha256": sha256_file(CERT),
            "cert_status": cert_doc.get("status"),
            "stage1": STAGE1,
            "stage1_sha256": sha256_file(STAGE1),
            "stage2": STAGE2,
            "stage2_sha256": sha256_file(STAGE2),
            "prompts": PROMPTS,
            "prompts_sha256": sha256_file(PROMPTS),
        },
        "selection": {
            "language": "en",
            "items": len(en),
            "stage1": len(stage1_en),
            "stage2": len(stage2_en),
            "scale_rows": len(scale_rows),
            "positive_rows": len(positive_rows),
            "labels": list(LABELS),
        },
        "positive_band": {
            "rule": "good variant, longest prefix <= 256 B ending on a word boundary",
            "sample_bytes": SAMPLE_BYTES,
            "full_bytes": {
                "min": min(lens_full), "median": st.median(lens_full),
                "max": max(lens_full), "le_256": sum(x <= SAMPLE_BYTES for x in lens_full),
            },
            "band_bytes": {
                "min": min(lens_256), "median": st.median(lens_256),
                "max": max(lens_256),
            },
            "format_constrained_items": [r["item_id"] for r in fmt],
            "sensitivity": "report M_d with and without the format-constrained items",
        },
        "role": {
            "scale": "judge scale and dimension separation only; not key-2 gold",
            "positive": "proxy positive band for M_d/F_d; instruction-response, not free generation",
            "negative": "3.62B generations from key2_generate.py plus section-16 salad",
        },
        "caveats": [
            "The cert set has 18 English items, not 20; the merged set is 18 en / 24 de / 18 zh.",
            "The good variants are authored/reviewed reference answers, not human free generations.",
            "The instructions are up to 195 B; the 128-B cap applies to the key-2 generation prompts, not to the judge calibration prompt.",
            "The 256-B prefix may end mid-sentence; the judge prompt must say so.",
            "A wrong-but-fluent cert answer can score high on key-2 dimensions; cert labels are not key-2 gold.",
        ],
        "files": {
            "scale": scale_path,
            "positive": positive_path,
        },
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(json.dumps({
        "cert_sha256": manifest["source"]["cert_sha256"],
        "items": len(en),
        "stage1": len(stage1_en),
        "stage2": len(stage2_en),
        "scale_rows": len(scale_rows),
        "positive_rows": len(positive_rows),
        "full_bytes": manifest["positive_band"]["full_bytes"],
        "band_bytes": manifest["positive_band"]["band_bytes"],
        "format_constrained": manifest["positive_band"]["format_constrained_items"],
        "scale_path": scale_path,
        "positive_path": positive_path,
        "manifest_path": manifest_path,
    }, indent=2))


if __name__ == "__main__":
    main()
