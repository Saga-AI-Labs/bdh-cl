#!/usr/bin/env bash
# P3 tiny smoke (prereg 5daf30c; concurrent with G1 - tiny model, ~1 GiB):
#   1. parent zh full-coverage anchor (b2 deterministic), no mask
#   2. 8-step P3 mixed-alternate train: tiny zh parent (mult 32) + --grow-mult 16
#      (-> 48), primary legal (dom A, side=new), secondary zh (dom B, side=old)
#   3. child zh full coverage with --mask-old-mult 32 -> must equal cell 1 on
#      all printed digits: frozen-path mechanism check (zero-grad gate masks +
#      step-end restore keep the old block bit-exact through training)
#   4. scripts/router_p3.py end-to-end on the child (S3/S4 instrument smoke)
set -u
cd /srv/coding/bdh-cl || exit 1
TINY=/tmp/opencode/tiny_ckpt
SMK=/tmp/opencode/p3_smoke
mkdir -p "$SMK"
ZH="--dataset textmix --text-mix zh:data/europarl/xscript_zh.txt --text-mix-mb 30 \
--n-embd 64 --n-head 4 --n-layer 2 --block-size 512"
LOG="$SMK/smoke.log"
: > "$LOG"

echo "### cell 1: parent zh fullcov (b2, no mask) $(date '+%F %T')"
.venv/bin/python -m pipeline.run eval $ZH \
  --mlp-internal-dim-multiplier 32 --mask-old-mult 0 \
  --batch-size 2 --eval-batch-size 2 --eval-deterministic \
  --out-dir "$TINY" --run-name tiny_mem --tag last 2>&1 | tee -a "$LOG"

echo "### cell 2: P3 mixed-alternate smoke train (8 steps) $(date '+%F %T')"
.venv/bin/python -m pipeline.run train \
  --model bdh --dataset textmix \
  --text-mix legal:data/textmix2/legal.txt \
  --text-mix2 zh:data/europarl/xscript_zh.txt \
  --text-mix-mb 30 --n-embd 64 --n-head 4 --n-layer 2 --block-size 512 \
  --init-from "$TINY/bdh_textmix_tiny_mem_last.pt" --grow-mult 16 \
  --mixed-alternate --route-aware --route-alpha 0.9 --route-split-backward \
  --learning-rate 1e-4 --weight-decay 0 --warmup-iters 2 --lr-decay-iters 100000 \
  --batch-size 1 --eval-batch-size 2 --max-iters 8 \
  --log-interval 1 --eval-interval 8 --eval-iters 2 \
  --no-compile \
  --out-dir "$SMK" --run-name tiny_p3 --tag last 2>&1 | tee -a "$LOG"

echo "### cell 3: child zh fullcov (b2, mask-old-mult 32) $(date '+%F %T')"
.venv/bin/python -m pipeline.run eval $ZH \
  --mlp-internal-dim-multiplier 48 --mask-old-mult 32 \
  --batch-size 2 --eval-batch-size 2 --eval-deterministic \
  --out-dir "$SMK" --run-name tiny_p3 --tag last 2>&1 | tee -a "$LOG"

echo "### cell 4: router_p3 smoke on child $(date '+%F %T')"
PYTHONPATH=. .venv/bin/python scripts/router_p3.py \
  "$SMK/bdh_textmix_tiny_p3_last.pt" --mask-old-mult 32 \
  --domain-a legal:data/textmix2/legal.txt \
  --domain-b zh:data/europarl/xscript_zh.txt \
  --batch 8 --window 128 2>&1 | tee -a "$LOG"

echo "### QA: mechanism prints present"
for pat in "dataset2:" "mixed-alternate:" "route-aware: mask side=new" \
           "growth: 32 -> 48" "dom A" "dom B" "eval mask: keep 512 of 768"; do
  if grep -q "$pat" "$LOG"; then echo "OK   $pat"; else echo "FAIL $pat"; fi
done

echo "### QA: S1 mechanism - parent vs child zh fullcov (must be identical)"
# Anchored to ^: the eval instrument prints val_loss/test_loss at line start;
# the train cell's in-loop eval ("step 8 | val_loss ...") and the done line
# ("done. best val_loss ...") are mid-line and must not be picked up.
v1=$(grep -oE '^val_loss [0-9.]+' "$LOG" | sed -n 1p | awk '{print $2}')
t1=$(grep -oE '^test_loss [0-9.]+' "$LOG" | sed -n 1p | awk '{print $2}')
v3=$(grep -oE '^val_loss [0-9.]+' "$LOG" | sed -n 2p | awk '{print $2}')
t3=$(grep -oE '^test_loss [0-9.]+' "$LOG" | sed -n 2p | awk '{print $2}')
echo "parent zh fullcov: val $v1 test $t1"
echo "child  zh fullcov: val $v3 test $t3"
if [ "$v1" = "$v3" ] && [ "$t1" = "$t3" ]; then
  echo "S1-MECHANISM-OK (bit-exact on all printed digits)"
else
  echo "S1-MECHANISM-FAIL"
fi
echo "### done $(date '+%F %T')"
