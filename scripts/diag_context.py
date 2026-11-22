"""Context diagnostics - three no-training controls (review 2026-11-18).

Question: is the word salad "too little language seen" (coverage) or
"cannot use context" (architecture/training)? Controls, all inference-only
on the existing checkpoints:

  1. Per-position NLL in the 512-B block. A model that uses context shows
     a falling curve well past position 64; a curve flat from ~64 means
     the block tail adds nothing.
  2. Byte n-gram baseline (seen-context backoff, no discounting) on the
     SAME val carve. If the network at ~1.11 nats sits only just below an
     order-6 n-gram, "statistics of statistics" is literal.
  3. Word-start vs word-interior NLL. Low interior loss with high
     word-start loss = vocabulary without syntax.

Instruments (diagnostic, NOT comparable to the fullcov b4 verdict series):
legal carve from _prepare_textmix("legal:data/textmix2/legal.txt", 30)
(28/1/1 MB); 128 evenly spaced 512-B offsets across the 1 MB val split;
batch 1; no_grad; collect_state=False. Masks as gen_serve_check: mult-896
keeps [0, 57344) neurons/head (the zh base, registered legal 1.66/1.71),
mult-1024 keeps [0, 65536) (the frozen P3 path, registered legal
1.1178/1.1250 and S1-identical to the parent full model).

n-gram: order-k tables counted on the 28-MB train carve; evaluation uses
the last <=k bytes of the val stream as context (may cross a block start
by <=7 bytes; registered), seen-context backoff k -> 0, uniform 1/256
fallback, no discounting.

Usage:
  python scripts/diag_context.py ngram [--orders 4,6]
  python scripts/diag_context.py positions <ckpt> --masks 896,1024 \
      [--blocks 128] [--block-size 512]
  python scripts/diag_context.py compare

Artifacts (out/, gitignored): diag_ngram.npz and diag_positions_<mask>.npz
carry the full per-position curves, class NLLs and class counts; the compare
mode joins them.
"""
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, ".")

from pipeline.data import _prepare_textmix

LEGAL = "legal:data/textmix2/legal.txt"


def word_classes(y: np.ndarray, prev: np.ndarray):
    """start = ASCII letter whose predecessor is not a letter; inter = letter
    after a letter; other = everything else. Targets are the 'current' bytes."""
    a = ((y >= 65) & (y <= 90)) | ((y >= 97) & (y <= 122))
    pa = ((prev >= 65) & (prev <= 90)) | ((prev >= 97) & (prev <= 122))
    return a & ~pa, a & pa, ~a


def load_carves():
    blocks, _, _, _ = _prepare_textmix(LEGAL, 30)
    # _prepare_textmix returns raw bytes; the n-gram tables need uint8 arrays
    return (np.frombuffer(blocks["legal"]["train"], dtype=np.uint8),
            np.frombuffer(blocks["legal"]["val"], dtype=np.uint8))


# ---------------------------------------------------------------- n-gram ---

def build_tables(arr: np.ndarray, orders):
    ctx = np.zeros(len(arr), dtype=np.uint64)
    tables = {}
    for k in orders:
        # context id over the last k bytes, built incrementally
        for j in range(1, k + 1):
            if j == 1:
                ctx[:] = 0
            ctx[k:] += arr[k - j : len(arr) - j].astype(np.uint64) << np.uint64(8 * (j - 1))
        ctx_end = len(arr) - 1
        pair = (ctx[k:ctx_end] << np.uint64(8)) | arr[k:ctx_end].astype(np.uint64)
        up, counts = np.unique(pair, return_counts=True)
        cids = up >> np.uint64(8)
        uctx, starts = np.unique(cids, return_index=True)
        ctx_tot = np.add.reduceat(counts, starts)
        tables[k] = (up, counts, uctx, ctx_tot)
        print(f"ngram order {k}: {len(up):,} observed pairs, "
              f"{len(ctx_tot):,} distinct contexts")
    return tables


def ngram_nll(val: np.ndarray, pos, tables):
    """NLL at the given stream target positions; context from the val stream
    with seen-context backoff to order 0 (uniform 1/256). Callers must pass
    pos >= max(order)."""
    y = val[pos].astype(np.uint64)
    prev = val[pos - 1].astype(np.int64)
    nll = np.full(len(pos), np.log(256.0))
    order = np.zeros(len(pos), dtype=np.int64)  # 0 = uniform fallback
    done = np.zeros(len(pos), dtype=bool)
    cid_cache = {}
    for k in sorted(tables, reverse=True):
        # context ids for each order, slicing back from pos
        if k not in cid_cache:
            cid = np.zeros(len(pos), dtype=np.uint64)
            for j in range(1, k + 1):
                cid += val[pos - j].astype(np.uint64) << np.uint64(8 * (j - 1))
            cid_cache[k] = cid
        cid = cid_cache[k]
        up, counts, uctx, ctx_tot = tables[k]
        pair = (cid << np.uint64(8)) | y
        # context seen?
        ci = np.searchsorted(uctx, cid)
        ci = np.clip(ci, 0, len(uctx) - 1)
        seen_ctx = uctx[ci] == cid
        pi = np.searchsorted(up, pair)
        pi = np.clip(pi, 0, len(up) - 1)
        seen_pair = up[pi] == pair
        m = ~done & seen_ctx & seen_pair
        nll[m] = -np.log(counts[pi[m]] / ctx_tot[ci[m]])
        order[m] = k
        done |= m
    return nll, y, prev, order


def run_ngram(orders):
    train, val = load_carves()
    tables = build_tables(train, orders)
    # same offsets as the positions control (registered: 128 evenly spaced)
    n_blocks, block_size = 128, 512
    offsets = np.linspace(0, len(val) - block_size - 2, n_blocks).astype(int)
    pos = np.concatenate([np.arange(o + 1, o + 1 + block_size) for o in offsets])
    block_of = np.repeat(offsets, block_size)
    keep = pos >= max(tables)
    pos, block_of = pos[keep], block_of[keep]
    nll, y, prev, order = ngram_nll(val, pos, tables)
    s, i, o = word_classes(y.astype(np.int64), prev.astype(np.int64))
    print(f"\nngram | legal val carve | {n_blocks} x {block_size} targets "
          f"| seen-context backoff")
    print(f"  mean NLL {nll.mean():.4f} nats/byte")
    for k in sorted(tables, reverse=True) + [0]:
        m = order == k
        if m.any():
            label = f"order {k}" if k else "uniform fallback"
            print(f"  resolved at {label:16s} n={m.sum():7,} "
                  f"({100 * m.mean():5.1f} %)  {nll[m].mean():.4f} nats/byte")
    for name, m in (("word-start", s), ("word-interior", i), ("other", o)):
        print(f"  {name:14s} {nll[m].mean():.4f} nats/byte  (n={m.sum():,})")
    cls_names = ["word-start", "word-interior", "other"]
    cls_masks = [s, i, o]
    cls_nll = np.array([nll[m].mean() for m in cls_masks])
    cls_cnt = np.array([int(m.sum()) for m in cls_masks])
    # per-position curve, same shape as the network control
    p_idx = pos - block_of - 1
    sums = np.bincount(p_idx, weights=nll, minlength=block_size)
    cnts = np.bincount(p_idx, minlength=block_size)
    curve = sums / np.maximum(cnts, 1)
    show = [0, 1, 2, 4, 8, 16, 32, 48, 64, 96, 128, 192, 256, 320, 384, 448, 511]
    print("  pos : " + " ".join(f"{p:>6d}" for p in show))
    print("  nll : " + " ".join(f"{curve[p]:6.3f}" for p in show))
    print(f"  head (0-63) {curve[:64].mean():.4f} | "
          f"context (64-511) {curve[64:].mean():.4f} | "
          f"tail (256-511) {curve[256:].mean():.4f}")
    out = "out/routed_probe/diag_ngram.npz"
    np.savez(out, curve=curve, nll=nll, order=order, pos=pos,
             offsets=offsets, classes=cls_names, cls_nll=cls_nll,
             cls_cnt=cls_cnt)
    print(f"  saved {out}")


# ------------------------------------------------------------- positions ---

def build_masks(model, mults):
    C = model.config
    nh, D = C.n_head, C.n_embd
    N = C.mlp_internal_dim_multiplier * D // nh
    dtype = next(model.parameters()).dtype
    out = {}
    for mult in mults:
        keep = mult * D // nh
        if 0 < keep < N:
            m = torch.zeros(N, dtype=dtype)
            m[:keep] = 1.0
            out[mult] = m
        elif keep >= N:
            out[mult] = None
        else:
            print(f"mask mult {mult}: not applicable (keep {keep} of {N})")
    return out


@torch.no_grad()
def run_positions(ckpt, mults, n_blocks, block_size):
    from pipeline.merge import load_model_mmap
    device = torch.device("cuda")
    model, _ = load_model_mmap(ckpt)
    model = model.to(device).eval()
    masks = {k: (v.to(device) if v is not None else None)
             for k, v in build_masks(model, mults).items()}

    _, val = load_carves()
    offsets = np.linspace(0, len(val) - block_size - 2, n_blocks).astype(int)
    print(f"diag-positions | {ckpt} | legal val | {n_blocks} x {block_size} "
          f"| evenly spaced offsets")

    show = [0, 1, 2, 4, 8, 16, 32, 48, 64, 96, 128, 192, 256, 320, 384, 448, 511]
    for mult, mask in masks.items():
        pos_sum = np.zeros(block_size)
        pos_cnt = np.zeros(block_size)
        cls_sum = {"word-start": 0.0, "word-interior": 0.0, "other": 0.0}
        cls_cnt = {"word-start": 0, "word-interior": 0, "other": 0}
        for off in offsets:
            x = torch.from_numpy(val[off : off + block_size].astype(np.int64)).to(device)[None]
            y = torch.from_numpy(val[off + 1 : off + 1 + block_size].astype(np.int64)).to(device)[None]
            logits, _, _ = model(x, None, None, neuron_mask=mask, collect_state=False)
            nll = F.cross_entropy(logits[0], y[0], reduction="none").float().cpu().numpy()
            pos_sum += nll
            pos_cnt += 1
            yn = y[0].cpu().numpy()
            prevn = np.concatenate([[x[0, 0].item()], yn[:-1]])
            s, i, o = word_classes(yn, prevn)
            for name, m in (("word-start", s), ("word-interior", i), ("other", o)):
                cls_sum[name] += float(nll[m].sum())
                cls_cnt[name] += int(m.sum())
        curve = pos_sum / pos_cnt
        print(f"\n[mask {mult}] mean {curve.mean():.4f} nats/byte")
        print("  pos : " + " ".join(f"{p:>6d}" for p in show))
        print("  nll : " + " ".join(f"{curve[p]:6.3f}" for p in show))
        print(f"  head (0-63) {curve[:64].mean():.4f} | "
              f"context (64-511) {curve[64:].mean():.4f} | "
              f"tail (256-511) {curve[256:].mean():.4f}")
        for name in cls_sum:
            if cls_cnt[name]:
                print(f"  {name:14s} {cls_sum[name] / cls_cnt[name]:.4f} nats/byte"
                      f"  (n={cls_cnt[name]:,})")
        # full curve for the position-wise network-vs-n-gram comparison
        names = list(cls_sum)
        out = f"out/routed_probe/diag_positions_{mult}.npz"
        np.savez(out, curve=curve, offsets=offsets, classes=names,
                 cls_nll=np.array([cls_sum[n] / max(cls_cnt[n], 1) for n in names]),
                 cls_cnt=np.array([cls_cnt[n] for n in names]))
        print(f"  saved {out}")


# --------------------------------------------------------------- compare ---

def run_compare():
    import os

    ng = np.load("out/routed_probe/diag_ngram.npz")
    print("network vs 6-gram, same 128 x 512 legal-val targets "
          "(delta = network - ngram, negative = network better)")
    show = [0, 1, 2, 4, 8, 16, 32, 48, 64, 96, 128, 192, 256, 320, 384, 448, 511]
    print("  pos      : " + " ".join(f"{p:>6d}" for p in show))
    print("  ngram    : " + " ".join(f"{ng['curve'][p]:6.3f}" for p in show))
    for mult in (896, 1024):
        path = f"out/routed_probe/diag_positions_{mult}.npz"
        if not os.path.exists(path):
            print(f"  [mask {mult}] missing {path}")
            continue
        m = np.load(path)
        d = m["curve"] - ng["curve"]
        print(f"  net@{mult:<4d} : " + " ".join(f"{m['curve'][p]:6.3f}" for p in show))
        print(f"  delta    : " + " ".join(f"{d[p]:+6.3f}" for p in show))
        slope = np.polyfit(np.arange(len(m["curve"])), m["curve"], 1)[0] * 100
        ng_slope = np.polyfit(np.arange(len(ng["curve"])), ng["curve"], 1)[0] * 100
        print(f"  [mask {mult}] mean {m['curve'].mean():.4f} vs ngram "
              f"{ng['curve'].mean():.4f} (delta {d.mean():+.4f}) | "
              f"head {d[:64].mean():+.4f} | ctx {d[64:].mean():+.4f} | "
              f"tail {d[256:].mean():+.4f}")
        print(f"  [mask {mult}] slope {slope:+.4f} nats/100 B "
              f"(ngram {ng_slope:+.4f}) | better on {100 * (d < 0).mean():.1f} % "
              f"of positions")
        for name, dn, mn in zip(m["classes"], m["cls_nll"], ng["cls_nll"]):
            print(f"  [mask {mult}] {str(name):14s} {dn:.4f} vs {mn:.4f} "
                  f"(delta {dn - mn:+.4f})")


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    mode = a[0]

    def arg(flag, default):
        return a[a.index(flag) + 1] if flag in a else default

    if mode == "ngram":
        run_ngram([int(k) for k in arg("--orders", "4,6").split(",")])
    elif mode == "positions":
        ckpt = a[1]
        mults = [int(m) for m in arg("--masks", "896,1024").split(",")]
        run_positions(ckpt, mults, int(arg("--blocks", "128")),
                      int(arg("--block-size", "512")))
    elif mode == "compare":
        run_compare()
    else:
        raise SystemExit(f"unknown mode {mode!r}")


if __name__ == "__main__":
    main()
