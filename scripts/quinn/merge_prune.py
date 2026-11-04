#!/usr/bin/env python3
"""Prune a merged BDH checkpoint down to a target width, physically.

Why this is not scripts/prune_eval.py: that script zeroes pruned neurons in place
and keeps the config, so a saved checkpoint would still be the full width with
mostly-zero columns (21.75 GB for our merged legal+zh). Replay training needs the
smaller shape, so this script slices the tensors and rewrites the config.

The neuron dimension is n = n_head * N with N = mult * n_embd // n_head. Pruning
to a smaller mult means keeping k positions out of N.

IMPORTANT: the kept positions are the SAME for every head. `attn.freqs` is a
single buffer of shape (1, 1, 1, N) shared across all heads -- the RoPE frequency
belongs to the neuron position, not to the head.

STATUS: THIS SCRIPT DOES NOT WORK. Three variants were tried on 2026-11-04 and all
three degraded a model that was never merged. Do not trust its output. Details in
docs/reports/2026-11-04_merge-experiments.md, section 4.

  attempt 1  per-head indices, freqs sliced      crash (5-D vs 4-D)
  attempt 2  shared indices, freqs sliced        zh_last 896->448: 5.64 -> 21.78
  attempt 3  shared indices, freqs recomputed    zh_last 896->448: 5.64 -> 57.48

Both control tests used the UNMERGED zh_last, so the degradation cannot be blamed
on cross-talk from a merge. Something about physically shortening the neuron
dimension is wrong in a way not yet identified.

The likely explanation, not yet tested: scripts/prune_eval.py (used for the August
recovery numbers) ZEROES encoder/encoder_v/decoder at the ORIGINAL width. The config
keeps mult 896, the model still computes over 57,344 neurons, some silent, and the
RoPE buffer is untouched because the width never changes. The August figures were
therefore measured on a zeroed model, not a physically narrower one. Slicing
produces a different architecture whose behaviour is unknown.

Next step to try, in this order:
  1. reproduce the August path exactly: zero weights, keep the config, replay.
  2. only then ask whether physical slicing can be made to work.

What IS correct here: attn.freqs is a rotation phase per neuron position and must
not be sliced from an unrelated index set. Both variants above respected that and
still failed, so the freqs handling was necessary but not sufficient.

Ranking is by mean |xy| over the evaluation protocol crops. The August
merge+prune work found random ordering ties or beats magnitude ranking, so both
orders are supported here and `random` is the default in the runner.

Usage:
    python scripts/quinn/merge_prune.py \\
        --ckpt out_a/...-merged.pt --target-mult 896 \\
        --domains legal:data/textmix2/legal.txt zh:data/europarl/xscript_zh.txt \\
        --order importance --out out_c/merge_probe/merged_pruned896.pt
"""

import argparse
import dataclasses
import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, ".")

from bdh import BDH, BDHConfig, _k_sparse_relu


@torch.no_grad()
def neuron_importance(model, arrays, block, n_batches, batch, ratio, device):
    """Mean |xy| per neuron, averaged over depth levels and batches."""
    C = model.config
    nh = C.n_head
    N = C.mlp_internal_dim_multiplier * C.n_embd // nh
    acc = torch.zeros(nh, N, device=device)
    seen = 0

    act = (lambda t: _k_sparse_relu(t, ratio)) if ratio > 0 else torch.nn.functional.relu

    for arr, idxs in arrays:
        data = torch.from_numpy(arr.astype(np.int64))
        for b0 in range(0, min(len(idxs), n_batches * batch), batch):
            chunk = idxs[b0:b0 + batch]
            if not chunk:
                continue
            idx = torch.stack([data[i:i + block] for i in chunk]).to(device)
            with torch.autocast("cuda", dtype=torch.bfloat16,
                                enabled=device.type == "cuda"):
                x = model.ln(model.embed(idx).unsqueeze(1))
                B, _, T, _ = x.shape
                for _lvl in range(C.n_layer):
                    x_s = act(x @ model.encoder)
                    yKV, _ = model.attn(x_s, x, state=None, pos_offset=0)
                    y_s = act(model.ln(yKV) @ model.encoder_v)
                    xy = x_s * y_s
                    acc += xy.abs().float().mean(dim=(0, 1, 2))
                    x = model.ln(x + model.ln(
                        xy.transpose(1, 2).reshape(B, 1, T, N * nh) @ model.decoder))
            seen += 1

    return acc.flatten() / max(seen, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--target-mult", type=int, required=True)
    ap.add_argument("--domains", nargs="+", required=True)
    ap.add_argument("--mb", type=int, default=30)
    ap.add_argument("--crops", type=int, default=200)
    ap.add_argument("--block", type=int, default=512)
    ap.add_argument("--batches", type=int, default=10)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--order", choices=["importance", "random"], default="importance")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ckpt = torch.load(args.ckpt, map_location="cpu", weights_only=False, mmap=True)
    cfg = BDHConfig(**{k: v for k, v in ckpt["cfg"].items()
                       if k in {f.name for f in dataclasses.fields(BDHConfig)}})
    nh, D = cfg.n_head, cfg.n_embd
    N_src = cfg.mlp_internal_dim_multiplier * D // nh
    N_dst = args.target_mult * D // nh
    if N_dst >= N_src:
        sys.exit("target width %d is not smaller than source %d" % (N_dst, N_src))
    keep_frac = N_dst / N_src
    print("source mult %d (N=%s) -> target mult %d (N=%s) | keep %.4f" %
          (cfg.mlp_internal_dim_multiplier, format(N_src, ","),
           args.target_mult, format(N_dst, ","), keep_frac))

    model = BDH(cfg)
    model.load_state_dict(ckpt["model_state"])
    model = model.to(device).eval()

    if args.order == "importance":
        arrays = []
        for item in args.domains:
            name, path = item.split(":", 1)
            arr = np.frombuffer(open(path, "rb").read(args.mb * 1_000_000)[-2_000_000:],
                                dtype=np.uint8)
            g = torch.Generator().manual_seed(1234)
            hi = len(arr) - args.block - 1
            idxs = [int(x) for x in torch.randint(hi, (args.crops,), generator=g)]
            arrays.append((arr, idxs))
            print("  domain %s: %d crops" % (name, len(idxs)))
        print("ranking neurons by union mean |xy| over %d batches (%d crops each)"
              % (args.batches, args.batch))
        imp = neuron_importance(model, arrays, args.block, args.batches,
                                args.batch, getattr(cfg, "k_sparse_ratio", 0.0), device)
        # average importance across heads: the index set must be head-shared
        shared = imp.view(nh, N_src).mean(dim=0)
        order = torch.argsort(shared, descending=True).cpu()
        print("importance averaged across %d heads (shared index set)" % nh)
    else:
        g = torch.Generator().manual_seed(7)
        order = torch.randperm(N_src, generator=g)
        print("random neuron order (seed 7, shared across heads)")

    keep_idx = order[:N_dst]                         # (N_dst,) shared source indices
    print("selected %d of %d neuron positions (shared across %d heads)" % (N_dst, N_src, nh))

    sd = ckpt["model_state"]
    new_sd = {}

    idx_enc = keep_idx.view(1, 1, N_dst).expand(nh, D, N_dst)
    idx_dec = keep_idx.view(1, N_dst, 1).expand(nh, N_dst, D)

    # encoder / encoder_v: (nh, D, N) -> gather along last dim
    for key in ("encoder", "encoder_v"):
        t = sd[key].float().cpu()
        new_sd[key] = torch.gather(t, 2, idx_enc).contiguous()

    # decoder: (nh*N, D) -> per-head row blocks, gather rows
    t = sd["decoder"].float().cpu().view(nh, N_src, D)
    new_sd["decoder"] = torch.gather(t, 1, idx_dec).reshape(nh * N_dst, D).contiguous()

    # attn.freqs: a phase per neuron position, NOT a per-neuron parameter.
    # Slicing it shifts every surviving neuron's phase; recompute for the new width.
    from bdh import get_freqs
    new_sd["attn.freqs"] = get_freqs(N_dst, theta=2**16,
                                     dtype=torch.float32).view(1, 1, 1, N_dst)
    old_freqs = sd["attn.freqs"].float().cpu()
    print("  attn.freqs recomputed for N=%d (was N=%d); first 4 phases: %s -> %s" %
          (N_dst, N_src,
           [round(float(x), 6) for x in old_freqs.view(-1)[:4]],
           [round(float(x), 6) for x in new_sd["attn.freqs"].view(-1)[:4]]))

    # tensors without an n dimension pass through unchanged
    for key in sd:
        if key not in new_sd:
            new_sd[key] = sd[key].clone().float()

    new_cfg = dataclasses.replace(cfg, mlp_internal_dim_multiplier=args.target_mult)
    out = {
        "cfg": dataclasses.asdict(new_cfg),
        "step": ckpt.get("step", 0),
        "best_val": ckpt.get("best_val"),
        "model_state": new_sd,
        "optimizer_state": None,
        "state": None,
        "pruned_from": args.ckpt,
        "prune_order": args.order,
        "prune_keep_frac": round(keep_frac, 6),
    }

    # build the target model and load, to prove the slicing is self-consistent
    m2 = BDH(new_cfg)
    m2.load_state_dict(new_sd)
    n_params = sum(p.numel() for p in m2.parameters())
    print("target model builds | params %s | mult %d" %
          (format(n_params, ","), new_cfg.mlp_internal_dim_multiplier))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    torch.save(out, args.out)
    print("saved %s | %.2f GB" % (args.out, os.path.getsize(args.out) / 1e9))


if __name__ == "__main__":
    main()
