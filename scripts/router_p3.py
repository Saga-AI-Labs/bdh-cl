"""P3 router certification (prereg 5daf30c, S3/S4): 2-mask argmin routing.

Builds the labeled mixed stream by interleaving 512-byte blocks of the two
domains' splits, scores each block's early window under the two route masks
(old prefix vs full width) with no-grad forwards through the model's
neuron_mask - the same mechanism P3 training uses - and reports:

  - per-sequence routing accuracy + confusion matrix (S3, threshold >= 95 %)
  - routed full-block NLL vs oracle-routed NLL (S4: routed <= oracle + 0.05)
  - the early-window margin distribution (diagnostic for the fallback window)

Oracle serving map (the probe's registered semantics): domain A is served by
the FULL width (its trained block), domain B by the OLD prefix. These are the
masks the post-run full-coverage cells use, so S4 compares like with like.

Usage:
    PYTHONPATH=. python scripts/router_p3.py <ckpt> \
        --mask-old-mult 896 \
        --domain-a legal:data/textmix2/legal.txt \
        --domain-b zh:data/europarl/xscript_zh.txt \
        [--mb 30] [--window 128] [--batch 8] [--splits val test]
"""
import argparse
import math
import sys

import numpy as np
import torch
from torch.nn import functional as F

sys.path.insert(0, ".")

T_DEFAULT = 512


def load_model_path(ckpt_path):
    """Path-direct loader with the eval.load_checkpoint memory pattern
    (mmap on CPU, state dict copied, mapping released before use)."""
    import gc

    from pipeline.config import Config, build_model

    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False, mmap=True)
    cfg = Config(**ckpt["cfg"])
    model = build_model(cfg)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    del ckpt
    gc.collect()
    return model, cfg


def per_block_nll(model, x, y, mask, device, ctx):
    """Mean NLL per block for a batch (x: B,T int64)."""
    with torch.no_grad(), ctx:
        logits, _, _ = model(x, None, None, neuron_mask=mask, collect_state=False)
    if logits.dim() == 4:
        logits = logits[:, 0]
    nll = F.cross_entropy(logits.reshape(-1, logits.size(-1)).float(),
                          y.reshape(-1), reduction="none")
    return nll.view(y.shape[0], y.shape[1]).mean(1)


def forward_ctx(device):
    if device.type == "cuda":
        return torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16)
    from contextlib import nullcontext
    return nullcontext()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ckpt")
    ap.add_argument("--mask-old-mult", type=int, required=True,
                    help="old-prefix width in multiplier units (e.g. 896)")
    ap.add_argument("--domain-a", required=True, help="spec served by FULL width")
    ap.add_argument("--domain-b", required=True, help="spec served by the OLD prefix")
    ap.add_argument("--mb", type=int, default=30)
    ap.add_argument("--window", type=int, default=128)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--block-size", type=int, default=T_DEFAULT)
    ap.add_argument("--splits", nargs="+", default=["val", "test"])
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    from pipeline.train import apply_memory_cap
    apply_memory_cap(device)
    ctx = forward_ctx(device)

    model, cfg = load_model_path(args.ckpt)
    model.to(device)
    nh, D, mult = cfg.n_head, cfg.n_embd, cfg.mlp_internal_dim_multiplier
    N = mult * D // nh
    n_old = args.mask_old_mult * D // nh
    assert 0 < n_old < N, (n_old, N)
    assert 0 < args.window < args.block_size
    mask_old = torch.zeros(N, device=device)
    mask_old[:n_old] = 1.0
    print(f"router: block {args.block_size} | window {args.window} | "
          f"mask old-prefix {n_old} of {N} neurons/head | "
          f"A={args.domain_a.split(':', 1)[0]}->full, "
          f"B={args.domain_b.split(':', 1)[0]}->old-prefix")

    from pipeline.data import load_dataset
    from pipeline.config import Config

    T, W, B = args.block_size, args.window, args.batch
    srcs = []
    for spec in (args.domain_a, args.domain_b):
        d = load_dataset(Config(dataset="textmix", text_mix=spec, text_mix_mb=args.mb))
        srcs.append(d)

    for split in args.splits:
        arrays = [getattr(d, split) for d in srcs]
        # (len - 1) // T, not len // T: the y slice of the last block
        # (j*T+1 : (j+1)*T+1) must stay inside the array. For the textmix
        # splits (1,000,000 bytes = exactly 1953*512 + 64) a plain // would
        # make the final y slice one byte short and np.stack would crash.
        n_blocks = [(len(a) - 1) // T for a in arrays]
        entries = []
        for i in range(max(n_blocks)):
            if i < n_blocks[0]:
                entries.append((0, i))
            if i < n_blocks[1]:
                entries.append((1, i))
        labels = np.array([0 if d == 0 else 1 for d, _ in entries])  # 0=A, 1=B
        preds = np.zeros(len(entries), dtype=np.int64)
        routed = np.zeros(len(entries))
        oracle = np.zeros(len(entries))
        margins = np.zeros(len(entries))

        def grab(eidx):
            xs = np.stack([arrays[d][j * T:(j + 1) * T].astype(np.int64)
                           for d, j in eidx])
            ys = np.stack([arrays[d][j * T + 1:(j + 1) * T + 1].astype(np.int64)
                           for d, j in eidx])
            return (torch.from_numpy(xs).to(device),
                    torch.from_numpy(ys).to(device))

        def run_grouped(eidx, mask_of):
            """Forwards per mask group; returns per-entry NLL aligned to eidx."""
            out = np.zeros(len(eidx))
            for mask_val in (None, "old"):
                sub = [k for k, e in enumerate(eidx) if (mask_of(e) == "old") == (mask_val == "old")]
                if not sub:
                    continue
                x, y = grab([eidx[k] for k in sub])
                nlls = per_block_nll(model, x, y, mask_old if mask_val == "old" else None,
                                     device, ctx)
                for k, v in zip(sub, nlls.tolist()):
                    out[k] = v
            return out

        for s in range(0, len(entries), B):
            eidx = entries[s:s + B]
            xw, yw = grab([(d, j) for d, j in eidx])
            # early-window scores: x/y truncated to the window
            xw = xw[:, :W].contiguous()
            yw = yw[:, :W].contiguous()
            nll_old = per_block_nll(model, xw, yw, mask_old, device, ctx).tolist()
            nll_full = per_block_nll(model, xw, yw, None, device, ctx).tolist()
            for k, (o, f) in enumerate(zip(nll_old, nll_full)):
                margins[s + k] = o - f          # > 0 -> old block worse, full wins
                preds[s + k] = 1 if o <= f else 0  # 1 = serve old prefix (argmin NLL)
            # routed: serve each block under its argmin-selected mask
            routed[s:s + B] = run_grouped(
                eidx, lambda e: "old" if preds[s + eidx.index(e)] == 1 else "full")
            # oracle: serve under the TRUE domain's registered serving mask
            oracle[s:s + B] = run_grouped(
                eidx, lambda e: "old" if e[0] == 1 else "full")

        acc = float((preds == labels).mean())
        conf = np.zeros((2, 2), dtype=np.int64)
        for l, p in zip(labels, preds):
            conf[l, p] += 1
        names = ["A(full)", "B(old)"]
        print(f"\n--- split {split}: {len(entries)} blocks "
              f"({n_blocks[0]} A / {n_blocks[1]} B) ---")
        print(f"router accuracy: {acc * 100:.2f} % (threshold 95 %)")
        print(f"confusion [rows=true A,B; cols=pred A,B]: {conf.tolist()}")
        r_mean, o_mean = float(routed.mean()), float(oracle.mean())
        print(f"routed NLL  {r_mean:.4f} | oracle NLL {o_mean:.4f} | "
              f"delta {r_mean - o_mean:+.4f} (S4 threshold +0.05)")
        for di, name in enumerate(names):
            m = labels == di
            print(f"  {name}: n={int(m.sum())} | acc {float((preds[m] == di).mean()) * 100:.2f} %"
                  f" | routed {float(routed[m].mean()):.4f} | oracle {float(oracle[m].mean()):.4f}"
                  f" | margin median {float(np.median(margins[m])):+.4f}")
        print(f"  margin (nll_old - nll_full): median {float(np.median(margins)):+.4f} "
              f"| min {float(margins.min()):+.4f} | p10 {float(np.quantile(margins, 0.1)):+.4f}")


if __name__ == "__main__":
    main()
