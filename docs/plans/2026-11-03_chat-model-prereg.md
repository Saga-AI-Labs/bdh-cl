# Usable BDH-CL Chat Model - Preregistration v0.2 (DRAFT)

**Status:** DRAFT v0.2 · v0.1 drafted 2026-11-03 · v0.2 2026-11-07 after the masked-serving measurements · **§4.4b FROZEN 2026-11-09** (judge set certified, hashes registered)

**Changelog v0.1 -> v0.2:** (1) §3 gains the scope decision - the first chat model is a
routable specialist library, not a generalist, with composition at prompt level;
(2) §4.3's choice of routed routes is now backed by a measurement (4/4 masked cells
reproduce their parent at +0.0000) and gains a router-policy sub-item;
(3) §4.4 splits the metric into isolation and composition, and records that composition
via prompting is unmeasured rather than contradicted;
(4) §6 gains the decision record and the open composition question.


**Status:** draft. No run has been authorised. Section 4.2 now carries the measured
H2 control result; sections 4.3 and 4.4 remain open decisions.

**Purpose.** The ladders and the K25/W1024 bridge are preparatory work: they exist to
establish how BDH behaves under continual learning, so that a *usable* model can be
trained. This prereg turns those findings into a training plan. It is not a continuation
of the routing investigation - it is the step that investigation was for.

## 1. What the bridge established, and what it did not

Settled and load-bearing for this plan:

| finding | evidence |
|---|---|
| A 24-phase grow ladder trains without forgetting (P5 bit-exact, K4 retention) | K25/W1024 chain, `docs/reports/2026-09-29_k20-gx10-results.md` |
| Routing over a grown stack works in the mean (99.44 % at n=100) | `docs/reports/2026-10-31_k25w1024-routing-matrix-results.md` |
| Accuracy falls monotonically with the routing margin (59.1 % in the lowest legal band) | same report, stage (a) |
| No cheap feature predicts a misroute (six tested, 800 pairs) | same report, stage (b) |
| A longer scoring window removes most misroutes at zero cost | same report, H2 |
| Wider routes generalise better off-domain (all five correlations negative) | same report, five-domain section |

Not settled, and this plan must not assume otherwise:

- **The window result is measured on two domains only.** The control runs on math and zh
  decide whether it is a mechanism or a fit to legal/code.
- **Window size does not transfer.** `window < block_size`, and block size is a training
  decision. A different block yields a different optimum; only the principle transfers.
- **Nothing here was measured on chat data.** Every corpus used so far is parliamentary
  text, legal prose or source code.

## 2. What carries over into the design

Three consequences follow directly, and each contradicts an assumption the bridge made:

**Fewer, better-separated routes.** The legal misroutes arise because legal text and
prose are both natural language, so route 53248 and the base route 8192 are both
competent on the same input. At three languages that overlap largely disappears: en, de
and zh are lexically and orthographically distinct. The 25-route taxonomy is a property
of the bridge experiment, not of the target model.

**The window is a design parameter, not a tuning knob.** Given a block size *b*, the
scoring window should be as large as possible while leaving a late span for measurement.
The exact fraction is what the control runs inform.

**A misroute has no cheap safety net.** Six features over 800 pairs found nothing that
permits a binary guard below 20 % fallback. A production model therefore needs routing
that is *right by construction* (few, well-separated routes) rather than guarded after
the fact.

## 3. Target model

First stage: **chat, without tool calling.**

| parameter | value | rationale |
|---|---|---|
| languages | **en, de, zh** | three maximally distinct scripts/language families |
| training data | high-quality corpora, not Europarl | to be selected from the running preliminary studies |
| hardware | 2x DGX Spark, TP=2, ~256 GB unified minus OS/overhead | available locally, no purchase lead time |
| routing | few routes (see section 4.3) | fewer boundaries, larger margins |

**Scope decision (operator sign-off 2026-11-07).** The first chat model is a
**routable specialist library**: one merged parameter set plus per-route masks, with
composition happening at prompt level (system prompt, retrieved context) rather than
inside the weights. It is not a generalist that pools domains in one forward pass.

This follows the masked-serving measurements: four of four masked cells reproduce
their parent **to +0.0000**, while the pooled forward costs 1.47 nats on pure zh and
1.89 nats on a mixed probe. The pooled forward is the worst of the three serving modes
measured. A generalist via pooled forward is the null hypothesis this program exists
to beat, not a target.

Option C (composition via co-trained mixture) remains a possible later scope change.
Its cheapest instrument is the 22-h B1b replay probe, which tests whether mixed
*training* data teaches the halves to cooperate; it stays on the optional list.

## 4. Decisions this prereg must not leave implicit

### 4.1 Block size

Block size couples three things: training length, activation memory, and the routing
window. Measured activation estimates from the K25 checkpoint (n_embd 1024, 6 layers,
mult 896):

| block | eval activations | training total incl. weights, grads, Adam, frozen backup |
|---|---|---|
| 512 | ~21 GiB | ~73 GiB |
| 768 | ~32 GiB | ~84 GiB |
| 1024 | ~42 GiB | ~94 GiB |
| 2048 | ~85 GiB | ~137 GiB (exceeds a single node) |

With TP=2 the pool roughly doubles, which makes block 1024 plausible and 2048 worth
checking. **The estimate is a working figure, not a measurement** - it needs a live
memory run at block 768 before any plan depends on it.

### 4.2 Window

**Measured, 2026-11-04.** Four domains at window 128 against 384 on identical crop
indices, 800 paired crops. A third point at 256 exists for legal and code.

| domain | @128 wrong | @256 wrong | @384 wrong |
|---|---|---|---|
| legal | 19 | 9 | 5 |
| code | 4 | 3 | 2 |
| math | 0 | - | 0 |
| zh | 0 | - | 0 |

17 misroutes fixed, 1 broken over the 800 pairs at 384 -- ratio 17:1, at zero additional
compute, because the forward covers the whole block and the window only selects the
averaged slice.

**CORRECTION (2026-11-04):** an earlier version of this section reported 17 fixed and 2
broken, with zh losing a case. That was wrong. The zh crop in question (91) is English
UNCCD text inside `xscript_zh.txt` -- 0.0 % CJK, 100.0 % Latin -- confirmed by two
independent corpus audits (`scripts/corpus_purity_census.py` and
`scripts/quinn/corpus_purity_audit.py`; all other 24 corpora clean). Read against its
content, that crop routes wrongly at 128 and correctly at 384: the longer window
**corrected a label-driven decision** rather than breaking a correct one. The single
remaining break is legal crop 39.

**Rule for the target model:** start from `block - 128`, then audit the training corpora
for label/content agreement before fixing it. The window cannot repair a mislabelled
crop; it can only expose one.

**What does not transfer:** the number 384 itself. Window is asserted below block size,
and block size is a training decision. A model trained at a different block has a
different optimum; only the procedure carries over.

**Not yet decided:** whether a block larger than 512 is worth it. Four legal crops are
wrong at all three windows, so more context will not rescue them; the slope has flattened
from -10 to -4 between 256 and 384.

### 4.3 Number of routes

Three candidate designs, to be decided before the training prereg is finalised:

| design | routes | risk |
|---|---|---|
| language-only | 3 (en, de, zh) | clean separation, but no prose/code split |
| language + prose base | 4 | base route may again compete on natural language |
| language + capability | 5-6 (add code, math) | more boundaries, but each still well separated |

The bridge evidence argues for the **smallest** set that covers the target use. The
legal-prose overlap is the concrete warning: two routes that are both plausible on the
same input are where boundary errors live.

**Measured (2026-11-07):** the routed-routes direction is now a measurement, not a
caution. On the sibling merge (`zh_b1_merged.pt`, mult 1792), segment masking
reproduces each parent to +0.0000:

| masked mode | nll | parent's own |
|---|---|---|
| `mask_a` on zh | 1.7306 | `zh_last` 1.7306 |
| `mask_a` on expert | 2.4476 | `zh_last` 2.4476 |
| `mask_b` on expert | 1.2839 | `expert_b1` 1.2839 |
| `mask_b` on zh | 3.8409 | `expert_b1` 3.8409 |

The pooled forward scores zh 3.1975 against 1.7306 isolated. The route count itself is
unchanged: the smallest set covering the target use.

#### 4.3a Router policy

The route count is not the whole routing decision. **Who routes, when, and what a
mistake costs** are separate questions, and the measurements now price a mistake:

| misroute | cost |
|---|---|
| zh query sent to the branch half | +2.11 nats |
| expert query sent to parent A | +1.16 nats |

The natural policy for a chat model is **per-conversation static routing**: language
detected once, route fixed for the conversation. This removes the router from
per-turn risk entirely. Per-turn dynamic routing is possible but would need an
accuracy requirement stated explicitly; the prereg's own misroute history (9.5 % at
legal, 1.18-nat worst case, no cheap guard) argues against adopting it without one.

### 4.4 Evaluation metric

Perplexity is insufficient for a chat model and was already a poor guide for routing:
legal's 9.5 % error rate cost only 0.03 nats aggregated, while a single misroute could
cost 1.18 nats. **The relevant unit is the worst case a user experiences, not the domain
mean.**

A response-quality metric must therefore be defined *before* training. Candidates:
held-out instruction-following with human or model-graded scoring, and a per-language
fluency check.

**The metric must separate two questions the measurements show can have opposite
answers:**

| question | instrument | status |
|---|---|---|
| **Isolation** - does routing recover each domain? | masked-recovery, the serving-eval protocol | **operational now** (4/4 at +0.0000) |
| **Composition** - does the model use two domains in one answer? | cross-domain-context instruction-following, post-SFT | **unmeasured**; cheap to probe once a chat-SFT exists |

The mixed probe (alternating 128-byte blocks of two domains) is **not** the
composition a chat model needs: it scores next-byte loss on raw text, not
instruction-following with cross-domain context. Against a naive two-domain average
the best mask pays only +0.24 nats (mask_a 2.3273 vs 2.0891), so the halves handle
language switching with a mild penalty. **Composition via prompting is unmeasured,
not contradicted.** The candidate for the §4.4 shortlist is therefore a masked model
given a cross-domain system prompt plus few-shot context, run after SFT.

#### 4.4a Judge topology (decision point)

The composition metric needs a judge, and the topology matters more than the model.
**A judge is an HTTP endpoint, not an agent session.** GLM under Opencode and LongCat
under Agent Zero are agents with context and agenda; firing 200 requests into an
agent session is not a judge, it is a conversation. The same models are also available
as programmatic endpoints:

| topology | rate limits | API cost | retry logic | German |
|---|---|---|---|---|
| local endpoint (GLM on 192.168.178.50:8888) | none | 0 | not needed | strong |
| cloud API (LongCat) | yes | yes | **required** | strong |
| local Qwen 3.8 Next Flash | none | 0 | not needed | weak |

The retry problem is real and non-trivial: a cloud judge will fail at least once in
200 queries, so the harness needs backoff, `Retry-After` handling, max retries, and a
"judge did not answer" case. A local endpoint removes that entire class of failure.

**Proposed topology (to be confirmed by the operator):**

1. **Primary judge:** local GLM endpoint (HTTP, no agent session) — independent of the
   training pipeline, no rate limits, no cost.
2. **Cross-check judge:** cloud judge, run on a subset only, to calibrate the primary.
3. **Agreement metric:** % agreement between the two; if they disagree on more than
   20 % of items, the metric is not usable and the disagreement is reported.
4. **Self-reference note:** LongCat as judge of LongCat is a self-reference. It is
   not disqualifying when a second independent judge exists, but it must be stated
   rather than assumed away.

**Not yet decided:** whether the primary judge is the local GLM endpoint or the cloud
judge. The cost is asymmetric (local: none; cloud: rate limits + retry logic + money),
and the quality question is open (a local GLM judge may be weaker than a frontier
cloud judge). This is an operator decision because it commits infrastructure, not
because the prereg cannot state a preference.

#### 4.4b Composition metric (post-SFT, structure fixed now)

The instrument is **cross-domain instruction-following**, not next-byte loss:

1. **Test set:** 200 instructions that require both domains (e.g. "explain the
difference between X and Y", "translate this code comment and explain the logic").
2. **Scoring:** 1-5 per criterion (factual correctness, domain coverage, language
   quality), graded by the judge topology in 4.4a.
3. **Gate:** worst case over the 200 items, not the mean. This is the §4.4 principle
   already stated: the relevant unit is the worst case a user experiences.
4. **Second stage (optional):** per-language fluency check, to test whether routing
   degrades language quality.
5. **Fact check (optional):** for instructions with factual claims, a retrieval or
   knowledge-base check rather than LLM judgment. Without it the metric measures
   plausibility, not correctness.

The structure is fixed before training; the judge choice and the item count are the
open parts. The threshold is **not** fixed here — it follows the judge calibration,
and fixing it before calibration is the R-gate error in a new form.

#### 4.4b FROZEN registration (2026-11-09)

The judge calibration is complete. The registered topology is a **two-judge
cross-check**, not a council: the third seat (GLM on `.50`) is unavailable, and the
cloud path is closed by provider policy, not capacity. Disagreement is reported,
not resolved.

**Set identity** (sha256, raw bytes):

```
783427ee9064b5c5a0a4320e12b4a4e23bfa8eda7c74005ac4f98a294bdd3ed7  cert_items.json        (stage 1, 30 items)
1b25f526db404f17842e3e1876df8264160b43ab34a6cecd27646b6085382281  cert_items_stage2.json (stage 2, 30 items)
8570d8cdd4e5227dddc9a6ae187bcc981d2e2f59c72ee1b7a33ece0122c6ce50  cert_items_merged.json (60 items, FROZEN)
```

All three carry `status: FROZEN`. Any post-freeze item change is set version v2;
these hashes stay historical.

**Certification criteria** (480 calls per judge, 60 items, rescore complete):

| criterion | gate | Gemma-4-31b-it | Qwen3.8-Flash-Next | primary |
|---|---|---|---|---|
| separation | gap ≥ 0,8 AND ≥ 80 % good ≥ 4 | **0,900 / 96,7 % pass** | 0,632 / 75,9 % fail | Gemma (cross-check) |
| fact-checking | ≥ 80 % planted ≤ 3 AND 0 % == 5 | 86,7 % / 11,7 % = 5 **fail** | **96,6 % / 0 % pass** | Qwen (primary) |
| constraint awareness | ≥ 80 % audience ≤ 3 | 66,7 % **fail** | **89,3 % pass** | Qwen (primary) |
| brevity bias | ≥ 80 % ≤ 2 AND mean ≤ 2,5 | pass | pass | both |
| floor | ≥ 70 % = 1 AND mean ≤ 1,5 | pass | pass | both |
| stability | ≥ 70 % exact AND ≥ 95 % ±1 | 78,3 % / 98,3 % pass | **100 % / 100 % pass** | both |
| ordinal | per item | 59/60 fail | 49/56 fail | — |

**Contested subset** (5 items, flagged in the set, excluded from ordinal
interpretation): `cert_de16`, `cert_de17`, `cert_de18`, `cert_de20`,
`cert_en08`. Their gold labels encode one position among several defensible ones;
the disagreement is legitimate, not a defect. See
`docs/notes/2026-11-09_judge-set-ambiguity.md`.

**Not-evaluable cells** (14 Qwen rows): `finish_reason=length`, `attempts=2`,
the 4096-token retry budget consumed by reasoning. They stay outside every gate
denominator; Qwen's ordinal denominator is 56, not 60. Gemma has 0 NULLs. A
larger retry budget or a reasoning-effort knob is a **set version v2** change.

**Acceptance thresholds** (anchor-normalized, per language, from the frozen
anchors):

| gate | rule |
|---|---|
| fact | any item judged factually wrong (≤ 2) is a hard fail — no averaging |
| constraint | any accepted constraint violation (≤ 3) is a hard fail |
| quality | mean ≥ `anchor_good − 0,5` and worst item ≥ `anchor_good − 1,5` |
| stability | ≥ 95 % within ±1 on a scored-twice subset |

Frozen anchors (`anchor_good`): Gemma de 4,83 / en 5,00 / zh 4,83; Qwen de 3,70 /
en 4,06 / zh 4,22. The anchor-refresh rule (> 0,4 shift) was tested and did not
trigger on the merged run.

**Environment:** Qwen3.8-Flash-Next on a DGX Spark (128 GB shared memory,
TensorFold recipe, fp8 KV drafts, MTP, 262.144 context); gemma-4-31b-it on an
RTX 4090 (24 GB VRAM, GGUF Q4_K_S, LM Studio). The judges are different kinds of
instrument, not two samples of one.

**Pool C2/C3 is a separate freeze.** The pool serves the chat model, which does
not exist yet; the cert-set freeze is independent.

## 5. What this prereg does not establish

- **No claim that three languages suffice.** The choice follows the stated target use
  (chat), not a measurement.
- **No claim that TP=2 will work with the BDH implementation.** The training code has not
  been ported to tensor parallelism; this is unbuilt and untested.
- **No claim about the window beyond the control result.** See 4.2.
- **No prediction of final quality.** The bridge measured routing and retention, not
  language ability.

## 6. Open items before this can become a training prereg

1. ~~H2 control result~~ - done 2026-11-04; see section 4.2.
2. A live memory measurement at block 768 on the target hardware.
3. Selection of training corpora from the running preliminary studies.
4. A response-quality metric (section 4.4) - the largest gap.
5. The TP=2 port itself, which is a development task, not an experiment.

Until items 1 and 4 are settled, this document is a frame, not a plan.
