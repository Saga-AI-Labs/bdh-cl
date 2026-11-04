#!/usr/bin/env python3
"""Evaluate a merged BDH checkpoint against its two parents.

Question this answers: does neuron-dimension concatenation of two *linear* phases
(the K25/W1024 ladder) produce anything beyond the later phase? By construction
it should not -- zh_last already contains phases 1-24, legal_last contains 1-22,
so a merge duplicates 22 phases rather than fusing disjoint experts. The paper's
merge (Section 6) works on two branches that diverge from a shared base.

If the merged model is worse than zh alone on zh, that is the paper's own
reported behaviour: the last-trained language pays for the embedding averaging.
Here the embeddings are bit-identical, so that penalty should not appear --
which makes this a cleaner test of the duplication question.

Protocol: same crop sampling as eval_router.py -- one generator seeded 1234 per
domain, read(mb*1e6)[-2e6:], block 512, 200 crops. That keeps the numbers
comparable to the stored score vectors for legal and zh.

Usage:
    python scripts/quinn/merge_probe_eval.py \\
        --models a.pt b.pt merged.pt --labels legal_last zh_last merged \\
        --domains legal:data/textmix2/legal.txt zh:data/europarl/xscript_zh.txt \\
        --out out_c/merge_probe/eval.json
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
import dataclasses


def load_model(path):
    ckpt = torch.load(path, map_location="cpu", weights_only=False, mmap=True)
    cfg = BDHConfig(**{k: v for k, v in ckpt["cfg"].items()
                       if k in {f.name for f in dataclasses.fields(BDHConfig)}})
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


def eval_domain(model, cfg, arr, idxs, block, device, batch=4):
    """Mean NLL over the crops, full block, no routing."""
    data = torch.from_numpy(arr.astype(np.int64))
    losses = []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16,
                                         enabled=device.type == "cuda"):
        for b0 in range(0, len(idxs), batch):
            chunk = idxs[b0:b0 + batch]
            x = torch.stack([data[i:i + block] for i in chunk]).to(device)
            y = torch.stack([data[i + 1:i + 1 + block] for i in chunk]).to(device)
            logits, _, _ = model(x)
            loss = torch.nn.functional.cross_entropy(
                logits.view(-1, logits.size(-1)), y.view(-1))
            losses.append(loss.item())
    m = sum(losses) / len(losses)
    return {"nll": round(m, 4), "ppl": round(math.exp(m), 2), "crops": len(idxs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--domains", nargs="+", required=True,
                    help="name:path entries")
    ap.add_argument("--mb", type=int, default=30)
    ap.add_argument("--crops", type=int, default=200)
    ap.add_argument("--block", type=int, default=512)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if len(args.models) != len(args.labels):
        sys.exit("models and labels must pair up")

    # Pre-load the crop offsets once per domain; arrays are shared across models.
    dom_specs = []
    for item in args.domains:
        name, path = item.split(":", 1)
        arr, idxs = crop_offsets(path, args.mb, args.crops, args.block)
        dom_specs.append((name, path, arr, idxs))
        print("domain %s: %d crops from %d bytes" % (name, len(idxs), len(arr)))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    results = {"domain_protocol": {"seed": 1234, "block": args.block,
                                  "crops": args.crops, "mb": args.mb},
               "models": {}}

    for label, path in zip(args.labels, args.models):
        print("\n=== %s : %s ===" % (label, path))
        model, cfg = load_model(path)
        model = model.to(device).eval()
        n_params = sum(p.numel() for p in model.parameters())
        print("  mult=%d | params %s | cuda %.1f GB" %
              (cfg.mlp_internal_dim_multiplier, format(n_params, ","),
               torch.cuda.memory_allocated() / 1e9 if device.type == "cuda" else 0.0))

        per_domain = {}
        for name, _, arr, idxs in dom_specs:
            r = eval_domain(model, cfg, arr, idxs, args.block, device, args.batch)
            per_domain[name] = r
            print("    %-6s nll %.4f | ppl %7.2f" % (name, r["nll"], r["ppl"]))

        results["models"][label] = {
            "path": path,
            "params": n_params,
            "mlp_internal_dim_multiplier": cfg.mlp_internal_dim_multiplier,
            "domains": per_domain,
        }

        del model
        torch.cuda.empty_cache()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print("\nwrote %s" % args.out)

    # Comparison table
    print("\n%-14s" % "model", end="")
    for name, *_ in dom_specs:
        print("%12s" % name, end="")
    print()
    print("-" * (14 + 12 * len(dom_specs)))
    for label in args.labels:
        print("%-14s" % label, end="")
        for name, *_ in dom_specs:
            print("%12.2f" % results["models"][label]["domains"][name]["ppl"], end="")
        print()


if __name__ == "__main__":
    main()
