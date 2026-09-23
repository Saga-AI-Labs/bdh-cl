# K20 restart probe result - gate failed, no production phase started

- Date: 2026-09-24. Seat: A0-Quinn.
- Restart amendment: `docs/plans/2026-09-24_scaling-readiness-k20-restart-amendment.md`
  (commit `c79afdef19db09d2cc8746639df83fb825356cf8`).
- Bus intent: `m_bdh-cl_0000000463`. Claim: `s_bdh-cl_000352_7d7744`, released
  HTTP 204 after the probes, registry empty.
- Verdict: **restart blocked**. No product phase started. The amendment's
  `--no-compile` change is refuted by the probes below and is not to be used.

## 1. The four representative probes

All four ran on the guest through the real training path: `--init-from` the
phase-12 `last` checkpoint (md5 `8d9af6d6f2a37b1e7e6a0f19e0ef4840`),
`--grow-mult` as listed, `--route-aware --route-alpha 0.9`, `--no-freeze-attn`,
`--batch-size 1`, `--block-size 512`, bf16, 5 steps, `expandable_segments`.
Output went to `/tmp` only and was deleted after reading. Peak is total VRAM as
sampled at 1 Hz by `nvidia-smi --query-gpu=memory.used`.

| arm | compile | grow | mult | width | train_rc | peak MiB | failed allocation | free at failure |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | OFF | 32 | 480 -> 512 | 32,768 | 1 | 23,600 | 512.00 MiB | 480.81 MiB |
| 2 | OFF | 512 | 480 -> 992 | 63,488 | 1 | 23,574 | 992.00 MiB | 506.81 MiB |
| 3 | ON | 32 | 480 -> 512 | 32,768 | 1 | 23,978 | 256.00 MiB | 102.81 MiB |
| 4 | ON | 416 | 480 -> 896 | 57,344 | 1 | 23,334 | 896.00 MiB | 746.81 MiB |

Arm 2 used `--grow-mult 512` instead of the intended 416 and therefore lands on
mult 992 / width 63,488, wider than any ladder phase. That is a script defect,
recorded here so the number is not mistaken for the ladder's final-width shape;
arm 4 is the exact final-width shape.

Every arm ended in `torch.OutOfMemoryError` inside the route-aware prefix
forward:

```
File "bdh.py", line 126, in forward
    QR = self.rope(r_phases, Q)
File "bdh.py", line 105, in rope
    return (v * phases_cos).to(v.dtype) + (v_rot * phases_sin).to(v.dtype)
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 256.00 MiB
```

## 2. What the probes say

- `--no-compile` is **not** a fix. Compile ON and OFF both fail, and the peaks
  sit within about 2 % of each other across a 2x width span (arms 1 and 3 at
  width 32,768: 23,600 vs 23,978; arms 2 and 4 across 63,488 vs 57,344: 23,574
  vs 23,334). Peak is therefore not a clean function of width for this path;
  the ceiling is set by the route-aware double forward, whose working set at
  mult 480-512 already exceeds a 24 GiB card.
- The practical boundary for this path on this card is between the last
  successful product phase (mult 480, width 30,720, 23,768 MiB) and the next
  one (mult 512, width 32,768), which OOMs in every variant tried.
- The 5-step probes from the pre-registration (mult 736: 18,174 MiB; mult 896:
  21,934 MiB) were indeed unrepresentative: they omitted `--init-from`,
  `--grow-mult` and `--route-aware`, as the restart amendment already stated.
  This result confirms that statement with the real path.

## 3. What stands and what does not

Stands (ladder A, phases 2-12): 11 of 11 P5 transitions PASS, cost ratios
1.13x-1.36x against the frozen 1.5x rule, first-phase retention delta 0.00,
last checkpoint `bdh_textmix_k20-A-it_last.pt` md5 `8d9af6d6f2a37b1e7e6a0f19e0ef4840`.

Does not exist: phase 13, phases 14-25, ladder B, the final 25x25 confusion,
and the K3/K5 verdicts. No product phase started in this restart attempt.

## 4. Options (material decision, not taken here)

1. **Move the ladder to a host with more memory** (the gx10 with 121 GB unified
   memory is the known candidate). Needs its own preflight: runtime, torch
   build, data paths, and an operator GO for the host.
2. **Close ladder A at 12 phases on the 4090** and report the measured memory
   knee (mult 480 / width 30,720) as the scaling result for this card, with the
   25-territory arm declared infeasible on 24 GiB. Ladder B was never started.
3. **Change the training code** to cut the route-aware working set (gradient
   checkpointing in the BDH forward, or moving the grow-path frozen snapshot
   off the GPU). This is a code change in the model path and needs its own
   pre-registration plus a bit-exactness gate on the frozen path before any
   product phase.

Nothing in the frozen protocol changes in any of these options without a new
recorded decision.

## 5. Cleanup performed

- Probe directories, logs and scripts under `/tmp` on the guest: deleted.
- Probe renewer: stopped. Claim: released HTTP 204, registry `active: []`.
- GPU at the end: 287 MiB of 24,564 MiB, 0 % utilisation, no `pipeline.run`,
  `k20_driver`, `k20_launch` or probe process left.
- No file in `out/`, `out_a/` or `out_c/scaling_readiness/k20/` was modified by
  the probes.

## 6. Ship

English, ASCII, newline-terminated; the j-space ship gate must report the
outgoing register holds. Bus: this result is posted as a reply to the probe
intent `m_bdh-cl_0000000463`. The restart amendment stays as landed; this
erratum is its correction, and no history is rewritten.
