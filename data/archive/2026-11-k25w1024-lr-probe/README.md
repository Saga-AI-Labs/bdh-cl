# Archive: K25/W1024 learning-rate probe (`lr_probe`)

**Date:** 2026-11
**Origin:** `out_c/expert_merge/lr_probe/` (BDH-CL training host)
**Size:** 190 GB, 6 checkpoints (3 arms x best/last)
**Status:** experiment complete, evaluated, closed

---

## What it was

A learning-rate probe on the K25/W1024 model (2.82 B parameters, `bdh`
architecture) to choose the learning rate for the expert-merge branch training.
Three arms were run, each 100 steps on a tiny model first, then on the real one:

| arm | learning rate | result |
|---|---|---|
| A | 1e-4 | selected (lowest rate in the +5 % band) |
| B | 3e-4 | — |
| C | 1e-3 | control (would be destructive on a 2.82 B fine-tune) |

The probe script is `scripts/quinn/lr_probe.sh` (in `out_c/expert_merge/`). The
log is `lr_probe.log`. The selection rule was registered before the run: the
lowest rate whose loss stayed inside the +5 % band of the best arm.

## Where the data lives

```
Hugging Face:  Saga-AI-Labs/bdh-expert-merge  lr_probe/   (6 x 33.83 GB)
               sha256 (LFS) d130f291e5b7 ... 9035ee14ffed
```

The checkpoints are **not** needed for reproduction of the probe result: the
selection is a table in the expert-merge report, not a re-runnable artifact.

## What it is good for now

Nothing active. The learning rate it selected was used for B1 and the graft
phases. If a future branch needs the same rate, the number is in the report; the
checkpoints themselves are the only record that the run happened.

## How it ended up here

The probe directory was under `out_c/expert_merge/lr_probe/`. `out_c/` was
retired 2026-11-22 as a "phantom structure" and its contents were either
archived or deleted after HF verification. This README exists so that the
archive is self-describing in six months.
