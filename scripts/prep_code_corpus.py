#!/usr/bin/env python3
"""Prep the code domain corpus for graft #2 (third domain, design B).

Reads the CodeSearchNet python train parquet, keeps whole functions from
`func_code_string` (python-only keeps the third domain homogeneous like every
per-language domain in the campaign), shuffles with a fixed seed, joins with
blank-line separators, and writes a byte corpus of the requested size.
Prints the lineage stats (counts, bytes, sha256) for the prereg registration.

Registered filter rules (graft-2 plan prereg):
  - drop empty / short / huge functions (len in [100, 200_000] utf-8 bytes)
  - drop anything with a NUL byte or any C0 control char outside \t\n\r
  - normalize CRLF / lone CR to LF
  - exact-duplicate drop (byte-exact functions)
  - shuffle at function level, seed 0 (breaks repo clustering of the parquet
    order; keeps the val/test carve diverse)
  - join with "\\n\\n" (a blank line between functions)
"""
import argparse
import hashlib
import random
import sys

import pyarrow.parquet as pq

CONTROL_OK = frozenset("\t\n\r")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("parquet")
    ap.add_argument("out")
    ap.add_argument("--target-bytes", type=int, default=33_000_000,
                    help="written file size (loader reads the first 30 MB: "
                         "28 train + 1 val + 1 test)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--min-bytes", type=int, default=100)
    ap.add_argument("--max-bytes", type=int, default=200_000)
    args = ap.parse_args()

    table = pq.read_table(args.parquet, columns=["func_code_string"])
    fns = table.column("func_code_string").to_pylist()
    print(f"parquet: {args.parquet} | rows {len(fns):,}")

    kept, seen = [], set()
    n_drop_size = n_drop_binary = n_drop_dupe = 0
    for fn in fns:
        if fn is None:
            continue
        s = fn.replace("\r\n", "\n").replace("\r", "\n")
        if not (args.min_bytes <= len(s.encode("utf-8")) <= args.max_bytes):
            n_drop_size += 1
            continue
        if "\x00" in s or any(ord(c) < 32 and c not in CONTROL_OK for c in s):
            n_drop_binary += 1
            continue
        h = hash(s)
        if h in seen:
            n_drop_dupe += 1
            continue
        seen.add(h)
        kept.append(s)
    print(f"filter: kept {len(kept):,} | drop size {n_drop_size:,} | "
          f"drop binary/control {n_drop_binary:,} | drop exact-dupe {n_drop_dupe:,}")

    random.Random(args.seed).shuffle(kept)

    parts, total = [], 0
    for s in kept:
        parts.append(s if total == 0 else "\n\n" + s)
        total += len(parts[-1].encode("utf-8"))
        if total >= args.target_bytes:
            break
    blob = "".join(parts)
    blob_bytes = blob.encode("utf-8")

    with open(args.out, "wb") as f:
        f.write(blob_bytes)
    h = hashlib.sha256(blob_bytes).hexdigest()

    print(f"written: {args.out} | {len(blob_bytes):,} B | sha256 {h}")
    print(f"functions written: {len(parts):,} | seed {args.seed}")
    print(f"sample[0]: {parts[0][:120]!r}")
    print(f"sample[mid]: {parts[len(parts)//2][:120]!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
