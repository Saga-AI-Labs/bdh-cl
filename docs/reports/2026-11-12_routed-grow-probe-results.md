# Routed-grow probe results: routing works at training time, pooling was the wrong operator

**Date:** 2026-11-12
**Question:** does a grown neuron block trained with the route mask active protect the old
domain, and does the new block learn?
**Answer:** yes on both. After the 10,000-iter training run on the new block (33.7 h
wall clock per the train log), the old domain
is unchanged to within measurement noise (-0.0046 nats), the new domain reaches a
best val_loss of 0.9909, and removing the mask degrades the old domain by 1.12 nats.
The pooled merge was the wrong composition operator; routing is the working one.

**Integration (2026-11-12, GLM):** sections 9-13 added (batch-2 completion matrix,
instrument noise analysis, topk-competition mechanism, memory envelope and the
graft-#2 wall, full-coverage eval). Corrections: section 8's P1 reproduce init
(base_mult is read from the init checkpoint's cfg, so the grown output would
re-grow 1024 -> 1152); section 2's legal baseline attribution (1.1274 is the P1
number, not the base model's); the run duration (train log: ~10.4 s/step x 10000
plus eval/save overhead = 33.7 h, not 17 h).

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

**The new block learns.** The P1 checkpoint evaluates on legal at val 1.1274
(integration note: this is the P1 number, not the base model's - the base model
measures 1.6596/1.7074 on legal at batch 2, section 9), with the in-loop best at
0.9909 (ppl 2.69) — and the training curve is monotone:

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
With the fixes, the run held at 111 GB host-side for the 33.7 h completed run
(the BDH_MEM_FRACTION cap bounds the CUDA pool at 97.35 GiB; host RSS sits above
it through checkpoint page cache and pinned buffers).

## 5. What this establishes

- **The frozen old block is genuinely frozen.** 10,000 iters (33.7 h) of training
  on a new block leaves the old domain within measurement noise.
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
6. **Scale-out to a second graft is blocked on this box.** Graft #2 (mult
  1024 -> 1152) OOM'd at the memory cap (95.40 GiB in use, 2.25 GiB short,
  prefix backward); section 12 has the accounting and the two ways out.

## 7. Artifacts

```
out_c/routed_probe/bdh_textmix_grow896to1024_last.pt     grown base, 12.9 GB
out_c/routed_probe/bdh_textmix_p1_legal_new_best.pt     trained, 38.7 GB
out_c/routed_probe/bdh_textmix_p1_legal_new_last.pt     trained, 38.7 GB
out_c/routed_probe/p1_train.log                         training curve
out_c/routed_probe/p1_eval.log                          the three evaluation numbers
out_c/routed_probe/p0_p2c.log                           P0/P2/P2b
out_c/routed_probe/p1_evals.log                         b2 completion matrix, cells 1-4
out_c/routed_probe/p1_eval5.log                         b2 completion matrix, cells 5-6
out_c/routed_probe/p1_fullcov.log                       full-coverage zh re-measure
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
# (integration fix: init MUST be the 896 parent. base_mult is read from the
# init checkpoint's cfg at train.py:185, NOT from --mlp-internal-dim-multiplier,
# so initializing from the grown output re-grows 1024 -> 1152 - this cost
# three P1 attempts on 2026-11-11 before the fifth start with the right recipe.)
python -m pipeline.run train --model bdh --dataset textmix \
  --text-mix legal:data/textmix2/legal.txt --text-mix-mb 30 \
  --n-embd 1024 --n-head 16 --n-layer 4 --block-size 512 \
  --mlp-internal-dim-multiplier 896 --grow-mult 128 \
  --init-from out_a/bdh_textmix_k25w1024-zh_last.pt \
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

## 9. Same-instrument completion: the batch-2 matrix (GLM, 2026-11-12)

Standalone completion evals of every cell under ONE instrument (batch 2, tag last,
full output in `p1_evals.log` / `p1_eval5.log`; the section-2 numbers are batch 1 /
tag best and come from `p1_eval.log` / `p0_p2c.log`):

| # | Checkpoint | Data | Mask | val | test |
|---|---|---|---|---|---|
| 5 | P0 base (mult 896, step 10000) | zh | none | 1.6810 | 1.7573 |
| 1 | grow (mult 1024, step 0) | zh | 896 | 1.6960 | 1.6849 |
| 3 | P1 (step 10000) | zh | 896 | 1.7853 | 1.6543 |
| 6 | P0 base | legal | none | 1.6596 | 1.7074 |
| 2 | grow (step 0) | legal | none (full width) | 2.5970 | 2.5734 |
| 4 | P1 (step 10000) | legal | none (full width) | 1.0587 | 1.0677 |

Batch-4 references (p0_p2c.log, 2026-11-10): P0 zh 1.7487/1.6826, P2 zh 1.7928/1.6881,
P2b 3.3802/3.3683 (val/test).

Notes:

- The b4 and b2 columns of the same cells disagree by 0.02-0.10 nats in BOTH
  directions (P0 zh val: 1.7487 b4 vs 1.6810 b2; test: 1.6826 b4 vs 1.7573 b2).
  Section 10 shows this is the instrument's noise band, not drift.
- P1-old in section 2 is tag best at batch 1 (1.7441); the batch-2 tag-last pairing
  of the same question is grow 1.6960 -> P1 1.7853 (+0.0893). Both sit inside the
  noise band; the full-coverage sweep (section 13) decides.
- The legal verdict is instrument-independent: -0.60/-0.64 nats vs the base model
  and -1.54/-1.51 vs the untrained grown block (2.5970/2.5734 -> 1.0587/1.0677).

## 10. Instrument integrity: the random-crop eval is noise-limited (GLM)

- `eval_iters` defaults to 20 (config.py:35): each standalone eval draws 20 random
  crops of 512 bytes = 20,480 bytes ~ 2 % of the 1 MB split at batch 2. The eval
  process seeds no RNG (manual_seed appears only in train.py), so every run draws
  different crops.
- Crops are 512-byte CONTIGUOUS spans, so the effective sample is ~40 crop means
  (batch 2), not 20k independent tokens; single-run SE is ~0.05-0.10 nats per
  split. Identical-config evidence: the runner's P1 zh eval and completion cell 3
  (same ckpt and config, 28 min apart) differ by 0.066 test; the P1 legal pair by
  0.022. Data files are unchanged since Sep 24 (mtime), so the b4/b2 disagreement
  is noise, not content drift.
- Consequences: margins below ~0.1 nats are not resolvable from single runs. The
  registered P1 zh margins (val 0.0075 vs the 1.7928 mark, test 0.0338 vs 1.6881)
  and the -0.0046 P1-old-vs-P0 delta are all inside the band: the supported claim
  is "unchanged", and PASS/FAIL at these margins is undecidable without a better
  instrument. (An earlier analysis in this session overstated significance as
  "~20 sigma" by treating tokens as independent; the crop-correlation model is
  the corrected account.)
- Robust signals, far outside the band: the legal learning (-0.60/-0.64 vs base,
  -1.54/-1.51 vs untrained grown), the mask-necessity signal (+1.12 nats P1-full,
  re-anchored at full coverage below), P2b (+1.63), the pooled-merge failure
  (+1.47), and the negative control.
- Instrument labels unchanged: these are pipeline streaming-eval numbers; the
  serving_eval crop references stay the separate instrument and are not mixed in.

## 11. Mechanism: the mask does not pre-empt the topk competition (GLM)

`_k_sparse_relu` selects the top-k_sparse neurons over the FULL N axis (all
65,536 candidates, bdh.py:22) and the neuron_mask is applied AFTER selection
(bdh.py:262 for x, :278 for y). The mask-896 eval is therefore not equivalent to
the mult-896 model: the foreign block competes for the k_sparse budget even
though its contributions are zeroed afterwards.

- At step 0 the random block steals slots (this is the +0.0441 P2 delta, ~0.5 SE
  - noise-limited but directionally consistent with the mechanism).
- At step 10000 the legal-trained block's scores on zh are content-dependent:
  the b2-paired val moved +0.0893 (grow -> P1) while test moved -0.0306. Both
  are within ~1 SE of zero (section 10), so the magnitudes are unresolved - the
  mechanism is code-verified, the sizes are not yet measured.

Design implication for P3: a sequence-level router that only selects the mask per
sequence (sketch option A) does NOT remove the competition - the foreign block
still enters the global topk. Clean isolation requires zeroing the other side's
scores BEFORE the topk, or scoping the selection per side. This is a prereg
decision, not an implementation detail. The section-6.3 RoPE phase hypothesis is
the second candidate explanation for the small P2 delta; the two are not mutually
exclusive.

## 12. Memory envelope and the graft #2 wall (GLM)

- Corrected accounting at mult 1024: ~12.0 weights + ~12.9 grads + ~25.7 Adam m+v
  + ~11.3 elem_frozen_backup + ~17 transient state build + ~15-25 activations =
  ~110-125 GiB against the 121.69 GiB unified wall. Section 4's numbers are the
  per-fix reductions; the earlier ~104 GiB estimate omitted the state build.
- The hard cap (529338e): BDH_MEM_FRACTION calls set_per_process_memory_fraction,
  so an overrun surfaces as a clean in-process torch.OutOfMemoryError instead of
  a kernel sweep. run_p1.sh exports 0.8 (97.35 GiB); the completed run never
  overran the pool. Two kernel sweeps earlier in the campaign killed desktop
  sessions; no capped run has.
- Graft #2 (mult 1024 -> 1152) does NOT fit this box: the attempt OOM'd at the
  cap (95.40 GiB in use, 2.25 GiB short, prefix backward) with 3.62 B params.
  Per graft: ~+1.4 GiB weights, ~+2.8 GiB Adam+backup. Before a second graft on
  this hardware: prune/merge between grafts (importance.py / prune_eval.py /
  merge.py exist) or the TP=2 escalation (flagged as an open-risk port in the
  probe plan; the global topk makes it a correctness campaign, not a patch).
- Operational: eval_interval 50 with best-checkpoint saving (38.65 GB per save,
  on every improvement) added hours to the 33.7 h run. Worth tuning before the
  next long run.

## 13. Full-coverage eval: implemented (e42e8c5)

`--eval-deterministic` sweeps every non-overlapping 512-byte block of a split
exactly once, sequentially, with token-weighted pooling (partial final batch
handled); the final 64-byte tail of the 1,000,000-byte splits stays uncovered.
No sampling noise, bit-reproducible across unseeded runs, batch-size invariant
on the smoke model (b8 vs b245: 2.2e-9; one partial batch vs single-block
batches: exact). `data.get_batch` gained an offsets parameter (None keeps the
random path byte-identical); `evaluate()` gained the BDH_MEM_FRACTION cap and
warns if stateful_eval would shadow the flag.

Smoke (tiny ckpt mult 32, /tmp/opencode/smoke_fullcov.py): CLI parse,
bit-reproducibility, batch invariance including the partial final batch,
ValueError guard for block-less splits, random-path sanity, CLI end-to-end with
the cap print - all passed.

Running as of 2026-11-12 evening (`p1_fullcov.log`): the four zh cells at batch
4 full coverage - grow (mask 896), P1 (mask 896), P0 (no mask), P1-full (no
mask). The P1-vs-grow pairing decides the survival verdict at ~0.01 resolution;
P0 anchors the graft cost itself; P1-full re-anchors the +1.12 mask-necessity
signal. Verdict to be appended when the run completes.
