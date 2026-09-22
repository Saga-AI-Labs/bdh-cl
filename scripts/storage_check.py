"""storage_check.py - harness for the grown-checkpoint storage-integrity test (P2).

Builds the EXACT frozen set from pipeline/train.py:197-203 plus embed/lm_head:
    enc_d[:, :, :n_old], encv_d[:, :, :n_old], dec_d[:, :n_old, :],
    embed.weight (full), lm_head (full)
where dec_d = decoder.view(n_head, n_new, -1). Compared BIT-EXACT against the
init checkpoint that cfg['init_from'] names. Newly grown columns and
attn.freqs (width-sized rotary buffer) are deliberately NOT compared.

Derived, never hardcoded: n_head, n_embd, mlp_internal_dim_multiplier are read
from each checkpoint's own cfg; n_old = init_mult * n_embd // n_head.

CPU-only by construction: CUDA_VISIBLE_DEVICES is cleared before torch import,
so this harness can never contend for a claimed GPU.

Usage:
  storage_check.py --ckpt <grown.pt> [--init <base.pt>] [--report json]
  storage_check.py --ckpt <grown.pt> --corrupt-frozen OUT.pt
  storage_check.py --ckpt <grown.pt> --corrupt-trainable OUT.pt
"""
import argparse
import json
import os
import sys

os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch  # noqa: E402


def load_pair(path):
    ck = torch.load(path, map_location="cpu", weights_only=False)
    return ck["cfg"], ck["model_state"]


def _region(name, g, i, report):
    same_shape = tuple(g.shape) == tuple(i.shape)
    ok = bool(same_shape and torch.equal(g, i))
    entry = {"region": name, "bit_exact": ok, "shape": list(g.shape)}
    if not ok:
        if same_shape:
            entry["mismatched_elements"] = int((g != i).sum())
            entry["max_abs_diff"] = float((g.float() - i.float()).abs().max())
        else:
            entry["shape_mismatch_vs_init"] = list(i.shape)
    report.append(entry)
    return ok


def check(grown_path, init_path):
    cfg, g = load_pair(grown_path)
    icfg, i = load_pair(init_path)
    nh, D = cfg["n_head"], cfg["n_embd"]
    n_new = cfg["mlp_internal_dim_multiplier"] * D // nh
    n_old = icfg["mlp_internal_dim_multiplier"] * D // nh
    assert icfg["n_head"] == nh and icfg["n_embd"] == D, "init/grown shape mismatch"
    assert n_new > n_old, "not a grown checkpoint"
    report = []
    ok = True
    for key in ("encoder", "encoder_v"):
        ok &= _region(f"{key}[:, :, :{n_old}]", g[key][:, :, :n_old], i[key], report)
    gd = g["decoder"].view(nh, n_new, -1)
    idl = i["decoder"].view(nh, n_old, -1)
    ok &= _region(f"decoder[:, :{n_old}, :]", gd[:, :n_old, :], idl[:, :n_old, :], report)
    ok &= _region("embed.weight", g["embed.weight"], i["embed.weight"], report)
    ok &= _region("lm_head", g["lm_head"], i["lm_head"], report)
    return {"verdict": "STORAGE_INTEGRITY_OK" if ok else "STORAGE_INTEGRITY_FAILED",
            "ckpt": grown_path, "init": init_path,
            "n_head": nh, "n_embd": D, "n_old": n_old, "n_new": n_new,
            "regions_compared": len(report),
            "regions_failed": sum(1 for r in report if not r["bit_exact"]),
            "report": report}


def corrupt(src_path, out_path, trainable=False):
    cfg, sd = load_pair(src_path)
    nh, D = cfg["n_head"], cfg["n_embd"]
    n = cfg["mlp_internal_dim_multiplier"] * D // nh
    idx = (0, 0, n - 1) if trainable else (0, 0, 0)
    with torch.no_grad():
        sd["encoder"][idx] += 1.0
    torch.save({"cfg": cfg, "model_state": sd, "state": sd}, out_path)
    print(f"CORRUPT {'TRAINABLE' if trainable else 'FROZEN'} copy -> {out_path} "
          f"(encoder{idx} bumped by 1.0)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--init", default=None)
    ap.add_argument("--report", choices=["json"], default=None)
    ap.add_argument("--corrupt-frozen", metavar="OUT")
    ap.add_argument("--corrupt-trainable", metavar="OUT")
    args = ap.parse_args()
    if args.corrupt_frozen:
        corrupt(args.ckpt, args.corrupt_frozen, trainable=False)
        return 0
    if args.corrupt_trainable:
        corrupt(args.ckpt, args.corrupt_trainable, trainable=True)
        return 0
    init = args.init
    if init is None:
        import os.path
        init = torch.load(args.ckpt, map_location="cpu", weights_only=False)["cfg"]["init_from"]
        print(f"init_from from cfg: {init}")
    res = check(args.ckpt, init)
    if args.report == "json":
        print(json.dumps(res, indent=1))
    else:
        for r in res["report"]:
            line = f"{r['region']:28s} {'OK' if r['bit_exact'] else 'FAIL'} shape={r['shape']}"
            if not r["bit_exact"]:
                line += f" mismatched={r['mismatched_elements']} maxabs={r['max_abs_diff']:.6g}"
            print(line)
        print(res["verdict"], f"regions={res['regions_compared']} failed={res['regions_failed']} "
              f"n_old={res['n_old']} n_new={res['n_new']}")
    return 0 if res["regions_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
