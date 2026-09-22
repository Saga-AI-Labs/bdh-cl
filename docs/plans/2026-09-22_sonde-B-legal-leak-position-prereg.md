# Sonde B - legal-leak position-decomposition pre-registration

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: DRAFT until frozen pre-run
Frozen design of record, written BEFORE any position-level measurement.

Companions:
- content probe (negative): docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-content-report.md
- window probe (attenuation): docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-window-report.md
- thread narrative: docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-thread-report.md
- operator GO: "residual half of the flips - ok".

---

## 0. What is left, and what this probe asks

Three eliminations now stand against the residual legal flip: it is not a capacity defect (ablation),
not explained by short scoring windows alone (window probe), and not a content or position signal at
the crop level (content probe, features and offsets both negative).

What has never been looked at is the **internal structure of the routing score itself**. The router
scores a prefix by the mean loss over the first `window` positions and takes the argmin. The total
score difference between the two candidate widths,

    M = sum over t of m(t),   where m(t) = loss_12288(t) - loss_14336(t),

is therefore a sum of per-position contributions. A flip downward means M < 0, i.e. the smaller prefix
scored better. **How that sum is built** is the question:

- **H-few:** a few positions carry the margin, and the flip is a few-token event.
- **H-cancel:** the per-position contributions are individually much larger than their sum - M is the
  small residual of near-cancellation between positions that disagree. On that reading the flip is a
  fragile arithmetic outcome, and its one-sidedness is a property of how losses scale with prefix
  width near the boundary, not of any particular position or crop.

These imply different follow-ups (read the decisive positions' bytes vs. study the cancellation itself),
so the probe is worth running before either.

## 1. Instrument (additive; pinned)

- `scripts/eval_router.py` @ `72399e12` plus one new additive flag, `--pos-dump domain:wA,wB`:
  for the named true domain it prints, per crop, the aggregate decomposition statistics below, and for
  every **leaker** (chosen wider-prefix != wB) plus a fixed reference sample of 20 stayers (the first 20
  stayers by crop index) it prints the full per-position margin array `m(1..window)` in compact form.
- The per-position losses are already inside the `rl` tensor the harness fills for every route and
  every crop (`rl[ri, ci, :]`); this flag only prints from that tensor. **Zero extra forwards.**
- Reproducibility gate: the same run must reproduce the window-384 confusion of the window probe
  (seed-2: 7 leakers at 12288 / 193 at 14336; reference: 5 at 12288 / 195 at 14336). If it does not,
  the probe is void and the discrepancy is the finding.

## 2. Frozen design

- Ladders: seed-2 `out_c/sondeB/harvest/bdh_textmix_harv-prose__legal_last.pt` (md5
  `d94686ad9f90d4750ba8d02b88ffd9ea`) and reference `out_c/sondeB/harvest_ref/...-prose__legal_last.pt`
  (md5 `8d89b2cabe0c0dccd595fc76bd74c822`).
- Scoring window **384** on both ladders - the window at which the surviving leaker sets were
  identified, so the crops analysed are exactly the crops the previous leg analysed.
- Routes 8192,10240,12288,14336,16384; crops 200; batch 4; `--route-grid` and `--pos-dump legal:12288,14336`;
  domains spec and order identical to every previous leg of this thread.
- Corpus `data/textmix2/legal.txt` md5 `0135960429085039dbe5385f649e75fe` (byte-stable).
- No training. Two re-evals (one per ladder). The crop draw is unchanged (`manual_seed(1234)`, crops
  drawn before `window` is used), so the 200 crops are the same byte ranges as in every previous leg.

## 3. Statistics per crop (declared in advance)

With `m(t) = loss_12288(t) - loss_14336(t)` over `t = 1..384`:

- `M = sum_t m(t)` - the signed total (its sign is the route decision).
- `A = sum_t |m(t)|` - the total absolute contribution.
- `R = |M| / A` - the **consistency ratio**, in [0,1]. Near 1 means the positions agree in direction;
  near 0 means they nearly cancel and `M` is a small residual.
- `k50` - the number of the largest `|m(t)|` needed to reach 50 percent of `A`. `k50 = 192` is the
  uniform case; small `k50` means a few positions dominate.
- `conc5` - share of `A` held by the five largest `|m(t)|`.
- `top1_pos` - the position of the largest `|m(t)|`.
- `neg_share` - fraction of positions with `m(t) < 0`.

## 4. Declared outcomes (falsifiable, frozen before the run)

Computed separately per ladder for **leakers** and for **stayers**, and reported for both in every case.
`n = 7` and `n = 5` leakers: descriptive only, no test statistic, no p-value.

- **H-few accepted** if, on BOTH ladders, the leakers' median `k50 <= 20` **and** their median
  `R >= 0.5` - a small number of positions carries a one-directional margin.
- **H-cancel accepted** if, on BOTH ladders, the leakers' median `R <= 0.15` - the margin is the
  residual of near-cancelling contributions. Under this reading `A` should be substantially larger
  than `|M|`; report `A`, `M` and the ratio for every leaker.
- Anything else is reported as **mixed**, with both ladders' numbers, and no promotion.
- **Secondary, reported and not promoted:** leakers vs stayers on `R`, `k50`, `conc5` and `neg_share`;
  and whether `top1_pos` clusters anywhere (it would be visible as a mode in the printed positions,
  not by a test).

## 5. What this probe can and cannot do

- It decomposes **where the margin sits**, not **why the flip is one-sided**. A clean H-cancel result
  would make the one-sidedness a question about how losses scale with prefix width near the boundary,
  which this probe does not answer.
- It cannot promote anything on n = 7 and n = 5; it can only discriminate between two structural
  readings strongly enough to pick the next instrument.
- It does not re-open the content probe: whole-crop byte statistics and positions were negative there,
  and this probe looks at per-position losses, not at bytes. If a few positions turn out decisive,
  reading their bytes becomes a *new* follow-up, declared here as a possible consequence rather than
  as part of this probe.
- It does not touch P1 (falsified at 189, band {191..199}), the ablation, or the window result's
  attenuation claim.

## 6. Expected cost and outputs

- Two re-evals at window 384 (one per ladder), crops 200, batch 4: the window probe ran ~2.6 min per
  cell, so expect under 10 minutes total on the 4090. One exclusive GPU claim, released on completion.
- Raw: `out_c/sondeB/harvest/posdump_w384_seed2.txt`, `out_c/sondeB/harvest_ref/posdump_w384_ref.txt`
- Report: `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-position-report.md`
- Bus: intent before, done after, three-way SHA on both commits.
