"""Build the host corpus from the FineWeb-Edu sample-10BT parquet shards.

Two stages, both deterministic:

  duplicates  Hash every document (id and text) and report the exact-duplicate
              share over the full corpus. Nothing is written except the report.
  carve       Deduplicate globally, split by document hash, apply the decimal-MB
              caps, and write train/val/test byte files plus a manifest.

The split is document-level and content-deduplicated: a text that appears twice
cannot land in two splits, and the cap is applied to distinct bytes.

Usage:
  .venv/bin/python scripts/quinn/build_host_corpus.py --stage duplicates
  .venv/bin/python scripts/quinn/build_host_corpus.py --stage all
"""

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

import pyarrow.parquet as pq

SHARDS = [
    "out/fineweb_edu_probe/sample/10BT/000_00000.parquet",
    "out/fineweb_edu_probe/sample/10BT/001_00000.parquet",
    "out/fineweb_edu_probe/sample/10BT/013_00000.parquet",
]
OUT_DIR = "data/host"
CAPS = {"train": 2_000_000_000, "val": 8_000_000, "test": 8_000_000}
SEP = b"\n\n"


def sha256_bytes(b):
    return hashlib.sha256(b).digest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_docs(shards):
    """Yield (shard_index, row_group, row_in_group, id, text_bytes)."""
    for si, path in enumerate(shards):
        pf = pq.ParquetFile(path)
        for rg in range(pf.num_row_groups):
            table = pf.read_row_group(rg, columns=["id", "text"])
            ids = table.column("id").to_pylist()
            texts = table.column("text").to_pylist()
            for i, (doc_id, text) in enumerate(zip(ids, texts)):
                if not isinstance(text, str):
                    text = str(text)
                yield si, rg, i, doc_id, text.encode("utf-8")


def scan(shards):
    """Pass 1: one record per document, sorted by document hash.

    Record: (h, content_hash, gidx, shard, row_group, row, nbytes).
    """
    recs = []
    total_bytes = 0
    for gidx, (si, rg, i, doc_id, b) in enumerate(iter_docs(shards)):
        h = int.from_bytes(hashlib.sha256(doc_id.encode("utf-8")).digest()[:8], "big")
        recs.append((h, sha256_bytes(b), gidx, si, rg, i, len(b)))
        total_bytes += len(b)
    recs.sort(key=lambda r: r[0])
    return recs, total_bytes


def dedupe(recs):
    """Return (distinct_bytes, report, keep_set) over hash order.

    keep_set holds the content hashes of the first occurrence; every later
    occurrence is a duplicate.
    """
    seen = {}
    dups = 0
    dup_bytes = 0
    groups = {}
    for h, ch, gidx, si, rg, i, n in recs:
        if ch in seen:
            dups += 1
            dup_bytes += n
            groups[ch] = groups.get(ch, 0) + 1
        else:
            seen[ch] = n
    distinct_bytes = sum(seen.values())
    largest = max(groups.values(), default=1)
    report = {
        "method": "sha256(text); first occurrence in ascending document hash wins",
        "documents_total": len(recs),
        "bytes_total": sum(r[6] for r in recs),
        "documents_distinct": len(seen),
        "bytes_distinct": distinct_bytes,
        "duplicate_documents": dups,
        "duplicate_bytes": dup_bytes,
        "duplicate_share_docs": round(dups / len(recs), 6) if recs else 0.0,
        "duplicate_share_bytes": round(dup_bytes / max(1, sum(r[6] for r in recs)), 6),
        "largest_duplicate_group": largest,
        "unique_bytes_gb": round(distinct_bytes / 1e9, 3),
    }
    return distinct_bytes, report, set(seen)


def carve(recs, distinct_bytes):
    """Select documents in hash order, split by h % 1000, apply decimal caps."""
    if distinct_bytes < CAPS["train"]:
        raise SystemExit(
            "distinct bytes %d < train cap %d: the corpus is smaller than the "
            "plan assumes; stop and decide with the operator"
            % (distinct_bytes, CAPS["train"]))
    emitted = set()
    sizes = {k: 0 for k in CAPS}
    sel = {}
    counts = {k: 0 for k in CAPS}
    meta = {k: {"first_h": None, "last_h": None} for k in CAPS}
    for h, ch, gidx, si, rg, i, n in recs:
        if ch in emitted:
            continue
        emitted.add(ch)
        bucket = h % 1000
        if bucket < 5:
            split = "val"
        elif bucket < 10:
            split = "test"
        else:
            split = "train"
        need = n + (len(SEP) if counts[split] else 0)
        if sizes[split] + need > CAPS[split]:
            continue
        sel[gidx] = (split, counts[split])
        counts[split] += 1
        sizes[split] += need
        if meta[split]["first_h"] is None:
            meta[split]["first_h"] = h
        meta[split]["last_h"] = h
    return sel, sizes, counts, meta


def write_splits(sel, shards, meta):
    parts = {k: {} for k in CAPS}
    for gidx, (si, rg, i, doc_id, b) in enumerate(iter_docs(shards)):
        hit = sel.get(gidx)
        if hit is None:
            continue
        split, rank = hit
        parts[split][rank] = b
    os.makedirs(OUT_DIR, exist_ok=True)
    out = {}
    for split, n in (("train", len(parts["train"])), ("val", len(parts["val"])),
                     ("test", len(parts["test"]))):
        missing = [r for r in range(n) if r not in parts[split]]
        if missing:
            raise SystemExit(f"{split}: {len(missing)} selected documents were not re-read")
        blob = SEP.join(parts[split][r] for r in range(n))
        path = os.path.join(OUT_DIR, f"fineweb_{split}.txt")
        with open(path, "wb") as f:
            f.write(blob)
        out[split] = {"path": path, "documents": n, "bytes": len(blob),
                      "sha256": hashlib.sha256(blob).hexdigest(),
                      "first_h": str(meta[split]["first_h"]),
                      "last_h": str(meta[split]["last_h"])}
        print(f"{split}: {n:,} docs | {len(blob):,} B | {out[split]['sha256'][:16]}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("duplicates", "all"), default="all")
    ap.add_argument("--shards", nargs="*", default=SHARDS)
    args = ap.parse_args()

    print("pass 1: hashing every document ...")
    recs, total_bytes = scan(args.shards)
    distinct_bytes, report, keep = dedupe(recs)
    print(json.dumps({k: v for k, v in report.items() if k != "method"}, indent=1))
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "duplicates.json"), "w") as f:
        json.dump(report, f, indent=1)
        f.write("\n")
    if args.stage == "duplicates":
        print("wrote", os.path.join(OUT_DIR, "duplicates.json"))
        return

    print("pass 2: carving ...")
    sel, sizes, counts, meta = carve(recs, distinct_bytes)
    splits = write_splits(sel, args.shards, meta)
    manifest = {
        "schema": "host_carve_v1",
        "date": datetime.date.today().isoformat(),
        "builder": "scripts/quinn/build_host_corpus.py",
        "builder_sha256": sha256_file(__file__),
        "git_sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                  text=True).stdout.strip(),
        "source": {
            "dataset": "HuggingFaceFW/fineweb-edu",
            "config": "sample-10BT",
            "files": [{"path": p, "bytes": os.path.getsize(p), "sha256": sha256_file(p)}
                      for p in args.shards],
        },
        "dedupe": report,
        "carve": {
            "unit": "one distinct document, UTF-8 bytes, joined with \\n\\n",
            "hash": "h = big-endian integer of sha256(id)[:8]",
            "buckets": "h % 1000 in [0,5) val, [5,10) test, else train",
            "order": "ascending h",
            "cap_unit": "decimal MB (1 MB = 1,000,000 bytes)",
            "caps_bytes": CAPS,
            "duplicate_policy": "drop later occurrences globally, before the split",
        },
        "splits": splits,
        "totals": {"documents_scanned": len(recs), "bytes_scanned": total_bytes,
                   "documents_distinct": report["documents_distinct"],
                   "bytes_distinct": distinct_bytes},
    }
    path = os.path.join(OUT_DIR, "carve_manifest.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")
    print("wrote", path)
    print("sizes:", sizes)
    print("counts:", counts)


if __name__ == "__main__":
    sys.exit(main())
