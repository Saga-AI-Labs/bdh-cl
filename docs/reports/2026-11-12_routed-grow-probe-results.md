# Routed-grow probe results: routing works at training time, pooling was the wrong operator

**Date:** 2026-11-12
**Question:** does a grown neuron block trained with the route mask active protect the old
domain, and does the new block learn?
**Answer:** yes on both. After the 10,000-iter training run on the new block (33.7 h
wall clock per the train log), the old domain
is unchanged - within measurement noise at the random-crop instrument (-0.0046
nats), and the same-day full-coverage re-measure makes it bit-exact (section 13).
The new domain reaches a
best val_loss of 0.9909, and removing the mask degrades the old domain by 1.12
nats (+0.79 nats re-anchored at full coverage, same tag).
The pooled merge was the wrong composition operator; routing is the working one.

**Integration (2026-11-12, GLM):** sections 9-13 added (batch-2 completion matrix,
instrument noise analysis, topk-competition mechanism, memory envelope and the
graft-#2 wall, full-coverage eval). Corrections: section 8's P1 reproduce init
(base_mult is read from the init checkpoint's cfg, so the grown output would
re-grow 1024 -> 1152); section 2's legal baseline attribution (1.1274 is the P1
number, not the base model's); the run duration (train log: ~10.4 s/step x 10000
plus eval/save overhead = 33.7 h, not 17 h). Evening update: the full-coverage
re-measure landed (section 13) - the zh verdict is bit-exact (A=B=C), the
section-11 topk-competition claim was withdrawn (k_sparse_ratio = 0 in all
cfgs: no topk runs), and the P3 isolation requirement flips to "a sequence-level
router suffices" on the ReLU path.

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
  (Full-coverage addendum: empirically void for these models - the grown masked
  forward is bit-identical to the base model's, A = C in section 13, so no
  RoPE-phase penalty is measurable and the +0.044 was instrument noise.)
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

## 11. Mechanism, corrected: the mask fully isolates in these runs (GLM, same-day correction)

Earlier today this section claimed the k_sparse topk runs over the full N axis
with the mask applied after selection (bdh.py:22/:262/:278), so a foreign block
would compete for topk slots and a sequence-level router would not give clean
isolation. The full-coverage re-measure (section 13) falsified the premise:
cells A, B and C came back identical to all printed digits across three
different checkpoints. The cfg check shows why: **every checkpoint in this probe
carries k_sparse_ratio = 0.0** (verified in grow, P1 and zh_last), so
`_k_sparse_relu` is never invoked - the models run the plain-ReLU path and the
neuron mask is a plain elementwise zeroing after a pointwise operation. With the
old parameters bit-copied by the grow and frozen through training, the masked
forward IS the base model's forward. There is no selection, hence no
competition, hence exact isolation by construction.

The general rule for k-sparse models stands in the code (bdh.py:12-18,
retraction 6754e83, derivation section 8): while k_sparse_ratio > 0, neither
masking order nor zero-init of new neurons restores forward exactness across a
growth step; sparse growth requires holding k ABSOLUTE (freeze pre-growth k, or
rescale the post-growth ratio to rho*N/N').

P3 implication (flipped from this morning): on the current ReLU-path models, a
sequence-level router that selects the mask per sequence (sketch option A) IS
sufficient for clean isolation - the pre-topk side-scoping requirement is
withdrawn. If k_sparse is ever enabled, the retraction's k-absolute growth rule
governs and the competition question returns.

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

## 13. Full-coverage eval: implemented (e42e8c5); the zh verdict is bit-exact

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

Results (2026-11-12 17:35-23:07, `p1_fullcov.log`, batch 4, 1953 blocks per
split, 999,936 of 1,000,000 bytes covered, 64-byte tail uncovered):

| cell | checkpoint | mask | val | test |
|---|---|---|---|---|
| A | grow (step 0) | 896 | 1.7603 | 1.6980 |
| B | P1 (step 10000) | 896 | 1.7603 | 1.6980 |
| C | P0 base (mult 896) | none | 1.7603 | 1.6980 |
| D | P1 (step 10000) | none | 2.5488 | 2.4933 |

**A, B and C are identical to all printed digits** (all six val/test numbers).
With k_sparse_ratio = 0 in every cfg (section 11) the masked forward of the
grown and the trained checkpoint is the base model's forward, up to
matmul-association effects (~1e-8; the smoke measured 2.2e-9 for a batch-shape
change alone). The survival verdict is therefore not "within noise" but exact:

- **Zero forgetting, bit-exact.** 10,000 iters of legal training changed nothing
  measurable in the old-prefix forward: B = A to all printed digits, and A = C
  means the grow itself (under the mask) also reproduces P0's forward exactly.
  The registered P1 zh margins (0.0075/0.0338) and the P2 +0.0441 were
  instrument noise around a true delta of 0 (section 10).
- **The pair-quantized freq invariant (ddf62e4) is verified at full scale:**
  A = C shows the grown frequency handling preserves the old neurons'
  computation bit-faithfully at the 3.2 B scale; the section-6.3 RoPE concern
  is empirically void for these ReLU-path models.
- **The mask is load-bearing, cleanly measured:** D - B = +0.7885 val /
  +0.7953 test. Without the mask, the trained block's contributions cost
  ~0.79 nats on zh (section 2's +1.12 compared tag-best against the b1
  instrument; same conclusion, now anchored at same-tag full coverage).
- Generation runs unmasked in every cell, so the samples show full-width
  behavior: A/C produce zh word-salad, B/D produce fluent legal-flavored
  English on the zh prompt - the trained block dominates generation whenever
  it is active, which is exactly what the router in P3 must gate per sequence.

zh verdict: **PASS, exact.** The survival criterion (val <= 1.7928) is met with
the true margin being 0.0000 +/- ~1e-4 rather than a noise-band coin flip.

## 14. P3 executed: mixed training with per-step routing (GLM, 2026-11-15)

Run per the amended prereg (5daf30c + amendments of 2026-11-13, commits
1013ea1/00018ad): init = 896 parent + `--grow-mult 128` (D1'), strict
alternation legal (dom A, side=new, even steps) / zh (dom B, side=old, odd
steps) (D2/D3), P1 envelope with wd 0 + step-end restore (D4), 10,000 iters,
b1 route-aware split-backward. Wall clock: Nov 13 05:26 -> Nov 15 01:20
(~44 h: 31.0 h train at 10.4 s/step, four fullcov cells ~1.4 h each, full
router certification ~7.1 h). All gates passed pre-run (G0/G1/G2/G3, prereg
section 4/10); G2's registered expectation was corrected pre-run: on the
untrained grow ckpt the argmin router routes everything to old (the random
new block degrades full-width everywhere), which is the geometrically correct
pre-training state - the A-side flip is an outcome of training, not a
pre-condition.

Post-run full-coverage matrix (all `--eval-deterministic --eval-batch-size 4`,
the identical instrument as the baseline cells; last checkpoint, step 10000,
like-for-like with the P1 anchor which is also a last-tag ckpt):

| cell | mask | val | test | registered comparator |
|---|---|---|---|---|
| S1: zh @ old prefix | 896 | **1.7603** | **1.6980** | == A=B=C (1.7603/1.6980) bit-exact |
| desc: zh @ full | none | 1.7470 | 1.6858 | P1: 2.5488/2.4933 (D-cell +0.7885/+0.7953) |
| S2: legal @ full | none | **1.1178** | 1.1250 | <= 1.1994 (P1 anchor 1.0994 + 0.10); hard floor 1.7087 |
| desc: legal @ old prefix | 896 | 1.7087 | 1.7091 | == base-on-legal (G1) bit-exact |

**Verdicts:**

- **S1 PASS, bit-exact (zero tolerance).** 10,000 mixed steps with per-step
  side routing left the old-prefix forward identical to all printed digits -
  the same regression as section 13, now under the routing regime. The
  snapshot/restore guarantee (not `wd 0` alone) carried it, as G3 certified
  at tiny scale.
- **Second bit-exact regression, free of charge:** legal @ old prefix =
  1.7087/1.7091 == base-on-legal (G1 cell 1) to all printed digits. The
  frozen prefix is a perfect base-model replica for BOTH domains after the
  run; combined with S1 this is the full isolation identity, measured.
- **S2 PASS.** 1.1178 <= 1.1994 with 50 % of the steps spent on the other
  domain; +0.018 nats over pure P1 (1.0994) is the measured price of mixed
  training on the fullcov instrument. The hard floor (<= base-on-legal
  1.7087) holds by 0.59 nats.
- **S4 PASS, routed below oracle.** Routed mixed-stream NLL 1.4329 val /
  1.4063 test vs oracle 1.4390/1.4115 (delta -0.0061/-0.0052, threshold
  +0.05). The router instrument cross-validates the post cells: its oracle
  means equal the S1/S2 cell numbers to ~0.002.
- **S3 MISS as registered (diagnostic, per the section-5 reading rule), and
  the miss is the finding:** accuracy 60.60 % val / 62.39 % test against the
  registered label map (A->full, B->old). Decomposition: the A-side flip
  emerged exactly as predicted - 99.69 %/99.49 % accuracy, margin median
  +0.54 nats (full beats old on legal once the new block is trained). The
  B-side "misses" route zh to FULL (78 % of zh val blocks, 75 % of test): full-width zh
  (1.7470/1.6858) now deterministically beats the frozen old prefix
  (1.7603/1.6980) by 0.0133/0.0122 nats. The registered oracle map (zh->old)
  went stale mid-probe - in the good direction.
- **Against the true optimum, the router is AT the NLL optimum, not short of
  it.** The registered oracle understates the router because it encodes the
  pre-run map. Post-run, the per-domain optimum is full-width for BOTH
  domains, so the best fixed policy ("always full") scores
  (1.1178 + 1.7470)/2 = 1.4324 val / (1.1250 + 1.6858)/2 = 1.4054 test. The
  router scored 1.4329/1.4063 - within +0.0005/+0.0009 nats of that bound.
  The true per-block optimum lies at or below the always-full bound (a
  minority of zh blocks favors old: margin min -0.4464 val / -0.2681 test),
  and the router's old-prefix routes were genuine recoveries of exactly those
  blocks (routed-B 1.7478/1.6867, BELOW the old-prefix block mean
  1.7603/1.6980 - selection, not window noise). S4 passes under both maps:
  1.4329 <= 1.4390 + 0.05 (registered oracle) and <= 1.4324 + 0.05 (true
  optimum bound). The S3 accuracy threshold (>= 95 %) measures agreement with
  a map this run itself falsified; reading the 60 % as a routing deficit
  would invert the result.

**The D-cell penalty collapsed.** Section 13 measured full-width zh at
+0.79 nats over the old prefix for P1 (the trained block's zh ignorance).
After P3's 10 %-weighted zh exposure on odd steps, full-width zh is
1.7470/1.6858 - 0.013 nats BELOW the old prefix. The new block learned the
host domain through exposure alone, well enough to edge out the frozen
specialist on the fullcov instrument. "Host + attach" extends to "attach
learned the host too".

**Deployment reading (registered as a policy choice, not an NLL fact):**
per-block argmin over the two masks is NLL-safe by construction (it can only
pick the better mask per block; hence routed <= oracle in S4 under BOTH the
registered and the true map). NLL-wise the post-run optimum policy is
"always full" (1.4324/1.4054), which the router matches to +0.0005/+0.0009
while keeping the ability to flip an individual block to the old prefix when
its window favors it. But if the deployment requirement is the bit-exact
guarantee (zh served by the frozen old block, identical to base by S1), the
zh->old route remains available at a measured cost of +0.013 nats. Which one
to ship is a policy decision the probe was designed to inform, not to make.

Notes for reproduction: (1) with `--log-interval 10` the dom markers sample
only odd steps (9, 19, 29, ...), so the long-run log shows only `dom B` -
alternation is verified by G0/tiny at `--log-interval 1` (A,B,A,B observed)
and by the outcomes (S1 bit-exact requires the zh side; S2 landing requires
the legal side). (2) best checkpoint landed at step 7600 (best_val 1.0333 on
the in-loop b1 random-crop instrument, 1.70 -> 1.03 trajectory); post cells
measure the last checkpoint, matching the P1 anchor's tag. (3) Disk stayed
bounded as registered (best + last, 38.65 GB each, fixed paths).

Artifacts: `out_c/routed_probe/p3_run.log` (train + post + inline S1 QA),
`p3_post_{s1_zh896,zh0,legal0,legal896,router}.txt`, `p3_g1.log` (anchors),
`p3_g2_router.log` (grow-ckpt router state), ckpts `bdh_textmix_p3_mixed_{best,last}.pt`.
Implementation: 1013ea1 (mixed-alternate + router + prereg amendments),
00018ad (router b4-chunking, G0/G2 records).

P3 verdict: **S1 exact, S2 pass, S4 pass, S3 diagnostic miss = stale oracle.**
The probe's central question - does per-step routed mixed training preserve
the host bit-exactly while the attach domain lands - is answered yes, and the
router story is better than registered: the full model became the best server
for both domains.
