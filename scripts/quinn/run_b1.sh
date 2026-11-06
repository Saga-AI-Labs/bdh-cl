#!/usr/bin/env bash
# B1: FP32 fine-tune of a zh_last clone on the Gutenberg branch corpus.
#
# Parameters from expert-merge prereg v0.3 section 2.3a:
#   peak lr 1e-4 (arm A won the measured probe: lowest rate inside the +5 % band)
#   warmup 500, cosine to min_lr 1e-5 -- min_lr BELOW the peak so the decay is real;
#     the default 1e-4 silently flattened arm A during the probe
#   seed 1234 (matched pairs with B2: batch order and dropout masks identical)
#   freeze-embed (embed.weight and lm_head bit-identical to the parent)
#   weight-decay 0 (the F-V9 guard refuses a grown-checkpoint init with decay when
#     there is no grow path; 0 matches the probe and keeps lr the only variable)
#
# LENGTH: train.txt is 21,058,594 B; _prepare_textmix carves 2 MB for val/test,
# leaving 19,058,594 B = 37,223 blocks of 512. A full epoch is therefore 37,223
# steps, not the ~19,500 the prereg's cost table assumed (that figure implies
# 9.98 MB of training data). At the probe's measured 3002 ms/step a full epoch is
# 31.0 h, outside the prereg's 15-29 h band. This run takes HALF an epoch
# (18,611 steps, ~15.5 h), which sits inside the band; a second half can follow
# from the saved checkpoint if the first looks good. Recorded, not hidden.
set -uo pipefail
cd /srv/coding/bdh-cl || exit 1

PY=.venv/bin/python
OUT=out_c/expert_merge
LOG=$OUT/b1_train.log
PARENT=out_a/bdh_textmix_k25w1024-zh_last.pt
STEPS=18611

mkdir -p "$OUT"
if [ ! -f "$PARENT" ]; then echo "FATAL: parent missing: $PARENT"; exit 1; fi

FREE=$(df -B1 --output=avail / | tail -1)
if [ "$FREE" -lt 200000000000 ]; then
  echo "FATAL: only $FREE bytes free, need >200 GB"; exit 1
fi

echo "### B1 start $(date '+%F %T') ###" | tee -a "$LOG"
echo "parent: $PARENT" | tee -a "$LOG"
echo "steps:  $STEPS (half epoch of 37,223) | peak lr 1e-4 | warmup 500 | min_lr 1e-5 | seed 1234" | tee -a "$LOG"

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
/usr/bin/time -f 'WALL=%es MAXRSS=%MkB' \
  $PY -u -m pipeline.run train \
    --model bdh --dataset textmix \
    --text-mix expert:data/expert/train.txt --text-mix-mb 30 \
    --n-embd 1024 --n-head 16 --mlp-internal-dim-multiplier 896 \
    --block-size 512 --batch-size 1 \
    --max-iters "$STEPS" --warmup-iters 500 --lr-decay-iters "$STEPS" \
    --learning-rate 1e-4 --min-lr 1e-5 \
    --weight-decay 0 --seed 1234 \
    --init-from "$PARENT" --freeze-embed \
    --out-dir "$OUT" --run-name expert-b1 \
  >> "$LOG" 2>&1

RC=$?
echo "### B1 done rc=$RC $(date '+%F %T') ###" | tee -a "$LOG"
echo "B1 rc=$RC $(date '+%F %T')" > "$OUT/b1.exit"
ls -lh "$OUT"/*expert-b1* 2>/dev/null | tee -a "$LOG"
