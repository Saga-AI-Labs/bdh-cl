# Scaling-readiness P0 - eval scale-up and dedup (report)

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: run complete
Design of record: `docs/plans/2026-09-22_scaling-readiness-p0-prereg.md` @ `1dc2810`
(reads the E1/E2 corrections of `docs/plans/2026-09-22_scaling-readiness-erratum.md` @ `ac6d046`)
Parent plan: `docs/plans/2026-09-22_scaling-readiness-gaps-and-probes-prereg.md` @ `76dd597`, section 3 P0.
Operator GO: "P0 + P1a + P2: go". No training. No writes under `out/` or `out_a/`.
Raw artifacts: `out_c/scaling_readiness/` on the guest (gitignored), md5-pinned in section 7.

## 1. Question

The 8% legal-leak price and the 9/200 vs 11/200 leak rates rest on n=200 crops. The two legal
cells were re-evaluated at N=1000 crops with the same routes, the same window, the same domain
order and the same instrument, and the crops were audited for the overlap that makes the nominal
n larger than the independent n.

## 2. What was established before any figure was read

Four gates, in this order. A failure at any gate stops the reading of the next one.

1. **Instrument gate.** `EVAL_ROUTER_MD5 70ddc5f31c0e3871c029f4f4f9dee7d2` (the instrument that
   produced the archived window-128 dumps) and `LEGAL_CORPUS_MD5 0135960429085039dbe5385f649e75fe`.
2. **G0-a reproduction gate (E1).** The `CROP_DUMP domain=legal` block of a fresh `--crops 200`
   rerun must equal the archived baseline block byte for byte. The gate prints:
   `G0A tag=seed2 rc=0 rows=200 block_md5=f245e20c3dfc08c25f93d2d2f929582d expect=f245e20c3dfc08c25f93d2d2f929582d`
   `G0A tag=ref   rc=0 rows=200 block_md5=be48bc0e052560a7d7faf5b47cbaab88 expect=be48bc0e052560a7d7faf5b47cbaab88`
   Both pass, and the whole-file md5 of the two rerun files (`168504a9...`, `51dd88cc...`) equals
   the archived dumps themselves: the rerun reproduced the archived artifacts exactly.
3. **Parser gate.** The parser that produced the numbers below, applied to the two 200-crop files,
   returns 9 leakers for seed-2 (8 at 12288, 1 at 10240) and 11 for the reference ladder (all at
   12288). These are the archived figures; the row counts agree, so the same parser may read the
   1000-crop files.
4. **Offset-replay gate.** The legal crop offsets used by R3/R4 were replayed from the instrument's
   own draw (`torch.Generator().manual_seed(1234)`, one generator, consumed in SPEC order
   prose, code, math, legal, ga; `hi = len(arr) - 512 - 1`). Compared as a sorted set with the
   archived 200-crop offset list (md5 `6fb994425e328c0c6271dc1fd1793ebf`, offset column) the two
   are equal. See section 8 for the one mistake this gate caught me making.

## 3. R1 - leak set at N=1000

| ladder  | crops | leakers | rate   | nominal Wilson 95%  | effective n | Wilson at effective n |
| ------- | ----: | ------: | -----: | ------------------- | ----------: | --------- |
| seed-2  |  1000 |      52 |  5.20% | 3.99% .. 6.76%      |         876 | 4.56% .. 7.70%        |
| ref     |  1000 |      63 |  6.30% | 4.95% .. 7.98%      |         876 | 5.66% .. 9.10%        |

Where a leaker is a crop whose chosen route is not the trained width 14336; the effective n is the
class count of section 5.

Route distribution of the leakers (the width they actually fall back to):

```
seed-2   49 @ 12288   2 @ 8192   1 @ 10240        (total 52)
ref      57 @ 12288   4 @ 8192   2 @ 10240        (total 63)
```

Not one leaker routes upward: no crop moves to 16384, and no crop on the trained width is counted
as a leaker. Mean margin (`scoreA - scoreB`, early window) is negative for the leakers (-0.0342
seed-2, -0.0276 ref) and positive for the stayers (+0.0873, +0.0973) - the same sign split that the
position probe of the same cell reported.

Against the n=200 baseline the rate rose slightly (4.5% to 5.2% seed-2; 5.5% to 6.3% ref). The
200-crop figures were, if anything, a little low, not an artifact of the small sample.

## 4. R2 - served ppl of legal, same scoring window (128)

```
ladder    ppl @12288   ppl @14336   ratio   excess
seed-2        2.38         2.20    1.0818   +8.2%
ref           2.39         2.20    1.0864   +8.6%
```

Both columns come from one `served ppl grid` block of the same run (rows=true domain, cols=forced
width), so the two columns share the crop set, the window and the order; only the width differs.

## 5. R3 - dedup audit of the 1000 legal crops

```
ladder    dup-offsets  pairs sharing > 256B  classes (single-linkage, gap <= 255)   n
seed-2            0  127  876   1000
ref               0  127  876   1000
```

No two crops share an offset, 127 pairs share more than half a block (which, for a 512-byte window,
is the same test as an offset gap of at most 255 bytes), and the merged classes give the effective
n of 876. The two ladders show the same three figures because they draw from one shared generator:
the 1000-offset list is identical across both ladders (one md5 `14d43b4b...` for both).

## 6. R4 - document-leakage view of the offsets

100 kB bins over the 2 MB read window: 20 of 21 bins occupied, mean 50.00 crops per bin, the
fullest bin (600-700 kB) holds 67 crops, the next 1400-1500 kB holds 62. Nothing is concentrated:
no bin stands out by more than a third above the mean, so no repeat-region of document-scale
proportions is to be found in the offset distribution. The caveat of the replay applies - the two
ladders share one offset list, so a spike that shows up on both ladders could not be evidence of
document leakage; it is predetermined by the sampler.

## 7. Reading of the frozen rule

The rule reads: CONFIRM if the leak rate lies in [2%, 8%] on both ladders AND the 14336/12288 cost
lies in [5%, 12%]. Both conditions hold: 5.20% and 6.30%, and 8.2% and 8.6%. The verdict of this
probe is therefore **CONFIRM**: the 8% leak price may be cited in the PoC budget.

What the gate does not cover, and what is stated here instead of being hidden:

- The rule reads the point estimate. The upper Wilson bound of the reference ladder at effective n
  (9.10%) lies above the 8% band; a reading that takes the bound instead of the point would give
  UPDATE for the reference ladder alone. The point estimate and the nominal bound of the same ladder
  (7.98%) both lie inside the band.
- Both CIs are Wilson intervals; neither is a significance test. No p-value was computed: n=52 and
  n=63 events are reported, no test statistic was calculated.
- The effective-n correction is a class count from a byte-overlap merge, not an estimate from a
  correlation model.
- One scoring window (128) and one corpus slice (2 MB tail of the 30 MB read) per cell, as in the
  archived baseline; the 200-crop figures are never overwritten, both sizes are reported.

## 8. Correction note

The first replay-validation script read the archived two-column list (crop index, offset) by
splitting on whitespace and compared all 400 tokens as one set; the comparison printed NO and would
have discarded a correct replay as unreliable. Reading the offset column only - the values above
1000 - shows the sets equal. The mistake was in the comparison, not in the replay; section 2 gate 4
records the corrected reading.

## 9. Artefacts

```
repro_seed2_200.txt          168504a92d0c5b44243dfb93d64d5b3b   12139 B   (equals archived baseline)
repro_ref_200.txt            51dd88cc0d9358ca061e9326e51e2465   12146 B   (equals archived baseline)
leakcontent_N1000_seed2.txt  68f66950f91d484e5127e53b5c718353   56181 B
leakcontent_N1000_ref.txt    a61f625c0eea74683dd345fe4e171c5c   56193 B
p0.log (driver transcript)   7e77ba36dc0b4e99551d03a7cfe147ec     999 B
off_seed2_200.txt (replay)   afe352308e72e0a2afcca47d21210bf7
off_seed2_1000.txt           14d43b4bc1c8961d85e3c85d3af02004
off_ref_1000.txt             14d43b4bc1c8961d85e3c85d3af02004   (same list, one generator)
driver p0_driver.sh          95012121f24cee3d86ef7c718eee1a07   (guest copy, md5 compared before launch)
```

Run on `bdh-4090`, guest run-site HEAD stays `e6bf359`, GPU claim `s_bdh-cl_000126_a818b3`
(claimed, renewed while running, released with 204), exclusive. Driver: `P0_DRIVER_DONE 2026-09-22
21:10:16 GATE=G0a_PASSED`, after which the card shows 287 MiB and 0% utilization and no process of
this run remains.
