#!/usr/bin/env bash
# G-A2 (graft-2 plan e8b93e1): real-scale dry run 1024 -> 1152 with
# --frozen-backup auto (resolves OFF at wd=0), then the mask identity eval.
#   1. 4-step grow dry run on the P3 last ckpt (mult 1024): growth print
#      (1024 -> 1152, +8192 neurons/head), frozen-backup off prints, dom
#      markers, clean ckpt write, and the NEW peak-memory print. Expect
#      ~82-85 GiB peak vs the 95.40 GiB that OOM'd (the freed ~12.9 GiB
#      backup; report section 12).
#   2. Identity eval: zh fullcov b4 on the dry-run ckpt at mask-old-mult 1024.
#      The frozen old prefix [0,65536) IS the full P3 model (bit-identical
#      sd copy + freq assert + zero old grads), so this must equal the P3
#      zh@0 post cell BIT-EXACT: val 1.7470 / test 1.6858. The mask-896
#      identity (1.7603/1.6980) holds implicitly (deepest prefix untouched).
set -u
cd /srv/coding/bdh-cl || exit 1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export BDH_MEM_FRACTION=0.8
PARENT=out_c/routed_probe/bdh_textmix_p3_mixed_last.pt
OUT=/tmp/opencode/ga2_dryrun
mkdir -p "$OUT"
LOG="$OUT/ga2.log"
: > "$LOG"

if pgrep -f 'pipeline\.run' > /dev/null; then
  echo "REFUSING: another pipeline.run process is active"; exit 1
fi

echo "### dry run: 4-step grow 1024 -> 1152, frozen-backup auto (wd=0 -> off) $(date '+%F %T')"
.venv/bin/python -u -m pipeline.run train \
  --model bdh --dataset textmix \
  --text-mix legal:data/textmix2/legal.txt \
  --text-mix2 zh:data/europarl/xscript_zh.txt \
  --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --init-from "$PARENT" --grow-mult 128 \
  --mixed-alternate --route-aware --route-alpha 0.9 --route-split-backward \
  --learning-rate 1e-4 --weight-decay 0 --warmup-iters 2 --lr-decay-iters 10000 \
  --batch-size 1 --max-iters 4 --eval-interval 4 --log-interval 1 \
  --no-compile \
  --out-dir "$OUT" --run-name p3_ga2_dryrun 2>&1 | tee "$LOG"

echo "### identity eval: zh fullcov b4 @ mask-old-mult 1024 (expect 1.7470/1.6858) $(date '+%F %T')"
.venv/bin/python -u -m pipeline.run eval \
  --dataset textmix --text-mix zh:data/europarl/xscript_zh.txt --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --mlp-internal-dim-multiplier 1152 --mask-old-mult 1024 \
  --batch-size 1 --eval-batch-size 4 --eval-deterministic \
  --out-dir "$OUT" --run-name p3_ga2_dryrun --tag last 2>&1 | tee -a "$LOG"

echo "### QA"
for pat in "growth: 1024 -> 1152 mult (+8192 neurons/head trainable)" \
           "frozen-backup: auto -> off (weight_decay=0)" \
           "frozen-backup: off | wd=0 restore is a mathematical no-op" \
           "route-aware: mask side=new | prefix 65536..73728" \
           "mixed-alternate: even steps -> legal" \
           "dom A" "dom B" \
           "memory: peak allocated" \
           "val_loss 1.7470" "test_loss 1.6858"; do
  grep -q "$pat" "$LOG" && echo "OK   $pat" || echo "FAIL $pat"
done
grep -q "frozen-backup: on" "$LOG" && echo "FAIL unexpected backup build" || echo "OK   no backup built"
ls -l "$OUT"/bdh_textmix_p3_ga2_dryrun_last.pt > /dev/null 2>&1 && echo "OK   ckpt written" || echo "FAIL ckpt missing"
echo "### G-A2 done $(date '+%F %T')"
