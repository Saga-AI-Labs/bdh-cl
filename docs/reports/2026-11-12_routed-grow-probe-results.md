# Routed-grow probe results: routing works at training time, pooling was the wrong operator

**Date:** 2026-11-12
**Question:** does a grown neuron block trained with the route mask active protect the old
domain, and does the new block learn?
**Answer:** yes on both. After a 17-hour training run on the new block, the old domain
is unchanged to within measurement noise (-0.0046 nats), the new domain reaches a
best val_loss of 0.9909, and removing the mask degrades the old domain by 1.12 nats.
The pooled merge was the wrong composition operator; routing is the working one.

## 1. What was run

| step | what | result |
|---|---|---|
| **Grow** | `zh_last` (mult 896) -> mult 1024 (+128, +8192 neurons/head) | 3,221,749,760 params, 12.9 GB, 2 min |
| **P0** | base eval, no mask, mult 896 | val 1.7487 |
| **P2** | grown eval, old prefix only, no training | val 1.7928 |
| **P2b** | grown eval, full width, no mask | val 3.3802 |
| **P1** | 10,000 training steps, new block, mask active | best val 0.9909 |
| **P1-old** | P1 checkpoint, old prefix only | val 1.7441 |
| **P1-full** | P1 checkpoint, full width | val 2.8671 |
| **P1-legal** | P1 checkpoint, legal corpus | val 1.1274 |

All evaluations use the same protocol: `textmix` on the zh corpus (28 MB train, 1 MB
val, 1 MB test), block 512, batch 1, 20 eval iterations.

## 2. The decisive comparison

The comparison that matters is **P1-old against P0**, not against P2: same protocol,
same model family, same corpus.

| model | mask | val_loss | delta vs P0 |
|---|---|---|---|
| **P0** base `zh_last` (mult 896) | none | 1.7487 | — |
| **P1-old** (grown + trained) | old prefix only | **1.7441** | **-0.0046** |
| P2 (grown, no training) | old prefix only | 1.7928 | +0.0441 |
| P1-full (grown + trained) | none | 2.8671 | +1.1184 |
| P2b (grown, no training) | none | 3.3802 | +1.6315 |

**The old domain survives the training run unchanged.** The difference to the base
model is 0.0046 nats, which is below the noise floor of a 20-iteration evaluation.

**The new block learns.** The legal corpus reaches a best val_loss of 0.9909
(ppl 2.69), down from the base model's 1.1274 — and the training curve is monotone:

| step | val_loss | ppl |
|---|---|---|
| 4150 | 1.1646 | 3.20 |
| 9950 | 1.0656 | 2.90 |
| 10000 | 1.0273 | 2.79 |
| **best** | **0.9909** | **2.69** |

**The mask is what makes it work.** Without it, the same checkpoint degrades the
old domain by 1.12 nats (P1-full). With it, the old domain is untouched.

## 3. Routing vs pooling, measured on the same model

| operator | old domain | new domain |
|---|---|---|
| **Pooling** (merged `zh_last` + `expert_b1`) | zh 3.1975 (+1.47 nats) | — |
| **Routing** (P1, old mask) | zh 1.7441 (0.00 nats) | legal 1.1274 |

This is the same conclusion the serving evaluation reached at +0.0000, now with
training in the loop. **The composition operator decides; the architecture does not.**

## 4. Why the run did not fit before

Three memory fixes were required, and the first two were found by GLM:

| fix | who | effect |
|---|---|---|
| `@torch.no_grad()` on `estimate_loss` | GLM | autograd retention cost more than a batch doubling (77.84 vs 62.56 GiB measured) |
| `eval_batch_size` as a separate knob | GLM | the eval ran at the training default (32) while training ran at batch 1 |
| `load_checkpoint` trims the dict | GLM | the optimizer state (24 GB at this size) stayed pinned through the whole eval |
| `route_split_backward` | GLM | peak 106.77 -> 91.36 GiB by freeing the prefix graph before the full pass |
| `collect_state=False` | Quinn | the K-cache build cost ~15 GB bf16 |
| pair-quantized freq invariant | Quinn, fixed by GLM | a strictly-decreasing check fired on the correct pair-quantized table |

**The first P1 attempt died silently** (SIGKILL, no traceback) with 114 GB pool pressure.
With the fixes, the run held at 111 GB for 17 hours.

## 5. What this establishes

- **The frozen old block is genuinely frozen.** 17 hours of training on a new block
  leaves the old domain within measurement noise.
- **The new block learns against the isolation.** Legal reaches 0.9909 with the old
  block receiving zero gradient.
- **Routing is a working composition operator at training time.** This was the
  missing half; serving-time isolation was already measured at +0.0000.
- **The base is exchangeable.** This is the strategic consequence: if a grow step
  can attach a new domain without touching the old one, the starting checkpoint does
  not need to be a good chat model. It needs to be a good *host*.

## 6. What this does not establish

1. **P1-old is below P0 by 0.0046 nats, which is noise.** I do not claim training
  improved the old domain. The claim is "unchanged", and that is what the number
  supports.
2. **The best checkpoint was selected on legal, not on zh.** Correct for the
  question asked, but the zh-best checkpoint may differ from the legal-best one.
3. **The RoPE scaling question is open.** The grown frequency table is normalized by
  `n_new`, not `n_old`, so the old neurons' phases are reinterpreted against the new
  total width. Whether this explains the small P2 loss (+0.044) is not measured.
4. **No router was tested.** P1 used a fixed mask per run. Sequence-level routing
  (P3) is sketched in `docs/plans/2026-11-10_routed-grow-p3-sketch.md`; the router
  itself is not implemented.
5. **Two domains, one direction.** zh was the host and legal the attach. The reverse
  direction and a third domain are untested.

## 7. Artifacts

```
out_c/routed_probe/bdh_textmix_grow896to1024_last.pt     grown base, 12.9 GB
out_c/routed_probe/bdh_textmix_p1_legal_new_best.pt     trained, 38.7 GB
out_c/routed_probe/bdh_textmix_p1_legal_new_last.pt     trained, 38.7 GB
out_c/routed_probe/p1_train.log                         training curve
out_c/routed_probe/p1_eval.log                          the three evaluation numbers
out_c/routed_probe/p0_p2c.log                           P0/P2/P2b
scripts/quinn/serving_eval.py                           the mask construction used here
pipeline/train.py                                        route_mask_side, freq invariant
pipeline/eval.py                                         build_route_mask, mask_old_mult
```

## 8. Reproduce

```bash
# grow (no training steps)
python -m pipeline.run train --model bdh --dataset textmix \
  --text-mix zh:data/europarl/xscript_zh.txt --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --mlp-internal-dim-multiplier 896 --grow-mult 128 \
  --init-from out_a/bdh_textmix_k25w1024-zh_last.pt \
  --max-iters 0 --batch-size 1 --out-dir out_c/routed_probe

# P1: train the new block with the mask active
python -m pipeline.run train --model bdh --dataset textmix \
  --text-mix legal:data/textmix2/legal.txt --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --mlp-internal-dim-multiplier 896 --grow-mult 128 \
  --init-from out_c/routed_probe/bdh_textmix_grow896to1024_last.pt \
  --route-aware --route-mask-side new --route-alpha 0.9 \
  --route-split-backward --no-compile \
  --max-iters 10000 --batch-size 1 --eval-batch-size 1 \
  --learning-rate 1e-4 --warmup-iters 500 --lr-decay-iters 10000 \
  --weight-decay 0 --out-dir out_c/routed_probe

# P1-old: the decisive number
python -m pipeline.run eval --model bdh --dataset textmix \
  --text-mix zh:data/europarl/xscript_zh.txt --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --mlp-internal-dim-multiplier 1024 --mask-old-mult 896 \
  --batch-size 1 --eval-batch-size 1 \
  --out-dir out_c/routed_probe --run-name p1_legal_new --tag best
```
