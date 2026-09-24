# K20 gx10 production resume amendment

- Date: 2026-09-24. Seat: A0-Quinn.
- Parent pre-registration: `docs/plans/2026-09-23_scaling-readiness-k20-prereg.md`.
- Parent probe documents: `docs/plans/2026-09-24_scaling-readiness-k20-gx10-phase13-probe-prereg.md` and
  `docs/plans/2026-09-24_scaling-readiness-k20-gx10-phase13-probe-amendment.md`.
- Operator GO: `OK, dann kannst du jetzt loslegen.`
- Target: gx10-50ef, NVIDIA GB10, aarch64, torch 2.13.0+cu130.
- Parent repository HEAD: `959ea6f4c9d7ff7445e6613905987c1f09ea6102`.
- Production driver local md5: `ecec2376eb7678e107b2720d6415b943`.
- Production driver source: `out_c/scaling_readiness/k20_gx10_resume.sh`.

## 1. Scope of this amendment

The K20 pre-registration remains the scientific authority. This amendment changes only
host-specific execution details for the ladder-A resume on gx10. It does not change the
territory order, corpus bytes, width schedule, model configuration, frozen route-aware
protocol, P5 storage gate, routing gate, retention gate, or ladder-agreement gate.

Ladder B is not started in this amendment. Ladder A is independent and may be archived
after completion without affecting a later B run.

## 2. Resume point and phase order

Ladder A resumes at phase 13, tag `et`, width 32768, from the transferred phase-12
checkpoint:

| object | path | md5 |
| --- | --- | --- |
| parent checkpoint | `/srv/coding/bdh/out_c/scaling_readiness/k20/bdh_textmix_k20-A-it_last.pt` | `8d9af6d6f2a37b1e7e6a0f19e0ef4840` |

Phases 2 through 12 are not rerun. Their 11 grow domains are included in the accumulated
`SPEC` list for every resumed own-width routdiag. The new sequence is fixed as:

| phase | tag | width |
| ---: | --- | ---: |
| 13 | et | 32768 |
| 14 | el | 34816 |
| 15 | sk | 36864 |
| 16 | sv | 38912 |
| 17 | ro | 40960 |
| 18 | nl | 43008 |
| 19 | sl | 45056 |
| 20 | lt | 47104 |
| 21 | code | 49152 |
| 22 | math | 51200 |
| 23 | legal | 53248 |
| 24 | ga | 55296 |
| 25 | zh | 57344 |

The final confusion evaluation uses all 25 widths from 8192 through 57344. The driver
checks the exact route string before starting that evaluation.

## 3. Production protocol

Each new phase uses the K20 protocol with compile enabled:

```
--model bdh --dataset textmix --text-mix <tag>:<pinned corpus> --text-mix-mb 30
--n-embd 512 --n-head 8 --block-size 512 --max-iters 10000 --batch-size 1
--warmup-iters 1000 --lr-decay-iters 10000 --grow-mult 32
--init-from <previous phase last checkpoint> --seed 1337
--no-freeze-attn --route-aware --route-alpha 0.9 --compile
--run-name k20-gx10-A-<tag> --out-dir out_c/scaling_readiness/k20
```

Fresh optimizer state is used per phase. `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
and unbuffered training output are set by the driver. The `best` and `last` checkpoints are
both retained in full. The probe checkpoints under `out_c/scaling_readiness/k20_gx10_probe/`
are evidence only and are never used as a product exit.

## 4. Measured gx10 K1 baseline

The compile probe completed successfully before this amendment:

- `train_rc=0`, `2000/2000` steps;
- wall time `2837 s`;
- `last` and `best` checkpoints present, each `4,833,026,049` bytes;
- 200 logged `ms/step` samples, median `1050 ms`, minimum `1037 ms`, maximum `4277 ms`;
- `1,412` unified-memory samples, minimum `MemAvailable=85768 MiB` and minimum
  `MemFree=45107 MiB`;
- no OOM; final log line `1049 ms/step`.

The production K1 prediction is therefore:

```
PRED(w) = ceil(1.4185 seconds_per_step * (w / 32768) * 10000)
```

where `1.4185 s/step` is the measured probe wall time per step (`2837 / 2000`).
This replaces the 4090 `0.094 s/width` model only for this gx10 run. The frozen K1 stop
rule remains a factor of `1.5`: a phase exceeding `1.5 * PRED(w)` stops and is reported.
The hard timeout is `2.5 * PRED(w)`.

## 5. Host-specific disk and claim rules

The gx10 filesystem had 296 GB free at the production dry-run. The measured checkpoint
regression from the 4090 run estimates approximately 164.9 GB for the remaining ladder-A
phases with full `best + last` storage. The operational disk floor for this host is
therefore fixed at `100,000,000,000` free bytes. This is a host-specific safety floor, not a
change to a scientific gate. A lower reading stops the run before the next phase.

The production run requires two live HAK scopes:

- `host://gx10`, exclusive, renewed by a dedicated renewer;
- `file:///srv/coding/bdh/out_c/scaling_readiness/k20`, exclusive, renewed by the same
  renewer.

The renewer writes `/tmp/k20_gx10_claim_live` atomically. Before every phase, the driver
requires this heartbeat to exist and to be no older than 900 seconds. A missing or stale
heartbeat stops the ladder before the next phase. `/tmp/k20_gx10_resume_done` is written on
every exit path.

## 6. Gates and instrument order

Before the first training step, the driver checks md5 pins for the six code/instrument
files, prose, the phase-12 checkpoint, and all 24 grow corpora. The 11 already completed
grow corpora are also checked before the resume. A mismatch aborts before training.

After every new phase:

1. the full `last` checkpoint must exist;
2. the phase wall time and ratio to `PRED(w)` are logged;
3. P5 must return exit code zero **and** its output must contain `P5-VERDICT: PASS` (or
   the equivalent `P5_PASS` marker);
4. the accumulated-domain own-width routdiag must return exit code zero;
5. the next phase uses the new `last` checkpoint.

The final 25x25 confusion is run only after phase 25. It must return exit code zero for the
ladder to receive the `K20_GX10_RESUME_DONE` marker.

## 7. Verification before launch

The production driver is copied to gx10 and its local and guest md5 values must match.
`bash -n` must pass. A guest dry-run with `DRY_RUN=1` must pass every gate and print
`DRY_RUN_OK`. The dedicated renewer must be alive and both scopes must be live before the
production process is started. The first log lines, process tree, claim scopes, disk space,
and heartbeat are checked after launch.

No report or completion claim is made from a timeout, a partial log, or a process that
has not reached its sentinel.

## 8. Unchanged claims and limits

This amendment does not claim that gx10 throughput equals the 4090. The measured rate is a
fresh host baseline. It does not make the two loaders byte-comparable: Europarl training
reads the file tail while textmix training reads the file head. It does not start ladder B,
and it does not alter the final routing or retention verdicts.
