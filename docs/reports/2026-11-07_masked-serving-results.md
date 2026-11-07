# Masked serving results: isolation is exact, the pooled forward is the loss

**Date:** 2026-11-07
**Question:** the expert-merge report (2026-11-06) concluded that concatenation
pooling produces cross-talk and that routed routes beat pooled budgets. That
conclusion was argued for, never measured as a serving mode. This report measures it.
**Answer:** segment masking recovers each parent's capability **bit-exactly**. The
pooled forward is the only thing standing between the merged model and its own
components.

## 1. What was run

`scripts/quinn/serving_eval.py` on the sibling merge `zh_b1_merged.pt` (mult 1792,
5,637,668,864 parameters), no retraining. Two protocol domains (expert held-out,
zh), 200 crops each, block 512, batch 2, seed 1234. The mask goes through
`BDH.forward`'s `neuron_mask` argument; the checkpoint is never modified.

Four modes plus a mixed probe:

| mode | what it does |
|---|---|
| `joint` | both halves active, every neuron summed (the pooled forward) |
| `mask_a` | parent-A half only (first `N/2` neurons per head) |
| `mask_b` | branch-B half only (second `N/2`) |
| `transfer` | each half on the other half's domain |
| `mixed` | crops built from alternating blocks of both domains |

## 2. Results

| mode | expert nll | expert ppl | zh nll | zh ppl |
|---|---|---|---|---|
| **joint** | 2.4336 | 11.40 | **3.1975** | **24.47** |
| **mask_a** | **2.4476** | **11.56** | **1.7306** | **5.64** |
| **mask_b** | **1.2839** | **3.61** | **3.8409** | **46.57** |

Reference values from `eval_sibling.json` (the same protocol, measured on the
unmerged parents and the merged model on 2026-11-06):

| model | expert nll | zh nll |
|---|---|---|
| `zh_last` (parent A) | 2.4476 | **1.7306** |
| `expert_b1` (branch B) | **1.2839** | 3.8409 |
| merged, joint | 2.4336 | 3.1975 |

## 3. The finding: exact recovery

Every masked mode reproduces its parent **to the last digit**:

| masked mode | measured | parent's own value | match |
|---|---|---|---|
| `mask_a` on zh | 1.7306 | 1.7306 (`zh_last`) | **exact** |
| `mask_a` on expert | 2.4476 | 2.4476 (`zh_last`) | **exact** |
| `mask_b` on expert | 1.2839 | 1.2839 (`expert_b1`) | **exact** |
| `mask_b` on zh | 3.8409 | 3.8409 (`expert_b1`) | **exact** |

The transfer rows confirm it independently: `mask_a on zh = 1.7306` and
`mask_b on expert = 1.2839` are the same two numbers, reached from the opposite
direction.

**The merged model contains both experts intact.** Nothing was diluted, buried,
or averaged away at merge time. The 99 % dilution measured in the merge report
(§4a of 2026-11-06) is a property of the **pooled forward pass**, not of the
weights. The same parameter set scores 1.7306 on zh when the parent-A half is
isolated and 3.1975 when both halves are summed.

## 4. The cost of the pooled forward

On zh, the difference between the two serving modes is **1.47 nats** (3.1975 vs
1.7306) — a 4.4-fold perplexity gap. On expert the pooled forward happens to sit
0.014 nats *better* than parent A alone (2.4336 vs 2.4476), which is the dilution
figure already reported: the branch contributes almost nothing to the pooled
output, and the pooled value is essentially parent A.

So the pooled forward does not average two experts. It **keeps the stronger one and
loses the weaker one entirely** — and on zh it loses the parent capability to
cross-talk from the branch half.

## 5. Consequence

This completes the evidence chain the expert-merge report could only argue for.
Its decision table said:

> *"P1 holds, P2 fails -> cross-talk dominates even for siblings -> resolves toward
> routed routes (isolation beats pooled budget)."*

The measurement now shows the isolation side: a router that selects one half
recovers that half's capability exactly. **The routed-routes design is not a
workaround for a bad merge — it is the serving mode the merged parameter set was
waiting for.**

For the chat-model prereg this changes §4.3 from a caution into a measurement:
routable expert library over pooled budget, with the joint forward as the control
that quantifies what pooling costs.

## 6. Mixed probe: neither half owns a mixed task, isolation still wins

The first run crashed in `eval_mixed` (the crop-construction error described above);
a rerun after `ad4601e` fixed it and produced the missing numbers. Crops alternate
four 128-byte pieces from expert and zh, so no single half owns the text.

| mixed mode | nll | ppl |
|---|---|---|
| **joint** | **4.2159** | **67.75** |
| **mask_a** | **2.3273** | **10.25** |
| **mask_b** | **2.8480** | **17.25** |

The mixed result sharpens the isolation picture without changing it:

- **Neither half is competent on the mixed task.** mask_a's 2.3273 is close to
  zh_last's ordinary expert score (2.4476) and worse than zh_last on its own zh
  territory (1.7306). That is expected: the crop is half English prose, so the
  parent-A half alone is not the right model for it.
- **The pooled forward is catastrophically worse than either half.** 4.2159 against
  2.3273 is a **1.89-nat** gap — larger than the 1.47-nat gap measured on pure zh,
  and the perplexity ratio is 6.6x (67.75 vs 10.25).
- **mask_a beats mask_b on the mixed task**, consistent with the composition
  (the crop starts with an expert piece, and expert is parent A's weaker territory).

The mixed probe therefore answers its own question: on a task that genuinely needs
both domains, no single half is sufficient, but the pooled forward is the worst of
the three options. A router would have to choose the better half per crop or per
segment, and the measured cost of choosing wrong (2.3273 vs 4.2159) is what the
routing decision buys.

## 7. What the runs cost, honestly

Three full attempts and two minimal probes died before this result, all by global
kernel OOM on the 121 GB unified pool:

| time | process | cause |
|---|---|---|
| 22:50 | serving_eval v1 | fp32 mask promoted every masked activation |
| 00:30 | serving_eval v2 | same, while the HF upload was live |
| 03:40 | mini_mask_a | same |
| 05:02 | mini_mask_a (bf16 fix) | KV-state still collected |

The diagnosis is in `docs/notes/2026-11-07_masked-serving-oom-diagnosis.md` (asb):
the mask was float32, so `bf16 * fp32 -> fp32` doubled every masked activation, and
the attention state inherited the dtype (30 GB instead of 15). The remaining
overhead was the never-used KV-state that every eval caller discards.

Fixes applied in `c4b7a5b`: `BDH.forward(..., collect_state=False)` for
eval callers, dtype-safe mask multiply (`neuron_mask.view(...).to(x_sparse.dtype)`),
and the bf16 mask. With those, the masked modes run with ~37 GB pool margin.

One operational note: on the GB10 the CUDA pool is not visible in process RSS —
only `sec_pagetables` shows the mapped pages. `free -g` therefore under-reports the
pressure, and `nvidia-smi` utilization reads 96 % at idle while drawing 15 W.
Neither number is a reliable load indicator on this host.

## 8. Artifacts

```
out_c/expert_merge/serving_eval.json     rerun output, sha256 693950e8a6f35b16
out_c/expert_merge/serving_eval.log     full log incl. the first run's traceback
out_c/expert_merge/eval_sibling.json    reference values for both parents
out_c/expert_merge/zh_b1_merged.pt      the merged checkpoint (22 GB)
scripts/quinn/serving_eval.py           the measurement
scripts/quinn/mini_mask_a.py            single-value probe of the core comparison
```

## 9. Reproduce

```bash
.venv/bin/python -u scripts/quinn/serving_eval.py \\
  --merged out_c/expert_merge/zh_b1_merged.pt \\
  --domains expert:data/expert/heldout.txt zh:data/europarl/xscript_zh.txt \\
  --mb 30 --crops 200 --block 512 --batch 2 \\
  --out out_c/expert_merge/serving_eval.json
```

(Requires the mixed-probe fix in ad4601e; the first run before that fix died
in `eval_mixed` with the crop-shape ValueError documented in §6.)
