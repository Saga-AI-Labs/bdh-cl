#!/usr/bin/env bash
# Test: --freeze-embed on a model small enough to be uninteresting.
#
# Why not the 2.82B checkpoint: the control arm of that test was OOM-killed
# before step 1 (same GB10 unified-pool limit that hit phase 23), so it produced
# no control evidence. Loading 30 GB to check a requires_grad flag is the wrong
# instrument. This runs the SAME code path -- same pipeline.train, same optimizer
# construction, same freeze branch -- on a model small enough that memory cannot
# be the explanation either way.
#
# Both arms start from the same locally-built checkpoint, so the only difference
# is --freeze-embed. The control MUST move the hashes; if it does not, the test
# proves nothing about the flag.
set -uo pipefail
cd /srv/coding/bdh-cl || exit 1

PY=.venv/bin/python
OUT=out_c/expert_merge/freeze_tiny
rm -rf "$OUT"; mkdir -p "$OUT"

BASE="--model bdh --dataset textmix --text-mix expert:data/expert/train.txt --text-mix-mb 5 \
  --n-embd 96 --n-head 4 --mlp-internal-dim-multiplier 24 \
  --block-size 128 --batch-size 2 --weight-decay 0 --out-dir $OUT"

echo "=== seed: tiny model, 5 steps from scratch ==="
$PY -u -m pipeline.run train $BASE --max-iters 5 --warmup-iters 1 \
  --run-name tiny-seed 2>&1 | tail -6

SEED=$(ls "$OUT"/*tiny-seed*_last.pt 2>/dev/null | head -1)
if [ -z "$SEED" ]; then echo "SEED CHECKPOINT MISSING - abort"; exit 1; fi
echo "seed: $SEED"

echo
echo "=== CONTROL: 3 more steps, NO --freeze-embed (hashes must move) ==="
$PY -u -m pipeline.run train $BASE --init-from "$SEED" \
  --max-iters 3 --warmup-iters 1 --run-name tiny-control 2>&1 | tail -5

echo
echo "=== TREATMENT: 3 more steps, WITH --freeze-embed (hashes must hold) ==="
$PY -u -m pipeline.run train $BASE --init-from "$SEED" \
  --max-iters 3 --warmup-iters 1 --run-name tiny-freeze --freeze-embed 2>&1 | tail -5

echo
echo "=== hash comparison against the seed ==="
$PY - << 'PY'
import torch, hashlib, glob, os

def h(t):
    return hashlib.sha256(t.detach().float().numpy().tobytes()).hexdigest()[:16]

def find(tag):
    f = sorted(glob.glob("out_c/expert_merge/freeze_tiny/*%s*_last.pt" % tag))
    return f[0] if f else None

seed_path = find("tiny-seed")
seed = torch.load(seed_path, map_location="cpu", weights_only=False, mmap=True)["model_state"]
ref = {k: h(seed[k]) for k in ("embed.weight", "lm_head")}
print("seed reference:")
for k, v in ref.items():
    print("  %-14s %s" % (k, v))

verdict = {}
for label, tag in (("control (no freeze)", "tiny-control"),
                   ("treatment (--freeze-embed)", "tiny-freeze")):
    path = find(tag)
    if not path:
        print("\n%s: NO CHECKPOINT" % label)
        verdict[label] = None
        continue
    ck = torch.load(path, map_location="cpu", weights_only=False, mmap=True)
    print("\n%s  [%s]" % (label, os.path.basename(path)))
    moved = {}
    for k in ("embed.weight", "lm_head"):
        got = h(ck["model_state"][k])
        m = got != ref[k]
        moved[k] = m
        print("  %-14s %s  %s" % (k, got, "CHANGED" if m else "UNCHANGED"))
    verdict[label] = all(moved.values())

print("\n=== verdict ===")
c = verdict.get("control (no freeze)")
t = verdict.get("treatment (--freeze-embed)")
if c is None or t is None:
    print("  INCONCLUSIVE - a checkpoint is missing")
elif c and not t:
    print("  PASS - control moved both tensors, treatment held both")
elif not c:
    print("  INCONCLUSIVE - control did NOT move the hashes; training had no effect")
else:
    print("  FAIL - treatment moved a tensor that should have been frozen")
PY
