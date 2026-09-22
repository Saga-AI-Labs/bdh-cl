# Sonde B - grown-capacity ablation pre-registration

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: DRAFT until frozen pre-run
Frozen design of record, written BEFORE any measurement on the grown cells.

Companions:
- replicate: docs/plans/2026-09-21_sonde-B-reference-ladder-replication-prereg.md
- result it interrogates: docs/reports/phase_2/2026-09-22_sonde-B-reference-ladder-replication-report.md
- external review it answers: HAK bdh-cl #393 (operator), the open next-experiment question.

---

## 0. Why this run exists

#393 named the live gap: dissociate "the router addresses the right region" from
"that region is what carries the capability". The homeless contrast gestures at it but is
not randomised - it changes addressing AND capacity at once. This run changes capacity
alone and reads the serving curve.

## 1. The design correction this pre-reg records (read the source, do not assume)

The #393 sketch proposed two stages: (1) a forced-width grid re-eval, and (2) a checkpoint
ablation that zeros the newly grown columns of a served cell. Reading bdh.py:forward (the
readout, ~lines 205-283) settles that stage 2 as literally proposed is DEGENERATE:

    xy_sparse = x_sparse * y_sparse          # B, nh, T, N
    yMLP = reshape(xy_sparse) @ decoder       # (B,1,T,N*nh) @ (nh*N, D)

The readout is a PURE SUM over the N per-head neurons, with NO normalisation over N. A
zeroed neuron and an absent neuron contribute the identical term (zero) to that sum. So:

    zero-the-grown-columns  ==  force-the-pre-growth-prefix-width

which is already one column of the stage-1 grid. Stage 2 collapses into stage 1, and the
router cannot "go" anywhere under a zeroed grow because the pre-growth and grown widths
then score identically (argmin ties to the lower index). The randomised-grown-content arm
is dropped too: in a pure sum it injects noise rather than removing content, answering a
different and less useful question. The capacity-usefulness question is answered fully by
the forced-width grid - cheaper and sharper than the two-stage sketch.

Recorded before measurement, as pre-registration requires: the frozen design deliberately
differs from the #393 sketch, and the difference is stated here, not discovered post hoc.

## 2. The claim under test

Grown capacity is domain-specific and load-bearing: a served cell's serving perplexity at
its trained (grown) width is far better than at its pre-growth width, so the grown neurons
carry the capability the cell was grown for.
Contrast (H0): capability is a property of the whole stack that merely happens to be
addressed at the grown width; then serving at the pre-growth width is near-equal.

## 3. Run-site and instruments (read-only pre-flight, 2026-09-22, SSH_RC=0)

- host alias bdh-4090 (192.168.178.200), user a0-quinn, key /root/.ssh/quinn_4090
- run-site /media/data/coding/bdh, HEAD e6bf359
- grown checkpoints present: checked by ls -la over SSH on the guest at 2026-09-22T03:30Z (SSH_RC=0), sizes below; no forward pass or md5 re-run at this pre-flight.
  - out_c/sondeB/harvest_ref/bdh_textmix_harv-prose__math_last.pt  (1813044888 B)
  - out_c/sondeB/harvest_ref/bdh_textmix_harv-prose__code_last.pt  (1511046808 B)
  - out_c/sondeB/harvest_ref/bdh_textmix_harv-math__ga_last.pt     (2417040985 B)
  - out_c/sondeB/harvest_ref/bdh_textmix_harv-prose__legal_last.pt (2115042989 B)
- disk free /media/data: 6.4 T (54% used)
- instrument: scripts/eval_router.py, additive --route-grid flag. It prints the per-width
  served-ppl grid from the tensor the harness already fills: zero extra forwards, no change
  to the computation.

## 4. Frozen design

- Cells: prose__math, prose__code, math__ga, prose__legal (legal folded in as target 2).
- Routes (per-head widths): 8192,10240,12288,14336,16384
- window 128, crops 200, batch 4 (identical to the harvest evals - identity is the point).
- Corpora: prose=data/textmix/wikitext-103-raw/wiki.train.raw, code=data/textmix2/code.txt,
  math=data/textmix2/latex.txt, legal=data/textmix2/legal.txt,
  ga=data/europarl/DGT.en-ga.ga.txt
- No training. No new checkpoints. A re-eval of the four existing grown cells only.
- Per cell, read from --route-grid: the true domain's served ppl at EVERY forced width,
  and the routed confusion.
- Grown vs pre-growth widths (from the harvest driver, grow_mult):
  - prose__math:  128 -> 192 (8192  -> 12288)
  - prose__code:  128 -> 160 (8192  -> 10240)
  - math__ga:     192 -> 256 (12288 -> 16384)
  - prose__legal: 128 -> 224 (8192  -> 14336)

## 5. Declared outcomes (falsifiable)

Let P(w) = the true domain's served ppl at forced width w; W_grown = trained width;
W_pre = pre-growth width.

- H1 (load-bearing): P(W_pre) is clearly worse than P(W_grown).
- H0 (not in the grown content): P(W_pre) ~ P(W_grown).
- Frozen falsification band: a cell counts as load-bearing iff P(W_pre) >= 2 x P(W_grown)
  AND the gap exceeds the crops-200 served-plane spread (~ +/-0.05 ppl, per the replication).
  Otherwise the cell is reported NOT load-bearing, plainly.
- Secondary read: is the ppl minimum over forced widths at W_grown? If the min sits at a
  width other than the trained one, growth aimed at a width that is not the optimum - worth
  reporting as-is.

## 6. What this does and does not settle

- Settles: whether the grown capacity is load-bearing, via the forced-width serving curve
  (the capacity half of #393's dissociation).
- Does not settle: the routing-selection half. The prose__legal leak (11/200 downward on the
  reference ladder) is a routing phenomenon and is orthogonal; this run cannot explain it.
  legal is target 2 only to test whether its grown columns are as load-bearing as the clean
  cells'. A null there supports "routing quirk, not capacity defect"; a positive there leaves
  the leak untouched either way.
- Does not re-open P1 (falsified at 189, band {191..199}) - untouched.

## 7. Cost and output

- Four cells x one re-eval at 5 forced widths, crops 200, window 128, batch 4. The harvest
  evals ran ~3-6 min/cell; expect ~15-30 min total on the 4090. One GPU claim (exclusive),
  released on completion.
- Raw: out_c/sondeB/harvest_ref/grid_<cell>.routdiag.txt
- Report: docs/reports/phase_2/2026-09-22_sonde-B-grown-capacity-ablation-report.md
- Bus: intent (working_on) before, done after; three-way SHA on the report commit.
