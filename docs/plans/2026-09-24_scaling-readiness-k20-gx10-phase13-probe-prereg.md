# K20 gx10 phase-13 probe - 2000 steps on the GB10, fresh K1 baseline

- Date: 2026-09-24. Seat: A0-Quinn.
- Operator GO: "Wir ziehen auf den gx10 um, wenn das geht."
- Preflight: `docs/plans/2026-09-24_scaling-readiness-k20-gx10-migration-preflight.md`
  (commit `a96a99ece679ceb82c821e93f0c23fe315a881bf`).
- Target: gx10-50ef, aarch64, NVIDIA GB10 (capability 12.1), driver 580.178.04,
  torch 2.13.0+cu130, unified memory 121 GB. Host claim `host://gx10`, scope
  `s_bdh-cl_000356_13cad7`.
- Purpose: establish whether the GB10 carries the phase-13 grow at all, and
  measure its own wall clock. The 4090 OOMed at this shape (rope, bdh.py line 105).
  No scientific parameter, threshold, verdict or phase order changes.

## 0. Objects (md5 pinned; a mismatch aborts, no training step taken)

Checked directly on gx10 for all six objects after the transfer, against the K20
pre-registration:

| object | md5 | size |
| --- | --- | --- |
| out_c/scaling_readiness/k20/bdh_textmix_k20-A-it_last.pt | 8d9af6d6f2a37b1e7e6a0f19e0ef4840 | 4,531,027,472 |
| data/textmix2/code.txt | 82fe4bf18725b550b23a4e1040b10a2d | 40,529,764 |
| data/textmix2/latex.txt | 6a1a069e969e85b00532328550e10540 | 40,006,401 |
| data/textmix2/legal.txt | 0135960429085039dbe5385f649e75fe | 40,347,823 |
| data/europarl/xscript_zh.txt | dc2203307a9dc80ddd897e3109dbf3f6 | 1,289,893,407 |
| data/europarl/DGT.en-ga.ga.txt | e170553dacb07a78aabf34c0ecbbdb2b | 55,409,138 |

The `et` corpus for the phase-13 grow is already on gx10
(`data/europarl/europarl-v7.et-en.et.txt`, 91,510,232 B, md5
`7a37eccafc03906d60501fd7538a78b9`). Code files are md5-identical to the 4090
guest at HEAD `e6bf359`: bdh.py `da6eff44...`, pipeline/train.py `3ad7848d...`,
pipeline/config.py `904b6954...`, pipeline/data.py `c45ea50d...`,
scripts/eval_router.py `73832ecd...`, scripts/p5_inchain_check.py `4456a8ec...`.

## 1. The run

Phase 13 of ladder A: tag `et`, corpus
`data/europarl/europarl-v7.et-en.et.txt`, grow +32 from mult 480 to 512
(width 32768), initialised from the phase-12 `last` checkpoint above.

Protocol, identical to the K20 pre-registration except for `--max-iters 2000`
instead of 10000 (one fifth of the production budget, to establish a wall-clock
baseline without a 24-hour commitment):

```
--model bdh --dataset textmix --text-mix et:data/europarl/europarl-v7.et-en.et.txt
--text-mix-mb 30 --n-embd 512 --n-head 8 --block-size 512
--max-iters 2000 --batch-size 1 --warmup-iters 200 --lr-decay-iters 2000
--grow-mult 32 --init-from <phase-12 last> --seed 1337
--no-freeze-attn --route-aware --route-alpha 0.9
--run-name k20-gx10-probe-et --out-dir out_c/scaling_readiness/k20_gx10_probe
```

`--no-compile` is **not** used: the 4090 probes refuted that idea, and the
pre-registered configuration is the one under test.

## 2. Measurements

- **Unified memory**: `/proc/meminfo` `MemAvailable` and `MemFree` sampled every
  2 s, because the GB10 exposes no per-process VRAM through `nvidia-smi`. The
  probe records the minimum `MemAvailable` during the run, which is the working
  set on this host.
- **Wall clock**: total seconds and seconds per step from the training log
  (`ms/step` lines), plus the 2000-step budget as the reference.
- **Completion**: `train_rc`, the presence of the `last` and `best` checkpoints,
  their sizes and md5, and the final val/test line.

## 3. What the probe decides

- **Fit**: if the run completes with rc=0, the GB10 carries the phase-13 shape.
  The probe checkpoint is not a product checkpoint and is not used as a ladder
  exit; the product phase re-runs the full 10000 steps from the same phase-12
  checkpoint afterwards.
- **K1 baseline**: seconds per step on the GB10 replaces the 4090 model for the
  remaining ladder. The 1.5x K1 stop rule then applies to that measured baseline,
  not to 0.094 s per width unit.
- **No fit**: if the run OOMs or the host reports an unacceptable minimum
  `MemAvailable` (below 8 GB free), the migration is reported as blocked with the
  numbers, and the gx10 option is closed.

## 4. Stop rules and cleanup

- Host claim must be live (renewer running) for the whole window; no training
  without a live claim.
- Hard timeout 3 h for 2000 steps; a timeout is reported as a wall-clock result,
  not as a fit.
- Output only to `out_c/scaling_readiness/k20_gx10_probe/`; `out/`, `out_a/` and
  the ladder-A directory are read-only on gx10 for this probe.
- The probe directory is kept as evidence; the host claim is released when the
  probe ends.

## 5. Ship

English, ASCII, newline-terminated; the j-space ship gate must report the
outgoing register holds. Bus: intent before the probe, done with the numbers after.
