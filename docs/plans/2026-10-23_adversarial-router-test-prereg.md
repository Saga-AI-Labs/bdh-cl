# Adversarial Router Test — Preregistration v0.1

**Status:** PRE-REGISTERED v0.1 · 2026-10-23 · Quinn
**Trigger:** after the K25/W1024 bridge completes (currently phase 15/24)
**Position:** post-hoc *characterization*, **not** a gate — it does not modify the bridge
protocol, and its result cannot invalidate the pre-registered bridge gates.

---

## Why this test exists

The K20 ladder's routing headline (99.18%, two seeds) is an **average over 200 crops per
domain**, drawn from a fixed corpus set. György, Lattimore, Lazić & Szepesvári
(*Beyond Statistical Learning*, arXiv:2506.23908) argue that performance on a fixed
benchmark does not certify anything about a new distribution — their exact-learning
criterion is a worst case over inputs, not an average.

Our legal domain is the concrete case: 169/200 crops route correctly, 31 route to prose.
We interpreted this as byte-geometry. Under the paper's framework it is equally
consistent with a **statistical shortcut** — low loss on the bulk, high loss on a
specific subset. Nothing we have run distinguishes the two.

**This test is the cheapest available way to find out which it is.**

---

## The exact-learning tension, stated once

BDH's own framing (Kosowski et al., arXiv:2509.26507v1) promises
"PAC-like bounds for generalization of reasoning over time". PAC is the statistical
paradigm the paper rejects. Both goals can be legitimate; they must not be conflated.

| Claim | Paper classification |
|---|---|
| P5 bit-exact preservation | **exact** — worst case over the frozen block |
| PAC-like generalization bounds | **statistical** — average over a distribution |
| K3 routing ≥95% | **statistical** — average over crops |

This test moves the *serving* side from the right column toward the left.

---

## Design

### Instrument

`scripts/eval_router.py` already computes per-crop NLL under every route and takes the
argmin. The test adds one quantity: the **margin** between the two best routes.

```
margin(crop) = NLL_second_best(crop) − NLL_best(crop)   [nats]
```

A crop with margin ≈ 0 sits exactly on the routing decision boundary. These are the
inputs an exact-learning criterion must handle and an average metric hides.

### Adversarial set construction (two stages)

**Stage 1 — boundary crops.**
Scan a pool of crops, keep the **bottom 5% by margin**.

- Pool: ~10,000 crops drawn from the bridge's own corpora (all 25 territories, window 128)
- Selected: ~500 crops with the smallest margin
- Cost: ~250,000 route scans — hours, not days, on the GB10

**Stage 2 — cross-domain pairs.**
For every territory *t*, take crops from each *other* territory's corpus and record
whether the router assigns them to *t* or to their true origin.

- Focus: all 25×24 ordered pairs, but prioritize the domains with the worst Stage-1 margin
- This is the systematic version of the legal→prose observation

### Metrics

| Metric | Definition | Why |
|---|---|---|
| Worst-domain accuracy | min over 25 domains of per-domain accuracy | replaces the 99.18% average |
| Margin distribution | P5 / P25 / median of margins over the adversarial set | how close to the boundary the failures sit |
| Boundary failure rate | fraction with margin < 0.1 nats **and** wrong argmin | counts decisions the model cannot justify |
| Cross-domain confusion | per-pair error matrix (25×24) | isolates legal/code-type leakage |

All four are computed on the **same** checkpoints as the bridge's final matrix, so the
comparison is apples-to-apples.

---

## Pre-registered decision rules

| Outcome | Verdict |
|---|---|
| Adversarial accuracy within 2 points of the average | Router is boundary-robust; the byte-geometry reading is supported |
| Adversarial accuracy drops >5 points | **Statistical shortcut confirmed** — the K20 headline is a benchmark statistic |
| Cross-domain errors concentrate on legal and code | Those domains are the router's weak surface; the Hero Run must address them |
| Boundary failures (>0.1 nats) occur at all | Exact routing is not achievable at this width; report as a bound, not a failure |

These thresholds are fixed **before** the test runs. They are not retro-fitted.

---

## Protocol invariants

- **No bridge modification.** The running chain (phase 15/24) is untouched. This test
  consumes its outputs; it does not alter its inputs.
- **Same router code.** `eval_router` as committed; no tuning, no retraining.
- **Same corpora and windows.** Window 128, the bridge's corpora, no new data.
- **Documented determinism.** Crop selection seeds and the scan configuration are
  written to the report before results are read.
- **Cost bound.** Target ≤1 day on the GB10 after the bridge. If Stage 1 alone exceeds
  that, Stage 2 is deferred — the boundary result is the load-bearing one.

---

## What the test cannot show

Stated plainly, because this is a position paper's criterion applied to a 25-territory
system:

1. **`sup` over all byte strings is intractable.** The paper's linear-classifier example
   is computable because `X` is small. Ours is every 128-byte window of every corpus.
   This test probes the boundary; it does not prove universal correctness.
2. **It says nothing about new territories.** A held-out *territory* (generalization
   split) is a separate test and is not part of this prereg.
3. **It does not touch continual learning.** The paper has no model for sequential
   preservation across phases; BDH-CL's core problem is outside its scope.
4. **It cannot upgrade P5.** Preservation is already exact; this test addresses serving.

---

## Deliverable

`docs/reports/2026-10-23_adversarial-router-test-results.md` — the four metrics, the
decision-rule verdict, and the raw margin distribution. Published alongside the bridge
report, not instead of it.

---

## Non-goals

- No retraining of the router
- No new corpora
- No change to any pre-registered bridge gate
- No claim of AGI or of deductive reasoning — BDH-CL claims storage and routing, not reasoning

---

— Quinn, @quinn-the-builder, 2026-10-23


---

# Amendment v0.2 -- 2026-11-02

**Status:** additive. Nothing in v0.1 above is altered or withdrawn. This section
records two measurements that were not available when v0.1 was written, and the
consequences for the test that has not yet run.

## A1 -- The 0.1 nat boundary threshold is too narrow

v0.1 defines a boundary failure as `margin < 0.1 nats` **and** wrong argmin. Measured
on `zh_last.pt` (K25/W1024 chain, see
`docs/reports/2026-10-31_k25w1024-routing-matrix-results.md`), the misroutes that
motivated this test sit at:

| domain | n | misroutes | margins of those misroutes |
|---|---|---|---|
| legal | 200 | 19 | 0.015 to 0.503, median 0.124 |
| code | 200 | 4 | 0.157 to 0.506 |

Under the v0.1 rule, **10 of 19 legal misroutes and all 4 code misroutes are not
boundary failures**, although every one of them is a wrong argmin close to the
decision boundary of its competing route.

**Decision:** the 0.1 nat threshold is retained as-is for scoring v0.1 comparability,
and a second label is reported alongside it: **near-boundary misroute** = wrong argmin
with `margin < 0.5 nats`. Both counts are always reported. Neither replaces the other.

## A2 -- Coherence R, not raw margin, is the reliability signal

A `--pos-dump` run over 200 code crops against two peers gives 400 (crop, peer) pairs.
For each pair the early window verdict (positions 0-127) was compared with the late
ordering (positions 128+):

| | count |
|---|---|
| early agrees with late | 397 |
| early contradicts late | 3 |

| metric | contradictions | agreeing (median) | separates? |
|---|---|---|---|
| R = abs(M)/A | 0.143 / 0.153 / 0.325 | 0.825 | **yes** |
| conc5 | 0.168 / 0.170 / 0.209 | 0.161 | no |
| k50 | 20 / 20 / 27 | 23 | no |

**Consequence for the test design:** a confidence gate keyed on the raw margin is
superseded. A margin gate at 0.2 would have missed two of the three known
contradictions. The gate candidate is now `R < 0.35`, which flags 3 % of pairs and
covers all three known cases (precision 25 %, recall 100 %, n=3).

**Open:** n=3 is not a rate. The threshold is a candidate, not a calibration. The next
`--pos-dump` run must target a domain with many misroutes -- legal has 9 per 100 crops,
which is enough to measure precision and recall properly.

## A3 -- Instrument changes required before the test runs

1. Every Stage-1 and Stage-2 measurement reports **R per crop**, not only the margin.
2. The crop sample is fixed explicitly (per-domain seed or a crop file). The current
evaluator consumes one shared generator across domains, so the per-domain sample
depends on how many domains are passed in a single call -- a defect recorded in the
routing report and fixed for the n=100 sweep by running one domain per call.
3. A domain whose early-window coherence is low is **reported**, not silently routed.

## A4 -- What this amendment does not do

- It does not lower the bar for the test: the decision rules in v0.1 remain the rules.
- It does not retro-fit results into v0.1's thresholds; A1 keeps both labels visible.
- It does not claim a calibrated gate. `R < 0.35` is a candidate with n=3 support.


## A5 -- Withdrawal of the A2 gate candidate (2026-11-02, same day)

A2 above proposed `R < 0.35` as a gate candidate on the strength of n=3 contradictions
in one domain. The calibration run on legal (200 crops, 19 misroutes against the base
route) refutes it. A2 is left unedited so the sequence stays visible; this section is
the operative statement.

### The measurement

200 (crop, route) pairs, 20 early-vs-late contradictions, 19 actual misroutes, 17 of 20
overlapping. Per-metric separation:

| metric | contradiction median | agreeing median | worst agreeing value | disagreements inside the agreeing range |
|---|---|---|---|---|
| R = abs(M)/A | 0.175 | 0.570 | **0.027** | 18/20 |
| conc5 | 0.274 | 0.309 | 0.183 | 19/20 |
| k50 | **14** | **11** | 6 | **20/20** |
| neg_share | 0.344 | 0.504 | 0.297 | 16/20 |

R has the largest median gap (3.3x) and the worst overlap behaviour: the single lowest
R in the dataset (0.027) belongs to an agreeing crop. k50 is **inverted** --
contradictions score higher than agreeing crops.

### Gate cost at equal coverage

| metric | flagged | share | contradictions caught | precision | recall |
|---|---|---|---|---|---|
| R <= 0.362 | 61 | 30.5 % | 18/20 | 29.5 % | 90 % |
| conc5 <= 0.285 | 61 | 30.5 % | 12/20 | 19.7 % | 60 % |
| k50 <= 10 | 77 | 38.5 % | 1/20 | 1.3 % | 5 % |

### What replaces A2

- **Withdrawn:** `R < 0.35` as a routing gate. Guarding 18 of 20 contradictions costs
  30.5 % of all traffic on legal; the code figure of 3 % was a three-point artefact.
- **Retained:** R as a **diagnostic**. Median 0.175 vs 0.570 is a real correlation across
  two domains and belongs in every report. It is a readout, not a switch.
- **Retained:** the A1 near-boundary label. It is orthogonal to the gate question.
- **Open:** no metric among these four permits a cheap binary decision. If a gate is
  wanted later it must be justified by a cost model that accepts 30 % fallback, or by a
  metric not yet tested. "Cheap confidence gating" is not available and must not be
  described as such.

### Methodological note

A threshold proposed from three cases and then tested on twenty was not tested at all.
Future amendments must state the sample size that supports any recommended threshold, and
no threshold enters a plan on fewer than two independent domains.
