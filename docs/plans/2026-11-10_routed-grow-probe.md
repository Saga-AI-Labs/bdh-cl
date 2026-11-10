# Routed-grow probe: does a router protect the old domain during growth?

**Date:** 2026-11-10
**Question:** if we grow a new neuron block and train it **with the router active** (old
neurons masked out, new neurons masked in), does the old domain survive better than in
the pooled merge, and does the new block actually learn?
**Status:** sketch, not a prereg. Three open design questions in section 4.

## 1. What this probe is not

It is **not** a retry of the pooled merge. The pooled merge is falsified:

```
joint  zh 3.1975  vs  mask_a 1.7306   →  1.47 nats lost to co-activation
```

The probe tests the **opposite composition operator**: instead of summing both
blocks, only one block is active at a time. The mechanism already exists and is
validated at serving time:

```python
# bdh.py:205, 261-262, 277-278
x_sparse = x_sparse * neuron_mask.view(1, 1, 1, -1).to(x_sparse.dtype)
```

What has **never** been tested is the training-time version: the mask applied
while gradients flow, not only at inference.

## 2. The three differences from the Bridge

| | Bridge | Pooled merge | This probe |
|---|---|---|---|
| composition | linear growth, all neurons active | concatenated, summed | growth + mask |
| forward during training | full width | n/a (merge only) | **masked** |
| what the new block learns | with full-width gradients | with summed gradients | **isolated gradients** |

## 3. Design

### 3.1 Setup

- **Base:** `out_a/bdh_textmix_k25w1024-zh_last.pt` (mult 896, 2.82B)
- **Grow:** one new block, e.g. mult 896 → 1120 (+25 %, 0.7B new parameters)
- **Mask:** contiguous — old block active for the base domain, new block active for
the new domain. The mask is the one `serving_eval.py` already builds:

```python
N = cfg.mlp_internal_dim_multiplier * cfg.n_embd // cfg.n_head   # 114688 at mult 896
mask_old = zeros(N, bf16); mask_old[:N] = 1.0          # base neurons
mask_new = zeros(N, bf16); mask_new[N:] = 1.0          # grown neurons
```

### 3.2 Three phases

| phase | mask | corpus | what it tests |
|---|---|---|---|
| **P1** | new block active, old masked | new domain corpus (e.g. de) | does the new block learn with isolated gradients? |
| **P2** | old block active, new masked | zh (base domain) | **does the old domain survive?** — the key question |
| **P3** | router-selected per sequence | mixed corpus | does sequence-level routing hold the isolation? |

### 3.3 Measurements

| metric | instrument | expectation if the probe works |
|---|---|---|
| base-domain loss | zh NLL, old mask | ≤ 1.7306 (the zh_last reference) |
| new-domain loss | new corpus NLL, new mask | clearly better than the base model on that corpus |
| mixed loss | alternating crops, router-selected | below the pooled number (3.1975) |

**The decisive comparison is P2.** If the base domain holds at ≤ 1.7306 while the new
block learns, then routed growth is a working composition operator — and the pooled
merge was the wrong operator, exactly as the co-activation diagnosis says.

## 4. Three open questions — I cannot answer them from the data

**Q1: Does the mask apply to gradients or only to the forward?**

`neuron_mask` in `bdh.py` multiplies **activations**, not gradients. If the old
block is masked in the forward, its gradients are zero — so it is frozen by
construction. That is the intended behaviour for P1/P2, but it means the old block
**cannot adapt** to the new data. Whether that is good (protection) or bad (no
co-adaptation) is the probe's question, not mine.

**Q2: Does the grown block have its own `attn.freqs`?**

The Bridge's grow path uses `get_freqs(N_dst)` for the new width. The merged
eval showed that a physically sliced model without recomputed freqs degrades. The
grown path may already handle this — **I have not verified it**. This must be
checked before any run, because a wrong freq table poisons the whole probe.

**Q3: Does this fit on one Spark?**

The base is at the edge ("dicht an die Grenze"). Adding 25 % width increases
the model to ~3.5B. The measured peak in the grow phase was **82 GB GPU** at
mult 896. A 25 % wider model is ~100 GB — **above the 121 GB unified pool with
training overhead**. This is the hard constraint, and it may kill the probe before
it starts.

## 5. Cost and stop conditions

| | |
|---|---|
| P1 + P2 | ~2 × 1 day GPU on one Spark |
| P3 | ~1 day |
| stop condition | if P2 shows base-domain loss > 1.9, the protection failed and the probe ends |
| stop condition | if the grow does not fit in memory, the probe ends before training |

## 6. Why this is worth trying — and why it might not be

**For:** it is the only composition operator that has not been falsified. The
serving-time isolation is measured at +0.0000; the training-time version is the
missing half. If it works, it is a path to a multi-domain model without the
co-activation loss.

**Against:** it builds on `zh_last`, and the standing decision is that the Bridge
was an experiment, not a foundation. **That decision is a scope choice, not a
measurement** — and it can be revisited, but it should be revisited explicitly.

**And the honest limit:** even if the probe works, it does not build a chat model.
It validates one operator on one Spark. The step from "routed growth works" to
"benutzbares Chat-Modell" is still a plan that does not exist.

## 7. Reproduce (after authorisation)

```
# 1. verify the freq table for the grown width
# 2. grow zh_last -> mult 1120, save the new checkpoint
# 3. P1: train new block only, mask_old=0/mask_new=1, on the new corpus
# 4. P2: evaluate zh with mask_old=1/mask_new=0  (the decisive number)
# 5. P3: mixed corpus with sequence-level router selection
# 6. compare against pooled (3.1975) and isolated (1.7306)
```
