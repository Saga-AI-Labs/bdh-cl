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

**Late addition (2026-11-18):** sections 16-18 register the word-salad
diagnosis (16: the observation and the coherence question; 17: the cause
ranking, plus a correction to 16's pass-count arithmetic - starvation,
not memorization; 18: three no-training controls and the cost envelope -
the network scores below a 6-gram on its own register, and the direct
data-scale route is excluded on this hardware; 18.6: review round 2 -
NLL is not a coherence gate, the 100M route is a hypothesis, and the
route-aware step cost is a measured 2.0x). The base-control salad cells (legal x old-mask) measure
the model's zero-exposure baseline in a register it never saw - inherent,
not graft-induced. Cause ranking: token-view starvation is DOMINANT (5.12
MB token-views per 10k-iter phase vs 3.62 B params; ~0.18 sightings per
512-B block per phase, ~0.37 cumulative on legal), the 512-B byte context
is secondary, zero dialogue data is categorical but moot until fluency -
and it is NOT overfitting (val/test gaps 0.007-0.061 nats). Chat
capability is out of reach for this training regime; the graft mechanism
is not the blocker.

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
learned the host too". Note: this is a teacher-forcing result; it does NOT
transfer to generation (see the deployment reading below).

**Efficiency accounting (review, 2026-11-15):** the zh exposure was 5,000 odd
steps at 0.1 loss weight - a gradient-weight equivalent of ~500 full-weight
steps. That is the budget that moved full-width zh from +0.79 (P1
interference) to -0.013 (marginal complementarity): a 0.80-nat swing in
~500 effective steps. Two precisions registered with it. (1) What the new
block learned is **complementarity to an expert host**: the odd-step full
term trains the new neurons against an already-expert old block that carries
the zh representations, so the new block did not re-learn zh from scratch -
it had to stop interfering and add marginal value. Attach learning is
complement learning, and complement learning is cheap; that is the mechanism
behind "attach learned the host too", and it is the reason to expect the
same economy for further domains. (2) The equivalence is a gradient-weight
accounting, not an Adam dynamics proof: with the even (legal) steps running
at ~1.0 effective weight, the second-moment accumulator and the momentum
carry-over are dominated by the 10x larger legal gradients, so the exact
per-step zh update size is fuzzy - the 500-step figure is the honest order
of magnitude, not an exact step count. (3) Scope: the measured claim is the
joint full-width zh forward (old + new); the new block's standalone zh
competence was not measured (a zh @ new-only cell would require a
mask keeping only neurons [57344, 65536) - trivially available if wanted).

**Deployment reading (revised 2026-11-15, review: NLL-optimality is not
deployment-optimality).** Every NLL in this report is teacher-forced. In the
generation regime the run's own samples refute the TF ordering: section 13's
observation ("B/D produce fluent legal-flavored English on the zh prompt")
persists on P3. The zh@0 post cell's unmasked samples are fluent English
legal text ("The present of the case of the part of the service a respect of
the constituted ..."), on the same zh-prompt seed regime where the base model
produced zh word-salad (A/C in section 13). The trained block's English prior
dominates the sampling dynamics regardless of the 0.013-nat TF zh edge. For
a chat application this is a functional failure, not a policy tradeoff: a
Chinese user would receive English legal text. **zh->old is therefore
functionally mandatory for chat serving, and the +0.013 nats are the price
of correctness, not a weighing.** Consequences registered: (a) the chat
serving map is domain-aware (zh->old), enforced by request labels or a
language gate - the NLL-argmin router is the teacher-forcing story, not the
deployment mechanism; (b) generation must become mask-aware (`generate()`
samples unmasked in every cell today) - that primitive is the actual
serving-integration work item; (c) the 60 % S3 accuracy is a TF-instrument
fact, irrelevant to chat routing.

**Deployment reading, second revision 2026-11-15 (mask-aware generation
validation, `scripts/gen_serve_check.py`, commits 17664f6/8f1cb0d).** The
functional-failure claim above is PROMPT-REGIME-BOUND, and the bound
decides the deployment question. Every sample behind the failure used the
eval's fixed ASCII prompt (`"\n = The "`), which encodes a legal-document
register - the model continues that register regardless of the domain
trained on. With a real zh prompt cut from the zh HELD-OUT split (80 bytes
of the val carve), the full-width P3 model produces CHINESE on every
sample (5/5, 98-100 % of generated bytes >= 0x80) - the registered
English-legal failure does not occur; a Chinese user typing Chinese
receives Chinese. The old mask (= base) also produces Chinese on 5/5
samples. Honest reading of the two cells: both are europarl-flavored
word-salad at COMPARABLE quality - the tentative single-sample impression
that full-width Chinese is more fluent did NOT survive 5 samples, so the
0.013-nat TF edge remains the only measured mask difference on zh (and it
favors full). On the ASCII legal prompt the registered picture holds:
full produces fluent English legal (the P3 competence, matching its 1.1178
NLL), old produces degraded English word-salad (base level, matching its
1.7087) - generation quality tracks the NLL ladder on legal. Corrected
consequences: (a) for realistic chat serving the language-failure argument
for zh->old does NOT hold; the NLL-optimal "always full" policy is also
generation-correct in language terms, so the chat serving map simplifies
to "always full" with zh->old retained as the bit-exact-base option
(reproducibility guarantee, not a functional necessity); (b) the
mask-aware generation primitive is validated regardless - per-cell behavior
is mask-consistent on 5/5 samples - and stays the drift instrument for
post-graft checks; (c) the open mixed-content case stands: an English
system prompt plus Chinese user content is exactly the regime where a
static map can be wrong again - window-level routing territory (the
router's reserved role).

**Deployment reading, third revision 2026-11-18 (the mixed-content case
quantified; `gen_serve_check` mixed cells, 59c880e, 5 x 200 tokens per
cell, both checkpoints, `/tmp/opencode/mixed_serve_check.log`).** Design:
the SAME 80-B zh content with an English chat system prompt prepended,
repeat-and-truncated to en:zh byte ratios 1:1 (80 B en), 2:1 (160 B en),
1:2 (40 B en); each ratio under full, old-mask 896, and mask-1024
(parent: 1024 == full, skipped). Results:

- **Realistic mixed content does NOT break the static map.** At 1:1 and
  1:2, ZERO English-register leaks in 25 samples per ratio (grown full /
  old / mask-1024 and parent full / old, 5 each): 98.5-100 % hi-byte on
  every sample. An English system prompt up to EQUAL size with the zh
  content leaves the model answering in Chinese, on both models and all
  three paths.
- **The leak exists only in the ENGLISH-DOMINANT regime (2:1); it is
  INHERENT; and the per-path rates differ (Quinn review corrections,
  2026-11-18).** Readout discipline, named: the registered quantity is
  the mean hi-byte share; any sample below 95 % is READ and classified -
  either an ENGLISH-REGISTER FLIP (the continuation leaves zh for English
  legal/code text) or DEGRADED-ZH (zh-led with ASCII digits/punctuation
  artifacts); a sample below 50 % is always a flip. At 2:1 (5 samples per
  path, mean hi-byte in parens): flips - grown full 2/5 (66.2 %), grown
  mask-1024 3/5 (51.0 %), parent full 1/5 (82.6 %), old paths 0/10;
  degraded-zh - old-mask 2/10 (77.5 % and 73 %, zh with English
  document-number bits - the class the raw < 95 % count mislabels as
  leaks). At 1:1 the same degraded-zh class appears once (grown old
  92.5 %); flips: NONE anywhere at 1:1 and 1:2. Per-path flip rates at
  2:1 therefore: full-family 3/10, old 0/10 - and, the decision-relevant
  fact the earlier pooled "~40 %" HID: **mask-1024, the post-map zh
  DEFAULT path, showed the highest observed flip rate (3/5, 60 %; hard
  flips 3/5)**, old the lowest. By the S1 identity grown mask-1024 ==
  parent full is the SAME computation (observed 3/5 vs 1/5 on identical
  distributions - n=5 cannot separate a path effect from binomial
  spread, but the observed ordering is what the map decision has to live
  with). Not graft-induced: the parent flips under the same pressure,
  and the flip ordering tracks the path's English-register competence
  (P3 legal NLL 1.11 vs base 1.71). Register classification of the 6
  flips: **5 legal-led - one of them carrying code bits** (grown full #1:
  "...in force on 12 July 1989. # The file the format a contained import
  a person") - **and 1 CODE-LED** (grown full #2: "(self.compensation of
  account..."). The code register responds to register pressure but is a
  minority (1 of 6); the dominant leak register is English legal.
- **Deployment consequence:** the chat serving map "always full" is
  correct for realistic mixed prompts (system prompt <= user content);
  the failing regime is an English-dominant context, where every path
  including the zh NLL-optimal mask can flip register per sample. That is
  the measured case for WINDOW-LEVEL register awareness (the router's
  reserved role) rather than a static map or a full-context mask choice;
  under register-dominant prompts the base path (old mask) is the most
  leak-robust but still not immune.
- Auxiliaries: parent zh x full 98.3 % (5/5 Chinese, replicates); parent
  legal x old shows one 41 %-zh sample out of 5 (8.2 % mean) - sampling
  noise at t=0.8, the base zh register sits close to the surface; grown
  zh x old 99.9 %, zh x full 99.9 %, code x full code-shaped 5/5 - all
  section-15 readings replicate.

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

P3 verdict: **S1 exact, S2 pass, S4 pass, S3 diagnostic miss = stale oracle
(teacher forcing); deployment verdict = zh->old is functionally mandatory.**
The probe's central question - does per-step routed mixed training preserve
the host bit-exactly while the attach domain lands - is answered yes. The
router story is better than registered on the TF instrument (at the true NLL
optimum, +0.0005/+0.0009 vs always-full) and sharper than registered on
deployment: full-width generation on zh prompts stays functionally broken
(fluent English legal output, section 13's B/D behavior on P3), so the chat
serving map is zh->old and the +0.013-nat TF edge is the price of
correctness.

(Correction 2026-11-17: this closing block's deployment sentence predates
the two later revisions above it - the failure was prompt-regime-bound
(second revision, 8a0433a), and after graft #2 the full-width grown model
STILL produces Chinese on zh prompts 5/5 (section 15). "Functionally
mandatory" no longer stands; zh->old is the NLL-optimal bit-exact-base
option.)

## 15. Graft #2 executed: code as the third domain, design B (GLM, 2026-11-15 -> 2026-11-17)

**Run** (prereg in the graft-2 plan section 8, commits f519724/c45a865):
grow 1024 -> 1152 on the P3 last ckpt, `text_mix` = legal (even, side=new,
0.9), `text_mix2` = code (odd, side=old, 0.1) - the P3 mirror with the
secondary corpus swapped, zero code changes. Backup auto -> off (wd=0).
Corpus: CodeSearchNet python train, `scripts/prep_code_corpus.py` ->
`data/textmix2/code.txt` (33,000,559 B, 30,938 functions, sha256
d4da44b4...39252; the-stack-smol gated/no access). Pre-run anchor:
code@0 = 3.5787/3.5327 (fullcov b4; the parent-side mask-1024 identity is
structural - the strict-prefix guard rejects it, and the child-side
machinery was already G-A2-validated on zh). Launch 2026-11-15 09:15, done
2026-11-16 21:26 (~36.2 h; the ~4 h over estimate is 200 in-loop evals +
ckpt writes). Peak memory 91.99/96.40 GiB - IDENTICAL to the G-A2 dry run;
stationary profile, headroom held, no OOM, no NaN.

**Post-matrix (7 fullcov b4 cells, zero-tolerance first):** all four
identity cells BIT-EXACT through the real 10000-step run - zh@mask-1024
1.7470/1.6858, zh@mask-896 1.7603/1.6980, legal@mask-1024 1.1178/1.1250,
code@mask-1024 3.5787/3.5327 (== anchor). The frozen prefix IS the full P3
model after 36 h without backup: the S1 mechanism is production-scale
verified. S2 legal@0 = 1.1111/1.1187 - legal IMPROVED (-0.0067/-0.0063 vs
the P3 anchor). Registered log: `out_c/routed_probe/g2_code_run.log`-
equivalent at `/tmp/opencode/ga3_run/ga3.log`, matrix at
`/tmp/opencode/ga3_matrix/matrix.log`.

**The probe question - does the complement economy generalize to a
meaningfully different domain? - answered YES, with both registered
magnitudes exceeded in the mechanism's favor:**

- **D-cell code@0: 1.6638/1.6738, swing -1.9149/-1.8589 nats** vs the
  pre-anchor. Registered expectation ~-0.8 (P1-D-cell/P3-zh analogy):
  direction supported, magnitude 2.4x deeper. Code absorbed at 0.1-weight
  odd steps into the +8192 fresh neurons.
- **zh@0: 1.8320/1.7760, erosion +0.0850/+0.0902** vs the anchor
  1.7470/1.6858. Registered expectation +0.5-0.8: ~7x smaller. The fresh
  neurons took the new domain WITHOUT disturbing full-width zh - the
  graft thesis (complement, not overwrite) at its strongest measured
  setting.

**Serving checks on the grown model** (`gen_serve_check`, 5 x 200
tokens/cell): zh x full = Chinese 5/5 (100 % hi-byte) - the
prompt-regime-bound reading HOLDS post-graft; zh x old = Chinese 5/5;
legal x full = fluent legal; legal/code x old = base salad. **code x full
= code-shaped output** (self./method-def/underscore forms, deep
indentation whitespace; register-level salad at its 1.66 NLL - the
europarl-salad analog): the code register lives in the new neurons, and
real-domain prompts map to their registers correctly. Auxiliary: 1 of 3
unmasked samples on the synthetic ASCII legal prompt drifts into code
forms (register bleed on the synthetic prompt; NLL is the verdict
instrument).

**Post-map: legal -> full, code -> full, zh -> mask-1024** (the registered
fallback: zh@mask-1024 is NLL-optimal 1.7470 vs 1.8320 and keeps base-zh
bit-exact). "Always full" stays available for zh - the +0.085 erosion is
negligible vs the registered +0.5-0.8 band and invisible in generation -
but the mask is free at inference and remains the drift instrument. Graft
#2 is the first deployment-scale use of the validated mask primitive, and
its serving map needs no request labels: full for two domains, one cheap
mask for the third.

---

## 16. Coherence: the serving checks answer the language question, not the quality question

**Added 2026-11-18 after the mixed-content evaluation. This is a side finding of
the serving checks, and it is the one with the largest consequence.**

### The observation

Every generated sample in `mixed_serve_check.log` is fluent in its register
and language - and none of it is coherent. Representative samples:

```
definisterings dulta ord an the constralis a charges a determinate,
the person of determing the desistion to the detainer ...

\xaf一切同时，但一个国家和关于有效的各国家庭发展方案方案的机会议的方案
和有效和有效其实施的各项目其不可能方面期发展的国家的国家的一步在执 ...
```

The first is the base model on a legal prompt: recognizable legal vocabulary,
no grammatical structure. The second is the grown model on a zh prompt:
recognizable Europarl-Chinese fragments, no discourse. **Both are the
"word salad" the earlier readings named - and the earlier readings treated
it as a caveat, not as a finding.**

### The corpus arithmetic

The serving checks are not a small-sample anomaly. The training volume per
domain is small enough that the arithmetic explains them:

| domain | corpus | train bytes used | ratio |
|---|---|---|---|
| legal | 39 MB (`data/textmix2/legal.txt`) | 28,000,000 B = 28 MB | **~72 % of the corpus in one pass** |
| code | 32 MB (`data/textmix2/code.txt`) | 28 MB | **~88 %** |
| zh | 1,231 MB (`data/europarl/xscript_zh.txt`) | 28 MB | ~2.3 % |

```
10,000 steps x 512 B = 5,120,000 samples drawn from 28,000,000 B
```

**The model saw the legal corpus roughly 200 times** *(unit error -
corrected below, GLM 2026-11-18; the corrected count is ~0.18 sightings
per block per phase)*. A val_loss of 1.05-1.12
on a 1 MB split carved from a corpus it trained on at that rate is a
memorization number, not a generalization number. The word salad is the
other face of the same thing: the model reproduces the corpus in fragments
because the corpus is too small to learn structure from.

**Correction (GLM, 2026-11-18, review at rebase):** the table's carve
column is right - the loader carves 28/1/1 MB for every domain (graft-2
log: "textmix legal: train 28,000,000 B", "textmix code: train
28,000,000 B") - but the pass-count arithmetic below it has a unit error,
and the corrected arithmetic REVERSES the memorization reading while
keeping the data-scale conclusion. "5,120,000 samples" are BYTES of
token-views: one step draws one 512-B block, so a 10,000-iter phase draws
10,000 blocks from the 54,688-block carve, 5.12 MB total (mixed phases:
5,000 draws per domain, 2.56 MB). Drawn with replacement, that is ~0.18
expected sightings per block and ~17 % of blocks ever touched - the legal
corpus was not seen 200 times; it was seen a FIFTH of once. Cumulative
over every phase that sampled legal (P1 10,000 + P3 5,000 even + graft-2
5,000 even = 20,000 draws): ~0.37 sightings per block, ~31 % of blocks
ever - about a third of ONE pass. And the memorization sign flips on the
instrument evidence: the same-instrument val/test gaps are 0.007-0.061
nats (section 17), and no serving sample recites a corpus passage
verbatim, which a 200-pass corpus would leave everywhere. So the corpus
arithmetic DOES explain the word salad - through STARVATION (too little
coverage to learn structure from), not memorization. Everything else in
this section stands.

### What this does and does not contradict

**It contradicts nothing measured so far.** Every claim in this report is a
relative, masked, or bit-exact comparison. None of them requires coherent
generation, and the routing results are unaffected: the mask identity is
exact regardless of what the forward computes.

**It does reframe the deployment readings.** The three revisions of the
deployment question asked *which language does the model answer in*. That
question is answered: the language follows the register, and the register
follows the prompt. **The question a chat product actually depends on - can
you hold a conversation with it - is unanswered, and the serving checks say
no.**

### Registered interpretation

- **The word salad is a data-scale consequence, not a routing defect.** The
  routing errors are excluded by the bit-exact identity cells; the salad
  appears under every mask and on the base model, and it scales with corpus
  size in the expected direction (zh at 1.2 GB is Europarl-flavored rather
  than Europarl-fragmented).
- **The corpus is a probe corpus, not a product corpus.** It was selected for
  measurability and routing separation (legal/code/zh, small and disjoint),
  which is the right choice for the experiments in this report and the wrong
  choice for a chat model.
- **Consequence for the plan:** the chat-model training prereg's open item 3
  (corpus selection) is not a formality. The Graft #2 serving checks are the
  first direct evidence for it.
- **Not registered as a quality metric.** This section is an observation with
  an explanation; it does not introduce a coherence instrument. Any future
  quality gate needs a registered metric, not a sample-reading.
---

## 17. Word-salad diagnosis: the cause ranking, and the answer to the operator's hypothesis list (GLM, 2026-11-18)

Section 16 (Quinn) registers the observation - every serving sample is
fluent in its register and none is coherent - and proposes the corpus
arithmetic as the explanation. This section registers (a) the cause
ranking behind that observation, (b) the correction to section 16's
arithmetic step (unit error; the corrected arithmetic gives STARVATION
and keeps the data-scale conclusion), and (c) the evidence-per-item
answer to the operator's hypothesis list: overfitting, too-small data,
byte-level @ 512, missing SFT, or something else.

**The quoted salad is the BASE path, not a trained one.** legal x old-mask
keeps only the original zh-base neurons [0, 57344) (896 x 64): the P1-legal
and graft-2 blocks are masked out, so the cell measures the P0 zh-only
model under an English legal prompt. The parent produces the same class of
output on the same cell ("Served Addifiltion of the Serving Act
(ENFC/2003/L.4/CN.1/201/L.2005/L.25/213)") - inherent to the model family,
not graft-induced; it is the model's zero-exposure baseline in a register
it never saw. The same prompt on the trained path (1.11 nats) yields
register-correct legal scaffolding with word-level slips ("the provision
on a parameters, in the financial any paragraph (1)...").

**Token accounting - the dominant factor.** Each campaign training phase
(P1, P3, graft #2: 10,000 iters x 512 B x batch 1) = 5.12 MB token-views;
mixed phases split per domain, 5,000 steps x 512 B = 2.56 MB each (legal
even / zh-or-code odd). The 28 MB train carve is 54,688 blocks of 512 B,
so 10k uniform draws ever touch ~17 % of blocks, ~0.18 sightings per
block - the corpus is not traversed once per phase, and cumulative
coverage over the phases that sampled a domain stays at ~0.09-0.37
sightings per block (legal, section 16 correction). Against 3.62 B params (grown): token-views/param ~ 0.0014
per phase (cumulative over all campaign phases: < 0.01), vs the
~20-tokens/param compute-optimal rule (Chinchilla-era scaling; literature
figure, not a registered number) - ~3-4 orders of magnitude short. Inverse
form: the whole corpus set (~100-140 MB across domains) would support
~5-7 M params at that rule, so the model is ~3 orders of magnitude larger
than its data base. The zh base model's own pre-campaign training history
(out_a/bdh_textmix_k25w1024-zh_last.pt) is not re-derived here; its
measured register (1.7487 val on the 28 MB carve) has the same structure.

**Overfitting is measured out.** Same-instrument val/test gaps (fullcov
b4): legal 1.1178/1.1250 (gap 0.007), zh 1.7470/1.6858 (gap 0.061),
code@1024 3.5787/3.5327 (gap 0.046); base-legal 1.6596/1.7074 (gap 0.048,
section-9 batch-2 protocol). No memorization signature - structurally
impossible at ~0.17 sightings per block. What the model learned is global
register statistics without coverage: boilerplate exact ("the Secretary of
State", "paragraph (1)", "决议草案", "self.add(self):"), rare content
salads. UNDERTRAINING / coverage failure, not overfitting.

**The register ladder (registered NLLs vs the serving-check sample
picture):**

| path | register NLL (val/test) | samples (gen_serve_check) |
|---|---|---|
| zh-base @896 on legal | 1.66/1.71 (batch-2 protocol; fullcov 1.7087/1.7091) | hard word salad |
| frozen-P3 @1024 on code (P3 never saw code) | 3.58/3.53 | (no serving cell at this mask) |
| graft block @0 on code (5,000 odd steps x 512 B = 2.56 MB views, 0.1 weight) | 1.66/1.67 | code-shaped, semantically empty |
| frozen-P3 @1024 on legal | 1.12/1.13 | register correct, incoherent |
| zh itself (frozen prefix, the model's home register) | 1.75/1.69 | UN flavor, fluent-looking, incoherent |

Calibration (literature-anchored, not registered here): strong published
byte-level LMs reach ~0.6-0.9 nats/byte on natural-text corpora (enwik8-scale
compression SOTA ~0.9-1.0 bits/byte ~ 0.63-0.69 nats). *(Directional only;
section 18 replaces this anchor for the legal register with the
corpus-internal 6-gram on the same carve - see 18.4.)* The trained
registers sit ~0.2-0.6 nats/byte above that - a real but not order-of-
magnitude gap, which makes the sample picture the sharper diagnostic:
equal NLL means different things in different data regimes. A model
reaching 1.11 nats/byte from a 10^3-10^4x larger corpus has seen real
sentences at scale; ours reaching it from 5 MB of views interpolates the
register's prior - statistics of statistics. Sample quality is bounded by
the data regime, not by the NLL level alone. At the base paths
(e^1.71 ~ 5.5 effective choices per byte) text cannot even hold register
texture; at the trained paths (e^1.11 ~ 3.0) it holds texture and loses
composition.

**Verdicts on the candidate causes:**

1. **Data volume: YES - dominant.** Not "cannot generalize" (val ~= test on
   the unseen carve: it fits the carve's statistics) but
   "token-views are orders of magnitude too small to get past register
   texture". *(Qualified in section 18.4: both splits share boilerplate, so
   this is anti-memorization evidence, not generalization to new
   documents.)* Semantics/fluency live on coverage, not on parameters.
2. **Byte-level @ 512: real, secondary.** 512 B ~ 85 English words / ~170
   zh characters; the model has never conditioned on more than ~2
   paragraphs, and token-free models commonly pay a ~2-4x sequence premium
   per unit of content (literature). But not the salad cause: the byte
   pipeline demonstrably learns register texture, and the salad level
   tracks data allocation, not tokenization. For CHAT it is architectural
   bottleneck #1 (dialogue needs longer windows; byte-level amplifies data
   hunger).
3. **Missing SFT: categorically right, currently moot.** The repo contains
   zero dialogue data - data/ is LM corpora only (UN zh: 1.29 GB source,
   28/1/1 MB carve; UK legal 40 MB; python 33 MB; latex 40 MB present but
   unused in campaign runs; europarl parallel; wikitext; tinyshakespeare).
   The model knows exactly one English register (statute prose); dialogic
   English is pure OOD, which is why the system prompt is OOD in the mixed
   cells. SFT presupposes fluency and comes after a data scale-up.
4. **Named extras:** (a) the sampling regime t=0.8 / top-k 3 amplifies
   salad on an undertrained model (NLL remains the verdict instrument;
   samples are auxiliary - a greedy comparison would quantify the sampling
   share); (b) the LR schedule forced the end at 10k iters while the curve
   was still falling (in-loop 1.0333 -> best 1.0140): register texture
   would have kept improving; the coverage ceiling would not have moved.

**What chat capability would cost - a different campaign, not this
mechanism.** (i) data 10^3-10^4x in token-views (GB+ regime) including
dialogue data, then an SFT phase - or, inversely, parameters down to
~10-50 M, which would put fluent register prose within reach of the
current corpus (still no chat without dialogue data); (ii) context
512 -> 2048+ B, or a BPE layer; (iii) SFT on top. The register/graft
mechanism is unaffected and reusable: this campaign proved domains are
composable (S1 bit-exact over 36 h; +1.9 nats code competence in one
phase). The ceiling is base competence, not the mechanism.

Cheap diagnostics if the salad needs sharper separation: greedy instead of
t=0.8 on 3-4 cells (~1 h, 1 sample x 50 tokens - separates the sampling
share from the model limit); train-carve vs val-carve continuations
(separates statistics from memorization; the NLL gaps above already
indicate little memorization).

---

## 18. Three no-training controls: the network is below a 6-gram on its own register (GLM, 2026-11-18)

Review round after section 17: Quinn asked for a quantitative cost basis
(GB, parameters, Spark wall clock) and flagged BPE as an architecture
decision that must be registered before planning, not introduced as an
alternative afterwards; Claude supplied three no-training controls
(per-position NLL, byte n-gram baseline, word-start vs interior) plus the
throughput gap, the wide-and-shallow hypothesis, and the host-competence
consequence. This section registers the controls and the cost envelope.
The forward-looking registrations live in the chat prereg, section 6,
items 6-10.

**Instrument (diagnostic series, NOT the fullcov b4 verdict series).**
Legal carve of `_prepare_textmix("legal:data/textmix2/legal.txt", 30)` =
28/1/1 MB; 128 evenly spaced 512-B offsets on the 1-MB val split; batch 1,
no_grad, `collect_state=False`; masks built as in `gen_serve_check`
(mult 896 keeps the zh-base prefix [0, 57344), mult 1024 is the full grown
width, S1-identical to the parent full model). The n-gram is counted on
the 28-MB train carve, order 4 and 6, seen-context backoff to order 0
(uniform 1/256), no discounting; evaluation context comes from the val
stream and may cross a block start by <= 7 bytes (registered). Order 6 is
the safe maximum: order 8 needs 72 bits per context id.

### 18.1 The byte n-gram baseline

| instrument (same val targets) | mean NLL | head (0-63) | context (64-511) | tail (256-511) | word-start | word-interior |
|---|---|---|---|---|---|---|
| 6-gram (train carve, backoff) | **0.8519** | 0.8722 | 0.8490 | 0.8392 | 2.2440 | 0.5324 |
| network @1024 (grown, full width) | 1.1155 | 1.2750 | 1.0927 | 1.0932 | 2.5638 | 0.8306 |
| network @896 (zh base) | 1.7116 | 1.8426 | 1.6929 | 1.7508 | 3.2979 | 1.4167 |

Resolution: 96.0 % of val targets resolve at order 6 (0.7511 nats on that
share), 2.6 % at order 4 (1.9539), 1.5 % at the uniform fallback (5.5452).
The backoff is therefore not what drives the 0.8519 mean: the val carve is
almost fully covered by the train carve's 6-gram statistics - the corpus
shares its boilerplate, exactly Claude's caveat about same-corpus splits.

**Reading.** The grown model (1.1155) sits **0.2635 nats/byte above the
6-gram on the same positions** and beats it on 0.4 % of positions (2 of
512; each curve point is the mean over 128 blocks); the zh-base path is
0.8597 above. The instrument cross-checks
against the registered fullcov series: 1.1155 vs 1.1178 at @1024, and
1.7116 vs 1.7087/1.7091 at @896 (section 14's S2/desc cells) - the
diagnostic is the same measurement within 0.003 nats, so the n-gram
comparison is not an instrument artifact.

**Context curve.** The model's context gain is front-loaded: 2.948 at
position 0, 0.999 at position 64 (head mean 1.2750), then flat through the
tail (1.0932 at 256-511; +0.18 nats over 447 further positions). All of its
context value sits in the first ~64 bytes; bytes 64-511 add nothing. A
6-byte counter is flat by construction (0.8822 at position 0, 0.828 at
511) and still 0.25 nats below the model's tail - so the model's extra
58-505 bytes of context are worth less than 6 bytes of exact counting.
The point-to-point wiggles are +-0.05 (128 blocks per point); the
head/context/tail means are over 32k targets each and stable. This is not
"the model ignores context" (without the first 64 B it would
sit at ~2.9 nats); it is "the model stops learning from context after
~64 B". More data, more depth or a longer block would only pay if
exploiting long context is learnable at this scale; the curve cannot say
which lever, but it rules out "the model already uses its 512 B".

**Word classes.** Model and 6-gram show the same profile: word starts are
3-4x harder than word interiors (model 2.5638/0.8306, 6-gram
2.2440/0.5324). The model's deficit is broad rather than class-specific
(+0.3198 starts, +0.2982 interiors, +0.1295 other): it is a weaker
statistical learner across all byte classes, not specifically "vocabulary
without syntax". As stated in the review, the third control does not
separate the model from a 6-byte baseline - the start/interior asymmetry
is a property of the register, not of the model. Registered as a negative
result for that control; the first two controls carry the separation.

### 18.2 What the three controls separate

1. **Coverage.** The n-gram's counting pass reads all 28 MB; the network's
   cumulative legal exposure over P1 + P3 + graft #2 is 10.24 MB of
   token-views (20,000 steps x 512 B, half of them legal in the mixed
   phases) - about a third of one counting pass. Part of the n-gram's
   advantage is therefore raw data volume, the section-17 starvation
   point.
2. **Estimator match.** The 6-gram is the estimator that matches order-6
   structure exactly. If a 3.62B network scores worse than it on the same
   carve, "the model learned the register statistics" is too generous: the
   network did not absorb what a count table extracts from the same bytes.
   "Statistics of statistics" becomes literal, not rhetorical.
3. **Context and syntax.** The per-position curve answers whether the
   network uses the 512-B window. The 6-gram has no position dependence by
   construction (its context is the last 6 B), so the network's curve
   relative to it is a clean context test: at position 64 the deficit is
   0.22 and it stays 0.15-0.35 for the remaining 447 positions - the
   model's 64 B of context are worth no more than the counter's 6 B.
   Local context up to ~64 B is used; the long window is not. The
   word-class split was meant to separate word lookup from composition,
   but both instruments show the same start/interior profile with a broad
   model deficit - that control does not separate the model from a local
   baseline (18.1).

### 18.3 Cost envelope: the direct route is excluded on this hardware

Quinn's review: "data 10^3-10^4x in token-views (GB+ regime) is the right
direction, but not a number. How many GB of tokens, how many parameters,
how much time on a Spark?" Answer, from measured logs where a measurement
exists (full derivation and sources: chat prereg section 6, item 6). All
rates are **one-pass**; the route-aware loop costs 2.0x (correction
below the table):

| route | params | token-views | rate | wall clock, one Spark |
|---|---|---|---|---|
| direct, compute-optimal | 3.62 B | 72.4 GB (20 B/param) | 44.8 B/s measured | **~51 years** |
| direct, minimum scale-up | 3.62 B | 5.12 GB (10^3x one campaign phase) | 44.8 B/s | **~3.6 years** |
| inverse, 100M host, 6 layers | 101 M | 2.0 GB (20 B/param, byte-level) | **1,868 B/s measured** (2,192 ms/step, b8/t512) | **12.4 days** |
| inverse, 100M host, 6 layers, compiled | 101 M | 2.0 GB | **3,997 B/s measured** (1,025 ms/step) | **5.8 days** |
| inverse, 100M host, 4 layers | 101 M | 2.0 GB | 2,764 B/s measured (1,482 ms/step) | 8.4 days |
| inverse, 10M | 10 M | 200 MB | ~18,700 B/s (10x scaling) | ~3 h |

The 3.62B rate is the p50 of 1,000 logged training steps (11,420 ms/step,
b1/t512); one 28-MB pass is 7.2 days. Peak memory is 91.99 GiB of the
97.35-GiB cap, so batch >1 does not exist at this size: the usual
throughput lever is absent. The 100M/4090 anchor is 230 ms/step at b8/t512
(report 2026-08-24, section 10.2).

**The Spark 100M probe (measured here, `scripts/bench_100m.py`).** 6
layers uncompiled (the campaign's `--no-compile` mode): 2,192 ms/step at
b8/t512 = 1,868 B/s, 23.1 GiB peak; 4 layers: 1,482 ms/step = 2,764 B/s.
Compiled (`torch.compile`, the 4090 reference's mode): 1,025 ms/step =
3,997 B/s, 16.6 GiB peak - 2.1x the uncompiled rate. Even compiled, the
Spark does ~2.4 TFLOP/s effective (6*N*T/time) vs ~10.8 on the 4090; the
4.5x gap is close to the 3.7x memory-bandwidth ratio (273 vs 1,008 GB/s),
so the implementation is memory-bound on both machines. Kernel work could
move the constant, but the direct route needs a ~400x move.

**Throughput correction (review).** The review's 450x ratio used 22,000
B/s; measured against the 3.62B p50 it is 17,808 / 44.8 = **397x**. The
direction stands. But the 4090 anchor is the wrong machine for a Spark
plan: the Spark's own 100M rate is 9.5x below the 4090 uncompiled
(1,868 vs 17,808 B/s, 6 layers) and 4.5x below it compiled (3,997 B/s).
The inverse-route wall clocks above use measured Spark numbers.

**Route-aware correction (review round 2).** Every row above is one-pass.
The graft/SFT loop is route-aware: two forward passes (prefix 0.9 + full
0.1, the P1/graft-2 shape) and one backward. Measured with that compute
shape (`scripts/bench_100m.py --two-pass`, 2026-11-18): 4,429 ms/step
uncompiled (925 B/s) and 2,091 ms/step compiled (1,958 B/s) at b8/t512 -
**2.0x the one-pass step**, 48.5/33.2 GiB peak. The table's 5.8-12.4 days
are host pretraining, not the route-aware phase; a 2-GB route-aware phase
is **~12-25 days uncompiled (~6-12 compiled)**. The real loop's
frozen-prefix split backward may be cheaper than the two-forward shape;
2.0x is the compute-shape bound, to be replaced by a measured pilot step.

**Verdict.** The direct route's GB+ regime is on disk (Europarl zh 1.3 GB,
wikitext-103 516 MB, textmix/files 215 MB, textmix2 109 MB, expert 23 MB -
~2.1 GB usable) but not reachable in training time at 3.62B. The inverse
route is the only campaign this box can run; it is a candidate bridge to a
competent host (prereg item 9), not a demonstrated one (18.6). At the
measured Spark rate a
compute-optimal 100M leg is **5.8 days compiled / 8.4-12.4 days
uncompiled** (6/4 layers), a 10M run ~3 h, a 50M/1-GB run ~3 days. The
direct route would still be decades even with the 2.1x compile gain. The
existing existence proof points the same way: a 101M model
reached 0.8219 nats/byte on 90 MB Europarl with 41 MB of views (report
2026-08-24) - below both our 3.62B grown model and our 6-gram on legal,
different corpus, so a direction only. BPE does not change this budget in
the favorable direction: 20 tokens/param counts tokens, so BPE at ~4
B/token needs ~8 GB of text for a 100M model, or four epochs over 2 GB.

### 18.4 Caveats registered with the controls (Claude)

- **The val/test gap is anti-memorization evidence, not generalization
  evidence.** Both splits are carves of the same corpus, and legal statutes
  and Python functions are boilerplate-heavy; 1.12 measures how well the
  register statistics sit, not transfer to new documents. That is enough
  to exclude memorization at 0.2-0.4 sightings per block; it is not enough
  for "the model generalizes".
- **The enwik8 calibration is directional only.** Nats/byte depend on
  corpus and script (zh UTF-8 is 3 B per character; legal boilerplate
  compresses). Section 17's 0.63-0.69 anchor is replaced, for this
  register, by the corpus-internal 6-gram on the same carve - a reference
  the network can be measured against directly.
- **The n-gram is an optimistic reference for boilerplate**, because 96 %
  of val contexts are seen in the train carve. The same optimism applies
  to the network, trained on the same carve; the comparison is fair, but
  it does not license "a 6-gram beats the model on new legal text".

### 18.5 What changes in section 17

The cause ranking stands: starvation dominant, 512-B context secondary,
zero dialogue categorical, overfitting excluded. Three things sharpen:

1. "The model learned global register statistics" becomes "the model
   learned **less than a 6-gram count table** on its own register"
   (0.2635 nats above it @1024; broad across byte classes).
2. "It fits the carve's statistics, which is not generalization to new
   documents" (18.4) replaces the generalization phrasing.
3. The context question is now quantitative and open: all of the model's
   context gain is in the first ~64 bytes, and bytes 64-511 add nothing.
   That is the home of the depth hypothesis (plan item 10), not a
   refutation of the starvation verdict - a 6-byte counter still beats
   the model's 64+-byte curve.

The third reviewer control (word-start vs interior) is registered as a
**negative result**: it does not separate the model from a 6-byte
baseline, because the profile is register-driven. The planning
consequences are registered in the chat prereg section 6, items 6-10.

### 18.6 Review round 2: three corrections registered (Quinn, 2026-11-18)

1. **NLL is not a coherence gate.** Section 18's own finding forbids it:
   the 3.62B model sits 0.2635 nats above a 6-gram and still yields word
   salad. The host gate therefore has two keys - a statistical floor on the
   host's own carve (necessary, not sufficient; the 0.8519 of 18.1 is the
   legal-carve value and does not transport) and a registered, sample-based
   coherence instrument (not yet existing; candidates are prereg item 4 and
   the 4.4a judge topology). Until that instrument is frozen, a host that
   clears the NLL floor is **not** scored as passing. Prereg item 9 is
   rewritten accordingly.
2. **The 100M route is a hypothesis, not a consequence of the diagnosis.**
   The diagnosis is specific to a 3.62B model at 0.18 sightings per block;
   transfer to 100M is an extrapolation across parameters, data and
   context, unmeasured until a 100M run exists. Registered in item 9 as
   outcomes A/B/C; the first 100M run is itself the instrument that tests
   the transfer.
3. **Route-aware overhead is real and measured: 2.0x.** The 100M bench is
   one-pass; the graft/SFT loop is two-pass at 0.9/0.1. Measured 4,429
   ms/step uncompiled and 2,091 compiled at b8/t512 - 2.0x the one-pass
   step, 48.5/33.2 GiB peak. The 5.8-12.4-day figures in 18.3 are one-pass
   pretraining; a route-aware 2-GB phase is ~12-25 days uncompiled
   (~6-12 compiled).
