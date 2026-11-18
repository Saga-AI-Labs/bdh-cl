#!/usr/bin/env bash
# G-A3 - the real graft run (graft-2 prereg f519724): grow 1024 -> 1152 on
# the P3 last checkpoint, design B (P3 mirror) with Code as the third
# domain. text_mix = legal (even steps, side=new, 0.9), text_mix2 = CODE
# (odd steps, side=old, 0.1 weight). Exactly the G-A2-certified profile
# (corpora swapped); zero code changes. Backup auto -> OFF at wd=0
# (G-A1-certified redundancy argument). Run name g2_code, ckpts to
# out_c/routed_probe. ~11.7 s/step -> ~32.5 h for 10000 iters.
# Monitoring: peak memory print at run end (G-A0 addendum b). Post-run
# cells are a separate step (prereg section 8).
set -u
cd /srv/coding/bdh-cl || exit 1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export BDH_MEM_FRACTION=0.8
OUT=/tmp/opencode/ga3_run
mkdir -p "$OUT"
LOG="$OUT/ga3.log"
: > "$LOG"

if pgrep -f 'pipeline\.run' > /dev/null; then
  echo "REFUSING: another pipeline.run process is active"; exit 1
fi

echo "### G-A3: graft #2, 1024 -> 1152, design B (legal even / code odd) $(date '+%F %T')"
.venv/bin/python -u -m pipeline.run train \
  --model bdh --dataset textmix \
  --text-mix legal:data/textmix2/legal.txt \
  --text-mix2 code:data/textmix2/code.txt \
  --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --init-from out_c/routed_probe/bdh_textmix_p3_mixed_last.pt --grow-mult 128 \
  --mixed-alternate --route-aware --route-alpha 0.9 --route-split-backward \
  --learning-rate 1e-4 --weight-decay 0 --frozen-backup auto \
  --warmup-iters 2 --lr-decay-iters 10000 \
  --batch-size 1 --max-iters 10000 --eval-interval 50 --no-compile \
  --out-dir out_c/routed_probe --run-name g2_code > "$LOG" 2>&1
RC=$?

echo "### QA"
[ "$RC" = 0 ] && echo "OK   train exit" || echo "FAIL train exit $RC"
for pat in "growth: 1024 -> 1152 mult (+8192 neurons/head trainable)" \
           "frozen-backup: auto -> off (weight_decay=0)" \
           "dataset2: textmix | code:data/textmix2/code.txt" \
           "route-aware: mask side=new | prefix 65536..73728" \
           "mixed-alternate: even steps -> legal" \
           "dom A" "dom B" \
           "memory: peak allocated"; do
  grep -q "$pat" "$LOG" && echo "OK   $pat" || echo "FAIL $pat"
done
grep -q "frozen-backup: on" "$LOG" && echo "FAIL unexpected backup build" || echo "OK   no backup built"
ls -l out_c/routed_probe/bdh_textmix_g2_code_last.pt > /dev/null 2>&1 \
  && echo "OK   ckpt written" || echo "FAIL ckpt missing"
echo "### G-A3 done $(date '+%F %T') (exit $RC)"
exit $RC
