# RBC-1 H1 contradicted by five-domain off-domain scores

**Date:** 2026-11-03
**Addressed to:** the author of `docs/plans/2026-11-02_router-bias-correction-escalation-prereg.md` (RBC-1 v0.1 draft, commit `ca4dab1`)
**Evidence:** `docs/reports/2026-10-31_k25w1024-routing-matrix-results.md`
**Status:** note, not an amendment. RBC-1 remains unedited; this records data that bear on it.

## What RBC-1 proposes

RBC-1 names two candidate causes for the one-sided routing flips:

- **H1 (per-route bias):** grown neurons are trained only on their own territory, so on
  non-domain text they contribute noise. The early-window score for route r contains an
  additive bias `tau_r > 0` for every route beyond the base. Raw-score comparison then
  pushes borderline crops toward the base route, always in the same direction.
- **H2 (window):** 128 tokens under-determine the base-vs-own comparison for a minority
  of crops; part of the flips is tie-break noise that longer windows remove.

## H1 as stated is contradicted

H1 predicts that wider routes score **worse** on foreign territory (positive bias).
Per-route early-window scores were collected for 200 crops on each of five domains, all
25 routes each, `--score-vector`, same checkpoint (`zh_last.pt`).

Pearson correlation between route width and mean off-domain score:

| domain | rho |
|---|---|
| legal | -0.007 |
| code | -0.648 |
| math | -0.530 |
| zh | -0.539 |
| ga | -0.176 |

All five are negative. Wider routes score **better** on foreign territory, not worse.
The best off-domain competitor is in every case one of the wider routes (53248, 49152,
57344), never a narrow one.

Rank of the base route 8192 among the 24 off-domain routes:

| domain | rank of 8192 | gap to the best off-domain route |
|---|---|---|
| legal | **#1** | 0.0000 |
| code | #6 | +1.8527 |
| math | #5 | +1.8931 |
| zh | #5 | +0.9317 |
| ga | #3 | +1.1996 |

The base route wins on legal only. A bias term that pushes crops toward the base route
cannot explain why the base route is mid-field on four of five domains.

## What the data support instead

A capacity monotonicity. A route of width `w` contains all neurons from phases 1..k, so
more width means more frozen territories and therefore a better generalist on foreign
text. legal is the exception because legal text is natural language, close to the prose
the base route was trained on: 8192 wins there because it is genuinely competent, not
because a noise term pushes it.

This is mechanically different from H1 and has a different remedy: capacity cannot be
bias-corrected away, whereas an additive score bias could be.

## What this note does not do

- **H2 is untouched.** This analysis says nothing about the scoring window. The
  `--window 384` run proposed in RBC-1 section 4 remains the right test for H2 and should
  proceed.
- **It does not separate width from growth order.** Width rises monotonically with
  training order, so the observed neighbour pattern (code to 53248, math to 53248, ga to
  57344) may be an ordering effect rather than a pure width effect. Five domains cannot
  decide this; the remaining twenty could.
- **It does not establish the negative correlation is causal.** It shows H1's predicted
  sign is wrong in every domain measured.

## Suggested consequence for RBC-1

Before building bias correction, check whether the score bias estimated on the five
domains already has the sign H1 forbids. If the correction subtracts a term that the
five-domain data say is negative, it will move the scores the wrong way.

H2's window test is unaffected and is the cheaper of the two investigations.
