# Scaling-readiness P3c pre-registration - acquisition pairs and capacity ablation on the P3 ladder

- Date: 2026-09-23. Seat: A0-Quinn. Operator GO: "P3c + K20 als Referenz-Leiter ... vorbereiten und starten".
- Scope: eval-only on EXISTING checkpoints. No training, no new weights, no card held beyond the
  measured runs. Reads out_c/scaling_readiness/p3/ and out_a/ (read-only), writes only
  out_c/scaling_readiness/p3c/.
- Why: pi-50 #455 named the two gaps this probe closes - P3 has no matched pre-growth/acquisition
  analysis and no capacity-ablation test ("unlike Sonde B"). Without it, K20 repeats the gap at 19
  transitions.

## 0. Objects (md5 pinned before the run; a mismatch aborts, no measurement taken)

- Instrument: guest scripts/eval_router.py at HEAD e6bf359, md5 73832ecd08f24eded93a98a74572be6e
  (the copy of record; the local build ed9fd326... carries unused dump flags and is NOT used).
- ck_0 (pre-growth control): out_a/bdh_textmix_ladA-A1-K5-seed2-base_last.pt, md5 8680bd26...
- ck_1..ck_7 (post-grow): out_c/scaling_readiness/p3/bdh_textmix_p3-{tag}_last.pt for
  tag in de es pl code math legal ga; md5s as pinned in the P3 report lines 30-37
  (de add1438f, es d74921a9, pl e9707f8f, code 89e90ecd, math 081f95ba, legal fd9f802d, ga 8814ddc6).
- Protocol per run (frozen, identical to the P3 instruments): --crops 200 --mb 30 --batch 4,
  window 128 tok, domain = the phase's own corpus only (prose for the base control, d_i for phase i).

## 1. The two measurements per phase i (tag d_i, width w_i = 8192 + 2048*i)

(a) ACQUISITION (matched pair, before vs after):
    - ppl(d_i, ck_0, routes=w_0=8192)   [pre-growth: the block d_i was trained for does not exist;
      routes above the base clamp to 8192]
    - ppl(d_i, ck_i, routes=w_i)          [post-grow: served at its own width]
    acquisition_gain_i := ppl(d_i, ck_0, 8192) - ppl(d_i, ck_i, w_i)   (positive = the grow helped)

(b) CAPACITY ABLATION (forced width, like the Sonde-B grown-capacity probe):
    - ppl(d_i, ck_i, routes=w_{i-1})      [narrow route: the grown columns (w_{i-1}+1 .. w_i) are
      not selected - the new block is not present in the served width]
    - ppl(d_i, ck_i, routes=w_i)          [= served at own width; same checkpoint, same crops]
    block_load_i := ppl(d_i, ck_i, w_{i-1}) / ppl(d_i, ck_i, w_i)      (ratio >= 1 = block load-bearing)

Same 200 crops per domain per comparison (the generator is seeded 1234 and drawn once per call
with --crops 200; the within-menu comparisons use identical crops because the crop draws are
taken at the same size and domain order as the P3/P3b runs - the P0 erratum E1 is respected:
comparisons are only made within a single run-set of crops, never across crop-count changes).

## 2. Frozen verdicts (set BEFORE measurement)

- F1 acquisition (per phase i): H-ACQ-POS holds for phase i if acquisition_gain_i >= 0.15 nats
  AND the domain was NOT previously trained at that width (true for all i: w_i > 8192 at ck_0).
  H-ACQ-NULL if |gain| < 0.15 nats. Per-phase reporting; no aggregate verdict is taken (seven
  phases, descriptive, no p-value).
- F2 block load-bearing (per phase i): H-LOAD holds for phase i if block_load_i >= 1.30.
  H-NULL-LOAD if block_load_i <= 1.02 (the grown block contributes nothing at the wider width).
  Between 1.02 and 1.30: reported as PARTIAL, no verdict.
- F3 ladder-level summary: fraction of phases with H-LOAD must be reported; if all 7 hold, the
  ladder supports the Sonde-B finding on a wider ladder; if 0 hold, P3 gains were not load-bearing
  and the K20 spend is flagged to the operator BEFORE any launch.
- F4 control sanity: ck_0 at 8192 for prose must reproduce 2.48 +/- 0.02 (the P3 retention gate).
  A miss aborts the interpretation (not the run) and is reported.
- Nothing is claimed about K20 from P3c; the extrapolation is modelled, not measured.

## 3. Cost (openly, measured P3 + arithmetic, never invented)

- P3 calibration (this repo, measured): grows at widths 10240..22528 took 1130,1375,1578,1497,
  2067,1963,2282 s; sum 11892 s. Linear fit wall ~ 0.094 s per width unit (residuals -10%..+10%).
- K20 (19 phases, widths 10240..47104, 10000 steps/phase, batch 1, fresh optimizer per phase,
  F-V9 step-end restore, expandable_segments, per the frozen P3 protocol):
    per ladder  sum_i 0.094*(8192+2048*i), i=1..19 = 0.094 * 544,768 = 51,208 s = 14.2 h;
    reference ladder doubles it: 2 x 14.2 h = 28.5 h on the 4090, exclusive claim, plus
    instruments (~21 route-reads per ladder at ~6.4 s per 200-crop run + ~30-60 s ckpt load) and
    P5 checks. Planned wall: 31-33 h across the two ladders; renewer for the whole window.
  - Domains: 19 corpora, all >= 30 MB (smallest 40.0 MB latex, 40.0 MB code, 40.3 MB legal,
    55.4 MB ga, 66.4..390.6 MB europarl) - the 200 crops at mb 30 are read without wrapping;
    tinyshakespeare (1.1 MB) is EXCLUDED as too small for the crops.
  - seed for the reference ladder differs by seed only; all other settings identical (INV-1).
- P3c itself: 7 phases x 3 route-reads = 21 eval_router runs, ~45 s each (ckpt load + 200 crops),
  ~20-45 min, eval-only, exclusive claim on gpu://rtx4090, released when idle.

## 4. Ship

- Reports ASCII, end with newline; j-space ship gate must report the outgoing register holds.
- Bus: intent before launch, done after, three-way SHA for the commit.
