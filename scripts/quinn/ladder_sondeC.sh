#!/usr/bin/env bash
# Sonde C0 — multilingual-base CL ladder + C-Labels (out_c/)
# Purpose: provide Sonde C's "family-adjacent" arm with a base that has multilingual
# context. This addresses the gap found in Sonde B (§6): the B base was English-prose-only,
# which invalidated the "family-adjacent to base" explanation for legal's P-B3 leak.
# C0 re-runs the Sonde B CL phases (code, math, legal, ga) from a PROSE+MULTILINGUAL base,
# then generates A2 argmin-NLL labels for Sonde C arms 1-3.
#
# Protocol: congruent with Sonde B and RA2b — route-aware alpha 0.9, grow +32, batch 1,
# fresh optimizer per phase (C4 ruling), F-V9 step-end restore.
# Host .200/rtx4090. Logs: out_c/logs. Checkpoints: out/ (ladC-* prefix).
# Announced on HAK.
set -euo pipefail
cd /media/data/coding/bdh
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=.venv/bin/python
LOG=out_c/logs
A=$LOG/ladder_sondeC_analysis.txt
mkdir -p $LOG out_c

# Base: prose + multilingual (de45 German + wiki45, no Europarl languages used later as CL phases)
# parl45 excluded: contents unverified, possible Europarl contamination risk per plan
BASE_SPEC="prose:data/textmix/wikitext-103-raw/wiki.train.raw,de:data/textmix/files/de45.txt,wikide:data/textmix/files/wiki45.txt"
# CL phases: same byte-distinct set as Sonde B
PH_SPECS=("code:data/textmix2/code.txt" "math:data/textmix2/latex.txt" "legal:data/textmix2/legal.txt" "ga:data/europarl/DGT.en-ga.ga.txt")
NAMES=(code math legal ga)
ROUTES="8192,10240,12288,14336,16384"

for i in "${!PH_SPECS[@]}"; do
  s=${PH_SPECS[$i]}; f=${s#*:}
  [ -f "$f" ] || { echo "MISSING corpus: $f" | tee -a $A; exit 3; }
done

echo "== C0 phase 1 base: prose+multilingual, mult 128, batch 4, 150k steps (~630 MB) ==" | tee -a $A
$PY -m pipeline.run train \
  --model bdh --dataset textmix --text-mix "$BASE_SPEC" --text-mix-mb 300 \
  --n-embd 512 --n-head 8 --mlp-internal-dim-multiplier 128 \
  --block-size 512 --max-iters 150000 --batch-size 4 \
  --warmup-iters 1000 --lr-decay-iters 150000 \
  --run-name "ladC-base" \
  2>&1 | tee "$LOG/ladC_base.log"

INIT="out/bdh_textmix_ladC-base_last.pt"
[ -f "$INIT" ] || { echo "MISSING C0 base checkpoint: $INIT" | tee -a $A; exit 4; }
echo "C0 base done; base_last mult=$(python3 -c "import torch; print(int(torch.load('$INIT',map_location='cpu',weights_only=False)['cfg']['mlp_internal_dim_multiplier']))")" | tee -a $A

SPEC="$BASE_SPEC"
for i in "${!PH_SPECS[@]}"; do
  PH=$((i+2)); tag=${NAMES[$i]}
  SPEC="$SPEC,${PH_SPECS[$i]}"
  echo "== C0 phase $PH: $tag (grow +32, alpha 0.9, batch 1, 10k steps) ==" | tee -a $A
  timeout 8h $PY -m pipeline.run train \
    --model bdh --dataset textmix --text-mix "${PH_SPECS[$i]}" --text-mix-mb 30 \
    --n-embd 512 --n-head 8 \
    --block-size 512 --max-iters 10000 --batch-size 1 \
    --warmup-iters 1000 --lr-decay-iters 10000 \
    --grow-mult 32 --init-from "$INIT" \
    --no-freeze-attn --route-aware --route-alpha 0.9 \
    --run-name "ladC-$tag" \
    2>&1 | tee "$LOG/ladC_$tag.log"
  INIT="out/bdh_textmix_ladC-${tag}_last.pt"
  [ -f "$INIT" ] || { echo "MISSING C0 phase $PH output: $INIT" | tee -a $A; exit 5; }
  echo "--- C0 phase $PH domain_eval (accumulated: $SPEC) ---" | tee -a $A
  $PY scripts/domain_eval.py "$INIT" "$SPEC" 30 >> "$A" 2>&1 || echo "domain_eval failed at $PH" >> $A
done

# P5 in-chain: verify storage thesis holds on multilingual base chain
echo "--- C0 P5 in-chain (4 transitions, multilingual base) ---" | tee -a $A
for pair in "base code" "code math" "math legal" "legal ga"; do
  set -- $pair
  par="out/bdh_textmix_ladC-$1_last.pt"
  chi="out/bdh_textmix_ladC-$2_last.pt"
  echo "P5 $1 -> $2:" >> $A
  $PY scripts/p5_inchain_check.py "$par" "$chi" >> $A 2>&1
  echo "p5_rc=$?" >> $A
done

# C0 Labels: argmin-NLL (A2 protocol, no human task IDs) for Sonde C arms 1-3
echo "--- C0 labels: routing confusion (all 5 domains, 200 crops, window 128) ---" | tee -a $A
$PY scripts/eval_router.py "$INIT" --routes "$ROUTES" \
  --domains "code:data/textmix2/code.txt,math:data/textmix2/latex.txt,legal:data/textmix2/legal.txt,ga:data/europarl/DGT.en-ga.ga.txt,prose:data/textmix/wikitext-103-raw/wiki.train.raw" \
  --crops 200 --window 128 --batch 4 > "$LOG/ladC_routdiag_labels.txt" 2>&1
echo "C0 label run done (rc=$?)" | tee -a $A
echo "--- C0 legal depth (200 crops, own prefix vs neighbours) ---" | tee -a $A
$PY scripts/eval_router.py "$INIT" --routes "$ROUTES" \
  --domains "legal:data/textmix2/legal.txt" --crops 200 --window 128 --batch 4 \
  > "$LOG/ladC_routdiag_legal.txt" 2>&1
echo "ladder-sondeC-done $(date '+%F %T')" | tee -a $A
