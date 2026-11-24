"""Key-1 byte n-gram counter, restricted to the contexts the val targets need.

A full order-6 table over 2 GB is tens of GB. The gate only needs the counts for
contexts that occur at the 128 x 512 val positions, so one chunked pass over the
train bytes counts exactly those and nothing else. The estimate is exact for
those positions, with seen-context backoff 6 -> 4 -> 0 (uniform 1/256), the same
instrument as report section 18.

Usage:
  .venv/bin/python scripts/quinn/key1_ngram.py --legal --out out/host/key1_legal.json
  .venv/bin/python scripts/quinn/key1_ngram.py \
      --train data/host/fineweb_train.txt --val data/host/fineweb_val.txt \
      --out out/host/key1_ngram.json
"""

import argparse
import datetime
import hashlib
import json
import os
import sys

import numpy as np

BLOCK = 512
N_BLOCKS = 128


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def legal_carves():
    sys.path.insert(0, ".")
    from pipeline.data import _prepare_textmix
    blocks, _, _, _ = _prepare_textmix("legal:data/textmix2/legal.txt", 30)
    return (np.frombuffer(blocks["legal"]["train"], dtype=np.uint8),
            np.frombuffer(blocks["legal"]["val"], dtype=np.uint8))


def context_ids(arr, pos, order):
    cid = np.zeros(len(pos), dtype=np.uint64)
    for j in range(1, order + 1):
        cid += arr[pos - j].astype(np.uint64) << np.uint64(8 * (j - 1))
    return cid


def count_order(train, ctx_sorted, order, chunk=1 << 25):
    """Count (context -> next byte) only for the given sorted contexts."""
    k = len(ctx_sorted)
    pair_acc = np.zeros(k * 256, dtype=np.int64)
    ctx_acc = np.zeros(k, dtype=np.int64)
    n = len(train)
    for s in range(0, n, chunk):
        lo = max(s, order)
        hi = min(n, s + chunk)
        if lo >= hi:
            continue
        cid = np.zeros(hi - lo, dtype=np.uint64)
        for j in range(1, order + 1):
            cid += train[lo - j:hi - j].astype(np.uint64) << np.uint64(8 * (j - 1))
        idx = np.searchsorted(ctx_sorted, cid)
        idx = np.clip(idx, 0, k - 1)
        hit = ctx_sorted[idx] == cid
        if not hit.any():
            continue
        ci = idx[hit]
        y = train[lo:hi][hit].astype(np.int64)
        pair_acc += np.bincount(ci * 256 + y, minlength=k * 256)
        ctx_acc += np.bincount(ci, minlength=k)
    return pair_acc, ctx_acc


def lookup(ctx_sorted, pair_acc, ctx_acc, val, pos, order):
    cid = context_ids(val, pos, order)
    idx = np.searchsorted(ctx_sorted, cid)
    idx = np.clip(idx, 0, max(0, len(ctx_sorted) - 1))
    seen = ctx_sorted[idx] == cid
    total = np.where(seen, ctx_acc[idx], 0)
    pair = np.where(seen, pair_acc[idx * 256 + val[pos].astype(np.int64)], 0)
    return total, pair


def word_classes(y, prev):
    a = ((y >= 65) & (y <= 90)) | ((y >= 97) & (y <= 122))
    pa = ((prev >= 65) & (prev <= 90)) | ((prev >= 97) & (prev <= 122))
    return a & ~pa, a & pa, ~a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train")
    ap.add_argument("--val")
    ap.add_argument("--legal", action="store_true",
                    help="use the registered 28/1 MB legal carve (acceptance check)")
    ap.add_argument("--orders", default="6,4")
    ap.add_argument("--block", type=int, default=BLOCK)
    ap.add_argument("--n-blocks", type=int, default=N_BLOCKS)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    orders = [int(k) for k in args.orders.split(",")]

    if args.legal:
        train, val = legal_carves()
        train_name, val_name = "legal carve (28 MB)", "legal val (1 MB)"
    else:
        if not (args.train and args.val):
            raise SystemExit("pass --train and --val, or --legal")
        train = np.memmap(args.train, dtype=np.uint8, mode="r")
        val = np.memmap(args.val, dtype=np.uint8, mode="r")
        train_name, val_name = args.train, args.val

    if len(val) < args.block + 2:
        raise SystemExit("val carve is shorter than one block")
    offsets = np.linspace(0, len(val) - args.block - 2, args.n_blocks).astype(int)
    pos = np.concatenate([np.arange(o + 1, o + 1 + args.block) for o in offsets])
    pos_local = np.tile(np.arange(args.block), args.n_blocks)
    keep = pos >= max(orders)
    pos, pos_local = pos[keep], pos_local[keep]
    y = val[pos].astype(np.int64)
    prev = val[pos - 1].astype(np.int64)

    nll = np.full(len(pos), np.log(256.0))
    used = np.zeros(len(pos), dtype=np.int64)
    done = np.zeros(len(pos), dtype=bool)
    per_order = {}
    for order in sorted(orders, reverse=True):
        cid = context_ids(val, pos, order)
        ctx_sorted = np.unique(cid)
        pair_acc, ctx_acc = count_order(train, ctx_sorted, order)
        total, pair = lookup(ctx_sorted, pair_acc, ctx_acc, val, pos, order)
        use = (~done) & (total > 0) & (pair > 0)
        nll[use] = -np.log(pair[use] / total[use])
        used[use] = order
        done |= use
        per_order[str(order)] = {
            "val_contexts": int(len(ctx_sorted)),
            "targets_resolved": int(use.sum()),
            "share": round(float(use.mean()), 6),
            "mean_nll_on_resolved": round(float(nll[use].mean()), 6) if use.any() else None,
        }
        del pair_acc, ctx_acc, total, pair
        print(f"order {order}: {len(ctx_sorted):,} val contexts | "
              f"{use.sum():,} targets resolved ({100 * use.mean():.2f} %)")

    # Block bootstrap for the standard error of the target mean.
    block_means = np.array([nll[pos_local == p].mean() for p in range(args.block)])
    rng = np.random.default_rng(1337)
    boot = np.array([block_means[rng.integers(0, len(block_means), len(block_means))].mean()
                     for _ in range(2000)])
    curve = block_means
    s, i, o = word_classes(y, prev)
    doc = {
        "schema": "key1_ngram_v1",
        "date": datetime.date.today().isoformat(),
        "train": train_name,
        "val": val_name,
        "train_bytes": int(len(train)),
        "val_bytes": int(len(val)),
        "orders": orders,
        "block": args.block,
        "n_blocks": args.n_blocks,
        "targets": int(len(pos)),
        "mean_nll": round(float(nll.mean()), 6),
        "mean_nll_bootstrap_se": round(float(boot.std(ddof=1)), 6),
        "bootstrap_ci95": [round(float(np.percentile(boot, 2.5)), 6),
                           round(float(np.percentile(boot, 97.5)), 6)],
        "resolution": {
            "6": round(float((used == 6).mean()), 6),
            "4": round(float((used == 4).mean()), 6),
            "0": round(float((used == 0).mean()), 6),
        },
        "per_order": per_order,
        "curve": [round(float(v), 6) for v in curve],
        "head_0_63": round(float(nll[pos_local < 64].mean()), 6),
        "context_64_511": round(float(nll[pos_local >= 64].mean()), 6),
        "tail_256_511": round(float(nll[pos_local >= 256].mean()), 6),
        "word_start": round(float(nll[s].mean()), 6) if s.any() else None,
        "word_interior": round(float(nll[i].mean()), 6) if i.any() else None,
        "other": round(float(nll[o].mean()), 6) if o.any() else None,
        "source_sha256": {
            "train": sha256_file(args.train) if not args.legal else None,
            "val": sha256_file(args.val) if not args.legal else None,
        },
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print(f"mean NLL {doc['mean_nll']:.4f} nats/byte | SE {doc['mean_nll_bootstrap_se']:.5f} "
          f"| resolution 6/4/0 {doc['resolution']['6']:.3f}/{doc['resolution']['4']:.3f}/"
          f"{doc['resolution']['0']:.5f}")
    print(f"head {doc['head_0_63']:.4f} | context {doc['context_64_511']:.4f} | "
          f"tail {doc['tail_256_511']:.4f}")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
