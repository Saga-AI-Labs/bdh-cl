# K20 gx10 phase-13 probe - amendment 1: --no-compile on the GB10

- Date: 2026-09-24. Seat: A0-Quinn.
- Probe pre-registration: `docs/plans/2026-09-24_scaling-readiness-k20-gx10-phase13-probe-prereg.md`
  (commit `21b3c9ea3d116d5ab6b818f8b75f5de7989c979f`).
- Operator GO: "Wir ziehen auf den gx10 um, wenn das geht."

## 1. What the first probe showed

The first run passed all six md5 gates on the gx10, built the model
(402,915,328 parameters, bf16, cuda) and then failed in the first forward with
`rc=1`, inside torch.compile / Triton:

```
/tmp/tmphguqcmcn/cuda_utils.c:9:10: fatal error: Python.h: No such file or directory
compilation terminated.
torch._inductor.exc.InductorError: ... gcc ... returned non-zero exit status 1
```

Measured on the host: `/usr/include/python3.12` exists but `Python.h` does not,
gcc 13.3.0 is present, and the seat `a0-quinn` has no passwordless sudo, so
`python3.12-dev` cannot be installed by this seat. The failure is a toolchain gap,
not a memory shortage: across five samples the minimum `MemAvailable` was
110,996 MiB and the minimum `MemFree` 89,294 MiB. The question "does the phase-13
shape fit on the GB10" is therefore **still open**, not answered.

## 2. The single deviation

`--no-compile` is added to the probe command. Nothing else changes: same host, same
phase-13 shape (tag `et`, grow +32 from mult 480 to 512, width 32768), same
`--init-from` phase-12 checkpoint, same seed 1337, same batch 1, block 512, bf16,
`--route-aware --route-alpha 0.9`, same `--max-iters 2000`, same output directory
`out_c/scaling_readiness/k20_gx10_probe/`.

What `--no-compile` is **not**: a memory fix. The four 4090 probes measured earlier
showed that disabling compilation changed the peak by about 2 percent and did not
prevent the OOM there. On the gx10 it is a **workaround for the missing Python
headers**: without it, the Inductor C build cannot compile at all and the run cannot
reach the first training step. The memory and wall-clock measurements of this probe
remain the deliverable; the timing is a GB10 baseline without Inductor fusion, so it
is an upper bound on the GB10 step time, and that caveat is recorded with the
numbers.

## 3. Decision rules (unchanged)

- `rc=0` with a `last` checkpoint present: the GB10 carries the phase-13 shape. The
  measured step time becomes the K1 baseline for the remaining 13 phases, with the
  no-compile caveat above.
- OOM, or minimum `MemAvailable` below 8,192 MiB: the gx10 option is closed with
  the numbers, and the 4090 memory knee stands as the scaling result.
- Hard timeout 3 h, reported as a wall-clock result, not as a fit.

## 4. What is not changed by this amendment

No data, no phase order, no width schedule, no threshold, no verdict, no
scientific parameter. The alternative (installing `python3.12-dev` on the gx10) is
a cross-seat action for the operator and is deliberately not taken here.

## 5. Ship

English, ASCII, newline-terminated; the j-space ship gate must report the outgoing
register holds. Bus: intent before the re-run, done with the numbers after.
