#!/usr/bin/env python
"""P-C4' -- OOD reject under byte-first routing.

Prereg: docs/plans/2026-09-17_pc4-ood-reject-prereg.md (amended, commit 3b7d24a).
Object under test: the byte-n-gram router (per-class char 4-gram, add-1) with
the two-axis reject rule, byte instantiation. Likelihood side (23 masked
routes + full-width joint) is the reference for route agreement.
No training, no threshold tuning; thresholds calibrated on trained held-out
crops only, frozen before any OOD scoring.
Byte scoring always uses uint8 rows (never int64 -- bytes() would inflate).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, ".")
sys.path.insert(0, "scripts/quinn")
from c_arms import ByteNGram, split_idx, wilson  # reuse, no reimplementation

TRAINED = "en es pl fr de cs da pt fi hu bg it et el sk sv ro nl sl lt".split()
OOD = [("lv", "data/europarl/europarl-v7.lv-en.lv.txt"),
       ("ga", "data/europarl/DGT.en-ga.ga.txt"),
       ("zh", "data/europarl/xscript_zh.txt"),
       ("ja", "data/europarl/xscript_ja.txt"),
       ("hi", "data/europarl/xscript_hi.txt"),
       ("iu", "data/europarl/xscript_iu_syl.txt")]
SEED0 = 9000


def ood_blocks(path, crops, bs, seed):
    rawf = open(path, "rb").read()
    tail = rawf[-2_000_000:] if len(rawf) > 2_000_000 else rawf
    arr = np.frombuffer(tail, dtype=np.uint8)
    hi = len(arr) - bs - 1
    if hi < 1:
        raise SystemExit(f"ood corpus too small: {path}")
    n = min(crops, len(arr) // bs) if Path(path).name == "xscript_iu_syl.txt" else crops
    g = torch.Generator().manual_seed(seed)
    idx = torch.randint(hi, (n,), generator=g)
    off = [int(i) for i in idx]
    blocks = np.stack([arr[j:j + bs] for j in off]).astype(np.uint8)
    return blocks, off, hashlib.sha256(rawf).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="/var/tmp/bdh_europarl_ladRA2b-lt_last.pt")
    ap.add_argument("--npz", default="out_c/c_arms_ra2b_r3.npz")
    ap.add_argument("--out", default="out_c/pc4_ood.json")
    ap.add_argument("--crops", type=int, default=96)
    ap.add_argument("--window", type=int, default=128)
    ap.add_argument("--batch", type=int, default=1)
    args = ap.parse_args()

    z = np.load(args.npz, allow_pickle=False)
    dom, raw = z["dom"], z["raw"]
    assert raw.dtype == np.uint8 and raw.ndim == 2, "Expected uint8 crop matrix"
    assert args.batch == 1 and 0 < args.window < 512
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    routes = [int(r) for r in z["routes"]]
    tr, _te = split_idx(dom, frac=0.7, seed=7)
    tr_set = {int(i) for i in tr}

    # ---- byte models: 20 per-class + 1 pooled (train crops only)
    print(f"[byte] fitting 20 class models + pooled on {len(tr)} train crops", flush=True)
    ng = {}
    for d in TRAINED:
        m = ByteNGram()
        m.fit(d, [raw[i] for i in np.where(dom == d)[0] if int(i) in tr_set])
        ng[d] = m
    pooled = ByteNGram()
    pooled.fit("__joint__", [raw[i] for i in tr])

    def joint_best(r):
        """r: uint8 row. Returns (joint nll/byte, best-class nll/byte, best class)."""
        nb = len(r)
        nj = -(pooled.logp("__joint__", r)) / nb
        best_v, best_d = None, None
        for d in TRAINED:
            v = -(ng[d].logp(d, r)) / nb
            if best_v is None or v < best_v:
                best_v, best_d = v, d
        return nj, best_v, best_d

    # ---- trained calibration (held-out 580 only; thresholds frozen here)
    rel_means, nll_means = {}, {}
    for d in TRAINED:
        rs = [raw[i] for i in np.where(dom == d)[0] if int(i) not in tr_set]
        rat, nll = [], []
        for r in rs:
            nj, nb, _ = joint_best(r)
            rat.append(nj / nb)
            nll.append(nb)
        rel_means[d] = float(np.mean(rat))
        nll_means[d] = float(np.mean(nll))
    tau_rel = min(rel_means.values())
    band = 10.0 * max(nll_means.values())
    worst_rel = min(rel_means, key=rel_means.get)
    worst_abs = max(nll_means, key=nll_means.get)
    print(f"[calib] tau_rel={tau_rel:.4f} (weakest trained: {worst_rel})", flush=True)
    print(f"[calib] band={band:.4f} (10x worst trained {worst_abs}, mean {max(nll_means.values()):.4f})", flush=True)

    # trained language -> its own territory width (modal A2 label route)
    own_width = {}
    for d in TRAINED:
        ys = [int(v) for i, v in enumerate(z["y"]) if dom[i] == d]
        own_width[d] = routes[max(set(ys), key=ys.count)]

    res = {"status": "calibrated", "configuration": vars(args),
           "input_deviation": "Use xscript_iu_syl.txt, not contaminated xscript_iu.txt; source: Stage-A V6 erratum, 2026-09-11. Corrected before scoring.",
           "router_labels": "Domain classes with modal A2 route mapping, matching c_arms.cmd_fit; not exclusively label-free fitting.",
           "tau_rel": tau_rel, "band": band,
           "trained": {d: {"ratio_mean": rel_means[d], "best_nll_mean": nll_means[d],
                           "accepted": bool(rel_means[d] >= tau_rel and nll_means[d] <= band)}
                       for d in TRAINED},
           "ood": {}}
    json.dump(res, open(args.out, "w"), indent=1)  # checkpoint: calibration frozen

    # ---- likelihood side (same masking mechanics as c_arms extract)
    from pipeline.analyze import _load_model
    model, cfg = _load_model(args.ckpt)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(dev).eval()
    C = model.config
    nh, D = C.n_head, C.n_embd
    N_full = C.mlp_internal_dim_multiplier * D // nh
    bs = cfg["block_size"]
    if bs != 512:
        raise ValueError(f"Checkpoint block_size={bs}; prereg requires 512")
    enc_b, encv_b, dec_b = (model.encoder.data.clone(),
                            model.encoder_v.data.clone(), model.decoder.data.clone())

    def set_prefix(k):
        msk = torch.zeros(N_full, device=dev)
        msk[:k] = 1.0
        with torch.no_grad():
            model.encoder.data.copy_(enc_b * msk.view(1, 1, -1))
            model.encoder_v.data.copy_(encv_b * msk.view(1, 1, -1))
            model.decoder.data.copy_(dec_b * msk.repeat(nh).unsqueeze(1))

    R = len(routes)

    def lik_scores(blocks):
        n = blocks.shape[0]
        sc = np.zeros((R + 1, n), dtype=np.float64)
        tb = torch.from_numpy(blocks.astype(np.int64))
        for ri, k in enumerate(routes + [None]):
            set_prefix(N_full if k is None else min(k, N_full))
            with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16,
                                                 enabled=dev.type == "cuda"):
                for b0 in range(0, n, args.batch):
                    xb = tb[b0:b0 + args.batch].to(dev)
                    yb = xb.roll(shifts=-1, dims=1)
                    logits, _, _ = model(xb)
                    l = torch.nn.functional.cross_entropy(
                        logits.reshape(-1, logits.size(-1)), yb.reshape(-1),
                        reduction="none").view(xb.shape[0], bs)
                    sc[R if k is None else ri, b0:b0 + xb.shape[0]] = \
                        l[:, :args.window].float().mean(dim=1).cpu().numpy()
        return sc

    # ---- OOD scoring
    agree_ks, agree_ns = 0, 0
    for li, (name, path) in enumerate(OOD):
        blocks, offsets, src_sha = ood_blocks(path, args.crops, bs, SEED0 + li)
        n = blocks.shape[0]
        rat, nll, bpred = [], [], []
        for r in blocks:
            nj, nb, bd = joint_best(r)
            rat.append(nj / nb)
            nll.append(nb)
            bpred.append(bd)
        print(f"[likelihood] starting {name}: {n} crops, {R + 1} forwards/crop", flush=True)
        scores = lik_scores(blocks)
        lik_choice = scores[:R].argmin(axis=0)
        matches = [own_width[bpred[c]] == routes[int(lik_choice[c])] for c in range(n)]
        km = int(sum(matches))
        lo, hi = wilson(km, n)
        k_rel = int(np.mean(rat) >= tau_rel)
        a_abs = int(np.mean(nll) <= band)
        res["ood"][name] = {
            "source_path": path, "src_sha256": src_sha, "tail_relative_crop_offsets": offsets,
            "crop_sha256": [hashlib.sha256(r.tobytes()).hexdigest() for r in blocks],
            "byte_ratios": rat, "byte_best_nlls": nll,
            "byte_predicted_widths": [own_width[d] for d in bpred],
            "likelihood_routes": routes, "likelihood_nlls": scores.tolist(),
            "agreement_count": km,
            "crop_accept_count": int(sum(r >= tau_rel and v <= band for r, v in zip(rat, nll))),
            "crop_accept_wilson": list(wilson(int(sum(r >= tau_rel and v <= band for r, v in zip(rat, nll))), n)),
            "n": int(n),
            "byte_ratio_mean": float(np.mean(rat)),
            "byte_best_nll_mean": float(np.mean(nll)),
            "accepted_rel": bool(k_rel), "accepted_abs": bool(a_abs),
            "accepted_both": bool(k_rel and a_abs),
            "byte_vs_lik_agree": float(km / n),
            "agree_wilson": [round(lo, 4), round(hi, 4)],
            "lik_best_ppl_mean": float(np.exp(scores[:R].min(axis=0).mean())),
            "lik_joint_ppl_mean": float(np.exp(scores[R].mean())),
        }
        agree_ks += km
        agree_ns += n
        print(f"[ood] {name}: n={n} ratio={np.mean(rat):.3f} nll={np.mean(nll):.3f} "
              f"rel={k_rel} abs={a_abs} agree={km}/{n}={km / n:.3f}", flush=True)
        json.dump(res, open(args.out, "w"), indent=1)  # incremental

    # ---- verdict summary (preregistered clauses)
    ood_acc = [v for v in res["ood"].values()]
    res["P-C4p-1_agreement_overall"] = float(agree_ks / agree_ns)
    res["P-C4p-1_verdict"] = "PASS" if agree_ks / agree_ns >= 0.90 and all(v["byte_vs_lik_agree"] >= 0.50 for v in ood_acc) else "FAIL"
    res["agreement_overall_wilson"] = list(wilson(agree_ks, agree_ns))
    res["P-C4p-2"] = ("PASS" if not any(v["accepted_both"] for v in ood_acc)
                      and all(v["accepted"] for v in res["trained"].values())
                      else "FAIL")
    res["P-C4p-3_ratio_only_admits_crossscript"] = any(
        res["ood"][d]["accepted_rel"] for d in ("zh", "ja", "hi", "iu"))
    res["status"] = "complete"
    json.dump(res, open(args.out, "w"), indent=1)
    print(f"[pc4] done: P-C4'-1={res['P-C4p-1_agreement_overall']:.4f} "
          f"P-C4'-2={res['P-C4p-2']} ratio-only admits cross-script="
          f"{res['P-C4p-3_ratio_only_admits_crossscript']}", flush=True)
    print(f"[pc4] summary -> {args.out}", flush=True)


def offsets_summary(offsets):
    return {"min": min(offsets), "max": max(offsets), "n": len(offsets),
            "first10": offsets[:10]}


if __name__ == "__main__":
    main()
