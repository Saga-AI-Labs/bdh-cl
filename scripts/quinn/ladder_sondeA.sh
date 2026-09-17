#!/usr/bin/env bash
# Sonde A — scaling ladder (pre-registered plan docs/plans/2026-09-16_sondeA-scaling-probe.md, v0.3)
#
# SCALES the mechanism that Sonde B/C measured; it does NOT redesign the router. Protocol
# is the exact B/C0 protocol (route-aware alpha 0.9, grow +32, batch 1, fresh optimizer
# per phase, F-V9 step-end restore), reusing the validated DOMAINS-ladder form from
# scripts/quinn/ladder_sondeB_resume.sh + ladder_sondeC.sh (NOT ladder_ra2b.sh, which is
# a LANGUAGE ladder with --europarl-langs; A's territories are textmix DOMAINS).
#
# Host .200/RTX 4090. This is a scaling probe: it measures cost/accuracy knees so the PoC
# config is read from measured curves. It is router-free for TRAINING; only the routing
# EVAL is fixed to the likelihood scan (eval_router), since the head/cascade measured dead.
#
# STORAGE SEPARATION (operator ruling): the phase-2 HF upload is still streaming the OLD
# files under out/ (PID 3376895). Sonde A must NOT write there or it pollutes that upload
# set. All A checkpoints go to out_a/ via --out-dir; analysis/logs go to out_c/logs.
# out/ is READ-ONLY from A's point of view and is never written by this script.
#
# Implemented + launchable now:  A1-K5   (five textmix domains == Sonde B's set, fresh).
# DECLARED but HARD-GUARDED (do not launch until the open questions below are resolved):
#   A1-K20 / A1-K40  -- open question 1: exact territory mix. The plan says 'Europarl-20
#                       PLUS the B/C classes', but it does not fix whether the count is
#                       20 or 24, nor how a single phase loads BOTH --dataset europarl (a
#                       language) and --dataset textmix (a domain) in one checkpoint. The
#                       sondeB base/prefix bug (europarl vs textmix prefix) shows this is
#                       not free. NO GUESS is encoded here.
#                    -- open question 2 (K40 only): byte-distinctness/inventory of the
#                       non-Europarl corpora (textmix/textmix2/wikitext/shakespeare) is
#                       unverified. The plan's K40 precondition must not be skipped.
#   A2-W512 / A2-W1024 -- Axis 2; W1024 (~400M) is the one arm that may need gx10 (see
#                       plan Budget); NOT started, gx10 stays up / Qwen stays on otherwise.
#
# Smoke test: SMOKE=1 bash ladder_sondeA.sh A1-K5   -> tiny iters, run-name ladA-smoke-*
#   so a smoke never overwrites a product checkpoint and runs the whole chain in seconds.
#
# Usage: bash ladder_sondeA.sh <arm>            e.g.  bash ladder_sondeA.sh A1-K5
# Deploy note: on .200 scripts/ is read-only for the runner user; run a copy from
# out_c/ that cd's back into the repo (scripts/ and .venv/ are used read-only).
set -euo pipefail
cd /media/data/coding/bdh
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export TORCHDYNAMO_DISABLE=1

ARM="${1:-}"
[ -n "$ARM" ] || { echo "usage: $0 <A1-K5|A1-K20|A1-K40|A2-W512|A2-W1024>  (SMOKE=1 to smoke)"; exit 2; }

PY=.venv/bin/python
# out_a/ isolates A's checkpoints from the still-running out/ phase-2 upload (never write out/)
OUT=out_a
OUT_C=out_c
LOG=$OUT_C/logs
# smoke runs a distinct run-name + tiny budget so it can't collide with a product run
SMOKE="${SMOKE:-0}"
if [ "$SMOKE" = "1" ]; then
  RUN="ladA-smoke-$ARM"; BASE_ITERS=8; PH_ITERS=8; WARMUP=4; DECAY=8; CROPS=4
else
  RUN="ladA-$ARM";       BASE_ITERS=150000; PH_ITERS=10000; WARMUP=1000; DECAY=10000; CROPS=200
fi
A=$LOG/${RUN}_analysis.txt
mkdir -p "$LOG" "$OUT" "$OUT_C"

GROW=32
NPH=64
BASE_MULT=128

# ------------------------------------------------------------------ A1-K5 (READY)
# Five textmix domains == Sonde B's set (prose base + code/math/legal/ga). ROUTES/eval
# config copied verbatim from ladder_sondeB_resume.sh + ladder_sondeC.sh (the C0-validated
# crops=200/window=128). base_last prefix MUST be bdh_textmix_ (the sondeB base/prefix bug).
if [ "$ARM" = "A1-K5" ]; then
  BASE_SPEC="prose:data/textmix/wikitext-103-raw/wiki.train.raw"
  PH_SPECS=("code:data/textmix2/code.txt" "math:data/textmix2/latex.txt" "legal:data/textmix2/legal.txt" "ga:data/europarl/DGT.en-ga.ga.txt")
  NAMES=(code math legal ga)
  # 5 territories -> 5 routes at BASE_MULT*64 stepping by GROW*64 (=2048): the K=5 grid
  ROUTES="8192,10240,12288,14336,16384"

  for s in "${PH_SPECS[@]}" "$BASE_SPEC"; do f=${s#*:}; [ -f "$f" ] || { echo "MISSING corpus: $f" | tee -a "$A"; exit 3; }; done

  # phase 1: fresh base pretrain (protocol-identity check, NOT reuse of ladB-base)
  echo "== $ARM smoke=$SMOKE phase 1: base (prose) mult=$BASE_MULT batch 4 iters=$BASE_ITERS ==" | tee -a "$A"
  $PY -m pipeline.run train \
    --model bdh --dataset textmix --text-mix "$BASE_SPEC" --text-mix-mb 300 \
    --n-embd 512 --n-head 8 --mlp-internal-dim-multiplier "$BASE_MULT" \
    --block-size 512 --max-iters "$BASE_ITERS" --batch-size 4 \
    --warmup-iters "$WARMUP" --lr-decay-iters "$DECAY" \
    --out-dir "$OUT" --run-name "${RUN}-base" \
    2>&1 | tee "$LOG/${RUN}_base.log"
  INIT="$OUT/bdh_textmix_${RUN}-base_last.pt"
  [ -f "$INIT" ] || { echo "MISSING base ckpt: $INIT" | tee -a "$A"; exit 4; }

  # phases 2..5: one CL phase per domain, grow +32, alpha 0.9, batch 1, fresh optimizer
  SPEC="$BASE_SPEC"; CHAIN=("$RUN-base")
  for i in "${!PH_SPECS[@]}"; do
    PH=$((i+2)); tag=${NAMES[$i]}
    SPEC="$SPEC,${PH_SPECS[$i]}"; CHAIN+=("$RUN-$tag")
    echo "== $ARM phase $PH: $tag (grow +32, alpha 0.9, batch 1, iters=$PH_ITERS) ==" | tee -a "$A"
    timeout 8h $PY -m pipeline.run train \
      --model bdh --dataset textmix --text-mix "${PH_SPECS[$i]}" --text-mix-mb 30 \
      --n-embd 512 --n-head 8 \
      --block-size 512 --max-iters "$PH_ITERS" --batch-size 1 \
      --warmup-iters "$WARMUP" --lr-decay-iters "$DECAY" \
      --grow-mult "$GROW" --init-from "$INIT" \
      --no-freeze-attn --route-aware --route-alpha 0.9 \
      --out-dir "$OUT" --run-name "${RUN}-${tag}" \
      2>&1 | tee "$LOG/${RUN}_${tag}.log"
    INIT="$OUT/bdh_textmix_${RUN}-${tag}_last.pt"
    [ -f "$INIT" ] || { echo "MISSING phase $PH ckpt: $INIT" | tee -a "$A"; exit 5; }
    echo "--- $ARM phase $PH domain_eval (accumulated) ---" | tee -a "$A"
    $PY scripts/domain_eval.py "$INIT" "$SPEC" 30 >> "$A" 2>&1 || echo "domain_eval failed at $PH" >> "$A"
  done

  # cost telemetry + disk (P-A1 / TBD-GB): checkpoint bytes per phase (wall-clock is in logs)
  { echo "--- $ARM telemetry: checkpoint bytes per phase (from $OUT/) ---"
    for c in "${CHAIN[@]}"; do p="$OUT/bdh_textmix_${c}_last.pt"; [ -f "$p" ] && echo "$c $(stat -c%s "$p")"; done
  } | tee -a "$A"

  # P5 in-chain EVERY transition (storage must hold at every scale step, not spot-checked)
  echo "--- $ARM P5 in-chain (${#CHAIN[@]} checkpoints, $((${#CHAIN[@]}-1)) transitions) ---" | tee -a "$A"
  for i in $(seq 0 $((${#CHAIN[@]}-2))); do
    par="$OUT/bdh_textmix_${CHAIN[$i]}_last.pt"; chi="$OUT/bdh_textmix_${CHAIN[$((i+1))]}_last.pt"
    $PY scripts/p5_inchain_check.py "$par" "$chi" >> "$A" 2>&1
    echo "p5_rc=$? ${CHAIN[$i]}->${CHAIN[$((i+1))]}" | tee -a "$A"
  done

  # routing (P-A2/A3): likelihood scan, K x K, crops=200, window 128 (C0-validated)
  echo "--- $ARM routing (eval_router likelihood scan, all 5 domains, crops=$CROPS) ---" | tee -a "$A"
  timeout 2h $PY scripts/eval_router.py "$INIT" --routes "$ROUTES" \
    --domains "$SPEC" --crops "$CROPS" --window 128 --batch 4 \
    > "$LOG/${RUN}_routdiag_final.txt" 2>&1
  echo "ladder-${RUN}-done $(date '+%F %T')" | tee -a "$A"
  exit 0
fi

# ------------------------------------------------------------------ DECLARED arms (GUARDED)
# Kept as explicit non-goals rather than guessed. Filling them is an operator decision on
# the open questions in the header + plan §Design; once fixed, extend this file and re-smoke.
case "$ARM" in
  A1-K20|A1-K40)
    echo "$ARM NOT IMPLEMENTED: territory mix + single-phase europarl+textmix loading +"
    echo "(K40) corpora byte-distinctness are unresolved. See plan §Design open questions."
    echo "Do not guess: the sondeB base/prefix bug (europarl vs textmix) is the exact failure"
    echo "mode this guard prevents. Resolve in the plan, then implement."; exit 6;;
  A2-W512|A2-W1024)
    echo "$ARM NOT IMPLEMENTED: Axis 2 reuses the A1-K20 exit, which itself is guarded."
    echo "W1024 (~400M, ~4x/step) is the only arm that may need gx10 — see plan §Budget;"
    echo "that requires an explicit operator GO before any gx10 takeover (Qwen stays up)."; exit 6;;
  *) echo "unknown arm '$ARM'"; exit 2;;
esac
