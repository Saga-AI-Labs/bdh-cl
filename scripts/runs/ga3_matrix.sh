#!/usr/bin/env bash
# G-A3 post-matrix (graft-2 prereg section 8, commit c45a865): the registered
# 7-cell fullcov b4 verdict on the grown g2_code LAST checkpoint (mult 1152).
# Zero-tolerance S1 identity cells FIRST (if the frozen prefix drifted, the
# rest is moot), then the comparison cells, then gen_serve_check on the new
# model (legal/zh/code prompts, full + old-mask). ~1.7 h per cell (measured),
# ~12 h total.
#   S1-a zh@mask-1024  == 1.7470/1.6858  ZERO tolerance (frozen-prefix identity)
#   S1-b zh@mask-896   == 1.7603/1.6980  ZERO tolerance
#   S1-c legal@mask-1024 == 1.1178/1.1250 ZERO tolerance
#   S1-d code@mask-1024 == 3.5787/3.5327  ZERO tolerance (pre-run anchor)
#   S2  legal@0        <= 1.2178 (P3 1.1178 + 0.10 convention)
#   D   code@0 post vs pre 3.5787/3.5327  headline swing, expect ~-0.8 nats
#   F   zh@0 post vs 1.7470/1.6858  free cell, registered erosion +0.5-0.8
set -u
set -o pipefail
cd /srv/coding/bdh-cl || exit 1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export BDH_MEM_FRACTION=0.8
CKPT_RUN=g2_code
OUT=/tmp/opencode/ga3_matrix
mkdir -p "$OUT"
LOG="$OUT/matrix.log"
: > "$LOG"

if pgrep -f 'pipeline\.run' > /dev/null; then
  echo "REFUSING: another pipeline.run process is active"; exit 1
fi

run_cell() {  # run_cell <name> <textmix-spec> [mask-old-mult]
  local name="$1" spec="$2" mask="${3:-}"
  local args=(--mlp-internal-dim-multiplier 1152)
  [ -n "$mask" ] && args+=(--mask-old-mult "$mask")
  echo "### cell $name | spec $spec | mask ${mask:-none} $(date '+%F %T')" | tee -a "$LOG"
  .venv/bin/python -u -m pipeline.run eval \
    --dataset textmix --text-mix "$spec" --text-mix-mb 30 \
    --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
    "${args[@]}" \
    --batch-size 1 --eval-batch-size 4 --eval-deterministic \
    --out-dir out_c/routed_probe --run-name "$CKPT_RUN" --tag last 2>&1 | tee -a "$LOG"
  echo "RC=$?"
}

# ---- zero-tolerance identity cells ----
run_cell "S1-a zh@mask-1024" "zh:data/europarl/xscript_zh.txt" 1024
run_cell "S1-b zh@mask-896"  "zh:data/europarl/xscript_zh.txt" 896
run_cell "S1-c legal@mask-1024" "legal:data/textmix2/legal.txt" 1024
run_cell "S1-d code@mask-1024"  "code:data/textmix2/code.txt"  1024
# ---- comparison cells ----
run_cell "S2 legal@0"  "legal:data/textmix2/legal.txt"
run_cell "D  code@0"   "code:data/textmix2/code.txt"
run_cell "F  zh@0"     "zh:data/europarl/xscript_zh.txt"

# ---- serving drift check on the grown model ----
echo "### gen_serve_check on g2_code last $(date '+%F %T')" | tee -a "$LOG"
.venv/bin/python -u scripts/gen_serve_check.py \
  out_c/routed_probe/bdh_textmix_g2_code_last.pt \
  --mask-old-mult 896 --tokens 200 --samples 5 2>&1 | tee -a "$LOG"

# ---- QA ----
echo "### QA" | tee -a "$LOG"
check_exact() {  # check_exact <cell> <expected-val> <expected-test>
  local cell="$1" ev="$2" et="$3"
  local block; block=$(awk "/### cell $cell /,/^RC=/" "$LOG" | grep -E '^(val|test)_loss')
  local v t
  v=$(grep -m1 '^val_loss' <<<"$block" | grep -o 'val_loss [0-9.]*')
  t=$(grep -m1 '^test_loss' <<<"$block" | grep -o 'test_loss [0-9.]*')
  if [[ "$v" == "val_loss $ev" && "$t" == "test_loss $et" ]]; then
    echo "OK   $cell bit-exact: $v / $t"
  else
    echo "FAIL $cell: expected val $ev / test $et, got [$v] / [$t]"
  fi
}
check_exact "S1-a zh@mask-1024"   1.7470 1.6858
check_exact "S1-b zh@mask-896"    1.7603 1.6980
check_exact "S1-c legal@mask-1024" 1.1178 1.1250
check_exact "S1-d code@mask-1024"  3.5787 3.5327
vS2=$(awk "/### cell S2 legal@0 /,/^RC=/" "$LOG" | grep -m1 '^val_loss' | sed 's/val_loss \([0-9.]*\).*/\1/')
awk -v x="$vS2" 'BEGIN { if (x <= 1.2178) printf "OK   S2 legal@0 val %s <= 1.2178\n", x; else printf "FAIL S2 legal@0 val %s > 1.2178\n", x }'
vD=$(awk "/### cell D  code@0 /,/^RC=/" "$LOG" | grep -m1 '^val_loss' | sed 's/val_loss \([0-9.]*\).*/\1/')
tD=$(awk "/### cell D  code@0 /,/^RC=/" "$LOG" | grep -m1 '^test_loss' | sed 's/test_loss \([0-9.]*\).*/\1/')
awk -v v="$vD" -v t="$tD" 'BEGIN { printf "READ D-cell code@0: val %s (pre 3.5787, swing %.4f) | test %s (pre 3.5327, swing %.4f)\n", v, 3.5787-v, t, 3.5327-t }'
vF=$(awk "/### cell F  zh@0 /,/^RC=/" "$LOG" | grep -m1 '^val_loss' | sed 's/val_loss \([0-9.]*\).*/\1/')
tF=$(awk "/### cell F  zh@0 /,/^RC=/" "$LOG" | grep -m1 '^test_loss' | sed 's/test_loss \([0-9.]*\).*/\1/')
awk -v v="$vF" -v t="$tF" 'BEGIN { printf "READ F zh@0: val %s (anchor 1.7470, erosion %+.4f) | test %s (anchor 1.6858, erosion %+.4f)\n", v, v-1.7470, t, t-1.6858 }'
echo "### G-A3 matrix done $(date '+%F %T')" | tee -a "$LOG"
