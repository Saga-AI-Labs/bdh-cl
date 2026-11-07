# Routing measured, composition open: amendment to the chat-model prereg

**Date:** 2026-11-07
**Addressed to:** `docs/plans/2026-11-03_chat-model-prereg.md` (v0.1 DRAFT)
**Evidence:** `docs/reports/2026-11-07_masked-serving-results.md`,
`docs/reports/2026-11-06_expert-merge-results.md`
**Status:** decision point, not a change. Nothing in the chat prereg is altered here;
this note records what the measurements now support and what they leave open.

## 1. What the measurements established

**§4.3 of the chat prereg** chose *routed routes over pooled budgets* on the strength of
the expert-merge report's decision table. That was an argument, not a serving
measurement. It is now a measurement:

| masked mode | nll | equals parent's own |
|---|---|---|
| `mask_a` on zh | 1.7306 | `zh_last` 1.7306 |
| `mask_a` on expert | 2.4476 | `zh_last` 2.4476 |
| `mask_b` on expert | 1.2839 | `expert_b1` 1.2839 |
| `mask_b` on zh | 3.8409 | `expert_b1` 3.8409 |

**Four of four masked cells reproduce their parent to +0.0000.** The two joint
cells reproduce the merged model's own 2026-11-06 numbers exactly — a separate
receipt, protocol reproducibility rather than isolation. The merged parameter set
contains both experts intact; the pooled forward pass is what loses the weaker one.
On pure zh the pooled forward costs **1.47 nats** against the better half; on the
mixed probe **1.89 nats**.

**Consequence for §4.3:** the choice is confirmed by measurement. The prereg can
now cite the isolation figure instead of the caution, and the route-count decision
(smallest set covering the target use) is unchanged.

## 2. What the measurements leave open: composition

The mixed probe asked the question the isolated modes could not: on a task that
genuinely needs both domains, does the merged model compose?

| mixed mode | nll | ppl |
|---|---|---|
| joint | 4.2159 | 67.75 |
| mask_a | 2.3273 | 10.25 |
| mask_b | 2.8480 | 17.25 |

Two findings, and they pull in opposite directions:

- **Isolation beats pooling** (1.89 nats) — the routed-routes direction holds.
- **The halves handle language switching with a mild penalty.** Against a naive
  two-domain average, the best mask pays only +0.24 nats (mask_a: 2.3273 vs
  2.0891) and mask_b +0.29 (2.8480 vs 2.5624). "Neither half is competent" would
  overstate it: the halves track the switch; the catastrophe is exclusively the
  pooled forward.

So the library is real, and it is not a general model. What the mixed probe does
**not** measure is the composition a chat model needs: next-byte loss on
alternating 128-byte blocks of raw text is a different task from
instruction-following with cross-domain context (system prompt, retrieved
passages, a code answer citing prose). That task does not exist until a chat-SFT
does, and it is cheap to probe once it does — a masked model given a
cross-domain prompt plus few-shot context. **Composition via prompting is
unmeasured, not contradicted.**

## 3. The decision the prereg now has to take

**Is composition part of the first chat model's goal?**

| option | what it means | evidence |
|---|---|---|
| **A. Routable specialist library** | the first model routes per domain and composes only at the prompt level (system + retrieved context), not inside the weights | measured: exact isolation, no composition |
| **B. Generalist via pooled forward** | accept cross-talk, train the pooled model to tolerate it | not measured; the pooled forward is the worst option on both probes |
| **C. Composition via co-trained mixture** | add a learned, input-dependent mixture (MoE-style) with co-training on mixed data | untested; requires a new prereg and a new training regime |

**My read (not a recommendation):** Option A is what the measurements support
today, and it is a coherent product — a router over domain experts with prompt-level
composition. Option C is the path to a general model, and it is a research field,
not a step in the current plan. Option B is not merely unmeasured: it is the **null
hypothesis this program exists to beat** — pooled, trained-through models are the
founding observation of the ladder line (P5's bit-exact retention works because
growth is masked and preserved, not pooled).

**Router policy is a separate decision.** A adds *who routes, when, and what a
mistake costs*. The masked table now prices a misroute: a zh query sent to the
branch half costs +2.11 nats, an expert query to parent A +1.16. For the chat model
the analog is the prereg's own misroute history (9.5 % at legal, 1.18-nat worst
case, no cheap guard). The natural policy is **per-conversation static routing** —
language detected once, route fixed — which moves the router out of per-turn risk
entirely. Per-turn dynamic routing would need an accuracy requirement stated
explicitly. This belongs as its own sub-item, not under the route count.

**Option C's cheapest instrument is already scoped.** The 22-h B1b replay probe
(optional in the sibling-merge note) is exactly the measurement that informs
C-lite: does mixed *training* data teach the halves to cooperate? The
co-activation model makes a falsifiable prediction — ancestor-like mild dilution
instead of the +1-nat sibling cross-talk. Without that link, C reads as more
unreachable than its probe is.

What the prereg should state explicitly: **the first chat model is A unless the
goal is changed.** If the goal is B or C, the prereg changes scope, and the
measurement above is the reason.

## 4. What this does not touch

- **Route count (§4.3):** unchanged. The smallest set covering the target use remains
  the right call; the isolation measurement strengthens it.
- **Evaluation metric (§4.4):** unchanged in principle, but the metric must now
  separate *isolation* (does routing recover each domain) from *composition* (does
  the model use two domains in one answer). They are different questions and the
  mixed probe shows they can have opposite answers.
- **The expert-merge report:** unchanged. Its P1–P3 verdicts stand; this note only
  carries its decision-table consequence forward.

## 5. Reproduce the evidence

```bash
# isolation (six cells, +0.0000)
.venv/bin/python -u scripts/quinn/serving_eval.py \\
  --merged out_c/expert_merge/zh_b1_merged.pt \\
  --domains expert:data/expert/heldout.txt zh:data/europarl/xscript_zh.txt \\
  --mb 30 --crops 200 --block 512 --batch 2 \\
  --out out_c/expert_merge/serving_eval.json
```

The rerun output is `out_c/expert_merge/serving_eval.json`
(sha256 `693950e8a6f35b16…`), and the full run history including the first
crash is `out_c/expert_merge/serving_eval.log`.
