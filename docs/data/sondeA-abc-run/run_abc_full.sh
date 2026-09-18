#!/usr/bin/env bash
# Full A/B/C sweeps for the Sonde-A add-on probes (pre-reg 2026-09-18).
# One GPU -> strictly serialized (; not &&), per-stage timeout, wall-clock stamps.
# Frozen argv verbatim; --mb left at its default 30 (do NOT pass it).
# Committed scripts/eval_router.py is never touched; run the staged copy.
cd /media/data/coding/bdh || exit 9
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export TORCHDYNAMO_DISABLE=1
export PYTHONPATH=.
CK=out_a/bdh_textmix_ladA-A1-K5
R=8192,10240,12288,14336,16384
D=prose:data/textmix/wikitext-103-raw/wiki.train.raw,code:data/textmix2/code.txt,math:data/textmix2/latex.txt,legal:data/textmix2/legal.txt,ga:data/europarl/DGT.en-ga.ga.txt
LOG=out_c/logs
SC=out_c/eval_router_grid.py
ts(){ date -u +%Y%m%dT%H%M%SZ; }
run(){ # $1=tag $2=ckpt $3=extra_flags
  local t=$1 ck=$2 xf=$3
  if [ ! -f "$ck" ]; then echo "${t}_SKIP_MISSING_CKPT $(ts) $ck" | tee -a "$LOG/${t}.log"; return; fi
  echo "${t}_START $(ts) ckpt=$ck" | tee -a "$LOG/${t}.log"
  timeout 3h .venv/bin/python "$SC" "$ck" --routes "$R" --domains "$D" \
    --window 128 --crops 200 --batch 1 $xf >> "$LOG/${t}.log" 2>&1
  echo "${t}_RC=$? $(ts)" | tee -a "$LOG/${t}.log"
}

# C: code_best re-route -> the drift-vs-intrinsic discriminator (one routed ppl)
run fullC "${CK}-code_best.pt" ""
# B: [true-domain x forced-width] served-ppl matrix on the routing ckpt
run fullB "${CK}-ga_last.pt" "--route-grid"
# A: retention = routed ppl of every domain under each phase-best ckpt
for p in base code math legal ga; do
  run "fullA_${p}" "${CK}-${p}_best.pt" ""
done
echo "ALL_DONE $(ts)" | tee -a "$LOG/run_abc_full.done"
