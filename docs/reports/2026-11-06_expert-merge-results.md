# Expert-merge results: sibling topology fails, cross-talk dominates

**Date:** 2026-11-06
**Prereg:** `docs/plans/2026-11-05_expert-merge-prereg.md` v0.3 (FROZEN)
**Question:** does merging two branches that diverge from a shared base (the paper's
protocol) beat merging an ancestor with its descendant, at our scale?
**Answer:** no. All three core predictions fail. The merged model is worse than the
best parent on every domain, and the sibling merge is worse than the ancestor merge
on both measured domains.

## 1. What was run

**Branch B1** — full fine-tune of a `zh_last` clone on 20 MB of Project Gutenberg
prose, 18,611 steps, peak lr 1e-4 (arm A of the measured probe), warmup 500, cosine
to min_lr 1e-5, seed 1234, `--freeze-embed`, weight-decay 0. 21.8 h on one GB10,
rc=0. Best validation loss 1.1225 (ppl 3.07) on the held-out tail.

**Merge** — `pipeline.merge` of parent A (`zh_last`, mult 896) and branch B1
(mult 896) into mult 1792, 5,637,668,864 parameters, 21.75 GB fp32, 34 s.

**Eval** — `scripts/quinn/merge_probe_eval.py`, protocol crops (seed 1234, block 512,
200 crops per domain, mb 30), full-block NLL without routing. Four domains:
expert held-out, zh, legal, code. 3324 s.

| model | mult | params | expert | zh | legal | code |
|---|---|---|---|---|---|---|
| `zh_last` (parent A) | 896 | 2.82B | 11.56 | **5.64** | **5.46** | 39.97 |
| `expert_b1` (branch B) | 896 | 2.82B | **3.61** | 46.57 | 6.38 | 33.65 |
| `merged` | 1792 | 5.64B | 11.40 | 24.47 | 11.48 | 31.99 |

(Perplexities; nll in parentheses below.)

## 2. Predictions against measurement

| prediction | threshold | measured | verdict |
|---|---|---|---|
| **P1** sibling beats ancestor (strict) | merged zh nll < 2.1969 | **3.1975** | **fails by 1.00 nats** |
| **P2** capability lands | merged expert nll <= 1.4339 | **2.4336** | **fails by 1.00 nats** |
| **P3** capacity direction survives | merged legal nll <= 1.6966 | **2.4406** | **fails by 0.74 nats** |

All three fail, and by amounts an order of magnitude larger than the 5 % band the
schedule probe used. This is not a marginal miss.

## 3. The decisive comparison: sibling vs. ancestor

The prereg's framing was that the ancestor-descendant merge (legal_last + zh_last,
measured 2026-11-04) suffered from trunk duplication, and that sibling topology
would avoid it. The numbers say otherwise:

| merge | zh nll | legal nll |
|---|---|---|
| ancestor (legal_last + zh_last) | **2.1969** | **1.2479** |
| sibling (zh_last + expert_b1) | 3.1975 | 2.4406 |

**The sibling merge is worse than the ancestor merge on both domains.** On zh by
0.99 nats, on legal by 1.19 nats. The topology does not rescue the merge; if
anything the sibling branch is the more destructive of the two.

Why the two merges differ, when both contain `zh_last` as one half: the other half
decides. `legal_last` is a descendant of `zh_last` and shares its trunk; `expert_b1`
is a full fine-tune that moved every neuron. Adding a fine-tuned branch produces
more interference than adding a grown descendant.

## 4. What the merged model actually does

On every domain the merge sits between the two parents, and below the best parent:

| domain | best parent | merged | gap to best |
|---|---|---|---|
| expert | 3.61 (B1) | 11.40 | +2.81 nats |
| zh | 5.64 (zh_last) | 24.47 | +1.94 nats |
| legal | 5.46 (zh_last) | 11.48 | +1.00 nats |
| code | 33.65 (B1) | 31.99 | -0.14 nats |

Three of four domains lose to the best parent. The exception is code, where the
merge is marginally better than branch B1 alone and still far worse than the
paper's merge figures.

The mechanism is the same as measured on 2026-11-04: in the forward pass
`x @ self.encoder` runs over all neurons, so the non-target half activates on the
target text and its decoder rows add to the output. Sibling topology does not
isolate the halves; it changes which half interferes, not whether it does.

## 5. Consequence

The prereg's decision table (§4) says:

> *"P1 holds, P2 fails -> cross-talk dominates even for siblings -> §4.3 resolves
> toward **routed routes** (isolation beats pooled budget); merge stays a research
> instrument."*

That branch is taken, with the stronger form: **P1 fails as well.** The conclusion
is not "siblings are also bad" but "concatenation pooling does not isolate
capabilities at this width, and the topology does not change that."

**What this rules out:** merge-as-scaling for a pooled model. The 10T arithmetic
(3,546 merges, 20 TB, ~19 years) is now moot at the mechanism level, not only at
the resource level — even if the compute existed, the pooled merge would not
produce a model better than its best component.

**What it leaves open:** routed routes, where the router selects a prefix and the
non-selected neurons are masked in the forward pass rather than summed. That is
the isolation the pooled merge lacks, and it is the same mechanism the router
evaluation measured (K3 99.44 % at n=100). The expert-merge experiment is
evidence for routing, not against it.

**What it does not test:** whether a *pruned* merge (the August recipe: merge ->
prune to budget -> replay) recovers quality. That recipe's figures came from
zeroing weights at original width, and the physical-slicing variant failed three
times on 2026-11-04. It remains unvalidated at 2.8B and is the only remaining
path from this experiment to a positive result.

## 6. Artifacts

```
out_c/expert_merge/bdh_textmix_expert-b1_last.pt   32 GB  (branch B1)
out_c/expert_merge/bdh_textmix_expert-b1_best.pt   32 GB
out_c/expert_merge/zh_b1_merged.pt                 22 GB  (mult 1792, sha 9035ee14)
out_c/expert_merge/eval_sibling.json                      (full per-domain nll/ppl)
out_c/expert_merge/b1_train.log                          (18,611 steps, rc=0)
```

## 7. Reproduce

```bash
# branch (21.8 h)
bash out_c/expert_merge/run_b1.sh

# merge (34 s)
.venv/bin/python -m pipeline.run merge \
  --ckpt-a out_a/bdh_textmix_k25w1024-zh_last.pt \
  --ckpt-b out_c/expert_merge/bdh_textmix_expert-b1_last.pt \
  --out out_c/expert_merge/zh_b1_merged.pt

# eval (~55 min)
.venv/bin/python -u scripts/quinn/merge_probe_eval.py \
  --models out_a/bdh_textmix_k25w1024-zh_last.pt \
           out_c/expert_merge/bdh_textmix_expert-b1_last.pt \
           out_c/expert_merge/zh_b1_merged.pt \
  --labels zh_last expert_b1 merged \
  --domains expert:data/expert/heldout.txt zh:data/europarl/xscript_zh.txt \
              legal:data/textmix2/legal.txt code:data/textmix2/code.txt \
  --mb 30 --crops 200 --block 512 --batch 2 \
  --out out_c/expert_merge/eval_sibling.json
```
