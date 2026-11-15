# QAT for BDH — Proposal v2

**Date:** 2026-11-15
**Status:** reminder draft. Not activated; activation is gated on the conditions in
section 8, which are unchanged from v1 except where marked.
**Owner:** Quinn (review seat) — design; MiMo (execution seat) — implementation.
**Supersedes:** `2026-08-28_qat-proposal.md` (v1), kept for history.

---

## 1. Why this exists

The 1.58-bit PTQ attempt collapsed to 0.000 on every benchmark. The failure was not
the target model — it was PTQ instead of QAT. BitNet-style quality only emerges when
quantization is simulated during training (straight-through estimator, fake-quant
forward pass). Any future quantization effort for BDH must therefore be QAT, never
PTQ.

## 2. Why BDH is QAT-friendly

1. **Coordinate separability:** the only cross-neuron coupling is LayerNorm. Encoder
   columns, per-neuron attention and decoder rows act independently per neuron, so
   quantization can be controlled per neuron/parameter slice. Transformer attention
   (QKV projections coupling across the sequence space) does not have this.
2. **Sparse Positive Activation rule (~5% active):** most quantization error lands on
   inactive paths and does not reach the output. QAT can exploit the sparsity as a
   noise sieve.
3. **Additive growth / CL compatibility:** quant scales and fake-quant operators must
   be defined per phase block and must survive the growth rule; the recipe's
   isolation properties (prefix selection, freeze, routing) must hold under quantized
   inference.

## 3. The warning: expansiveness amplifies injections

Measured directional gains 1.05–1.89 per level over L=6 levels. A per-level
quantization injection gets multiplied across levels — conservative worst case
roughly 6^1.5 ~ 15x, realistically less because LayerNorm renormalizes, but not
negligible.

Implication: QAT for BDH must simulate quantization **per level with separate
scales**, not a single global quantizer. The Q1 quality gate must be measured under
the exact same evaluation protocol as FP32.

## 4. What changed since v1 (2026-08-28)

v1 was written before the routed-grow probe existed. Four facts from that campaign
change the QAT picture:

1. **The mask path is now measured.** Every checkpoint in the probe carries
   `k_sparse_ratio = 0.0` — plain ReLU, no topk. The neuron mask is an exact
   elementwise zeroing, and the masked forward of the grown and trained checkpoints
   is bit-identical to the base model's (probe report section 13, cells A=B=C). **A
   quantized masked forward must preserve this identity** — the new gate in section 7.
2. **The noise floor is now known.** Single-run random-crop eval noise is ~0.05–0.10
   nats; fullcov is batch-invariant to 2.2e-9. The Q1 quality gate must name its
   instrument, or it measures the instrument rather than the quantizer.
3. **The frozen-prefix guarantee is mechanism-based, not assumption-based.** It rests
   on snapshot/restore of the frozen regions at step end (`wd > 0` regimes), or on
   the AdamW decay guard plus zero gradients (`wd = 0`). Quantization interacts with
   both: fake-quant changes what "zero" means, and per-level scales change what
   "restore" restores.
4. **TP=2 is registered separately** (chat-prereg section 6 item 5,
   `docs/plans/2026-11-15_tp2-bridge-study.md`). TP=2 and QAT interact on reduction
   order and accumulation precision — **they should not be activated in the same
   window.** If both are live, a drift has two possible causes and neither is isolated.

## 5. Phases and gates

| Phase | Trigger | Content | Exit gate |
|---|---|---|---|
| **R3** | now | CL science: manuscript revision, growth+routing results, freeze_attn diagnostic | manuscript submission-ready |
| **Q1** | R3 complete | Feasibility on tiny model (~0.3M params): fake-quant forward, STE, per-level scales; quality vs FP32 baseline on the SAME instrument | **quant loss <= 0.1 nats** vs FP32 on the same data/protocol. If not met, QAT for BDH is a dead end - stop early and cheap |
| **Q2** | Q1 green | Quantize train/infer at 100M scale; measure acquisition / erosion / routing under quant with the same falsifiers | routing and isolation metrics match FP32 within protocol tolerance |
| **Q3** | Q2 green | Full CL + QAT combination: consolidation under quant, growth under quant, routing under quant | near-joint parity of the consolidated quantized model vs its FP32 counterpart |

## 6. Hard rules

1. Never PTQ a BDH post-hoc at extreme bit-widths (the Qapdex failure mode).
2. Never measure QAT results against FP32 under a different protocol.
3. Never run QAT experiments while the FP32 CL protocol is still the active
   measurement baseline.
4. Per-level quantization scales are mandatory; global-only quantization is rejected.
5. Any selection operator entering via quantization (top-k / sparse positive
   activation) must be width-invariant under growth: hold k ABSOLUTE across the
   growth step. Masking the new block does NOT restore exactness (counting argument,
   commit 6754e83).
6. **New (v2): the masked-forward identity is a QAT gate, not a footnote.** After any
   fake-quant change, the grown-and-trained checkpoint evaluated under the old mask
   must still equal the base model's value to the printed digits. If quantization
   breaks that identity, the isolation story is gone and QAT stops here.
7. **New (v2): do not activate QAT and TP=2 in the same window.** Both perturb
   reduction order; combined they cannot attribute drift.

## 7. Open design questions

- Optimal bit-width: whether the Sparse Positive Activation rule permits 1.58-bit
  ternary weights, or whether 2-4 bit is the real target.
- Interaction of quant scales with the additive growth rule: do scales need to be per
  phase block and frozen on growth?
- Whether the compiled detector / likelihood router remain accurate on quantized
  activations, or need quant-aware thresholds.
- **New (v2): how fake-quant interacts with the step-end restore.** The restore
  copies frozen tensors back after the optimizer step; under fake-quant the stored
  values and the restored values may differ in precision semantics. This must be
  settled before Q2, not discovered there.

## 8. Activation conditions (unchanged from v1)

Revise this plan (and turn it active) when ALL of:

(a) manuscript R3 is committed,
(b) growth+routing results are reviewed and accepted,
(c) the freeze_attn diagnostic has a final verdict.

GLM's reading of the timing: the earliest sensible activation is **after Graft #2 +
serving gate + the third-domain run**, i.e. after the FP32 plateau. That is consistent
with (a)-(c); the additional constraint from section 6 is that TP=2 and QAT are not
both live.

Until then this stays a reminder draft.
