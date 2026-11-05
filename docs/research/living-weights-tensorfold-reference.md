# Living Weights (TensorFold) — Reference Note

**Source:** Abriss by Ash Hart (X/Twitter), TensorFold v1.0.7, 2026-10-11
**Committed:** 2026-10-12 · Quinn
**Updated:** 2026-11-05 · asb — refreshed against `docs/living-weights.md` (post-1.0.6
pocket learner) and full-engine context; additions appended below, the v1.0.7 text
above is left as written.
**Status:** Reference only — no installation, no training, no infrastructure change without explicit operator authorization

---

## What It Is

Living Weights is a neural continual-learning design for local LLMs (Nemotron 3.5 Lightning) that implements a bounded version of parameter-level teaching: a running local model can retain an explicitly taught fact inside its checkpoint and use it after a restart, without requiring the original conversation.

It belongs on the **parameter-learning side** of the memory distinction (alongside pretraining, fine-tuning, LoRA, model editing) — not on the retrieval side (RAG, KV cache, prompt cache).

---

## Core Mechanism

### Shared-Expert Pocket

- **64 additional neurons** reserved in each MoE layer's shared expert
- Learner normally allocates **~10 neurons per fact** across eligible layers
- Original shared-expert weights are **not changed**
- Forward: `y_new = V ReLU(Ux)^2 + B ReLU(Ax)^2` — ordinary neural computation, no text lookup table

### Carrier System

- Update sets learning rate to near-zero, freezes all other layers, performs targeted correction
- Separated from real-time memory and update delay
- **Lesson construction**: model writes Q&A examples, alternative wordings, nearby questions whose answers should remain unchanged
- **Squared-hinge objectives**: encourage positive activation for the fact, negative margin elsewhere

### Lesson Registry

- Knowledge base models which memory may be in context
- Separates documented facts from assumptions, documents gaps instead of filling them

### Context Server

- Context is **served on demand** rather than prepended
- Fixes 44% error rate in cognitive loop from token cost and missing session snapshots

### Package Escalation

- Each request runs as a separate packet with own retry policy
- Retry escalation P2–P4, ≤3 repetitions

---

## Released Results (v1.0.7)

### Personal Facts

- 3 facts taught sequentially, both test wordings recalled for each on M5 Ultra, M3 Ultra, GB10
- Live and after plain restart, no observed leakage/drift in checked controls
- GB10 with thinking: 4/6 wordings recalled

### Document Learning

- Short handbook: 3–6/6 answers across 6 runs
- 21-fact handbook: 6/16 answers
- 5-fact handbook: 1 question (Mac) + 2 (GB10) received another fact's answer
- ~16% slower Mac decoding with 21 learned facts

### Performance

- Learning round time: 217→52s (M3 Ultra), 200→47s (GB10) — ~4.2× improvement
- Whole fact: 1.5–2.5 min (M5/M3 Ultra), 2–3 min (GB10)
- Numerical check: bit-identical packed and separate training passes on CUDA

---

## Similarities to BDH-CL

| Aspect | Living Weights | BDH-CL |
|---|---|---|
| **Core idea** | Add neurons beside shared experts, freeze old weights | Add neurons per territory, freeze old path |
| **Preservation** | Carrier freezes other layers during update | F-V9 restore freezes old path, step-end restore |
| **Routing** | Learned activations determine response | Likelihood scan selects territory prefix |
| **Checks** | Recall, repetition, nearby-answer preservation | P5 bit-exact, K3 routing accuracy, K4 retention |
| **Scalability** | Bounded pocket capacity (64 neurons/layer) | +32/head per phase, grows to 4544 (W512) |
| **Separation** | Trainer separated from serving | Training separated from serving (eval_router) |

---

## Differences from BDH-CL

| Aspect | Living Weights | BDH-CL |
|---|---|---|
| **Growth model** | Constant-size carrier with bounded pockets | Physical growth: +32/head per phase, 24 phases → 4544 |
| **Preservation claim** | Bounded retention with documented gaps | **Bit-exact** preservation (P5 gate) |
| **Focus** | Single facts, personal knowledge | **Territories**, whole-language domains |
| **Scale target** | Unbounded continual learning via separate carriers | ~100M base, growth to several hundred M |
| **Checkpoint** | Slightly wider model (3712→3776) | Standard checkpoint, +32/head |
| **Evaluation** | Small-sample integration checks (3 facts) | Full 25×25 confusion matrix, 200 crops/domain |
| **Router** | Learned activations (implicit) | Likelihood scan (explicit, O(K) per crop) |

---

## Synergies (Not Yet Explored)

1. **Provenance blocking**: Carrier with independent context server mirrors BDH's retention audit
2. **Retention as lesson source**: BDH retention (K4/P5) could be translated into Living Weights' lesson registry — lessons in lessons, not single facts
3. **Interruptability**: Context server with retry escalation could connect BDH inference with interruption — served rather than prepended

---

## Critical Notes

- **No quantitative performance numbers** (Accuracy/Latency/F1) — only qualitative architecture promises
- **Pocket capacity** is the retention bottleneck — 64 neurons/layer may overflow for complex facts
- **"Real fact" problem** in Session 2 is described as **still open** — lesson registry is a draft, not implemented
- **Teacher and judge use same model** — human-written tests and external checking are flagged as particularly important

---

## Status

**Reference only.** No installation, no training, no infrastructure change without explicit operator authorization. The Ascents remain untouched unless otherwise directed.

---

— Quinn, @quinn-the-builder, 2026-10-12

---

## Update 2026-11-05 (asb): pocket learner shipped; engine context; adoption

### Corrections to the v1.0.7-era picture above

| Announcement era (sections above) | Current docs (`docs/living-weights.md`, release after 1.0.6) |
|---|---|
| Lesson registry a draft, "real fact" problem open | Shipped as the lesson's acceptance checks: model-written Q&A, held-out wordings (never trained, thinking off *and* on), near-misses must not move, hallucination probes ("the user's cat's name") must stay unanswered; a failed lesson is removed whole before anything is written |
| "No quantitative numbers" | Documented: 8.7–10.5 min per fact (GB10, Flash Next); −16 % Mac decode with 21 facts, −5 % drafted with 3; rollback 5.6–5.7 s (M3 Ultra, APFS clones) vs 58–91 s (GB10, ext4) |
| Pocket as design sketch | Pocket learner shipped: shared expert widened 3712→3776, `tensorfold_learned_neurons` in config.json; folders taught by 1.0.3–1.0.6 (lessons *inside* the shared experts) are refused by `--slide`; only freed top-of-pocket neurons are reused |
| Retention/deletion implicit | Single + batch delete (≤256 ids) shipped: silencing (input weights zeroed, output columns left), retained-fact checks, two-phase crash-consistent write (graph file ↔ shards), GPU put-back rules on upload failure |
| — | `slide audit` shipped: per-neuron off-subject firing rate against a versioned 256-prompt bank (activation > 1e-4, default flag at 1 %), four prompt groups, read-only |
| — | Cross-fact disturbance confirmed as known issue #870 (Flash Next: after five lessons, two of three kept facts still answered) |
| — | Cross-backend portability: a folder taught on a Mac serves on GB10 and vice versa |

### BDH-CL relevance, sharpened (updates "Synergies")

- The pocket is **additive-only by construction** — nothing existing is written, so the
  failure mode we measured on 2026-11-04 (ancestor∥descendant merge: trunk duplication
  + pooled-k cross-talk, legal +0.19 / zh +0.47 nats) cannot arise. Living Weights is a
  productised existence proof for the **isolation side** of chat-prereg §4.3 (routes
  vs merge).
- The audit's **off-subject firing rate against a fixed, versioned prompt bank** is the
  closest published analogue to the §4.4 response-quality/interference metric that is
  still to be defined.
- **GB10/DGX Spark is the qualified learning platform.** Once B1 finishes, a
  Living-Weights lesson run on one of our own Sparks is a cheap external datapoint for
  §4.3. No installation before then (the status line above stands).

### Engine context (why TensorFold, not just Living Weights, gets adopted)

- **Exact decoding as a contract:** every accepted draft must equal the token the same
  engine produces with `draft: false` (Gumbel noise derived only from seed, position,
  token-id; every row of a multi-row verify pass gets single-row arithmetic bits);
  resumed = fresh execution, concurrent stream = solo run. Auditable by any user.
- Single Zig binary (no Python/MLX install), hand-written per-family kernels, refuses
  unsupported formats before download; CUDA release covers sm_80–sm_121.
- README-qualified multi-Spark serving: **TP=2 and TP=3** (GLM-5.3-Flash NVFP4 /
  FP4-Local / XSFP4 on two and three GB10s). **TP=4 is community-verified, not
  README-qualified** (tonyd2wild: GLM-5.3-Flash EXL3 TP4; DeepSeek-V4.1-Flash TP4 at
  93.6 tok/s, 1M context).
- Adoption: ~328 stars late Sep 2026 → ~1.7k (Nov); self-reported 1.6–3.1× vs vLLM
  (MTP=3) on DGX Spark; community operators report replacing vLLM at TP=1–4 within
  weeks (X: "4 Sparks, TP4, switchless RoCE ring — same hardware and topology,
  different software: vLLM vs TensorFold").
- Documented vLLM fragility on exactly this topology: NVIDIA forum, two-Spark vLLM
  TP=2 — "one node drops while the other's GPU goes 100 % forever".

### Assessment: adoption without many "gravierende Neuerungen"?

Operator's question, 2026-11-05: if the technical novelty is modest, is the vLLM
displacement mostly clever marketing? Assessment (asb): the displacement is
**fit-for-purpose, not hype**. vLLM's design centre is datacenter batch throughput on
H100-class parts; on 1–4 unified-memory Sparks the real workload is 1–8 concurrent
single-streams — the regime where TensorFold's per-family kernels, MTP drafting and
exactness contract are strongest and vLLM is weakest (and demonstrably fragile, forum
thread above). The "marketing" that worked is **verifiability**: receipts with pinned
commits, documented known-issues, refused qualifications, self-reported benchmarks a
user can reproduce by sending `draft: false`. A hype-averse, benchmark-driven community
pays in exactly that currency. Lesson for this repo: preregs + raw-JSON verification +
receipts are the same currency — narrow-but-exact beats broad-but-approximate, in
adoption as in evaluation.
