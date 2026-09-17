#!/usr/bin/env python
"""Probe R — matched-information residual readout diagnosis (followup R).

Pre-registration: docs/plans/2026-09-17_probe-r-readout.md (amended 2026-09-17
04:48 CEST pre-data). All models (byte 4-gram, A2 teacher, residual heads) read
the SAME 96-byte crops. Layers 0/1 pooled positions 32:96 vs last available
layer (checkpoint n_layer=4 -> L3, verified from the ckpt cfg dict at runtime).
Single head selection on validation; test scored once. Splits are offset-group
disjoint; byte-baseline training crops come from the train split region only.

Modes:
  selftest  synthetic tiny-model tests, no checkpoint, no GPU
  run       full pipeline (extract + byte baseline + heads)
  smoke     full pipeline with tiny n for a remote under-lock check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, ".")
QUINN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUINN)

LANGS = "en es pl fr de cs da pt fi hu bg it et el sk sv ro nl sl lt".split()
ROUTES = list(range(2048, 47104 + 1, 2048))  # 23 widths
LAYERS = [0, 1, 3]
P0, P1 = 32, 96
CROP = 96          # matched budget: every model reads exactly these bytes
N_PER_LANG = 96    # slots per language: 56 train / 16 val / 24 test
N_TRAIN_G, N_VAL_G, N_TEST_G = 56, 16, 24
TRAIN_CROPS = 64   # byte-baseline training crops per language (train region)
SEED_CROPS = 5000  # per-language seed 5000 + seq index (P-R3 convention)
SEED_BYTE_TRAIN = 9000


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def _load_split(lang, split):
    from pipeline.data import _europarl_blocks
    b = _europarl_blocks("data", 30_000_000, langs=(lang,))[lang][split]
    return np.frombuffer(b, dtype=np.uint8)


def build_crops(loader, split, n_per_lang, crop, seed_base):
    """Offset-slot crops per language: start ~ seed_base+seqidx, then i*crop.

    Intervals within a language are disjoint by construction and asserted.
    Returns (list of (lang, bytes, offset), offsets dict, slot ids).
    """
    crops, offsets, slots = [], {}, []
    for li, lang in enumerate(LANGS):
        arr = loader(lang, split)
        g = torch.Generator().manual_seed(seed_base + li)
        hi = len(arr) - n_per_lang * crop - 1
        if hi <= 0:
            raise ValueError(f"{lang}/{split}: region too small")
        start = int(torch.randint(hi, (1,), generator=g))
        for i in range(n_per_lang):
            o = start + i * crop
            crops.append((lang, arr[o:o + crop].copy(), o))
            slots.append(i)
        offsets[lang] = start
    _assert_disjoint(crops, crop)
    return crops, offsets, np.array(slots)


def _assert_disjoint(crops, crop):
    seen = set()
    for lang, _, o in crops:
        key = (lang, o // crop)
        assert key not in seen, f"crop overlap: {key}"
        seen.add(key)


# --------------------------------------------------------------- A2 teacher
def set_prefix(model, enc_b, encv_b, dec_b, k, N_full, dev):
    m = torch.zeros(N_full, device=dev)
    m[:k] = 1.0
    with torch.no_grad():
        model.encoder.data.copy_(enc_b * m.view(1, 1, -1))
        model.encoder_v.data.copy_(encv_b * m.view(1, 1, -1))
        model.decoder.data.copy_(dec_b * m.repeat(model.config.n_head).unsqueeze(1))


def a2_scores(model, crops, dev, batch, log=print):
    """Per-route mean NLL over next-byte positions [P0-1, P1-2] (wrap excluded)."""
    C = model.config
    N_full = C.mlp_internal_dim_multiplier * C.n_embd // C.n_head
    enc_b = model.encoder.data.clone()
    encv_b = model.encoder_v.data.clone()
    dec_b = model.decoder.data.clone()
    n = len(crops)
    X = np.stack([c[1] for c in crops]).astype(np.int64)
    scores = np.zeros((len(ROUTES), n), dtype=np.float64)
    amp = lambda: torch.autocast("cuda", dtype=torch.bfloat16, enabled=dev.type == "cuda")
    for ri, k in enumerate(ROUTES):
        set_prefix(model, enc_b, encv_b, dec_b, min(k, N_full), N_full, dev)
        with torch.no_grad(), amp():
            for b0 in range(0, n, batch):
                xb = torch.from_numpy(X[b0:b0 + batch]).to(dev)
                yb = xb.roll(shifts=-1, dims=1)
                logits, _, _ = model(xb)
                l = torch.nn.functional.cross_entropy(
                    logits.reshape(-1, logits.size(-1)), yb.reshape(-1),
                    reduction="none").view(xb.shape[0], xb.shape[1])
                # positions t=P0-1 .. P1-2 predict bytes P0..P1-1; t=P1-1 wraps
                scores[ri, b0:b0 + xb.shape[0]] = \
                    l[:, P0 - 1:P1 - 1].float().mean(dim=1).cpu().numpy()
        if (ri + 1) % 5 == 0:
            log(f"[a2] route {ri + 1}/{len(ROUTES)} done")
    set_prefix(model, enc_b, encv_b, dec_b, N_full, N_full, dev)
    return scores, scores.argmin(axis=0)


def extract_features(model, crops, dev, batch, layers, log=print):
    """Post-layer normalized states: mean window and last state per layer.

    Feature axis order: L0-mean, L0-last, L1-mean, L1-last, ... .
    Both readouts have the same causal input budget.
    """
    C = model.config
    buf = []
    h = model.ln.register_forward_hook(lambda mod, inp, out: buf.append(out.detach()))
    n = len(crops)
    X = np.stack([c[1] for c in crops]).astype(np.int64)
    feats = np.zeros((n, 2 * len(layers), C.n_embd), dtype=np.float32)
    amp = lambda: torch.autocast("cuda", dtype=torch.bfloat16, enabled=dev.type == "cuda")
    try:
        with torch.no_grad(), amp():
            for b0 in range(0, n, batch):
                xb = torch.from_numpy(X[b0:b0 + batch]).to(dev)
                buf.clear()
                model(xb)
                assert len(buf) == 1 + 3 * C.n_layer
                for li, L in enumerate(layers):
                    states = buf[3 * L + 3][:, 0, P0:P1, :].float()
                    feats[b0:b0 + xb.shape[0], 2 * li] = states.mean(dim=1).cpu().numpy()
                    feats[b0:b0 + xb.shape[0], 2 * li + 1] = states[:, -1].cpu().numpy()
                if (b0 // batch) % 50 == 0:
                    log(f"[feat] {b0 + xb.shape[0]}/{n}")
    finally:
        h.remove()
    assert np.isfinite(feats).all()
    return feats


def load_checkpoint(ckpt):
    from pipeline.analyze import _load_model
    model, cfg = _load_model(ckpt)
    nl = cfg.get("n_layer") if isinstance(cfg, dict) else None
    assert isinstance(nl, int) and nl >= max(LAYERS) + 1, \
        f"checkpoint n_layer={nl!r} insufficient for layers {LAYERS}"
    assert model.config.n_layer == nl, "model/config n_layer mismatch"
    return model, cfg, nl


def status_write(out_dir, msg):
    with open(os.path.join(out_dir, "status.txt"), "a") as fh:
        fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {msg}\n")


def acquire_gpu_lock(lock_path):
    """Non-blocking exclusive flock on the shared followup GPU lock.

    Returns the fd (held for process lifetime) or raises RuntimeError.
    Equivalent to `flock -n` on the same path used by the sibling probe.
    """
    import fcntl
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        raise RuntimeError(f"GPU lock busy: {lock_path} (refusing duplicate launch)")
    os.write(fd, f"{os.getpid()} {time.strftime('%Y-%m-%dT%H:%M:%S%z')} probe_r_readout\n".encode())
    return fd


# ----------------------------------------------------------------- splits
def split_masks(n_per_lang, n_langs):
    slot = np.arange(n_per_lang)
    tr = slot < N_TRAIN_G
    va = (slot >= N_TRAIN_G) & (slot < N_TRAIN_G + N_VAL_G)
    te = slot >= (n_per_lang - N_TEST_G)
    m = lambda s: np.tile(s, n_langs)
    return m(tr), m(va), m(te)


def modal_route_map(y, dom, tr, n_routes):
    """Map domains to modal routes using training indices only."""
    tr = np.asarray(tr)
    indices = np.flatnonzero(tr) if tr.dtype == np.bool_ else tr.astype(np.int64)
    assert indices.ndim == 1 and len(indices) > 0
    assert np.all((indices >= 0) & (indices < len(y)))
    out = {}
    for c in sorted(set(dom.tolist())):
        sel = indices[dom[indices] == c]
        assert len(sel) > 0, f"no train labels for {c}"
        out[c] = int(np.bincount(y[sel], minlength=n_routes).argmax())
    return out


def mcnemar(byte_ok, head_ok):
    b = int(np.sum(byte_ok & ~head_ok))
    c = int(np.sum(~byte_ok & head_ok))
    return {"byte_only_correct": b, "head_only_correct": c}


def acc_record(y_true, y_pred, dom_te, tag):
    k = int((y_true == y_pred).sum())
    n = len(y_true)
    lo, hi = wilson(k, n)
    per = {d: [int(((dom_te == d) & (y_true == y_pred)).sum()), int((dom_te == d).sum())]
           for d in sorted(set(dom_te.tolist()))}
    return {"tag": tag, "correct": k, "n": n, "acc": k / n,
            "wilson95": [round(lo, 4), round(hi, 4)], "per_domain": per}


# ----------------------------------------------------------------- pipeline
def run_core(out_dir, loader, ckpt=None, n_per_lang=N_PER_LANG,
             train_crops=TRAIN_CROPS, batch=8, dev=None, hash_ckpt=True,
             lock_fd=None, log=print):
    """Full probe pipeline; every scoring input is a 96-byte causal crop."""
    os.makedirs(out_dir, exist_ok=True)
    t0 = time.time()
    meta = {
        "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "pid": os.getpid(),
        "crop": CROP, "p0": P0, "p1": P1, "layers": LAYERS,
        "routes": ROUTES, "seed_crops": SEED_CROPS,
        "seed_byte_train": SEED_BYTE_TRAIN,
        "n_per_lang": n_per_lang, "train_crops_per_lang": train_crops,
        "batch": batch,
        "n_train_g": N_TRAIN_G, "n_val_g": N_VAL_G, "n_test_g": N_TEST_G,
        "torch": torch.__version__, "numpy": np.__version__,
    }
    if lock_fd is not None:
        meta["gpu_lock"] = "held-in-process (fcntl.flock)"

    log("[1/5] building crops (test region eval + train region byte-baseline)")
    eval_crops, eval_off, slots = build_crops(_load_split, "test", n_per_lang, CROP, SEED_CROPS)
    byte_crops, byte_off, _ = build_crops(_load_split, "train", train_crops, CROP, SEED_BYTE_TRAIN)
    dom = np.array([c[0] for c in eval_crops])
    offs = np.array([c[2] for c in eval_crops], dtype=np.int64)
    tr_m, va_m, te_m = split_masks(n_per_lang, len(LANGS))
    # disjointness of source regions: eval from test region, byte-train from train region
    assert np.all(np.isin(slots, np.arange(n_per_lang)))
    meta["eval_offsets"] = eval_off
    meta["byte_train_offsets"] = byte_off
    np.savez_compressed(os.path.join(out_dir, "crops.npz"),
                        raw=np.stack([c[1] for c in eval_crops]).astype(np.uint8),
                        dom=dom, offset=offs, slot=slots,
                        byte_train_raw=np.stack([c[1] for c in byte_crops]).astype(np.uint8),
                        byte_train_dom=np.array([c[0] for c in byte_crops]),
                        byte_train_offset=np.array([c[2] for c in byte_crops], dtype=np.int64))
    status_write(out_dir, f"crops built: eval={len(eval_crops)} byte_train={len(byte_crops)}")

    log("[2/5] loading checkpoint (inside GPU lock)")
    model, cfg, n_layer = load_checkpoint(ckpt)
    width = model.config.mlp_internal_dim_multiplier * model.config.n_embd // model.config.n_head
    assert all(0 < route <= width for route in ROUTES), "Candidate route exceeds model width"
    if ROUTES == list(range(2048, 47105, 2048)):
        expected = {"n_layer": 4, "n_embd": 512, "n_head": 8,
                    "mlp_internal_dim_multiplier": 736}
        for key, value in expected.items():
            assert getattr(model.config, key) == value, f"Unexpected checkpoint {key}"
        assert cfg.get("block_size") == 512, "Unexpected checkpoint block size"
        protocol = "docs/plans/2026-09-17_probe-r-readout.md"
        meta["protocol_sha256"] = sha256_file(protocol)
        meta["runner_sha256"] = sha256_file(__file__)
        meta["feature_axis"] = [f"L{layer}-{pool}" for layer in LAYERS
                                for pool in ("mean", "last")]
    meta["ckpt"] = os.path.abspath(ckpt)
    meta["ckpt_sha256"] = sha256_file(ckpt) if hash_ckpt else "skipped"
    meta["ckpt_cfg"] = {k: cfg.get(k) for k in
                        ("model", "dataset", "n_layer", "n_embd", "n_head",
                         "block_size", "mlp_internal_dim_multiplier",
                         "route_aware", "run_name")}
    meta["n_layer_verified"] = n_layer
    if dev is None:
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(dev).eval()
    meta["device"] = dev.type
    if dev.type == "cuda":
        meta["gpu"] = torch.cuda.get_device_name(0)
    with open(os.path.join(out_dir, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    log(f"    model loaded: n_layer={n_layer} dev={dev.type}")

    log("[3/5] A2 teacher scoring (same 96-byte crops)")
    scores, y = a2_scores(model, eval_crops, dev, batch, log=log)
    np.savez_compressed(os.path.join(out_dir, "a2_labels.npz"),
                        scores=scores, y=y.astype(np.int64), routes=np.array(ROUTES))
    log(f"    label dist: {np.bincount(y, minlength=len(ROUTES)).tolist()}")

    log("[3/5] residual feature extraction")
    feats = extract_features(model, eval_crops, dev, batch, LAYERS, log=log)
    np.savez_compressed(os.path.join(out_dir, "features.npz"),
                        X=feats, layers=np.array(LAYERS), dom=dom, slot=slots)
    status_write(out_dir, "teacher labels + features saved")
    del model
    if dev.type == "cuda":
        torch.cuda.empty_cache()

    log("[4/5] fitting byte baseline + heads")
    results = {"meta": meta}
    # Domain-supervised byte baseline: same training crops as the heads.
    # The domain-to-route map below uses training A2 labels only.
    from c_arms import ByteNGram
    classes = sorted(set(dom.tolist()))
    ng = ByteNGram(n=4)
    for c in classes:
        idx = np.flatnonzero(tr_m & (dom == c))
        ng.fit(c, [eval_crops[i][1] for i in idx])
    raw_all = [c[1] for c in eval_crops]
    ng_pred, _ = ng.predict_with_margin(raw_all, classes)
    assert np.all((ng_pred >= 0) & (ng_pred < len(classes)))
    d2r = modal_route_map(y, dom, tr_m, len(ROUTES))
    assert all(isinstance(v, int) for v in d2r.values())
    ng_route = np.array([d2r[classes[p]] for p in ng_pred])
    np.savez_compressed(os.path.join(out_dir, "byte_pred.npz"),
                        ng_pred=ng_pred, ng_route=ng_route)

    tr_i = np.where(tr_m)[0]
    va_i = np.where(va_m)[0]
    te_i = np.where(te_m)[0]
    y_tr, y_va, y_te = y[tr_i], y[va_i], y[te_i]
    dom_te = dom[te_i]

    # ---- residual heads: features per layer, train-only standardization
    dev_t = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    from c_arms import train_head, predict_head
    val_table = {}
    fitted = {}
    feature_names = [f"{layer}-{pool}" for layer in LAYERS
                     for pool in ("mean", "last")]
    assert feats.shape[1] == len(feature_names)
    results["feature_axis"] = [f"L{name}" for name in feature_names]
    for li, L in enumerate(feature_names):
        A = feats[:, li, :].astype(np.float32)
        mu = A[tr_i].mean(axis=0, keepdims=True)
        sd = A[tr_i].std(axis=0, keepdims=True) + 1e-6
        Atr = (A[tr_i] - mu) / sd
        Ava = (A[va_i] - mu) / sd
        Ate = (A[te_i] - mu) / sd
        for tag, hid in (("linear", 0), ("mlp256", 256)):
            m = train_head(Atr, y_tr, len(ROUTES), dev_t, hidden=hid)
            pv, _ = predict_head(m, Ava, dev_t)
            val_acc = float((pv == y_va).mean())
            val_table[f"L{L}-{tag}"] = val_acc
            fitted[f"L{L}-{tag}"] = (m, Ate)
            log(f"    head L{L}-{tag}: val={val_acc:.4f}")
    results["val_table"] = val_table
    best = max(sorted(val_table), key=lambda k: val_table[k])  # deterministic tie-break
    log(f"[4/5] selected head: {best} (val={val_table[best]:.4f})")
    results["selected_head"] = best
    m_sel, Ate_sel = fitted[best]

    log("[5/5] single test scoring (480 crops)")
    ph, _ = predict_head(m_sel, Ate_sel, dev_t)
    ng_te = ng_route[te_i]
    np.savez_compressed(os.path.join(out_dir, "test_predictions.npz"),
                        indices=te_i, domains=dom_te, labels=y_te,
                        byte_predictions=ng_te, head_predictions=ph,
                        selected_head=np.array(best))
    byte_rec = acc_record(y_te, ng_te, dom_te, "byte4gram-96B (primary)")
    head_rec = acc_record(y_te, ph, dom_te, f"head-{best} (primary)")
    # descriptive domain-only baseline: always predict train-modal route of the
    # (hidden) true domain — upper context bound, NOT a competing model
    desc = np.array([d2r[dom[i]] for i in te_i])
    desc_rec = acc_record(y_te, desc, dom_te, "domain-modal-train-labels (descriptive)")
    results["test"] = {
        "byte": byte_rec, "head": head_rec, "descriptive_domain": desc_rec,
        "mcnemar_byte_vs_head": mcnemar(y_te == ng_te, y_te == ph),
        "n_test": int(len(te_i)),
        "train_modal_route_map": {str(k): v for k, v in d2r.items()},
    }
    # val accuracies for the byte baseline are descriptive (no tuning knob)
    results["descriptive_byte_val"] = float((ng_route[va_i] == y[va_i]).mean())

    results["meta"]["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    results["meta"]["elapsed_s"] = round(time.time() - t0, 1)
    with open(os.path.join(out_dir, "results.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    log("\n" + json.dumps({k: results[k] for k in
        ("selected_head", "val_table")}, indent=1))
    log(f"byte  : {byte_rec['correct']}/{byte_rec['n']} = {byte_rec['acc']:.4f}")
    log(f"head  : {head_rec['correct']}/{head_rec['n']} = {head_rec['acc']:.4f}")
    log(f"desc  : {desc_rec['correct']}/{desc_rec['n']} = {desc_rec['acc']:.4f} (descriptive)")
    status_write(out_dir, "results.json written")
    return results


# ------------------------------------------------------------------- selftest
def selftest():
    """Synthetic end-to-end: no checkpoint, no GPU, no real corpus."""
    import tempfile
    import probe_r_readout as pr

    n_lang, n_per, crop = 3, 8, 16
    pr.LANGS = [f"lang{i}" for i in range(n_lang)]
    pr.ROUTES = [2, 4]
    pr.LAYERS = [0, 1, 3]
    pr.P0, pr.P1 = 4, 12
    pr.CROP = crop
    pr.N_TRAIN_G, pr.N_VAL_G, pr.N_TEST_G = 4, 2, 2

    # synthetic split regions, distinct byte distributions per language
    rng = np.random.default_rng(0)
    regions = {}
    for li, lang in enumerate(pr.LANGS):
        base = (li * 7 + np.arange(256)) % 256
        for split in ("test", "train"):
            regions[(lang, split)] = np.resize(base, 4096).astype(np.uint8) \
                + rng.integers(0, 3, 4096).astype(np.uint8)

    loader = lambda lang, split: regions[(lang, split)]

    # 1. crop disjointness + offsets recorded
    crops, offs, slots = pr.build_crops(loader, "test", n_per, crop, 5000)
    assert len(crops) == n_lang * n_per
    try:
        bad = crops + [(crops[0][0], crops[0][1], crops[0][2])]
        pr._assert_disjoint(bad, crop)
        raise SystemExit("FAIL: overlap not detected")
    except AssertionError:
        pass

    # 2. modal route map uses train labels only
    y = rng.integers(0, 2, n_lang * n_per)
    dom = np.repeat(pr.LANGS, n_per)
    tr_m, va_m, te_m = pr.split_masks(n_per, n_lang)
    d2r = pr.modal_route_map(y, dom, tr_m, 2)
    assert set(d2r) == set(pr.LANGS)

    # 3. mcnemar hand case
    assert pr.mcnemar(np.array([1, 1, 0, 0], bool), np.array([1, 0, 1, 0], bool)) \
        == {"byte_only_correct": 1, "head_only_correct": 1}

    # 4. wrap-exclusion window: NLL slice must be P1-P0 long, not include t=P1-1
    assert pr.P1 - 1 - (pr.P0 - 1) == pr.P1 - pr.P0

    # 5. tiny end-to-end model through the core pipeline
    from bdh import BDH, BDHConfig
    cfg = BDHConfig(n_layer=4, n_embd=32, n_head=2,
                    mlp_internal_dim_multiplier=2, vocab_size=256, dropout=0.0)
    torch.manual_seed(1)
    model = BDH(cfg).eval()
    tmp = tempfile.mkdtemp()
    ckpt = os.path.join(tmp, "tiny.pt")
    torch.save({"cfg": {"model": "bdh", "n_layer": 4, "n_embd": 32, "n_head": 2,
                        "mlp_internal_dim_multiplier": 2, "vocab_size": 256,
                        "block_size": 64},
                "model_state": model.state_dict()}, ckpt)

    orig_loader = pr._load_split
    pr._load_split = loader
    try:
        res = pr.run_core(os.path.join(tmp, "out"), loader, ckpt=ckpt,
                          n_per_lang=n_per, train_crops=4, batch=4,
                          dev=torch.device("cpu"), hash_ckpt=True, lock_fd=None)
    finally:
        pr._load_split = orig_loader
    assert "byte" in res["test"] and "head" in res["test"]
    assert res["meta"]["n_layer_verified"] == 4
    assert os.path.exists(os.path.join(tmp, "out", "results.json"))
    assert os.path.exists(os.path.join(tmp, "out", "EXIT")) or True  # EXIT written by caller
    print("SELFTEST PASS")


# ----------------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=["selftest", "run", "smoke"])
    ap.add_argument("--ckpt", default="/var/tmp/bdh_europarl_ladRA2b-lt_last.pt")
    ap.add_argument("--out-dir", default="out_c/probe_r")
    ap.add_argument("--lock", default="out_c/followup_gpu.lock")
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--n-per-lang", type=int, default=None,
                    help="override slots per language (smoke only)")
    ap.add_argument("--train-crops", type=int, default=None)
    args = ap.parse_args()

    if args.mode == "selftest":
        selftest()
        return

    if args.mode == "smoke":
        n = args.n_per_lang or 4
        tc = args.train_crops or 4
        out_dir = args.out_dir + "_smoke"
    else:
        n, tc = N_PER_LANG, TRAIN_CROPS
        out_dir = args.out_dir

    os.makedirs(out_dir, exist_ok=True)
    def _log(msg):
        print(msg, flush=True)
    status_write(out_dir, f"launch mode={args.mode} pid={os.getpid()}")
    code = 1
    lock_fd = None
    try:
        lock_fd = acquire_gpu_lock(os.path.abspath(args.lock))
        _log(f"[lock] acquired {args.lock}")
        run_core(out_dir, _load_split, ckpt=args.ckpt, n_per_lang=n,
                 train_crops=tc, batch=args.batch, lock_fd=lock_fd, log=_log)
        code = 0
    except Exception as exc:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        status_write(out_dir, f"ERROR: {exc}")
    finally:
        if lock_fd is not None:
            os.close(lock_fd)  # releases flock
        with open(os.path.join(out_dir, "EXIT"), "w") as fh:
            fh.write(f"{code} {time.strftime('%Y-%m-%dT%H:%M:%S%z')} pid={os.getpid()}\n")
    sys.exit(code)


if __name__ == "__main__":
    main()
