#!/usr/bin/env bash
# Sonde B RESUME (phases 2-5) from the completed base pretrain.
# Original ladder (ladder_sondeB.sh) completed phase 1 (base prose pretrain,
# best val ppl 2.38) but crashed before phase 2 because it looked for the base
# checkpoint under the europarl prefix (bdh_europarl_ladB-base_last.pt) while the
# textmix pipeline writes bdh_textmix_ladB-base_last.pt. This resume uses the
# correct prefix and does NOT re-run the 150k base steps.
# Protocol congruent with the pre-registered plan (gates P-B1..P-B5) and RA2b:
# route-aware alpha 0.9, grow +32, batch 1, fresh optimizer per phase, step-end
# restore (F-V9). Writes: out/bdh_textmix_ladB-* and out/logs only. Announced on
# HAK. Host .200/rtx4090.
set -euo pipefail
cd /media/data/coding/bdh
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=.venv/bin/python
LOG=out/logs
A=$LOG/ladder_sondeB_analysis.txt
mkdir -p $LOG
BASE_SPEC="prose:data/textmix/wikitext-103-raw/wiki.train.raw"
PH_SPECS=("code:data/textmix2/code.txt" "math:data/textmix2/latex.txt" "legal:data/textmix2/legal.txt" "ga:data/europarl/DGT.en-ga.ga.txt")
NAMES=(code math legal ga)
ROUTES="8192,10240,12288,14336,16384"
for i in "${!PH_SPECS[@]}"; do
  s=${PH_SPECS[$i]}; f=${s#*:}
  [ -f "$f" ] || { echo "MISSING corpus: $f" | tee -a $A; exit 3; }
done
INIT=out/bdh_textmix_ladB-base_last.pt
[ -f "$INIT" ] || { echo "MISSING base checkpoint: $INIT (resume cannot run)" | tee -a $A; exit 4; }
SPEC="$BASE_SPEC"
echo "== RESUME: base present ($(date '+%F %T')), reusing $INIT; running phases 2-5 ==" | tee -a $A
for i in "${!PH_SPECS[@]}"; do
  PH=$((i+2)); tag=${NAMES[$i]}
  SPEC="$SPEC,${PH_SPECS[$i]}"
  echo "== phase $PH: $tag (grow +32, alpha 0.9, batch 1, 10k steps) ==" | tee -a $A
  timeout 8h $PY -m pipeline.run train \
    --model bdh --dataset textmix --text-mix "${PH_SPECS[$i]}" --text-mix-mb 30 \
    --n-embd 512 --n-head 8 \
    --block-size 512 --max-iters 10000 --batch-size 1 \
    --warmup-iters 1000 --lr-decay-iters 10000 \
    --grow-mult 32 --init-from "$INIT" \
    --no-freeze-attn --route-aware --route-alpha 0.9 \
    --run-name "ladB-$tag" \
    2>&1 | tee "$LOG/ladB_$tag.log"
  INIT="out/bdh_textmix_ladB-${tag}_last.pt"
  [ -f "$INIT" ] || { echo "MISSING phase $PH output: $INIT" | tee -a $A; exit 5; }
  echo "--- phase $PH domain_eval (accumulated: $SPEC) ---" | tee -a $A
  $PY scripts/domain_eval.py "$INIT" "$SPEC" 30 >> "$A" 2>&1 || echo "domain_eval failed at $PH" >> $A
done
echo "--- final routing diagnosis (own prefix vs true phase) ---" | tee -a $A
timeout 2h $PY scripts/eval_router.py "$INIT" --routes "$ROUTES" \
  --domains "code:data/textmix2/code.txt,math:data/textmix2/latex.txt,legal:data/textmix2/legal.txt,ga:data/europarl/DGT.en-ga.ga.txt,prose:data/textmix/wikitext-103-raw/wiki.train.raw" \
  --batch 4 > $LOG/ladB_routdiag_final.txt 2>&1
echo "ladder-sondeB-resume-done $(date '+%F %T')" | tee -a $A
