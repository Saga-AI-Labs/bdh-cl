"""Label-free likelihood routing over grown BDH stacks (prefix experts).

Each route (neuron-prefix mask) scores the EARLY positions of a block; arg-min
routes the LATE positions. Reports routing accuracy vs true domain plus routed
and joint perplexity on the served positions. An oracle served-ppl column is
computed only when --oracle-routes name:width,... is supplied (per-domain true
prefix width); without it, no oracle quantity is promised or printed.

Usage:
    PYTHONPATH=. python scripts/eval_router.py <ckpt> \
        --routes 8192,10240,12288 --domains wiki:path,books:path,parl:path \
        [--window 128] [--crops 40] [--batch 4]
"""
import argparse
import math
import sys

import numpy as np
import torch

sys.path.insert(0, ".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ckpt")
    ap.add_argument("--routes", required=True)
    ap.add_argument("--domains", required=True)
    ap.add_argument("--mb", type=int, default=30)
    ap.add_argument("--window", type=int, default=128)
    ap.add_argument("--crops", type=int, default=40)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--oracle-routes", default=None,
                    help="optional name:width,... per-domain true prefix widths; adds an oracle served-ppl column")
    ap.add_argument("--route-grid", action="store_true",
                    help="emit a [true-domain x forced-width] served-ppl grid from the already-filled rl tensor (zero extra forwards)")
    ap.add_argument("--crop-dump", default=None,
                    help="domain:wA,wB - per-crop early-window scores at two routes, chosen route, and late-window loss at both, for that true domain")
    ap.add_argument("--pos-dump", default=None,
                    help="domain:wA,wB - per-crop position-decomposition of the early-window margin from the already-filled rl tensor (zero extra forwards)")
    args = ap.parse_args()

    from pipeline.analyze import _load_model

    model, cfg = _load_model(args.ckpt)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device).eval()
    nh, D = model.config.n_head, model.config.n_embd
    N_full = model.config.mlp_internal_dim_multiplier * D // nh
    bs = cfg["block_size"]
    assert 0 < args.window < bs

    enc_b = model.encoder.data.clone()
    encv_b = model.encoder_v.data.clone()
    dec_b = model.decoder.data.clone()

    def set_prefix(k):
        m = torch.zeros(N_full, device=device)
        m[:k] = 1.0
        with torch.no_grad():
            model.encoder.data.copy_(enc_b * m.view(1, 1, -1))
            model.encoder_v.data.copy_(encv_b * m.view(1, 1, -1))
            model.decoder.data.copy_(dec_b * m.repeat(nh).unsqueeze(1))

    routes = [int(r) for r in args.routes.split(",")]
    oracle_map = {}
    if args.oracle_routes:
        for item in filter(None, map(str.strip, args.oracle_routes.split(","))):
            name, w = item.split(":", 1)
            w = int(w)
            if w not in routes:
                print(f"error: oracle width {w} for {name} is not in --routes", file=sys.stderr)
                sys.exit(2)
            oracle_map[name] = routes.index(w)
    doms = []
    g = torch.Generator().manual_seed(1234)
    for item in filter(None, map(str.strip, args.domains.split(","))):
        name, path = item.split(":", 1)
        arr = np.frombuffer(open(path, "rb").read(args.mb * 1_000_000)[-2_000_000:],
                            dtype=np.uint8)
        hi = len(arr) - bs - 1
        crops = np.stack([arr[int(i):int(i) + bs]
                          for i in torch.randint(hi, (args.crops,), generator=g)])
        doms.append((name, torch.from_numpy(crops.astype(np.int64))))

    print(f"router ckpt={args.ckpt} | routes={routes} n/head | window={args.window} tok "
          f"| {args.crops} crops/domain")

    names = [n for n, _ in doms]
    R = len(routes)
    conf = torch.zeros(len(doms), R, dtype=torch.int64)
    routed_ppl = {}
    oracle_ppl = {}
    joint_losses = []
    grid_rows = []

    for ti, (tname, blocks) in enumerate(doms):
        rl = torch.zeros(R, args.crops, bs)
        for ri, k in enumerate(routes):
            set_prefix(min(k, N_full))
            amp = torch.autocast("cuda", dtype=torch.bfloat16, enabled=device.type == "cuda")
            with torch.no_grad(), amp:
                for b0 in range(0, args.crops, args.batch):
                    xb = blocks[b0:b0 + args.batch].to(device)
                    yb = xb.roll(shifts=-1, dims=1)
                    logits, _, _ = model(xb)
                    l = torch.nn.functional.cross_entropy(
                        logits.reshape(-1, logits.size(-1)), yb.reshape(-1),
                        reduction="none").view(xb.shape[0], bs)
                    rl[ri, b0:b0 + args.batch] = l.float().cpu()

        scores = rl[:, :, : args.window].mean(dim=2)
        choice = scores.argmin(dim=0)
        served = rl[choice, torch.arange(args.crops), args.window:].mean(dim=1)
        if args.route_grid:
            grid_rows.append(rl[:, :, args.window:].mean(dim=(1, 2)).float().cpu().exp().tolist())

        if args.crop_dump:
            dname, wspec = args.crop_dump.split(":", 1)
            if dname == tname:
                wa, wb = (int(x) for x in wspec.split(","))
                ia, ib = routes.index(wa), routes.index(wb)
                print(f"CROP_DUMP domain={tname} wA={wa} wB={wb} window={args.window} crops={args.crops}")
                print("crop_idx|scoreA|scoreB|margin_AminusB|lateA|lateB|chosen")
                for ci in range(args.crops):
                    print(f"{ci}|{scores[ia, ci].item():.6f}|{scores[ib, ci].item():.6f}|"
                          f"{(scores[ia, ci] - scores[ib, ci]).item():.6f}|"
                          f"{rl[ia, ci, args.window:].mean().item():.6f}|"
                          f"{rl[ib, ci, args.window:].mean().item():.6f}|{routes[choice[ci].item()]}")

        if args.pos_dump:
            dname, wspec = args.pos_dump.split(":", 1)
            if dname == tname:
                wa, wb = (int(x) for x in wspec.split(","))
                ia, ib = routes.index(wa), routes.index(wb)
                print(f"POS_DUMP domain={tname} wA={wa} wB={wb} window={args.window} crops={args.crops}")
                print("crop_idx|M|A|R|k50|conc5|top1_pos|neg_share|lateA|lateB|chosen")
                for ci in range(args.crops):
                    m = rl[ia, ci, : args.window] - rl[ib, ci, : args.window]
                    M = m.sum().item()
                    A = m.abs().sum().item()
                    Rv = (abs(M) / A) if A > 0 else 0.0
                    srt, idxs = torch.sort(m.abs(), descending=True)
                    cum = torch.cumsum(srt, 0)
                    k50 = int((cum < 0.5 * A).sum().item()) + 1 if A > 0 else 0
                    conc5 = (srt[:5].sum().item() / A) if A > 0 else 0.0
                    top1 = int(idxs[0].item()) if A > 0 else -1
                    neg_share = (m < 0).float().mean().item()
                    chosen = routes[choice[ci].item()]
                    print(f"{ci}|{M:.6f}|{A:.6f}|{Rv:.6f}|{k50}|{conc5:.6f}|{top1}|{neg_share:.6f}|"
                          f"{rl[ia, ci, args.window:].mean().item():.6f}|{rl[ib, ci, args.window:].mean().item():.6f}|{chosen}")
                leakers = [ci for ci in range(args.crops) if routes[choice[ci].item()] != wb]
                stayers = [ci for ci in range(args.crops) if routes[choice[ci].item()] == wb][:20]
                print(f"POS_ARRAYS wB={wb} leakers={leakers} stayers={stayers}")
                for ci in leakers + stayers:
                    m = rl[ia, ci, : args.window] - rl[ib, ci, : args.window]
                    print(f"POS_ROW {ci} " + " ".join(f"{v:.4f}" for v in m.tolist()))

        conf[ti] += torch.bincount(choice, minlength=R)
        routed_ppl[tname] = math.exp(served.mean().item())
        if tname in oracle_map:
            oi = oracle_map[tname]
            oserved = rl[oi, torch.arange(args.crops), args.window:].mean(dim=1)
            oracle_ppl[tname] = math.exp(oserved.mean().item())

        set_prefix(N_full)
        amp = torch.autocast("cuda", dtype=torch.bfloat16, enabled=device.type == "cuda")
        with torch.no_grad(), amp:
            for b0 in range(0, args.crops, args.batch):
                xb = blocks[b0:b0 + args.batch].to(device)
                yb = xb.roll(shifts=-1, dims=1)
                logits, _, _ = model(xb)
                l = torch.nn.functional.cross_entropy(
                    logits.reshape(-1, logits.size(-1)), yb.reshape(-1),
                    reduction="none").view(xb.shape[0], bs)
                joint_losses.extend(l[:, args.window:].float().mean(dim=1).cpu().tolist())

    print("\nconfusion (rows=true domain, cols=routed prefix width):")
    print("          " + "".join(f"{r:>9}" for r in routes))
    for i, n in enumerate(names):
        print(f"{n:>9} " + "".join(f"{conf[i, j].item():>9}" for j in range(R)))
    if args.route_grid:
        print("\nserved ppl grid (rows=true domain, cols=forced width):")
        print("          " + "".join(f"{r:>9}" for r in routes))
        for gi, gn in enumerate(names):
            print(f"{gn:>9} " + "".join(f"{gv:>9.2f}" for gv in grid_rows[gi]))
    if oracle_ppl:
        print(f"\n{'domain':>9} {'routed':>8} {'oracle':>8}")
        for n in names:
            print(f"{n:>9} {routed_ppl[n]:>8.2f} {oracle_ppl.get(n, float('nan')):>8.2f}")
    else:
        print(f"\n{'domain':>9} {'routed':>8}")
        for n in names:
            print(f"{n:>9} {routed_ppl[n]:>8.2f}")
    print(f"\njoint full-width reference: ppl {math.exp(sum(joint_losses)/len(joint_losses)):.2f}"
          f"  (served positions only)")


if __name__ == "__main__":
    main()
