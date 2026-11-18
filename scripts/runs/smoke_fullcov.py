#!/usr/bin/env python3
"""Smoke test for the deterministic full-coverage eval (--eval-deterministic).

Covers, against the tiny zh checkpoint (/tmp/opencode/tiny_ckpt, mult 32):
  1. CLI parse: --eval-deterministic / --no-eval-deterministic (BooleanOptionalAction)
  2. Bit-reproducibility: identical batch shape -> bit-identical loss, unseeded
  3. Batch invariance incl. partial final batch: batch 245 vs batch 8 on the
     1,000,000-byte split (1953 blocks -> final batch 238 of 245), and batch 4
     (single partial batch) vs batch 1 on a 1200-byte synthetic split
  4. Coverage accounting print: exact blocks/bytes/tail numbers
  5. ValueError guard for a split with no full block
  6. Random-path sanity: default instrument (20 random crops) still runs and
     still draws different crops per call (unseeded)
  7. evaluate() end-to-end through the CLI incl. the memory-cap print
"""
import io
import os
import subprocess
import sys
from contextlib import nullcontext, redirect_stdout

os.chdir("/srv/coding/bdh-cl")
sys.path.insert(0, "/srv/coding/bdh-cl")

import torch  # noqa: E402

from pipeline.config import Config, parse_args  # noqa: E402
from pipeline.data import ByteDataset, load_dataset  # noqa: E402
from pipeline.eval import load_checkpoint  # noqa: E402
from pipeline.train import estimate_loss  # noqa: E402

DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CTX = (torch.amp.autocast(device_type=DEV.type, dtype=torch.bfloat16)
       if DEV.type == "cuda" else nullcontext())
print(f"device: {DEV}")

# --- 1. CLI parse -----------------------------------------------------------
cfg = parse_args(["--eval-deterministic", "--eval-batch-size", "4"])
assert cfg.eval_deterministic is True and cfg.eval_batch_size == 4
assert parse_args(["--no-eval-deterministic"]).eval_deterministic is False
assert parse_args([]).eval_deterministic is False  # default off
print("1. CLI parse OK (--eval-deterministic / --no-eval-deterministic, default False)")

# --- 2+3+4. sweep on the real split: reproducibility, invariance, coverage ---
base = torch.load("/tmp/opencode/tiny_ckpt/bdh_textmix_tiny_mem_last.pt",
                  map_location="cpu", weights_only=False)
cfgA = Config(**base["cfg"])          # out_dir/run_name/dataset = tiny_mem/textmix-zh
del base
cfgA.eval_deterministic = True
cfgA.eval_batch_size = 245            # 1953 blocks -> batches of 245 x7 + 238 (partial)

model, _ = load_checkpoint(cfgA, "last")
model.to(DEV).eval()
data = load_dataset(cfgA)
mask = None

def sweep(c):
    buf = io.StringIO()
    with redirect_stdout(buf):
        loss = estimate_loss(model, data, c, DEV, CTX, "val", neuron_mask=mask)
    return loss, buf.getvalue()

l245, out245 = sweep(cfgA)
l245b, out245b = sweep(cfgA)
assert l245 == l245b, f"not bit-reproducible: {l245!r} vs {l245b!r}"
assert out245 == out245b
assert "deterministic eval (val): 1953 blocks, 999936 of 1000000 bytes covered, batch 245" in out245, out245
print(f"2. bit-reproducible OK: {l245:.6f} (unseeded, two runs identical)")

cfgB = Config(**vars(cfgA))
cfgB.eval_batch_size = 8               # 245 batches: 243 full + 1 partial (1 block)
l8, out8 = sweep(cfgB)
d = abs(l8 - l245)
assert d < 0.01, f"batch invariance broken: {l8:.6f} vs {l245:.6f}"
assert "999936 of 1000000 bytes covered, batch 8" in out8
print(f"3. batch invariance OK: batch 8 vs 245 delta {d:.2e} (partial final batch in both)")

# --- 3b. synthetic partial-batch case: 1200 B -> 2 blocks, batch 4 = one partial
cfgS = Config(**vars(cfgA))
cfgS.eval_batch_size = 4
synth = ByteDataset(bytes(1200), bytes(1200))

def sweep_on(ds, c):
    buf = io.StringIO()
    with redirect_stdout(buf):
        loss = estimate_loss(model, ds, c, DEV, CTX, "val", neuron_mask=None)
    return loss, buf.getvalue()

l_s4, out_s4 = sweep_on(synth, cfgS)
assert "deterministic eval (val): 2 blocks, 1024 of 1200 bytes covered, batch 4" in out_s4, out_s4
cfgS1 = Config(**vars(cfgS))
cfgS1.eval_batch_size = 1              # two full single-block batches
l_s1, out_s1 = sweep_on(synth, cfgS1)
d = abs(l_s4 - l_s1)
assert d < 0.01, f"partial-batch pooling broken: {l_s4:.6f} vs {l_s1:.6f}"
print(f"3b. partial final batch OK: 1200 B split, batch 4 (1 partial) vs batch 1, delta {d:.2e}")

# --- 5. guard: split without a full block -----------------------------------
tiny_ds = ByteDataset(bytes(300), bytes(300))   # 300 B < 512 -> n_blocks == 0
try:
    sweep_on(tiny_ds, cfgS)
    raise AssertionError("expected ValueError for a split with no full block")
except ValueError as e:
    print(f"5. ValueError guard OK: {e}")

# --- 6. random-path sanity (default instrument untouched) --------------------
cfgR = Config(**vars(cfgA))
cfgR.eval_deterministic = False
cfgR.eval_iters = 2
cfgR.eval_batch_size = 2
l_r1, _ = sweep(cfgR)
l_r2, _ = sweep(cfgR)
assert l_r1 != l_r2, "random path returned identical losses - RNG no longer consumed?"
print(f"6. random-path sanity OK: two unseeded runs differ ({l_r1:.4f} vs {l_r2:.4f})")

# --- 7. evaluate() end-to-end through the CLI, incl. cap print ----------------
env = dict(os.environ)
env["BDH_MEM_FRACTION"] = "0.3"
env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
cmd = [".venv/bin/python", "-m", "pipeline.run", "eval",
       "--model", "bdh", "--dataset", "textmix",
       "--text-mix", "zh:data/europarl/xscript_zh.txt", "--text-mix-mb", "30",
       "--n-embd", "64", "--n-head", "4", "--n-layer", "2", "--block-size", "512",
       "--mlp-internal-dim-multiplier", "32",
       "--out-dir", "/tmp/opencode/tiny_ckpt", "--run-name", "tiny_mem", "--tag", "last",
       "--eval-batch-size", "245", "--eval-deterministic"]
res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=600)
out = res.stdout + res.stderr
for needle in ["cuda memory cap: 30%", "deterministic eval (val): 1953 blocks, "
               "999936 of 1000000 bytes covered, batch 245",
               "deterministic eval (test): 1953 blocks", "val_loss", "test_loss",
               "--- samples ---"]:
    assert needle in out, f"missing {needle!r} in CLI output:\n{out}"
assert res.returncode == 0, res.stderr[-2000:]
print("7. evaluate() end-to-end OK: cap print + deterministic val/test + samples")
print("\nALL SMOKE CHECKS PASSED")
