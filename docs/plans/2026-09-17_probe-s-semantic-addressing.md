# Probe S — Semantic Addressing Under Identical Language Surface

Status: PREREGISTRATION, RUNNER PENDING · 2026-09-17 · Quinn

Operator GO: third approved follow-up probe. This document is written before any runner code is executed. No commits or pushes are authorized by this document.

## Question

Can BDH-style growth addressing select the correct memory territory when language, script, style and topic template are identical and only the factual content differs? This is the chat-relevant open core named in the Sonde C report §7 — it is NOT tested by P-C4, R or J.

## Design (minimal closed world)

Synthetic byte-level fact corpora with identical language surface:

- Two territories A (base) and B (grown). Facts are short templated sentences, e.g. `the zubble of flarn is QUILT.` where the content word is drawn from a fixed closed vocabulary of 64 nonce content words per slot. Territory A and B share templates and function words exactly; only the fact–slot bindings differ.
- Corpus A: 256 facts, corpus B: 256 facts, disjoint fact sets, no shared content bindings. A held-out split of 32 facts per territory is generated from the same templates with unseen slot bindings (composition generalization, not interpolation).
- All text is lowercase ASCII, so the byte router is maximally competent on surface: this is deliberate — surface statistics MUST NOT be able to distinguish territories beyond arbitrary content-word frequency differences, which we measure and report as the byte router's honest ceiling on this task.

## Training

1. Train a small BDH (n_layer=2, n_embd=256, n_head=4, block 512, mult 128) from scratch on corpus A to completion criterion: held-out A perplexity <= 1.15 or 4000 steps cap.
2. Grow per Mechanism B exactly as `pipeline/train.py --grow-mult` implements: copy old segments, fresh tail, gradient masks, bit-exact frozen-path restore each step (F-decay-leak fix), embed/lm_head frozen. Train only on corpus B with `neuron_mask` prefix masking (route-aware alpha=1.0, no full-width mixing) so territory B lives in new neurons only.
3. Growth criterion: held-out B perplexity under prefix-masked forward <= 1.15 or 2000 steps cap; A perplexity under full forward must not degrade by more than 0.05 from its post-A value (retention check).

## Query protocol (amended before any runner code exists)

Two query sets, both answerable and answer-free at routing time:

- **Q-trained (192 queries):** paraphrase-style prefixes of trained facts (word-order variants of the template, same trained fact-binding), prefix truncated before the content word. This tests recall of trained bindings under surface variation.
- **Q-comp (64 queries):** compositional held-out queries — combinations of two trained bindings from the same territory never seen together in training (e.g. cross-slot recombination). This tests systematic combination, not arbitrary unseen facts.

Routing may use only the query text up to the truncation point. Route selection must not condition on the target word or use the answer in any form; a route-selection signal that requires the withheld answer is invalid and aborts the run.

1. **Oracle route:** the correct territory's mask (B: new-neuron prefix; A: full-width and old-masked variants both recorded).
2. **A2 route:** argmin over candidate routes of the NLL the route assigns to the *complete query sentence minus its final content word*, using territory-internal likelihood only; then read that route's next-token prediction at the query position. Record route-choice agreement with oracle. Because both territories share the same surface, a wrong-territory route should assign the sentence higher NLL precisely when the bindings conflict — that is the quantity under test.
3. **Byte baseline (fairness-critical):** a territory-association model trained ONLY on function words and template positions, blinded to content words (content-word tokens masked out of its input). A content-word-aware association baseline is reported separately as the surface-statistics ceiling; only the blinded variant is a fair address router.

Primary metric: next-token accuracy at the query position per routing condition, on Q-trained and Q-comp separately. Secondary: rank and NLL of the true token.

## Predictions and falsifiers (frozen)

- P-S1: oracle route accuracy >= 0.80 on held-out facts of both territories. If oracle fails, storage/acquisition fails first — stop, do not interpret routing. (Mechanism check, not address check.)
- P-S2: A2-selected route equals oracle route on >= 0.85 of queries. Falsifier: A2 min-NLL route selection at or below chance-corrected floor (0.25 + 0.1) despite passing P-S1.
- P-S3: byte-association baseline accuracy on this task is reported and must be compared honestly; if the byte baseline matches A2 routing, the addressing result does not demonstrate model-internal addressing.
- P-S4 (retention): territory A accuracy >= 0.75 post-growth under full-width reading.

Gate S-PASS requires P-S1 AND P-S2. P-S3 failing (byte baseline high) downgrades the claim to surface-resolvable, reported as such.

## Known limits (declared up front)

- Two territories, one template family: minimum viable demonstration, not scaling evidence.
- A2 route selection here uses width-mask NLL, not the production likelihood router across languages.
- Truncated-prefix queries are simpler than open chat; passing this does not establish chat-grade memory addressing.
- Growth uses the exact audited Mechanism B code path; any deviation (e.g. skip frozen-path restore) aborts the run as invalid.

## Execution

Runner `scripts/quinn/probe_s_semantic.py`, CPU/GPU on bdh-4090 under `out_c/followup_gpu.lock` after R completes. Smoke test with 8 facts, 200 steps on synthetic data first; assert exact-copy of Mechanism B semantics by comparing one optimizer step's frozen-region checksums against `pipeline/train.py` behavior. Persist corpora, seeds, checkpoints, per-query predictions and decisions under `out_c/probe_s/`. No threshold or recipe changes after launch; failures are reported as failures.
