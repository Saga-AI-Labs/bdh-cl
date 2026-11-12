# Routed-grow probe P3 prereg: mixed training with a sequence-level router

**Date:** 2026-11-12
**Status:** preregistered design. Gates G0-G2 and the implementation are next; the
run itself starts only after the gates pass.
**Depends on:** P3 sketch (bb30cf7), probe report (96dcf5a - sections 10, 11, 13),
full-coverage eval (e42e8c5), P1 recipe lessons (report section 2.1, attempt
history).

## 1. Question

One checkpoint, two domains, per-sequence routing. After mixed training from the
grown state:

- the old domain must be **bit-preserved** (this is now a zero-tolerance check,
  not a noise-band comparison - report section 13),
- the new domain must land at its P1 level (or better),
- the router must select the right side often enough that deployment routing
  behaves like oracle routing.

This is the probe that turns "the base is a host" (report section 5) into a
working two-domain serving story.

## 2. What changed since the sketch (2026-11-10)

1. **The instrument.** All registered numbers are now full-coverage deterministic
   evals (--eval-deterministic, e42e8c5), not 20-crop random evals. The
   sketch's thresholds were random-crop numbers; section 4 re-anchors them.
2. **The mechanism.** Report section 11 (corrected): every checkpoint in this
   probe carries k_sparse_ratio = 0.0 - plain ReLU path, no topk. The neuron
   mask is an exact elementwise zeroing, so a sequence-level router (sketch
   option A) IS sufficient for clean isolation. The pre-topk side-scoping
   question is withdrawn. If k_sparse is ever enabled, the code's retraction
   rule governs (bdh.py:12-18, 6754e83: hold k ABSOLUTE across growth).
3. **The anchors.** zh old-prefix fullcov is 1.7603/1.6980 and the grow/P1/P0
   cells are bit-identical; the P2 "+0.0441 degradation" was instrument noise
   around a true delta of 0. The survival criterion is no longer "<= 1.7928"
   but "== 1.7603/1.6980".

## 3. Registered design decisions

| id | decision | rationale |
|---|---|---|
| D1 | Init from the grown checkpoint `out_c/routed_probe/bdh_textmix_grow896to1024_last.pt` (mult 1024, step 0), **no `--grow-mult`** | One mixed run does both jobs: the new block learns legal from scratch while zh batches flow through. The base_mult trap (train.py:185) does not apply because there is no growth. The F-V9 path must be verified first (gate G0). |
| D2 | Mixed stream = **strict alternation of homogeneous batches** (legal step, zh step, legal step, ...), starting with legal | Each batch draws its 512-byte crops from ONE domain, so the existing (N,) neuron mask broadcasts unchanged - **no bdh.py change**. Strict alternation gives exact 50/50 exposure and a seed-reproducible schedule. Labels come from the schedule, not from a classifier. |
| D3 | Per-step route side: legal step -> `side=new` (prefix = new-only, alpha 0.9, full term 0.1 - P1-identical); zh step -> `side=old` (prefix = old-only, frozen -> dead grads; the 0.1 full term is the new block's only zh signal) | "The mask is the only change from P1" (sketch section 3.2), generalized to two sides. Consequence registered as descriptive: the trained block sees weak zh exposure, so the D-cell penalty (+0.79 nats, report section 13) may shrink. |
| D4 | Optimizer/loop: batch 1, lr 1e-4, warmup 500, lr-decay 10000, wd 0, no-compile, route-split-backward, `BDH_MEM_FRACTION=0.8`, **10000 iters**, `eval_interval 200` | P1's proven envelope (~10.4 s/step, ~34 h wall, peak under the 97.35 GiB cap). eval_interval 200 avoids the best-save storm (38.65 GB per save added hours in P1, report section 12). |
| D5 | In-loop eval: legal val under the side=new mask (P1-comparable curve); zh has no learning to monitor (frozen block) | Comparability with the P1 trajectory (2.50 -> 1.03). |

## 4. Gates (run before the long run)

| gate | what | cost |
|---|---|---|
| G0 | Dry run on the real grow ckpt: load without `--grow-mult` (F-V9 / `allow_unfrozen_grown_init` semantics with wd 0), 4 steps alternating legal/zh; verify the route-aware prints BOTH sides ("prefix 57344..65536" on legal steps, "prefix 0..57344" on zh steps), memory under the cap, clean checkpoint write | ~10 min |
| G1 | Legal full-coverage anchors, 3 cells (all --eval-deterministic b4): P0 on legal (mask 0), grow on legal (mask 0), P1 on legal (mask 0) | ~30 min |
| G2 | Router smoke: the new 2-mask argmin router (section 7) on the mixed val stream with the GROW ckpt; expect ~100 % accuracy - at step 0 the margins are huge (zh block: old-only ~1.76 vs full ~3.3+; legal block: old-only ~1.7 vs full ~2.6) | ~10 min |

G1 anchors are registered into S2 before the training run starts; the matrix
they produce also completes the full-coverage 2x2 for the probe.

## 5. Registered success criteria (full-coverage instrument)

| id | criterion | threshold |
|---|---|---|
| S1 | zh, mask 896, fullcov, after P3 | **== 1.7603 / 1.6980 to all printed digits** (zero tolerance; any move = the freeze broke = FAIL + investigation) |
| S2 | legal, mask 0 (full width), fullcov, val | <= P1-legal-fullcov-anchor (from G1) **+ 0.10**; hard floor: <= base-on-legal-fullcov (from G1). Target: ~P1 level |
| S3 | router accuracy on the mixed val AND test streams | >= 95 % per sequence (argmin over the two masks, no margin rule); confusion matrix reported |
| S4 | routed mixed-stream NLL | <= oracle-routed NLL (token-weighted mean of zh@896-fullcov and legal@full-fullcov) + 0.05 |
| desc | zh, mask 0, fullcov | vs 2.5488/2.4933 (does 0.1-weight zh exposure shrink the D-cell penalty?) |
| desc | legal, mask 896 (old-only), fullcov | completes the 2x2; expected ~base-on-legal |

S1 is the point of the whole probe design: because the old block is frozen and
the ReLU-path mask is exact, the old-domain number is a **bit-exact regression
test** on the training run, not a statistical estimate.

## 6. Registered fallbacks (decided now, not improvised)

- **S2 miss** (legal > anchor + 0.10): continue from the last checkpoint with
  weights-only init (no faithful resume exists - init-from loads weights only,
  optimizer/step/best_val restart; train.py:255/:435), 5000 iters, warmup 200,
  decay 5000, fresh Adam - documented as non-faithful. If S2 misses because the
  zh full-term interferes (check the legal curve shape), instead rerun with the
  zh-step loss weighted 0 (pure P1 + monitoring).
- **S3 miss** (< 95 %): report the margin distribution; retry eval with
  window 256 (registered now: 128 primary, 256 fallback). If still < 95 %, the
  router is the finding, not a blocker - S1/S2 stand on their own.
- **OOM**: the cap makes it readable (exit 1 with a traceback, no kernel sweep).
  b1 route-aware is the proven envelope; do not raise batch size mid-run.

## 7. Implementation surface (small; no bdh.py changes)

1. `pipeline/config.py`: `--text-mix2 <spec>` (second corpus) + `--mixed-alternate`
   flag.
2. `pipeline/train.py`: when mixed-alternate, build BOTH route masks up front
   (side new/old are both supported at train.py:356-361 today), pick per step by
   the alternation schedule, keep everything else (loss shape, freeze,
   split-backward) as is. ~30-50 lines.
3. `scripts/router_p3.py` (new): build the labeled mixed val/test stream
   (interleaved 512-byte blocks from the two 1 MB splits), score each block's
   first `--window` bytes under both masks (no-grad forwards through the loaded
   model with `neuron_mask` - NOT the physical weight masking of
   scripts/eval_router.py, so the P1 mechanism is what gets certified), argmin,
   report accuracy + confusion + routed NLL vs oracle.
4. `out_c/routed_probe/run_p3.sh`: P1-recipe-based runner (D1-D5), gates first.

Smoke before the long run: the mixed-alternate loop on the tiny model
(mult 32, /tmp/opencode/tiny_ckpt) - 8 steps alternating two tiny corpora,
verifying per-step side switching, mask shapes, loss bookkeeping, checkpoint
write, and the S1-style exactness property at tiny scale.

## 8. What P3 does not establish

- Sequence-level routing only; token-level routing needs a different mask shape.
- Two domains, one direction (zh host, legal attach); a third domain = third
  corpus + rerun.
- The router is corpus-schedule-certified, not learned; a learned router head
  (sketch option B) is a separate question.
- ReLU-path only: enabling k_sparse invokes the 6754e83 k-absolute growth rule
  and reopens the competition question (report section 11).
- No serving integration; the router runs as a pre-forward decision in the
  training/eval loop, not inside the model forward.

## 9. Timeline

Gates G0-G2: ~50 min (G1 first - it is pure measurement and anchors S2).
Implementation + smoke: the rest of the day. Run: ~34 h. Post-run fullcov matrix
(6 cells) + router eval: ~50 min. Then the verdict update to the probe report.
