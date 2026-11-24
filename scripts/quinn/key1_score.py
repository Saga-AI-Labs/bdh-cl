"""Score a checkpoint with key 1 and compare it with the n-gram counter.

Reads the same 128 x 512 val positions the counter used, runs the model at each
block, and reports the delta on identical targets (negative = model better),
plus the 8.7 diagnostics: head/context/tail, word classes, win share, block
bootstrap CI.

Usage:
  .venv/bin/python scripts/quinn/key1_score.py \
      --ckpt out/host/bdh_files_host100m-e1_last.pt \
      --val data/host/fineweb_val.txt \
      --ngram out/host/key1_ngram.json \
      --out out/host/key1_host100m.json
"""

import argparse
import datetime
import hashlib
import json

import numpy as np
import torch
import torch.nn.functional as F

BLOCK = 512
N_BLOCKS = 128


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def word_classes(y, prev):
    a = ((y >= 65) & (y <= 90)) | ((y >= 97) & (y <= 122))
    pa = ((prev >= 65) & (prev <= 90)) | ((prev >= 97) & (prev <= 122))
    return a & ~pa, a & pa, ~a


def legal_val():
    import sys
    sys.path.insert(0, ".")
    from pipeline.data import _prepare_textmix
    blocks, _, _, _ = _prepare_textmix("legal:data/textmix2/legal.txt", 30)
    return np.frombuffer(blocks["legal"]["val"], dtype=np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--val")
    ap.add_argument("--legal", action="store_true")
    ap.add_argument("--ngram", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--block", type=int, default=BLOCK)
    ap.add_argument("--n-blocks", type=int, default=N_BLOCKS)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    ng = json.load(open(args.ngram))
    val = legal_val() if args.legal else np.memmap(args.val, dtype=np.uint8, mode="r")
    if len(val) < args.block + 2:
        raise SystemExit("val carve is shorter than one block")
    offsets = np.linspace(0, len(val) - args.block - 2, args.n_blocks).astype(int)
    pos_local = np.arange(args.block)
    y = val[np.concatenate([np.arange(o + 1, o + 1 + args.block) for o in offsets])]
    prev = val[np.concatenate([np.arange(o, o + args.block) for o in offsets])]

    from pipeline.merge import load_model_mmap
    model, cfg = load_model_mmap(args.ckpt)
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    print(f"model: {args.ckpt} | n_embd {cfg.get('n_embd')} | mult "
          f"{cfg.get('mlp_internal_dim_multiplier')} | block {args.block}")

    curve = np.zeros(args.block, dtype=np.float64)
    nlls = []
    for bi, off in enumerate(offsets):
        x = torch.from_numpy(np.asarray(val[off:off + args.block]).astype(np.int64))[None].to(device)
        yy = torch.from_numpy(np.asarray(val[off + 1:off + 1 + args.block]).astype(np.int64))[None].to(device)
        with torch.no_grad():
            logits, _, _ = model(x, None, None, collect_state=False)
            nll = F.cross_entropy(logits[0].float(), yy[0], reduction="none").cpu().numpy()
        curve += nll
        nlls.append(nll)
        if (bi + 1) % 32 == 0:
            print(f"  {bi + 1}/{len(offsets)} blocks")
    curve /= len(offsets)
    nll_all = np.concatenate(nlls)

    ng_curve = np.array(ng["curve"], dtype=np.float64)
    if len(ng_curve) != args.block:
        raise SystemExit(f"ngram curve is {len(ng_curve)} positions, expected {args.block}")
    delta_curve = curve - ng_curve
    rng = np.random.default_rng(1337)
    boot = np.array([delta_curve[rng.integers(0, args.block, args.block)].mean()
                     for _ in range(2000)])

    # per-target NLL for the word-class split (exact, not the per-position mean)
    s, i, o = word_classes(y.astype(np.int64), prev.astype(np.int64))
    doc = {
        "schema": "key1_score_v1",
        "date": datetime.date.today().isoformat(),
        "checkpoint": args.ckpt,
        "checkpoint_bytes": None,
        "checkpoint_sha256": sha256_file(args.ckpt),
        "checkpoint_cfg": {k: cfg.get(k) for k in
                          ("n_embd", "n_head", "n_layer", "mlp_internal_dim_multiplier",
                           "block_size", "dropout")},
        "ngram_json": args.ngram,
        "ngram_sha256": sha256_file(args.ngram),
        "val": args.val if not args.legal else "legal val (1 MB)",
        "val_bytes": int(len(val)),
        "block": args.block,
        "n_blocks": args.n_blocks,
        "model_mean_nll": round(float(curve.mean()), 6),
        "ngram_mean_nll": round(float(ng_curve.mean()), 6),
        "delta": round(float(delta_curve.mean()), 6),
        "delta_bootstrap_se": round(float(boot.std(ddof=1)), 6),
        "delta_ci95": [round(float(np.percentile(boot, 2.5)), 6),
                       round(float(np.percentile(boot, 97.5)), 6)],
        "model_better_share": round(float((delta_curve < 0).mean()), 4),
        "model_head_0_63": round(float(curve[:64].mean()), 6),
        "model_context_64_511": round(float(curve[64:].mean()), 6),
        "model_tail_256_511": round(float(curve[256:].mean()), 6),
        "ngram_head_0_63": ng.get("head_0_63"),
        "ngram_context_64_511": ng.get("context_64_511"),
        "ngram_tail_256_511": ng.get("tail_256_511"),
        "word_start": round(float(nll_all[s].mean()), 6) if s.any() else None,
        "word_interior": round(float(nll_all[i].mean()), 6) if i.any() else None,
        "other": round(float(nll_all[o].mean()), 6) if o.any() else None,
        "curve": [round(float(v), 6) for v in curve],
        "ngram_resolution": ng.get("resolution"),
    }
    with open(args.out, "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print(f"model {doc['model_mean_nll']:.4f} vs ngram {doc['ngram_mean_nll']:.4f} "
          f"| delta {doc['delta']:+.4f} (95 % {doc['delta_ci95'][0]:+.4f}.."
          f"{doc['delta_ci95'][1]:+.4f}) | better on {100 * doc['model_better_share']:.1f} %")
    print(f"head {doc['model_head_0_63']:.4f} | context {doc['model_context_64_511']:.4f} "
          f"| tail {doc['model_tail_256_511']:.4f}")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
