#!/usr/bin/env bash
# G-A3 pre-run anchors (graft-2 prereg f519724): code@0 and code@mask-1024
# on the P3 last checkpoint (mult 1024), fullcov b4, eval-deterministic.
#   - code@0: the code D-cell baseline (code was never trained on P3).
#   - code@mask-1024: on the mult-1024 parent the mask keeps all 65536
#     neurons/head = identity, so it must equal code@0 BIT-EXACT. This
#     sanity-checks the mask machinery at full keep before the post-run
#     S1-d zero-tolerance cell ties the grown child to these numbers.
set -u
set -o pipefail
cd /srv/coding/bdh-cl || exit 1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export BDH_MEM_FRACTION=0.8
OUT=/tmp/opencode/ga3_anchor
mkdir -p "$OUT"
LOG="$OUT/anchor.log"
: > "$LOG"

if pgrep -f 'pipeline\.run' > /dev/null; then
  echo "REFUSING: another pipeline.run process is active"; exit 1
fi

echo "### anchor 1/2: code@0, fullcov b4 deterministic $(date '+%F %T')"
.venv/bin/python -u -m pipeline.run eval \
  --dataset textmix --text-mix code:data/textmix2/code.txt --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --mlp-internal-dim-multiplier 1024 \
  --batch-size 1 --eval-batch-size 4 --eval-deterministic \
  --out-dir out_c/routed_probe --run-name p3_mixed --tag last 2>&1 | tee -a "$LOG"
RC1=$?

echo "### anchor 2/2: code@mask-1024, fullcov b4 deterministic $(date '+%F %T')"
.venv/bin/python -u -m pipeline.run eval \
  --dataset textmix --text-mix code:data/textmix2/code.txt --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --mlp-internal-dim-multiplier 1024 --mask-old-mult 1024 \
  --batch-size 1 --eval-batch-size 4 --eval-deterministic \
  --out-dir out_c/routed_probe --run-name p3_mixed --tag last 2>&1 | tee -a "$LOG"
RC2=$?

echo "### QA"
[ "$RC1" = 0 ] && echo "OK   anchor 1 exit" || echo "FAIL anchor 1 exit $RC1"
[ "$RC2" = 0 ] && echo "OK   anchor 2 exit" || echo "FAIL anchor 2 exit $RC2"
N=$(grep -c '^val_loss' "$LOG")
[ "$N" = 2 ] && echo "OK   2 val_loss lines" || echo "FAIL val_loss lines: $N"
V0=$(grep '^val_loss' "$LOG" | head -1)
V1=$(grep '^val_loss' "$LOG" | tail -1)
[ "$V0" = "$V1" ] && echo "OK   mask-1024 identity bit-exact: $V0" || echo "FAIL identity mismatch: [$V0] vs [$V1]"
echo "### G-A3 anchors done $(date '+%F %T')"
