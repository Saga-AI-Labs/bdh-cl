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
| **P1b** home band (soft) | merged zh nll <= 2.03 | **3.1975** | **fails by 1.17 nats** |
| **P2** capability lands | merged expert nll <= 1.4339 | **2.4336** | **fails by 1.00 nats** |
| **P3** capacity direction (v0.3 sharpened) | merged legal nll <= 1.2479 | **2.4406** | **fails by 1.19 nats** |

**Four of four core predictions fail.** Against the frozen v0.3 thresholds, not the
v0.1 ones: P3 was sharpened from <= 1.6966 to <= 1.2479 (the ancestor merge's own
legal nll) because clearing the old bar would have established nothing beyond a
confounded merge. The failure is stronger under the sharper gate, not weaker.

All misses are ~1 nat, an order of magnitude beyond the 5 % band the schedule probe
used. This is not a marginal result.

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

| domain | best parent (nll) | merged (nll) | gap to best |
|---|---|---|---|
| expert | 1.2839 (B1) | 2.4336 | **+1.15 nats** |
| zh | 1.7306 (zh_last) | 3.1975 | **+1.47 nats** |
| legal | 1.6966 (zh_last) | 2.4406 | **+0.74 nats** |
| code | 3.5159 (B1) | 3.4654 | **-0.05 nats** |

Three of four domains lose to the best parent; on code the merged model is the best
of the three (3.4654 against B1's 3.5159 and zh_last's 3.6882). The gaps are in nats,
computed from `eval_sibling.json`, not read off the perplexity column. The code win
is 0.05 nats against 1-nat failures elsewhere and does not soften the verdict; it
does mean the sentence "worse than the best parent on every domain" would be wrong,
and it is corrected here.

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

## 5a. Open items: P4 and P5

Two of the five preregistered predictions remain unmeasured. Both are recorded
here rather than left out, because "not run" and "ran and failed" are different
results.

**P4 (QAT gate, ≤ 0.1 nats B2 vs B1) — not run.** It was scheduled to run in
parallel with B1 on the second Spark, which never happened: B1 consumed the only
free GPU for its full 21.8 h, and B2 requires the Q1 probe (0.3M, ≤ 0.1 nat) to be
green first under the QAT proposal's binding ordering. The Q1 probe itself was never
started. Neither the probe nor B2 was blocked by a measurement result; the schedule
simply did not free a GPU. Ordering stands either way.

**P5 (repaired-prune control, ≤ 7.0 ppl both domains, no replay) — failed three
times, documented, not a measurement of pruning.** The control requires that the
pruning instrument itself degrade a never-merged model only mildly. All three
attempts on 2026-11-04 degraded the unmerged `zh_last` catastrophically:

| attempt | variant | zh 896->448 result |
|---|---|---|
| 1 | per-head indices, freqs sliced | crash (5-D vs 4-D) |
| 2 | shared indices, freqs sliced | 5.64 -> 21.78 |
| 3 | shared indices, freqs recomputed | 5.64 -> 57.48 |

Attempt 2 used the UNMERGED parent, so the degradation cannot be blamed on cross-talk
from a merge. The likely cause, recorded but untested: `scripts/prune_eval.py`, which
produced the August merge->prune->replay figures, ZEROES encoder/encoder_v/decoder at
the ORIGINAL width and keeps the config. The August numbers were therefore measured on
a zeroed model, not a physically narrower one, and slicing produces a different
architecture whose behaviour is unknown.

**Why P5 is not the next step.** The measured result of this report is that pooled
concatenation produces cross-talk that dominates capability. Pruning removes neurons;
it does not stop the surviving neurons of both halves from co-activating and summing.
So a successful prune+replay would have to demonstrate recovery of a deficit that the
measurement suggests pruning cannot cause and cannot cure. It remains the only path
from this experiment to a positive result, but it should be treated as a separate
hypothesis with its own preregistered success criterion, not as a loose end of this
one. GLM's proposed criterion is sound and worth adopting: **recovered >= best parent
on both domains (zh 5.64 / legal 5.46)** — anything less and the honest move is to
serve the untouched parent, which must first justify itself against doing nothing.

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
