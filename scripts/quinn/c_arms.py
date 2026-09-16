#!/usr/bin/env python
"""Sonde C Arms 1-3: self-distilled residual addressing vs byte-n-gram (+ cascade).

Pre-registration: docs/plans/2026-09-11_sondeC-embedding-router-probe.md
  Arm 1  self-distilled head on BDH early residuals      (own-AI default)
  Arm 2  external sentence-embedding upper bound         (foreign competence, control only)
  Arm 3  byte-n-gram stage 1 + residual stage 2 cascade  (production shape)

Labels are always the A2 protocol -- the argmin-NLL route over the candidate
widths, which is exactly the quantity scripts/eval_router.py measures. No human
task IDs and no domain names are used as labels.

Modes
  extract  crops (byte-identical to eval_router: shared generator seed 1234) +
           A2 labels + pooled residuals per requested layer + raw crop bytes
           + label table (domain, crop, chosen width, per-route scores)  ->  <out>.npz/.tsv
  fit      arms 1 + byte-n-gram stage-1 baseline + cascade on an extract npz,
           held-out split, per layer, per domain, Wilson CI
  arm2     MiniLM sentence embeddings, same fit protocol (external upper bound)
  arm3     cascade sweep: cascade accuracy vs stage-2 fraction (from an npz)
"""
from __future__ import annotations

import argparse
import json
import math
import sys

import numpy as np
import torch

sys.path.insert(0, ".")

SEED = 1234          # identical to eval_router.py -> byte-identical crops


# --------------------------------------------------------------------- helpers
def wilson(k, n, z=1.96):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


R3_SEQ = "en es pl fr de cs da pt fi hu bg it et el sk sv ro nl sl lt".split()


def build_crops(dom_spec, mb, crops, bs, source="tail"):
    """Crop construction.

    source="tail" : byte-identical to scripts/eval_router.py (shared generator, seed 1234).
    source="r3"   : byte-identical to scripts/pi50/r3_byte_addressing.py -- same loader
                    test split, same per-language seeds (5000 + SEQ index) and same SEQ
                    order. Use this for the apples-to-apples P-C1 test against the
                    published P-R3 agreement (0.762; es/pl/sk at 0.00).
    """
    if source == "r3":
        from pipeline.data import _europarl_blocks
        names = [it.split(":", 1)[0]
                 for it in filter(None, map(str.strip, dom_spec.split(",")))]
        out = []
        for name in names:
            li = R3_SEQ.index(name)
            raw = _europarl_blocks("data", 30_000_000, langs=(name,))[name]
            d = torch.from_numpy(np.frombuffer(raw["test"], dtype=np.uint8).astype(np.int64))
            g = torch.Generator().manual_seed(5000 + li)
            idx = torch.randint(len(d) - bs - 1, (crops,), generator=g)
            out.append((name, torch.stack([d[int(i):int(i) + bs] for i in idx]).numpy()))
        return out
    g = torch.Generator().manual_seed(SEED)
    out = []
    for item in filter(None, map(str.strip, dom_spec.split(","))):
        name, path = item.split(":", 1)
        arr = np.frombuffer(open(path, "rb").read(mb * 1_000_000)[-2_000_000:],
                            dtype=np.uint8)
        hi = len(arr) - bs - 1
        idx = torch.randint(hi, (crops,), generator=g)
        out.append((name, np.stack([arr[int(i):int(i) + bs] for i in idx]).astype(np.int64)))
    return out


def split_idx(dom, frac=0.7, seed=7):
    """Per-domain shuffle split so every class is represented in train and test."""
    rng = np.random.default_rng(seed)
    tr, te = [], []
    for d in np.unique(dom):
        ix = np.where(dom == d)[0]
        rng.shuffle(ix)
        cut = int(len(ix) * frac)
        tr += list(ix[:cut])
        te += list(ix[cut:])
    return np.array(tr), np.array(te)


class ByteNGram:
    """Stage-1 cascade predictor: per-class char n-gram with add-1 smoothing."""

    def __init__(self, n=4, vocab=256):
        self.n = n
        self.vocab = vocab
        self.ng = {}
        self.cx = {}

    def fit(self, cls, raws):
        c = self.ng.setdefault(cls, {})
        x = self.cx.setdefault(cls, {})
        n = self.n
        for r in raws:
            b = bytes(r)
            for i in range(len(b) - n + 1):
                k = b[i:i + n]
                c[k] = c.get(k, 0) + 1
                ctx = b[i:i + n - 1]
                x[ctx] = x.get(ctx, 0) + 1

    def logp(self, cls, r):
        b = bytes(r)
        c = self.ng[cls]
        x = self.cx[cls]
        n = self.n
        s = 0.0
        for i in range(len(b) - n + 1):
            s += math.log((c.get(b[i:i + n], 0) + 1.0)
                          / (x.get(b[i:i + n - 1], 0) + self.vocab))
        return s

    def predict_with_margin(self, raws, classes):
        pred, margin, order = [], [], []
        for r in raws:
            lp = [(self.logp(c, r), c) for c in classes]
            lp.sort(reverse=True)
            pred.append(classes.index(lp[0][1]))
            margin.append((lp[0][0] - lp[1][0]) / max(1, len(r)))
        return np.array(pred), np.array(margin)


# ------------------------------------------------------------------- Arm 1/3
class ResidualHead(torch.nn.Module):
    def __init__(self, d_in, n_out, hidden=0):
        super().__init__()
        if hidden:
            self.net = torch.nn.Sequential(
                torch.nn.Linear(d_in, hidden), torch.nn.ReLU(),
                torch.nn.Linear(hidden, n_out))
        else:
            self.net = torch.nn.Linear(d_in, n_out)

    def forward(self, x):
        return self.net(x)


def train_head(Xtr, ytr, n_out, dev, hidden=0, steps=600, lr=3e-2, wd=1e-4, seed=0):
    torch.manual_seed(seed)
    m = ResidualHead(Xtr.shape[1], n_out, hidden).to(dev)
    opt = torch.optim.Adam(m.parameters(), lr=lr, weight_decay=wd)
    lossf = torch.nn.CrossEntropyLoss()
    Xt = torch.from_numpy(Xtr).to(dev)
    yt = torch.from_numpy(ytr).to(dev)
    for _ in range(steps):
        opt.zero_grad()
        loss = lossf(m(Xt), yt)
        loss.backward()
        opt.step()
    m.eval()
    return m


@torch.no_grad()
def predict_head(m, X, dev):
    out = m(torch.from_numpy(X.astype(np.float32)).to(dev))
    return out.argmax(dim=1).cpu().numpy(), out.softmax(dim=1).cpu().numpy()


def standardize(Xtr, Xte):
    mu = Xtr.mean(axis=0, keepdims=True)
    sd = Xtr.std(axis=0, keepdims=True) + 1e-6
    return (Xtr - mu) / sd, (Xte - mu) / sd


def acc_line(tag, y_true, y_pred, dom, dom_te):
    k = int((y_true == y_pred).sum())
    n = len(y_true)
    lo, hi = wilson(k, n)
    out = [f"{tag:<26} acc {k}/{n} = {k / n:.4f}  Wilson [{lo:.3f}, {hi:.3f}]  per-domain:"]
    for d in np.unique(dom_te):
        m = dom_te == d
        kk = int((y_true[m] == y_pred[m]).sum())
        nn = int(m.sum())
        out.append(f"      {d:<10} {kk}/{nn}")
    return "\n".join(out)


# ---------------------------------------------------------------------- modes
def cmd_extract(args):
    from pipeline.analyze import _load_model

    model, cfg = _load_model(args.ckpt)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(dev).eval()
    C = model.config
    nh, D = C.n_head, C.n_embd
    N_full = C.mlp_internal_dim_multiplier * D // nh
    bs = cfg["block_size"]
    routes = [int(r) for r in args.routes.split(",")]
    layers = [int(x) for x in args.layers.split(",")]
    doms = build_crops(args.domains, args.mb, args.crops, bs, args.crop_source)

    enc_b = model.encoder.data.clone()
    encv_b = model.encoder_v.data.clone()
    dec_b = model.decoder.data.clone()

    def set_prefix(k):
        m = torch.zeros(N_full, device=dev)
        m[:k] = 1.0
        with torch.no_grad():
            model.encoder.data.copy_(enc_b * m.view(1, 1, -1))
            model.encoder_v.data.copy_(encv_b * m.view(1, 1, -1))
            model.decoder.data.copy_(dec_b * m.repeat(nh).unsqueeze(1))

    def amp():
        return torch.autocast("cuda", dtype=torch.bfloat16, enabled=dev.type == "cuda")

    R = len(routes)
    feats, lab, domn, cropn, raws, score_tab = [], [], [], [], [], []
    for name, blocks in doms:
        n = blocks.shape[0]
        scores = np.zeros((R, n), dtype=np.float64)
        for ri, k in enumerate(routes):
            set_prefix(min(k, N_full))
            with torch.no_grad(), amp():
                for b0 in range(0, n, args.batch):
                    xb = torch.from_numpy(blocks[b0:b0 + args.batch]).to(dev)
                    yb = xb.roll(shifts=-1, dims=1)
                    logits, _, _ = model(xb)
                    l = torch.nn.functional.cross_entropy(
                        logits.reshape(-1, logits.size(-1)), yb.reshape(-1),
                        reduction="none").view(xb.shape[0], bs)
                    scores[ri, b0:b0 + xb.shape[0]] = \
                        l[:, :args.window].float().mean(dim=1).cpu().numpy()
        choice = scores.argmin(axis=0)

        # residuals at full width (the served model), captured on model.ln:
        # ln is called 1 + 3*n_layer times per forward; post-layer-L residual is 3L+3.
        buf = []
        h = model.ln.register_forward_hook(lambda mod, inp, out: buf.append(out.detach()))
        set_prefix(N_full)
        with torch.no_grad(), amp():
            for b0 in range(0, n, args.batch):
                xb = torch.from_numpy(blocks[b0:b0 + args.batch]).to(dev)
                buf.clear()
                model(xb)
                per_layer = [buf[3 * L + 3][:, 0, args.p0:args.p1, :].float().mean(dim=1)
                             for L in layers]
                feats.append(torch.stack(per_layer, dim=1).cpu().numpy())
        h.remove()

        lab += list(choice)
        domn += [name] * n
        cropn += list(range(n))
        raws.append(blocks)
        for ci in range(n):
            score_tab.append((name, ci, routes[int(choice[ci])],
                              [round(float(scores[ri, ci]), 6) for ri in range(R)]))
        print(f"[extract] {name}: n={n} label-dist="
              f"{np.bincount(choice, minlength=R).tolist()} routes={routes}", flush=True)

    X = np.concatenate(feats).astype(np.float32)          # (N, nL, D)
    np.savez_compressed(args.out, X=X, y=np.array(lab, dtype=np.int64),
                        dom=np.array(domn), crop=np.array(cropn),
                        raw=np.concatenate(raws).astype(np.uint8),
                        routes=np.array(routes), layers=np.array(layers),
                        p0=args.p0, p1=args.p1, ckpt=args.ckpt,
                        crop_source=args.crop_source)
    with open(args.out + ".labels.tsv", "w") as fh:
        fh.write("domain\tcrop\tchosen_width\t" +
                 "\t".join(f"score_{r}" for r in routes) + "\n")
        for d, ci, w, sc in score_tab:
            fh.write(f"{d}\t{ci}\t{w}\t" + "\t".join(str(x) for x in sc) + "\n")
    print(f"[extract] saved {args.out}: X{X.shape} y{len(lab)} layers={layers} "
          f"p[{args.p0}:{args.p1}] ckpt={args.ckpt}")
    print(f"[extract] labels -> {args.out}.labels.tsv ({len(score_tab)} rows)")


def load_npz(path):
    z = np.load(path, allow_pickle=False)
    return {k: z[k] for k in z.files}


def cmd_fit(args):
    z = load_npz(args.npz)
    X, y, dom, raw = z["X"], z["y"], z["dom"], z["raw"]
    routes = [int(r) for r in z["routes"]]
    layers = [int(r) for r in z["layers"]]
    nL, D = X.shape[1], X.shape[2]
    R = len(routes)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tr, te = split_idx(dom, frac=args.train_frac)
    dom_te = dom[te]
    print(f"[fit] npz={args.npz} N={len(y)} train={len(tr)} test={len(te)} "
          f"routes={routes} layers={layers} classes={R}")
    results = {}

    # ---- Arm 3 stage 1: byte-n-gram (also the P-R3-style baseline)
    ng = ByteNGram(n=args.ngram)
    classes = sorted(set(dom.tolist()))
    for c in classes:
        idx = tr[dom[tr] == c]
        ng.fit(c, [raw[i] for i in idx])
    ng_pred, ng_margin = ng.predict_with_margin([raw[i] for i in te], classes)
    ng_pred = np.array([list(classes).index(classes[p]) for p in ng_pred])
    # label = route index chosen by argmin-NLL; map domain-class -> route index
    dom_to_route = {}
    for c in classes:
        m = dom == c
        dom_to_route[c] = int(np.bincount(y[m], minlength=R).argmax())
    ng_pred_route = np.array([dom_to_route[classes[p]] for p in ng_pred])
    y_te = y[te]
    print("\n" + acc_line("byte-n-gram (stage 1)", y_te, ng_pred_route, dom, dom_te))
    results["byte_ngram"] = float((y_te == ng_pred_route).mean())

    # ---- Arm 1: residual head per layer (linear + MLP)
    for li, L in enumerate(layers):
        A = X[:, li, :]
        Atr, Ate = standardize(A[tr].astype(np.float32), A[te].astype(np.float32))
        for tag, hid in (("linear", 0), ("mlp256", 256)):
            m = train_head(Atr, y[tr], R, dev, hidden=hid)
            pr, _ = predict_head(m, Ate, dev)
            name = f"arm1 L{L} {tag}"
            print("\n" + acc_line(name, y_te, pr, dom, dom_te))
            results[name] = float((y_te == pr).mean())

        # ---- Arm 3: cascade (stage 1 = n-gram, stage 2 = this layer's linear head)
        m = train_head(Atr, y[tr], R, dev, hidden=0)
        pr, _ = predict_head(m, Ate, dev)
        for frac in (0.0, 0.1, 0.2, 0.3):
            if frac <= 0:
                thr = -1e9
            else:
                thr = float(np.quantile(ng_margin, frac))
            use2 = ng_margin < thr
            cas = np.where(use2, pr, ng_pred_route)
            k = int((y_te == cas).sum())
            lo, hi = wilson(k, len(y_te))
            s2 = int(use2.sum())
            print(f"\n[arm3 L{L}] stage2-frac={frac:.1f} -> used {s2}/{len(y_te)} "
                  f"({s2 / len(y_te):.3f})  cascade acc {k}/{len(y_te)}={k / len(y_te):.4f} "
                  f"Wilson [{lo:.3f}, {hi:.3f}]")
            results[f"arm3 L{L} s2={frac:.1f}"] = float(k / len(y_te))

    with open(args.npz + ".fit.json", "w") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(f"\n[fit] summary -> {args.npz}.fit.json")
    for k in sorted(results):
        print(f"  {k:<22} {results[k]:.4f}")


def cmd_arm2(args):
    from sentence_transformers import SentenceTransformer
    z = load_npz(args.npz)
    y, dom, raw = z["y"], z["dom"], z["raw"]
    routes = [int(r) for r in z["routes"]]
    R = len(routes)
    tr, te = split_idx(dom, frac=args.train_frac)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    enc = SentenceTransformer(args.model)
    texts = [bytes(r).decode("latin-1") for r in raw]
    E = enc.encode(texts, batch_size=32, show_progress_bar=False,
                   convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)
    print(f"[arm2] model={args.model} emb={E.shape}")
    Etr, Ete = standardize(E[tr], E[te])
    m = train_head(Etr, y[tr], R, dev, hidden=0)
    pr, _ = predict_head(m, Ete, dev)
    print("\n" + acc_line(f"arm2 {args.model.split('/')[-1]}", y[te], pr, dom, dom[te]))
    m2 = train_head(Etr, y[tr], R, dev, hidden=256)
    pr2, _ = predict_head(m2, Ete, dev)
    print("\n" + acc_line("arm2 + mlp256", y[te], pr2, dom, dom[te]))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    e = sub.add_parser("extract")
    e.add_argument("ckpt")
    e.add_argument("--domains", required=True)
    e.add_argument("--routes", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--mb", type=int, default=30)
    e.add_argument("--crops", type=int, default=200)
    e.add_argument("--batch", type=int, default=4)
    e.add_argument("--window", type=int, default=128)
    e.add_argument("--layers", default="0,1")
    e.add_argument("--p0", type=int, default=32)
    e.add_argument("--p1", type=int, default=96)
    e.add_argument("--crop-source", default="tail", choices=["tail", "r3"],
                   help="tail = eval_router crops (default); r3 = P-R3 loader crops")

    f = sub.add_parser("fit")
    f.add_argument("npz")
    f.add_argument("--train-frac", type=float, default=0.7)
    f.add_argument("--ngram", type=int, default=4)

    a2 = sub.add_parser("arm2")
    a2.add_argument("npz")
    a2.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    a2.add_argument("--train-frac", type=float, default=0.7)

    args = ap.parse_args()
    {"extract": cmd_extract, "fit": cmd_fit, "arm2": cmd_arm2}[args.mode](args)


if __name__ == "__main__":
    main()
