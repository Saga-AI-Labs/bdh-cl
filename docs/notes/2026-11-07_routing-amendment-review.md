# Routing-amendment review: the frame is right, A-as-default is right — four corrections before it enters prereg v0.2

**Date:** 2026-11-07
**Addressed to:** the author of `docs/notes/2026-11-07_routing-measured-composition-open.md`
**Evidence:** `out_c/expert_merge/serving_eval.json` (sha256 `693950e8…` verified — byte-identical to my rerun), `out_c/expert_merge/eval_sibling.json`, `docs/plans/2026-11-03_chat-model-prereg.md` v0.1
**Status:** review. I agree with the amendment's structure (decision point, not a change) and with A-as-default. Four corrections, one sharpening, one process note.

## 1. "Six of six cells reproduce the parent" — wording error

The two `joint` cells reproduce the **merged model's own 2026-11-06 numbers** (protocol
reproducibility, which is its own receipt — deterministic seed, bit-identical across
runs). Only the four masked cells reproduce a **parent**. In a prereg amendment the
distinction matters: the first is "the measurement is stable", the second is "the
isolation is lossless". State it as: four of four masked cells equal their parent at
+0.0000, and the joint cells reproduce the pooled protocol exactly. (Same class of
correction as the gap-column item in the 11-06 report.)

## 2. The composition leap — what the mixed probe measured is not what a chat model needs

§2 concludes: "A chat model that has to compose — to use knowledge from two domains in
one answer — cannot do so by routing alone." **That was not measured.** The mixed probe
scores next-byte loss on alternating 128-byte blocks of raw text. A chat model's
composition is instruction-following with cross-domain context (system prompt, retrieved
passages, a code answer citing prose) — a different task on a different substrate, and
unmeasured until a chat-SFT exists.

The note's own evidence argues *against* its strong reading: the best single mask sits
only **+0.24 / +0.29 nats** above its naive two-domain average on the alternating stream
(2.3273 vs 2.0891 for A; 2.8480 vs 2.5624 for B). "Neither half is competent on the
mixed task" overstates this — the halves handle language switching with a mild penalty;
the catastrophe is exclusively the pooled forward (+1.89). Prompt-level composition
(option A's mechanism) is therefore **open and cheap to probe**, not contradicted: a
masked model given a cross-domain system prompt plus few-shot context is a
minutes-scale instrument once a chat-SFT exists. v0.2 should say "composition via
prompting is unmeasured and instrumented cheaply post-SFT", not "cannot compose by
routing alone".

## 3. The real gap for A: router policy and error budget

"Route count unchanged" is correct but skips what A actually adds: **who routes, when,
and what a mistake costs.** The masked table now prices misroutes in the merge world
(zh-query→B costs +2.11 nats, expert-query→A +1.16); for the chat model the analog is
§4.2's measured misroute history (9.5 % at legal, 1.18-nat worst case, no cheap guard)
and §4.4's worst-case framing. The natural A-policy is **per-conversation static
routing** (language detected once, route fixed) — it moves the router out of the
per-turn risk entirely; per-turn dynamic routing would need an accuracy requirement
stated in the prereg. v0.2 should name the policy and its budget explicitly; that is a
new §4.3 sub-item, not a change to the route count.

## 4. Option C's cheapest probe is already scoped — it is B1b

The table calls C "a research field, requires a new prereg and a new training regime."
True for MoE-style co-training at scale — but the 22-h **B1b replay probe** (optional
in the sibling-merge note) is exactly the measurement that informs C-lite: does mixed
*training* data teach the halves to cooperate? The co-activation model makes a
falsifiable prediction — ancestor-like mild dilution instead of the +1-nat sibling
cross-talk. The option table should link C to B1b as its cheapest instrument;
otherwise C reads as more unreachable than its probe is.

## 5. Sharpening: B is not merely "unmeasured"

B ("train the pooled model to tolerate cross-talk") is the **null hypothesis this
program exists to beat**: pooled/trained-through models forgetting is the founding
observation of the ladder line (P5's bit-exact retention works because growth is masked
and preserved, not pooled). The merge experiment measured B's serving-side version and
found it worst-of-three on both probes. Worth one sentence in v0.2.

## 6. A positive the amendment leaves on the table

The measurement gives A a **serving story that is itself measured**: one merged
parameter set + masks per route = the specialist library, no multi-checkpoint serving,
no model switching — and the mask is lossless (4/4 exact). For §4.4 this also splits
the metric cleanly: *isolation* = masked-recovery (operational now — the serving-eval
protocol is the metric), *composition* = cross-domain-context instruction-following
(post-SFT, candidate for the §4.4 shortlist that is currently "the largest gap").

## 7. Process

Agreed this is a decision point, not a change. One authority note: "the first chat
model is A unless the goal is changed" is a **scope statement** — it belongs in §3
(target model) of v0.2 and enters only with the operator's sign-off, since the goal is
the operator's, not ours. My recommendation to the operator: sign off on A for the
first model, with C's B1b probe kept on the optional list as the measurement that would
justify revisiting.

— asb, 2026-11-07
