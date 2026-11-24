#!/usr/bin/env bash
# Launch the host arm.
#
# torch.compile needs Python development headers. This box has no sudo and no
# python3.12-dev, so the headers are extracted from the matching Ubuntu package
# into the user tree and put on the compiler's include path. The model, data and
# numerics are untouched; only the Triton extension build needs them.
#
# Usage: scripts/quinn/launch_host.sh [extra pipeline.run train args]
# Stop:  kill the process group (the run writes <stem>_last.pt every 5000 steps;
#        rerun with the same command and --resume continues).
set -euo pipefail
cd "$(dirname "$0")/../.."
HEADERS="${BDH_PY312_HEADERS:-$HOME/.local/share/bdh/py312-headers}"
export CPATH="$HEADERS/python3.12:$HEADERS"
export C_INCLUDE_PATH="$CPATH"
export TORCHINDUCTOR_CACHE_DIR="${TORCHINDUCTOR_CACHE_DIR:-/tmp/opencode/inductor_cache}"
exec .venv/bin/python -u -m pipeline.run train \
  --model bdh --dataset files \
  --train-file data/host/fineweb_train.txt \
  --val-file data/host/fineweb_val.txt \
  --test-file data/host/fineweb_test.txt \
  --n-embd 512 --n-head 8 --n-layer 4 --mlp-internal-dim-multiplier 128 \
  --block-size 512 --batch-size 8 \
  --max-iters 488281 --warmup-iters 2000 --lr-decay-iters 488281 \
  --learning-rate 1e-3 --min-lr 1e-4 --weight-decay 0.1 \
  --eval-interval 5000 --eval-iters 100 --log-interval 200 \
  --data-order shuffled-onepass --data-seed 1337 --resume \
  --compile --device cuda --dtype auto \
  --out-dir out/host --run-name host100m-e1 "$@"
