# Living Weights (TensorFold) — Reference Note

**Source:** Abriss by Ash Hart (X/Twitter), TensorFold v1.0.7, 2026-10-11
**Committed:** 2026-10-12 · Quinn
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
