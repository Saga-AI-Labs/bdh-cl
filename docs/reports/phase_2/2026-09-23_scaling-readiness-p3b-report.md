# Scaling-readiness P3b report - leak rate vs K and the window question (eval-only)

- Date: 2026-09-23 (driver window 06:32:06 - 07:26:21 host time, 54 min 15 s,
  10 instrumented runs, all rc=0)
- Seat: A0-Quinn. Pre-registration: `docs/plans/2026-09-23_scaling-readiness-p3b-prereg.md`
  (`ecc77d73` + additive correction `71b192f`), verdicts frozen before measurement.
- Operator GO ("minimaler Zeitaufwand -> go") answering pi50 #442; bus intent
  `m_bdh-cl_0000000452`, pin-correction status `m_bdh-cl_0000000454`.
- GPU claim `s_bdh-cl_000216_65960c` (`gpu://rtx4090`, exclusive), renewer held it
  for every minute of the run (renew HTTP 200 throughout), released HTTP 204 when
  the card was verified idle (287 MiB, 0 %) by each of nvidia-smi and ps, both of
  which showed no work.
- No training. No weight movement. Evals only, on the eight existing checkpoints of
  the P3 ladder. Writes only `out_c/scaling_readiness/p3b/`.
- Instrument: guest `scripts/eval_router.py` at HEAD `e6bf359`, md5
  `73832ecd08f24eded93a98a74572be6e`, git-clean against that HEAD (verified by each
  of: md5sum in the driver log, `git status --porcelain` empty for the file). The
  pre-registration's first pin (`ed9fd326`, local build `2f0dc9d1`) named a file that
  was never on the guest path; the md5 gate aborted the first launch exactly as
  designed (exit 4, zero measurements), and the pin was corrected additively in
  `71b192f` - the error is documented, not hidden.
- Checkpoint identity: each of the seven grown files was md5-pinned at measurement
  time and each matched its P3 ledger entry (de `add1438f`, es `d74921a9`, pl
  `e9707f8f`, code `89e90ecd`, math `081f95ba`, legal `fd9f802d`, ga `8814ddc6`);
  the base control is `8680bd26` (size 1211147753). Artifacts transferred to local
  verified by each of: md5sum equality guest-vs-local for all ten files.

## 1. Run A - the leak rate as a function of K (Q1)

The 8x8 confusion at each checkpoint of the ladder (window 128 tok, 200
rows/domain, routes 8192..22528; routes above a checkpoint's width clamp to it -
the widths are not comparable across checkpoints where a column did not yet
exist). Diagonal := each domain at the width it had at that checkpoint (a domain
not yet trained rides at 8192 - the width of the base). Off-diagonal :=
1600 - diagonal; leak := off/1600. Counted by the parser, not by hand; the parsed
per-row values are reproduced below so the count is checkable.

| ckpt (K) | diagonal | off | leak % | rows off the diagonal (verbatim) |
| --- | --- | --- | --- | --- |
| base (K=1) | 1600 | 0 | 0.00 | none (all eight domains ride 8192 - no leak by construction, the control) |
| de (K=2) | 1487 | 113 | 7.06 | de 1->8192, es 2, pl 3, code 85, math 19, ga 3 |
| es (K=3) | 1479 | 121 | 7.56 | de 1, pl 1+2, code 44+46, math 3+19, ga 3+2 |
| pl (K=4) | 1481 | 119 | 7.44 | de 1, code 44+45+1, math 3+17+3, ga 2+2+1 |
| code (K=5) | 1318 | 282 | 17.62 | pl 2, code 3, math 18->8192 + 182->16384, legal 145 + 55, ga 161 + 38 + 1 |
| math (K=6) | 1500 | 100 | 6.25 | de 1, pl 2, code 3, legal 144->8192 + 56->16384, ga 162 + 37 + 1 |
| legal (K=7) | 1549 | 51 | 3.19 | de 1, pl 2, code 3, legal 5, ga 160 + 35 + 4 + 1 |
| ga (K=8) | 1589 | 11 | 0.69 | de 1, pl 2, code 3, legal 5 |

The curve is not monotone: flat at 7.0-7.6 % (K=2..4), a spike to 17.62 % at
K=5, then falling 6.25 -> 3.19 -> 0.69 %. The spike explains itself from the
rows: when the code block was grown (16384), the domains not yet trained on it
migrated to it en masse - math 182 of 200, legal 55, ga 38. Each later phase
called its own domain back (math 18 -> 200, legal 145 -> 195, ga 161 -> 200) and
the leak fell, until at K=8 every domain holds its own trained block and only 11
of 1600 crops stray (de 1, pl 2, code 3, legal 5 - all upward, none downward).

### Frozen verdict Q1

- Requirement: `leak(ga) <= 0.50 * leak(de)` for H-scalefree-decreasing.
- Measured: leak(ga) = 0.00688, leak(de) = 0.07062, ratio 0.0973, threshold
  0.50 - verified by the parser run over all eight files.
- **CONFIRMED over all eight checkpoint files: H-scalefree-decreasing.** The pi50 thesis (relative damage of the
  leak shrinks as the ladder grows) is supported; the scale-free prediction
  H-flat (band 0.50-1.50) is refuted by the same measurement.
- Reading: the 0.69 % terminal leak is a property of the fully-trained ladder,
  not of routing at scale; the K-dependence is dominated by the freshness of the
  newly grown block, which transiently steals from the not-yet-trained domains.

## 2. Run B - the window of the leak (Q2)

ga_last (`8814ddc6`, the same file for both readings), legal only, 200 crops,
routes 8192,22528 - the two-way menu, the widths 10240..20480 are absent.

| window | legal -> 8192 | legal -> 22528 | share at the narrow column |
| --- | --- | --- | --- |
| 128 tok | 194 | 6 | 0.9700 |
| 384 tok | 197 | 3 | 0.9850 |

### Frozen verdict Q2

- Requirement: `share384 <= 0.70 * share128` for H-window-dependent.
- Measured: 0.9850 vs 0.70 * 0.9700 = 0.6790 - no attenuation; if anything a
  slight increase (+3 crops at the narrow column). Verified by the parser over both files of the window probe.
- **H-window-INDEPENDENT** (no attenuation).
- Consequence for the programme: the P0 cost figures (8.2 / 8.6 % at the
  12-token window) are window-128 numbers. They do not attenuate when read with
  the 384-token window, therefore they are stated window-conditional in the
  manuscript, not as a property of the model.
- Limitation stated: the two-way menu carries only 8192 and 22528; without the
  intermediate widths the test is a comparison within this menu only, and the
  printed ppl of both readings are not comparable with each other (the late span
  of the evaluation changes with the window: 128 vs 384 tokens).

## 3. Reproduction

```
ssh bdh-4090 'cd /media/data/coding/bdh && bash /tmp/p3b_driver.sh'
# driver log: /tmp/p3b.log  (P3B_DRIVER_START/ER_MD5/LEGAL_MD5/BASE_MD5 lines,
#   per-checkpoint rc/wall/md5/bytes lines, P3B_DRIVER_DONE 2026-09-23 07:26:21)
# artifacts: out_c/scaling_readiness/p3b/ (eight confusion files, two window
#   files, p3b_analysis.txt)
# local copies verified by md5sum equality for all ten files: ga 87d057b2,
#   w128 50f44328, w384 d8f0e261
```

## 4. Open, not measured

- single ladder, single seed, n = 200/domain, descriptive, no p-value.
- the per-phase curve is read from the same 200 crops at each checkpoint - the
  crops are not independent of the checkpoint's own history (the base and each
  grown file are fixed objects).
- the K-sweep of the leak on a reference ladder (second seed) was not asked for
  and was not done.
- the spike at K=5 was not rehearsed without the code phase; its mechanism
  (freshly grown block attracts the not-yet-trained domains) is read from the
  confusion rows, not from an additional probe.
