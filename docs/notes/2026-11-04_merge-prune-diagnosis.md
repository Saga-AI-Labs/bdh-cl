# Merge-prune diagnosis: keep neuron pairs with their trained frequencies (gather, not recompute); and why no prune can rescue the ancestor-descendant merge

**Date:** 2026-11-04
**Addressed to:** the author of `docs/reports/2026-11-04_merge-experiments.md` (section 4: "Something about physically shortening the neuron dimension is wrong in a way not yet identified")
**Evidence:** `bdh.py` (`get_freqs`, `Attention.rope`, `_k_sparse_relu`, block forward), `pipeline/merge.py`, `scripts/quinn/merge_prune.py`, raw evals in `out_c/merge_probe/*.json`
**Status:** note. All report numbers were re-verified against the raw JSON artifacts first; they check out exactly.

## 1. Report numbers verified

| artifact | model | legal | zh | matches report |
|---|---|---|---|---|
| `eval.json` | legal_last / zh_last / merged | 2.88 / 5.46 / 3.48 | 40.74 / 5.64 / 9.00 | ✓ |
| `eval_pruned.json` | merged_pruned896 | 11.54 | 41.31 | ✓ |
| `eval_zh_pruned448.json` | zh_last 896→448, freqs sliced | 14.43 | 21.78 | ✓ |
| `eval_zh_fixed.json` | zh_last 896→448, freqs recomputed | 18.36 | 57.48 | ✓ |

Params also check out: 2,617,769,984 + 2,819,096,576 = 5,436,342,272 (embeddings
bit-identical, so the average is a no-op and the sum is exact).

Frame check against `2026-11-04_bdh-paper-merge-claim-verified-with-caveats.md`
(written before the probe ran): prediction 2 confirmed (merged beats the *other*
parent on its home turf: legal 1.2479 < 1.6966 nll; zh 2.1969 < 3.7072). Prediction 1
(home dilution < 0.1 nats) is violated in exactly the direction the note's lineage
confound predicted (legal +0.19, zh +0.47 nats). One addition to that confound: the
duplicated trunk is not even a clean copy. `merge.py` concatenates the parents' freqs
buffers, and `get_freqs(n)[j] ∝ θ^(−2⌊j/2⌋/n)` depends on the parent's width — the
same trunk neuron carries exponent 2j/53248 in the legal half and 2j/57344 in the zh
half. Same weights, slightly different time-scales, correlated top-k behaviour: the
cross-talk section 3 describes is overdetermined.

## 2. The two bugs in merge_prune.py

### Bug A: the prune must keep neuron PAIRS, not neurons

`Attention.rope` rotates *adjacent pairs* of the neuron axis:

```
out[2j]   = v[2j]·cos(ph[2j])   − v[2j+1]·sin(ph[2j])
out[2j+1] = v[2j+1]·cos(ph[2j+1]) + v[2j]·sin(ph[2j+1])
```

This is a rotation of the pair only when `ph[2j] == ph[2j+1]` — which `get_freqs`
guarantees for a fresh buffer via `quantize(t, q=2)`. A keep-set of *scattered
positions* (`--order random` / importance scatter, shared across heads but arbitrary
within N) re-pairs survivors with strangers at the new positions: even with perfect
frequency values, the rotation structure of every kept neuron is destroyed. This bug
is independent of freqs handling and alone explains a large degradation.

### Bug B: frequencies are trained properties — gather, never recompute

Each neuron's RoPE frequency is the time-scale its weights were trained against (the
paper's freq0–freq7 buckets: slow-acting vs fast-acting halves). The merged
checkpoint's freqs buffer carries the *trained* value at every position (concat of the
two parents' schedules; the restart at position 53248 is harmless because `rope`
indexes the buffer by local position and both parent widths are even and
pair-quantized — the merge itself is freqs-correct).

Attempt 2 sliced the buffer; attempt 3 recomputed `get_freqs(N_dst)`. Recomputing
assigns the schedule of a *fresh* N_dst model: `θ^(−2p/28672) = (θ^(−2p/57344))²` —
the trained frequency is *squared*. At pair p=10000 that is ~30× off; the first four
pairs differ only in the fourth decimal (0.158725 → 0.159032, exactly as printed in
the report), which is why the damage is invisible in the log line and catastrophic in
perplexity. That attempt 3 came out *worse* than attempt 2 (57.48 vs 21.78) is
consistent: the exponent mismatch grows along the axis, and the recomputed schedule
misaligns every kept neuron, while the sliced variant at least leaves low indices
nearly correct.

### The fix (one selection rule)

Select **pair** indices, keep both members adjacent in original order, gather the
original frequencies:

```python
pair_imp  = shared.view(N_src // 2, 2).mean(dim=1)      # or randperm over pairs
keep_p    = torch.argsort(pair_imp, descending=True)[:N_dst // 2]
keep_p    = torch.sort(keep_p).values                  # ladder order, holes allowed
keep_idx  = torch.stack([2 * keep_p, 2 * keep_p + 1], dim=1).view(-1)
new_freqs = sd["attn.freqs"].float().cpu().view(-1)[keep_idx]   # gather, NOT get_freqs
```

The encoder/encoder_v/decoder gathers in the committed script are already correct for
a shared index set and need no change.

### Why the fixed prune should be measured, not feared

With pair-gather + freqs-gather the pruned model is the original *minus the removed
pairs' contributions*, up to two bounded effects: (i) `_k_sparse_relu` top-k refills
the freed budget from just below threshold (removed neurons are low-|xy| by
selection, so the refill is second-order); (ii) no LayerNorm spans the neuron axis —
all `ln` calls normalize over D — so there is no renormalization surprise. Prediction:
unmerged `zh_last` 896→448 with the fixed script lands near 5.46/5.64 plus a small
delta. If that control passes, the instrument measures pruning instead of bugs, and
only then does it touch the merge.

## 3. The structural verdict: a correct prune still cannot rescue this merge

For an ancestor∥descendant merge the deduplicated union of the two neuron sets is the
descendant: `zh_last` already contains phases 0–21 (shared, bit-exact), legal's phase
22 (frozen into zh_last at legal-trained weights), and its own phases 23–24. Keeping
the coherent zh block `[53248..110592)` reproduces `zh_last` bit-exact (weights *and*
its freqs schedule); keeping anything else is a franken-selection. There is no subset
of this merge that beats both parents at mult 896 — the information content just is
not there.

This is why the August prune+replay recovery worked and this one cannot: August merged
**siblings** (union strictly contains both parents; pruning faces a genuine selection
problem), while `legal_last ∥ zh_last` merged an ancestor with its descendant. The
report's section 5 says this in one line; the arithmetic above is the proof that no
script fix changes it. The 7-day divergent-branch experiment (report §6.3) remains the
decisive test, and the fixed prune script is exactly the instrument it needs.

## Addendum (2026-11-05, per the author's review)

The review corrects the attempt-2 record: the original frequencies were **gathered**
(not sliced, not recomputed) and the control still failed (5.64 → 21.78). The
pair/sequence mechanism above therefore stands — scattered positions destroy the
rotation structure through re-pairing and an irregular phase sequence even when the
gathered values are correct. The recommended fix is now **contiguous blocks**
(`--block` in `scripts/prune_eval.py`, already implemented there): it preserves the
pairing *and* the local ladder, and it is the variant the August evidence was measured
against. A pair-wise sorted gather remains theoretically equivalent (the attention
kernel sum is commutative over pairs) but is untested. The recompute diagnosis
(attempt 3, squared frequencies) is unchanged.
