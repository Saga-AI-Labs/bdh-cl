#!/usr/bin/env python3
"""Segment-masked serving evaluation for a merged BDH checkpoint.

Question this answers: the expert-merge report (2026-11-06) found that pooling two
experts by neuron-dimension concatenation produces cross-talk, and its decision
table concluded that routed routes beat pooled budgets. That conclusion has never
been measured as a serving mode. This script measures it.

Three modes on the SAME merged checkpoint, no retraining:

  joint      -- both halves active, every neuron summed (the mode already measured,
                expected to reproduce the cross-talk result)
  mask_a     -- only the first half active (parent A; merged[key] = cat([a, b]))
  mask_b     -- only the second half active (branch B)

The mask goes through BDH.forward's existing `neuron_mask` argument, which multiplies
x_sparse and y_sparse after the encoder and before the decoder. Zeroing those
activations is equivalent to not summing the corresponding decoder rows: the neurons
cannot contribute to the output either way. The checkpoint is never modified.

Plus two extras the prereg's proposal asked for:
  mixed      -- a crop built by alternating blocks from two domains, testing whether
                the two halves interfere on a task that genuinely needs both
  transfer   -- each half evaluated on the OTHER half's domain, i.e. the isolation
                question in its sharpest form: does masking remove capability or
                remove interference?

Implementation note (learned the hard way): x and y are sliced from the WHOLE
array with an offset -- `x = data[i:i+block]`, `y = data[i+1:i+1+block]` -- exactly as
`merge_probe_eval.py` does it. The first version of this script built a crop of
exactly `block` bytes and then took `y = crop[1:block+1]`, which yields only
block-1 bytes and produced `ValueError: expected batch_size 1024 to match
target batch_size 1022`. The offsets, not a padding helper, are the fix.

Usage:
    python scripts/quinn/serving_eval.py \\
        --merged out_c/expert_merge/zh_b1_merged.pt \\
        --domains expert:data/expert/heldout.txt zh:data/europarl/xscript_zh.txt \\
        --mb 30 --crops 200 --block 512 --batch 2 \\
        --out out_c/expert_merge/serving_eval.json
"""

import argparse
import json
import math
import os
import sys

import numpy as np
import torch

sys.path.insert(0, ".")

from bdh import BDH, BDHConfig


def load_model(path):
    ckpt = torch.load(path, map_location="cpu", weights_only=False, mmap=True)
    cfg = BDHConfig(**{k: v for k, v in ckpt["cfg"].items()
                       if k in {f.name for f in __import__("dataclasses").fields(BDHConfig)}})
    model = BDH(cfg)
    model.load_state_dict(ckpt["model_state"])
    del ckpt
    return model, cfg


def crop_offsets(path, mb, crops, block, seed=1234):
    arr = np.frombuffer(open(path, "rb").read(mb * 1_000_000)[-2_000_000:],
                        dtype=np.uint8)
    g = torch.Generator().manual_seed(seed)
    hi = len(arr) - block - 1
    idxs = [int(x) for x in torch.randint(hi, (crops,), generator=g)]
    return arr, idxs


def eval_domain(model, cfg, arr, idxs, block, device, batch, mask=None):
    """Mean NLL over the crops, full block, no routing. Same construction as
    merge_probe_eval.py: x and y are offset slices of the whole array, so both
    have exactly `block` elements."""
    data = torch.from_numpy(arr.astype(np.int64))
    losses = []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16,
                                         enabled=device.type == "cuda"):
        for b0 in range(0, len(idxs), batch):
            chunk = idxs[b0:b0 + batch]
            x = torch.stack([data[i:i + block] for i in chunk]).to(device)
            y = torch.stack([data[i + 1:i + 1 + block] for i in chunk]).to(device)
            logits, _, _ = model(x, y, None, neuron_mask=mask, collect_state=False)
            loss = torch.nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)), y.view(-1))
            losses.append(loss.item())
    m = sum(losses) / len(losses)
    return {"nll": round(m, 4), "ppl": round(math.exp(m), 2), "crops": len(idxs)}


def build_mixed(arr_a, idxs_a, arr_b, idxs_b, block, pieces=4):
    """Alternating blocks from two domains inside one crop, built as bytes."""
    out = []
    piece_len = block // pieces
    for k in range(len(idxs_a)):
        ia, ib = idxs_a[k], idxs_b[k]
        parts = []
        for p in range(pieces):
            src, start = (arr_a, ia) if p % 2 == 0 else (arr_b, ib)
            off = piece_len * p
            piece = bytes(src[start + off:start + off + piece_len])
            if len(piece) < piece_len:
                piece += b"\x00" * (piece_len - len(piece))
            parts.append(piece)
        # One more byte, continuing the alternation (piece index `pieces`, even
        # -> arr_a), so y = crop[1:block+1] has a true next byte. Without it the
        # loss sees 1022 targets for 1024 logits -- the same "learned the hard
        # way" bug the main eval had before the offset construction.
        src, start = (arr_a, ia) if pieces % 2 == 0 else (arr_b, ib)
        piece = bytes(src[start + block:start + block + 1])
        if len(piece) < 1:
            piece += b"\x00"
        out.append(b"".join(parts) + piece)
    return out


def eval_mixed(model, cfg, crops, block, device, batch, mask=None):
    """Mixed crops are built from alternating domain blocks, so they have no
    natural 'next byte' offset; evaluate them as full-length targets."""
    losses = []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16,
                                         enabled=device.type == "cuda"):
        for b0 in range(0, len(crops), batch):
            chunk = crops[b0:b0 + batch]
            x = torch.stack([torch.from_numpy(np.frombuffer(c, dtype=np.uint8)
                                               .astype(np.int64)[:block])
                             for c in chunk]).to(device)
            y = torch.stack([torch.from_numpy(np.frombuffer(c, dtype=np.uint8)
                                               .astype(np.int64)[1:block + 1])
                             for c in chunk]).to(device)
            logits, _, _ = model(x, y, None, neuron_mask=mask, collect_state=False)
            losses.append(torch.nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)), y.view(-1)).item())
    m = sum(losses) / len(losses)
    return {"nll": round(m, 4), "ppl": round(math.exp(m), 2), "crops": len(crops)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged", required=True)
    ap.add_argument("--domains", nargs="+", required=True)
    ap.add_argument("--mb", type=int, default=30)
    ap.add_argument("--crops", type=int, default=200)
    ap.add_argument("--block", type=int, default=512)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    doms = []
    for item in args.domains:
        name, path = item.split(":", 1)
        arr, idxs = crop_offsets(path, args.mb, args.crops, args.block)
        doms.append((name, path, arr, idxs))
        print("domain %s: %d crops from %d bytes" % (name, len(idxs), len(arr)))

    model, cfg = load_model(args.merged)
    model = model.to(device).eval()
    nh, D = cfg.n_head, cfg.n_embd
    N = cfg.mlp_internal_dim_multiplier * D // nh
    total_neurons = N * nh
    print("merged: mult=%d | params %s | neurons %s"
          % (cfg.mlp_internal_dim_multiplier,
             format(sum(p.numel() for p in model.parameters()), ","),
             format(total_neurons, ",")))

    # neuron_mask is per-head: bdh.py documents it as "optional (N,) float tensor"
    # and applies it as neuron_mask.view(1, 1, 1, -1) to x_sparse (B, nh, T, N).
    # An earlier version built masks over N*nh = 1,835,008 entries and crashed with
    # "size of tensor a (114688) must match the size of tensor b (1835008)".
    N = total_neurons // nh
    half = N // 2
    # The mask MUST be bf16. A float32 mask promotes every masked activation to
    # fp32 (bf16 * fp32 -> fp32), doubling each (B,nh,T,N) tensor from 3.76 GB to
    # 7.52 GB, and the attention state inherits the dtype, taking the KV cache from
    # 15 GB to 30 GB. On a 121 GB unified pool that is the difference between a
    # run that fits and one killed by the global OOM killer -- measured: joint ran
    # 400 crops cleanly, mask_a died in batch 1. Diagnosis in
    # docs/notes/2026-11-07_masked-serving-oom-diagnosis.md. 0 and 1 are exact in
    # bf16, so the numerics are unchanged.
    mask_a = torch.zeros(N, device=device, dtype=torch.bfloat16)
    mask_a[:half] = 1.0                      # parent A half
    mask_b = torch.zeros(N, device=device, dtype=torch.bfloat16)
    mask_b[half:] = 1.0                      # branch B half
    mask_none = None
    print("mask per head: N=%d | half=%d | mask_a=%d mask_b=%d"
          % (N, half, int(mask_a.sum()), int(mask_b.sum())))

    modes = [("joint", mask_none), ("mask_a", mask_a), ("mask_b", mask_b)]
    results = {"protocol": {"seed": 1234, "block": args.block, "crops": args.crops,
                            "mb": args.mb, "merged": args.merged},
               "modes": {}}

    for mode_name, mask in modes:
        # release the allocator's cached blocks before switching modes: the joint
        # pass leaves ~65 GB of cached bf16 blocks, and the masked path wants
        # slightly different block sizes on top.
        torch.cuda.empty_cache()
        print("\n=== %s ===" % mode_name)
        per = {}
        for name, _, arr, idxs in doms:
            r = eval_domain(model, cfg, arr, idxs, args.block, device, args.batch, mask)
            per[name] = r
            print("  %-8s nll %.4f | ppl %8.2f" % (name, r["nll"], r["ppl"]))
        results["modes"][mode_name] = per

    # transfer: each half on the OTHER half's domain (sharpest isolation test)
    if len(doms) >= 2:
        a_name, _, a_arr, a_idx = doms[0]
        b_name, _, b_arr, b_idx = doms[1]
        print("\n=== transfer (each half on the other half's domain) ===")
        results["transfer"] = {}
        for half, mask, on_name, arr, idxs in (
                ("mask_a", mask_a, b_name, b_arr, b_idx),
                ("mask_b", mask_b, a_name, a_arr, a_idx)):
            r = eval_domain(model, cfg, arr, idxs, args.block, device, args.batch, mask)
            results["transfer"][half] = {"on": on_name, **r}
            print("  %s on %-8s nll %.4f | ppl %8.2f"
                  % (half, on_name, r["nll"], r["ppl"]))

    # mixed probe: alternating blocks from the two domains
    if len(doms) >= 2:
        a_name, _, a_arr, a_idx = doms[0]
        b_name, _, b_arr, b_idx = doms[1]
        mixed = build_mixed(a_arr, a_idx, b_arr, b_idx, args.block)
        print("\n=== mixed probe (alternating 4-block pieces, %s + %s) ===" % (a_name, b_name))
        results["mixed"] = {}
        for mode_name, mask in modes:
            torch.cuda.empty_cache()
            r = eval_mixed(model, cfg, mixed, args.block, device, args.batch, mask)
            results["mixed"][mode_name] = r
            print("  %-8s nll %.4f | ppl %8.2f" % (mode_name, r["nll"], r["ppl"]))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote %s" % args.out)


if __name__ == "__main__":
    main()
