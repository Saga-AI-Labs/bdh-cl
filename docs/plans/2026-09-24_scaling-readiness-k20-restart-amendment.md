# K20 restart amendment - resume ladder A at phase 13 with compilation disabled

- Date: 2026-09-24. Seat: A0-Quinn.
- Operator GO: "Bitte den K20-Neustart machen." (after the P3c report landed and the
  Spanish-drafter adaptation was explicitly declared out of scope for now).
- Pre-registration: `docs/plans/2026-09-23_scaling-readiness-k20-prereg.md`
  (commit `1556d9f031e44da5d0045be763bfd34e709de4ce`). This amendment changes
  exactly one runtime setting and adds one stop rule. It changes no scientific
  parameter, no phase order, no threshold, and no verdict.

## 1. Why the run stopped

Ladder A completed phases 2 through 12 (11 grows, territories `es` through `it`,
widths 10240 to 30720) and was stopped at the phase boundary before phase 13
(`et`, width 32768) started. Recorded evidence on the guest:

- 11 of 11 P5 transitions carry `P5-VERDICT: PASS` in the raw p5 files.
- Phase cost ratios stayed between 1.13x and 1.36x of the 0.094 s/width model,
  inside the frozen 1.5x stop rule.
- First-phase retention: prose 2.46 before and after grow 1, delta 0.00.
- The last valid checkpoint is
  `out_c/scaling_readiness/k20/bdh_textmix_k20-A-it_last.pt`,
  md5 `8d9af6d6f2a37b1e7e6a0f19e0ef4840`, 4,531,027,472 bytes.

The stop reason is VRAM headroom. During phase 12 the real route-aware training
process held **23,768 MiB** (`nvidia-smi --query-compute-apps`) and the card read
**24,064 MiB of 24,564 MiB** at 100 % utilisation, leaving about 500 MiB.
The ladder still had 13 phases to go, with the final width at 57,344.

The earlier 5-step memory probes (mult 736: 18,174 MiB; mult 896: 21,934 MiB)
were **not representative** of the training path: they omitted `--init-from`,
`--grow-mult` and `--route-aware`, so they carried neither the grow snapshots nor
the second (full) forward that route-aware training performs. That gap between the
probe and the real process is the reason for this amendment; it is not a result.

## 2. The one setting that changes

`--no-compile` is added to every grow command for both ladders.

Everything else stays exactly as pre-registered: `--model bdh --dataset textmix
--text-mix <tag>:<corpus> --text-mix-mb 30 --n-embd 512 --n-head 8 --block-size 512
--max-iters 10000 --batch-size 1 --warmup-iters 1000 --lr-decay-iters 10000
--grow-mult 32 --init-from <prev> --seed <seed> --no-freeze-attn --route-aware
--route-alpha 0.9`, fresh optimizer per phase, F-V9 step-end restore,
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

Compilation is a runtime optimisation, not a protocol parameter. It may change
timing and, in principle, the last bits of a float; the data stream, phase
order, widths, alpha, seed and the frozen-path restore are untouched. The K1
cost model and its 1.5x stop rule stay in force, so a timing penalty cannot pass
unnoticed.

## 3. Restart point

- Ladder A resumes at **phase 13, `et`, width 32768**, initialised from the
  phase-12 `last` checkpoint above. Phases 2-12 are not re-run.
- Ladder B starts unchanged from its base (`out_a/bdh_textmix_ladA-A1-K5-seed2-base_last.pt`,
  md5 `8680bd26ed55ddd2883bd077ad49e665`, seed 2), with `--no-compile` as well.
- The accumulated domain list for every resumed routdiag contains all phases
  1-12 plus the phases completed after the resume, so the final confusion is the
  full 25-territory grid.

## 4. Restart gate (probes before the first product step)

Two 5-step probes run under the exclusive `gpu://rtx4090` claim, write only to
`/tmp`, and are deleted afterwards. Neither writes a checkpoint into
`out_c/scaling_readiness/k20/`.

1. **Phase-13 shape:** `--init-from <phase-12 last> --grow-mult 32 --route-aware
   --route-alpha 0.9 --no-compile`, seed 1337, 5 steps.
2. **Worst-case shape:** the same command with `--grow-mult 512`, which lands on
   mult 896 / width 57,344 in one grow, the final ladder width. It is not a phase
   of the ladder; it is a memory probe of the widest shape.

**Gate:** peak total VRAM must be **<= 23,000 MiB** in both probes (at least
1,564 MiB headroom on a 24,564 MiB card). If either probe exceeds the gate, no
product phase starts; the result is reported with the measured peak.

## 5. Production guard (new stop rule)

During every product grow the driver samples `nvidia-smi --query-gpu=memory.used`
every 2 s and records the peak for the phase.

- Peak above **23,000 MiB**: the grow is terminated and the ladder stops with
  `K20_LADDER_A_STOPPED vram phase=<tag> peak=<MiB>`.
- Wall time above **1.5x** the predicted wall (unchanged from the pre-reg): the
  ladder stops with the existing `K1_STOP` line.
- P5 non-zero exit at any transition: the ladder stops, as pre-registered.

## 6. Record hygiene

The two `K20_LADDER_A_STOPPED manual_safety_stop` lines in the guest analysis
file (00:06:03 and 00:06:16) are one event recorded twice by a repeated shutdown
command. The file is left as it is; this note is the correction, and the resume
appends after a `RESUME` marker rather than editing the earlier record.

## 7. Ship

English, ASCII, newline-terminated; j-space ship gate must report that the
outgoing register holds. Bus: intent before the probes, intent before the resume,
done after each ladder. All checkpoint and corpus md5 gates run before the first
step of the resumed ladder, exactly as in the pre-registration.
