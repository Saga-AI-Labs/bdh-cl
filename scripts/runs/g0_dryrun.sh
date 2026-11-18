#!/usr/bin/env bash
# P3 gate G0 (prereg, D1'): dry run on the real ckpts.
# 896-Parent + --grow-mult 128 + mixed-alternate, 4 steps. Verify:
# dataset2 print (zh secondary), growth print (896 -> 1024, +128 neurons/head),
# mixed-alternate print, per-step dom markers (A even, B odd), memory under the
# cap (completion without OOM = pass; P1 envelope ~91-93 GiB expected),
# clean checkpoint write. Ckpts land in /tmp (dry-run artifacts, deleted after).
set -u
cd /srv/coding/bdh-cl || exit 1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export BDH_MEM_FRACTION=0.8
OUT=/tmp/opencode/p3_dryrun
mkdir -p "$OUT"

if pgrep -f 'pipeline\.run' > /dev/null; then
  echo "REFUSING: another pipeline.run process is active"; exit 1
fi

.venv/bin/python -m pipeline.run train \
  --model bdh --dataset textmix \
  --text-mix legal:data/textmix2/legal.txt \
  --text-mix2 zh:data/europarl/xscript_zh.txt \
  --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --init-from out_a/bdh_textmix_k25w1024-zh_last.pt --grow-mult 128 \
  --mixed-alternate --route-aware --route-alpha 0.9 --route-split-backward \
  --learning-rate 1e-4 --weight-decay 0 --warmup-iters 2 --lr-decay-iters 10000 \
  --batch-size 1 --max-iters 4 --eval-interval 4 --log-interval 1 \
  --no-compile \
  --out-dir "$OUT" --run-name p3_dryrun 2>&1 | tee "$OUT/g0_dryrun.log"

echo "### QA: required prints"
LOG="$OUT/g0_dryrun.log"
for pat in "dataset2: textmix | zh:data/europarl" \
           "growth: 896 -> 1024 mult (+128 neurons/head" \
           "mixed-alternate: even steps -> legal" \
           "route-aware: mask side=new | prefix 57344..65536" \
           "dom A" "dom B"; do
  if [ -n "$LOG" ] && grep -q "$pat" "$LOG"; then echo "OK   $pat"; else echo "FAIL $pat"; fi
done
echo "### ckpt write check"
ls -la "$OUT"/bdh_textmix_p3_dryrun_*.pt 2>/dev/null || echo "FAIL no checkpoints"
echo "### done $(date '+%F %T')"
