#!/usr/bin/env bash
# G-A1 (graft-2 plan e8b93e1): tiny-scale certification of --frozen-backup.
#   Run A: the P3 tiny smoke recipe verbatim (wd=0, default auto) -> auto must
#          resolve OFF; the S1 mechanism (zero-grad gate masks) must keep the
#          child masked zh fullcov BIT-EXACT to the parent anchor
#          (registered: val 5.5378 / test 5.5381).
#   Run B: backup-ON control (auto -> on) under REAL wd>0 decay pressure:
#          AdamW now actively decays the old elements every step and the
#          step-end restore must undo it bit-exactly -> child masked zh
#          fullcov == parent anchor on all printed digits again. This is the
#          standing wd>0 regression test (plan addendum a).
#   Run C: error case: --frozen-backup off + wd>0 must raise, not train.
# Parent anchor: /tmp/opencode/tiny_ckpt/bdh_textmix_tiny_mem_last.pt
# (mult 32, zh; N=512 neurons/head; child grows 32 -> 48, mask keeps 512).
set -u
cd /srv/coding/bdh-cl || exit 1
TINY=/tmp/opencode/tiny_ckpt
OUT=/tmp/opencode/ga1
mkdir -p "$OUT"
LOG="$OUT/ga1.log"
ZH="--dataset textmix --text-mix zh:data/europarl/xscript_zh.txt --text-mix-mb 30 \
--n-embd 64 --n-head 4 --n-layer 2 --block-size 512"
TRAINFLAGS="--model bdh --dataset textmix \
--text-mix legal:data/textmix2/legal.txt \
--text-mix2 zh:data/europarl/xscript_zh.txt \
--text-mix-mb 30 --n-embd 64 --n-head 4 --n-layer 2 --block-size 512 \
--init-from $TINY/bdh_textmix_tiny_mem_last.pt --grow-mult 16 \
--mixed-alternate --route-aware --route-alpha 0.9 --route-split-backward \
--learning-rate 1e-4 --warmup-iters 2 --lr-decay-iters 100000 \
--batch-size 1 --eval-batch-size 2 --max-iters 8 \
--log-interval 1 --eval-interval 8 --eval-iters 2 \
--no-compile"
: > "$LOG"

if pgrep -f 'pipeline\.run' > /dev/null; then
  echo "REFUSING: another pipeline.run process is active"; exit 1
fi

echo "### cell 1: parent zh fullcov anchor (b2, no mask) $(date '+%F %T')"
.venv/bin/python -m pipeline.run eval $ZH \
  --mlp-internal-dim-multiplier 32 --mask-old-mult 0 \
  --batch-size 2 --eval-batch-size 2 --eval-deterministic \
  --out-dir "$TINY" --run-name tiny_mem --tag last 2>&1 | tee -a "$LOG"

echo "### Run A: 8-step smoke, wd=0, frozen-backup auto (expect auto -> off) $(date '+%F %T')"
.venv/bin/python -m pipeline.run train $TRAINFLAGS \
  --weight-decay 0 \
  --out-dir "$OUT" --run-name tiny_ga1_off --tag last 2>&1 | tee -a "$LOG"

echo "### cell 3A: child zh fullcov (b2, mask-old-mult 32), backup OFF $(date '+%F %T')"
.venv/bin/python -m pipeline.run eval $ZH \
  --mlp-internal-dim-multiplier 48 --mask-old-mult 32 \
  --batch-size 2 --eval-batch-size 2 --eval-deterministic \
  --out-dir "$OUT" --run-name tiny_ga1_off --tag last 2>&1 | tee -a "$LOG"

echo "### Run B: backup-ON control, wd=0.01, frozen-backup auto (expect auto -> on + size) $(date '+%F %T')"
.venv/bin/python -m pipeline.run train $TRAINFLAGS \
  --weight-decay 0.01 \
  --out-dir "$OUT" --run-name tiny_ga1_on --tag last 2>&1 | tee -a "$LOG"

echo "### cell 3B: child zh fullcov (b2, mask-old-mult 32), backup ON under real decay $(date '+%F %T')"
.venv/bin/python -m pipeline.run eval $ZH \
  --mlp-internal-dim-multiplier 48 --mask-old-mult 32 \
  --batch-size 2 --eval-batch-size 2 --eval-deterministic \
  --out-dir "$OUT" --run-name tiny_ga1_on --tag last 2>&1 | tee -a "$LOG"

echo "### Run C: error case, --frozen-backup off + wd>0 must raise $(date '+%F %T')"
if .venv/bin/python -m pipeline.run train $TRAINFLAGS \
  --weight-decay 0.01 --frozen-backup off --max-iters 2 \
  --out-dir "$OUT" --run-name tiny_ga1_err --tag last 2>&1 | tee -a "$LOG"; then
  echo "FAIL: off+wd>0 completed instead of raising" | tee -a "$LOG"
else
  echo "OK: off+wd>0 raised as required" | tee -a "$LOG"
fi

echo "### QA: cell equality + required prints"
VALS=($(grep '^val_loss' "$LOG" | awk '{print $2}'))
TESTS=($(grep '^test_loss' "$LOG" | awk '{print $2}'))
echo "cells: parent=(${VALS[0]}/${TESTS[0]}) 3A=(${VALS[1]}/${TESTS[1]}) 3B=(${VALS[2]}/${TESTS[2]})"
[ "${VALS[0]}" = "${VALS[1]}" ] && [ "${TESTS[0]}" = "${TESTS[1]}" ] \
  && echo "OK   3A == parent (backup off, bit-exact)" || echo "FAIL 3A != parent"
[ "${VALS[0]}" = "${VALS[2]}" ] && [ "${TESTS[0]}" = "${TESTS[2]}" ] \
  && echo "OK   3B == parent (backup on + real wd, bit-exact)" || echo "FAIL 3B != parent"
[ "${VALS[0]}" = "5.5378" ] && [ "${TESTS[0]}" = "5.5381" ] \
  && echo "OK   anchor matches registered 5.5378/5.5381" || echo "FAIL anchor drifted"
for pat in "frozen-backup: auto -> off" \
           "frozen-backup: off | wd=0 restore is a mathematical no-op" \
           "frozen-backup: auto -> on" \
           "frozen-backup: on | " \
           "OK: off+wd>0 raised as required"; do
  if grep -q "$pat" "$LOG"; then echo "OK   $pat"; else echo "FAIL $pat"; fi
done
echo "### G-A1 done $(date '+%F %T')"
