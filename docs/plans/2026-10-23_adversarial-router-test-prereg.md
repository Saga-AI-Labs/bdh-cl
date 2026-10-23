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
