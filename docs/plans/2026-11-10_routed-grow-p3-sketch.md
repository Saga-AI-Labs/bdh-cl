# Routed-grow probe P3: mixed training with a sequence-level router

**Date:** 2026-11-10
**Status:** sketch. The router does not exist; section 2 is the open part.
**Depends on:** P1 (train the new block with `route_mask_side=new`), P2 (old domain survives
a grow step — measured: 1.7928 vs base 1.7487, +0.0441 nats).

## 1. What P3 asks

P1/P2 used **one** mask per run: either the new block or the old block is active.
P3 asks whether the model can **switch** between them per sequence:

```
sequence is zh  -> old block active
sequence is legal -> new block active
```

The measurement is the same as P2's: after P3, the old domain must still be at
≤ 1.7928, and the new domain must be better than the base model was on it.

## 2. The missing piece: the router

**What exists today is a constant, not a router:**

```python
route_neuron_mask = keep.clone()   # 0..n_old = 0, n_old..n_new = 1
```

It is built once at growth time and applied to every batch. For P3 the mask must
be **selected per sequence**. Two candidate mechanisms, in order of preference:

### Option A: pre-forward byte classifier (recommended first)

Reuse the mechanism already validated in `scripts/eval_router.py`: score the
first N bytes of each sequence against each domain's corpus and pick the side.

```
score(side) = mean NLL of the sequence's first 128 bytes under that side's corpus
side = argmin(score)
```

| | |
|---|---|
| Cost | one extra forward per sequence (or a cheap token-level score) |
| Training cost | none — the classifier is corpus-based, not learned |
| Failure mode | sequences with mixed content (the mixed probe showed this: joint 4.2159 vs mask_a 2.3273) |
| Strength | exactly the mechanism that produced the measured isolation |

**This is the honest first choice** because it is the same instrument that gave us
+0.0000 on six cells. A learned router would be a second variable in the same
experiment.

### Option B: learned router head

A small head (linear or MLP) on the residual stream that predicts the side. It
needs:

- a training signal (the corpus labels)
- a load-balancing loss, or the router collapses to one side
- re-certification as part of the model

**Not recommended for the probe.** It answers a different question (can a router
be learned) and would confound the isolation measurement.

## 3. Design

### 3.1 Mixed corpus

Interleave the two domains at the sequence level, not the byte level:

```
[zh block][legal block][zh block][legal block] ...
```

Each block is one `block_size` window. The split is recorded per block so the
router can be evaluated against it.

### 3.2 Training loop

```python
for block in mixed_stream:
    side = router(block)              # A: byte classifier, B: learned head
    mask = mask_for(side)             # keep old or keep new
    _, prefix_loss, _ = model(block, neuron_mask=mask)
    _, full_loss, _    = model(block)                  # reference
    loss = alpha * prefix_loss + (1 - alpha) * full_loss
```

**The mask is the only change from P1.** The loss shape, the frozen old block,
and the full-width reference stay as they are.

### 3.3 Measurements

| metric | instrument | pass condition |
|---|---|---|
| old-domain survival | zh NLL, old mask | ≤ 1.7928 (the P2 result) |
| new-domain gain | legal NLL, new mask | better than base `zh_last` on legal |
| router accuracy | side vs corpus label | ≥ 95 % on the mixed stream |
| mixed NLL | router-selected mask | below the pooled number |

**The router accuracy is the diagnostic that matters.** If the router is wrong on
5 % of blocks, the isolation measurement is contaminated and the old-domain
number is not interpretable.

## 4. Open questions

1. **Where does the router run?** In the training loop (a Python-level decision per
   batch) or inside the forward pass (a tensor-level switch)? The former is simpler
   and matches the eval protocol; the latter is what a serving model would need.
2. **What is the block granularity?** Sequence-level routing is the probe's
   question. Token-level routing is a later question and needs a different mask
   shape (per-token, not per-sequence).
3. **Does the router see the same 128 bytes the eval protocol uses?** `eval_router.py`
   uses a 128-byte window with `--window`; the training router should use the same
   window, or the two measurements are not comparable.
4. **Is the mixed corpus balanced?** An imbalanced mix would bias the router and the
   loss. The split must be recorded and audited before the run.

## 5. What P3 does not establish

- **It does not build a chat model.** It validates one operator on two domains.
- **It does not test token-level routing.** Sequence-level is the probe's scope.
- **It does not prove the router generalizes to unseen domains.** The classifier is
  corpus-based; a third domain needs a third corpus and a re-run.
- **The mixed-probe result (joint 4.2159 vs mask_a 2.3273) says composition is hard.**
  P3 tests whether routing is the right composition operator, not whether
  composition itself is solved.

## 6. Reproduce (after P1)

```
# 1. build the mixed stream: zh + legal, block-aligned, split recorded
# 2. router: byte classifier over the first 128 bytes of each block
# 3. train: --route-aware --route-mask-side <router-selected> --route-alpha 0.9
# 4. measure: zh old-mask, legal new-mask, router accuracy, mixed NLL
# 5. compare against P2 (1.7928) and the pooled merge (3.1975)
```
