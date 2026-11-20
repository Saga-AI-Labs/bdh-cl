# Key 2 - coherence rubric for free generation (draft, 2026-11-19)

**Purpose.** Key 2 is the second gate of the host program: a frozen, sample-based
coherence instrument. Key 1 (NLL against a corpus 6-gram) is necessary but not
sufficient - report section 18 showed a model 0.2635 nats above a 6-gram that
still produces word salad. Key 2 must measure the thing section 18 could not.

**Status.** Draft for the planning round. Not frozen. Nothing here authorizes a
run; the round must freeze rubric + prompt set with a hash (gate G1).

**Review 2026-11-20.** The draft above stands as the record. Section 8 is the
correction block that governs G0; where it conflicts with sections 1-7, section
8 applies.

**Depends on:** chat planning round (`docs/plans/2026-11-19_chat-host-planning-round.md`,
D1), report sections 16-18 (the diagnosis and the counterexample), planning input
addenda 6.1 (judge topology).

---

## 1. What key 2 measures, and what it does not

**It measures:** whether a freely generated text holds together - one line of
thought, on-topic, and readable.

**It does not measure:** instruction following. That is the certified judge set
(`data/evals/judge_set_v1/`, 60 items, two local judges). The two instruments are
separate objects; reusing 4.4b for key 2 would consume the composition series and
measure the wrong thing.

| | 4.4b (certified) | key 2 (this draft) |
|---|---|---|
| object | answer to an instruction | free generation from a prompt |
| gold | yes (good/mediocre/bad) | no gold; the rubric scores the sample |
| languages | 10/10/10 en/de/zh | English only (the host is English-first) |
| judge | Qwen + Gemma (local) | same topology |
| usable for an en host | 20 of 60 items | 30 new items |

**Consequence:** the 20 English items of the certified set are a **calibration
baseline** for the judges' English register competence, not part of key 2.

## 2. The three dimensions

| dimension | question | scale | anchor (5) | anchor (1) |
|---|---|---|---|---|
| **coherence** | does the text hold one line of thought? | 1-5 | a single thread, each sentence follows | topic jumps within sentences |
| **relevance** | does it answer the prompt? | 1-5 | stays on the prompt throughout | ignores the prompt |
| **language** | is it grammatical and fluent? | 1-5 | clean prose | broken word salad |

**Why three and not one:** section 16's samples were fluent in register and
broken in composition. A single "quality" score would have merged the two and
let one compensate the other. Three dimensions keep them separable.

**Worst-case rule, registered:** the gate is the **minimum** across items of the
**mean of the three dimensions**, not the overall mean. A model that is coherent
on 29 prompts and incoherent on one fails. This is the same unit choice as
4.4b section 4 ("the worst case a user experiences, not the domain mean").

## 3. Prompt set

**Decision D-count (2026-11-20, operator): 100 prompts.** The alternatives were
50 and 200. The reasoning recorded: a higher count is presumably better, a
lower count presumably faster, and neither the right value nor the smallest
sufficiently stable one is known - so take the middle.

**One correction to that reasoning, registered with the decision:** the gate
unit is the minimum over items (section 2), so a larger count is not strictly
better. More items widen the chance of drawing a bad prompt, and the worst case
sharpens with n. **n=100 is a compromise between measurement accuracy and
worst-case sharpness, not a monotone improvement.** The real lever is prompt
quality: 100 weak prompts lose to 50 good ones.

**Decision D-source (2026-11-20): authored, not corpus-sampled.** This is
registered as an exclusion rule rather than a preference - a prompt drawn from
the training data would measure memorization, not coherence.

**Families (34 each, registered):**

1. **Explain** - "Explain how a bill becomes a law." / "Explain why the sky
   is blue." / "Explain what a router does."
2. **Describe a process** - "Describe how to bake bread." / "Describe how a
   compiler turns code into a program."
3. **Opinion/argue** - "Should cities ban cars in the centre? Argue your case."

**Contamination control:** prompts must be authored, not sampled from a corpus.
A prompt that appears in the training data would measure memorization, not
coherence. The prompt set gets a sha256 at freeze time; the hash is part of G1.

**Registered decisions, all six (2026-11-20, operator):**

| # | decision | value | alternatives considered |
|---|---|---|---|
| D-count | prompt count | **100** | 50 / 200 |
| D-source | prompt origin | **authored** | held-out document openings |
| D-decoding | generation | **greedy, temperature 0** | seeded fixed-seed sampling |
| D-length | output cap | **256 bytes** | 128 / 256 |
| D-threshold | set from | **base-host and certified-baseline quartiles, then frozen** | a fixed number up front |
| D-stability | stability slice | **5 items x 3 repeats, >=95% within +/-1** | 3 x 3 |

**On the absence of certainty:** these are decisions under ignorance, not
measurements. The honest state is: no prior run exists for this object, so no
value here is known to be right. What is registered is therefore the value and
the alternatives - the falsification routes in section 6 remain the way any of
them gets corrected.

## 4. Decoding

**Deterministic.** Greedy (temperature 0) for the verdict run. Rationale: t=0.8 /
top-k 3 amplifies salad on an undertrained model (report section 17), and a
sampling threshold would be tuned after seeing the samples.

**Length cap:** 256 bytes per sample, registered. The model is byte-level at
block 512; a longer cap would let a model fail by running out of context, not by
incoherence.

## 5. Judge protocol

- **Two local seats:** Qwen 3.8 Flash Next (DGX Spark, TP=1) primary, Gemma 4
  31B (RTX 4090) cross-check. Deepseek is the second team seat.
- **Bias rule unchanged:** no Meituan (LongCat) and no GLM as judges.
- **Prompt format:** the rubric as system message, then `Prompt:` + prompt +
  `Text:` + sample. JSON out: `{"coherence": n, "relevance": n, "language": n,
  "reason": "..."}`.
- **Reasoning budget:** `max_tokens >= 2048`, retry at 4096 on
  `finish_reason=length` (the 14 NULL cells of the certification run are the
  precedent).
- **Reproducibility:** temperature 0, three repeats on a 5-item stability slice;
  >= 95% within +/-1 required.

## 6. Threshold - to be set before the first run

**Not proposed here.** A number chosen now would be chosen against a model that
does not exist. Registered procedure instead:

1. Score the **base English host** (the pilot run) and the **certified-set
   baseline** on the same rubric.
2. Set the threshold from the **lower of the two quartiles**, before any graft.
3. Freeze it with the prompt hash.

**Falsification, registered:** if a model clears key 1 (beats the 6-gram) and
fails key 2, the coherence verdict stands and the host is rejected. If a model
clears key 2 and fails key 1, the rubric is wrong - coherence without statistical
fit is not possible, so the rubric is mis-scored.

## 7. Cost

- Rubric + 30 prompts: ~1 day (authoring, no training).
- Certification pass on the base host: 30 prompts x 2 judges = 60 calls, ~1 h at
  the local rates.
- Re-scoring per arm: 60 calls, ~1 h.

**Key 2 is the cheapest item in the cascade and the only one that blocks the
host.**

---

## 8. Review 2026-11-20 - corrections before freeze

**Status of this block.** Non-destructive review outcome. The draft in sections
1-7 stays as the record of what was decided before the review; this block is
what G0 freezes. Four design decisions were confirmed by the operator on
2026-11-20: per-dimension mean + floor, threshold from human answers plus the
3.62B salad, the argue family as diagnostic only, and the 100-item gate variant
(50 explain + 50 describe gate, 33 argue diagnostic, 133 total). The D-count of
section 3 is re-registered at 133; the other five operator decisions stand, with
the procedures for length, threshold and stability replaced below.

### 8.1 Confirmed changes

| item | draft (sections 1-7) | corrected for G0 |
|---|---|---|
| gate unit | min over items of the mean of the three dimensions | per dimension: `mean_d >= M_d` and `min_d >= F_d`; no cross-dimension mean |
| threshold source | quartiles of the pilot host + certified baseline | human answers (positive) + 3.62B salad (negative), frozen before any host sample |
| prompt families | three families, all in the gate | explain + describe in the gate; argue diagnostic only |
| prompt count | 100 decided, 30/102 in the text | 133 total: 100 gate (50 explain + 50 describe), 33 argue diagnostic; D-count re-registered |
| stability | 5 items x 3 repeats, >= 95 % | 10 items x 3 = 30, >= 29/30 within +/-1, stratified |
| length | 256 B | unchanged; local-coherence scope, prompt <= 128 B, word-boundary truncation |

### 8.2 Gate: per-dimension mean + floor

For every dimension d in {coherence, relevance, language}:

- **quality:** `mean_d` over the gate items >= `M_d`;
- **floor:** `min_d` over the gate items >= `F_d`.

There is no mean across the three dimensions. The mean of the three dimensions
is reported as a diagnostic, not gated.

**Why.** The draft gate is the minimum over items of the mean of the three
dimensions. A section 16 sample that is fluent and on-topic but compositionally
broken scores language 5, relevance 5, coherence 1 - mean 3.67 - and can pass a
threshold <= 3.67. That is the exact failure key 2 exists to catch. The draft
also justifies the min with "a model that is coherent on 29 prompts and
incoherent on one fails"; under the draft rule that failure is not guaranteed,
because the incoherent item can be compensated by the other two dimensions. The
4.4b precedent is mean + worst-item floor; this block applies that form per
dimension instead of inventing a third unit.

`F_d` is set between the salad maximum and the human minimum. `M_d` is set below
the human mean with a margin. Both are frozen from the reference calibration in
8.3, not chosen against the host. Any item below `F_d` is re-scored blind by the
third seat; if the breach is confirmed, the run fails.

### 8.3 Threshold: human positive, 3.62B salad negative

The threshold is calibrated on references that exist before the host run. No
host sample is scored before the freeze.

**Prompt split.** The operator chose the 100-item gate variant (2026-11-20):
100 gate prompts (50 explain + 50 describe) plus 33 argue diagnostic, 133
total. The gate statistics (`mean_d` and the `min_d` floor) are computed over
the 100 gate items; the 33 argue items are scored and reported separately. The
D-count of section 3 is re-registered from 100 to 133 by this decision; gate
count and total count are now distinct and both are frozen at G0.

**Reference set.**

| role | material | expected |
|---|---|---|
| positive | 20 human 256-B answers to 20 of the 100 gate prompts, stratified 10 explain / 10 describe | all dimensions >= 4, mean >= 4.5 |
| negative | section 16 samples + 133 generations from the 3.62B checkpoint on the full 133-prompt set; the gate uses the 100 gate items | coherence and language <= 2, max <= 3 |
| mid (optional) | 100M/90MB pilot samples | between human and 3.62B; register-confounded |
| dissociation A | section 16 "fluent but incoherent" samples | language >= 4, coherence <= 2 |
| dissociation B | clean off-topic passages | language >= 4, relevance <= 2, coherence >= 4 |

The 3.62B checkpoint is on disk as `bdh_textmix_p3_mixed_best.pt` and
`bdh_textmix_p1_legal_new_best.pt` (38.7 GB). The 133 generations are the
negative distribution; the gate uses the 100 gate items, and the two section 16
samples alone are not a distribution.

**Procedure.**

1. Score every reference blind with both judges, on the same rubric and the same
   protocol as the verdict run.
2. Set `F_d` between the salad maximum and the human minimum, and `M_d` below
   the human mean with a margin.
3. If the human and salad distributions overlap on a dimension, the rubric is
   not separating that dimension. Revise the anchors before freezing; do not
   split the overlap with a threshold.
4. Freeze `M_d`, `F_d`, the rubric text, the prompt set, the judge system
   message, the decoding parameters, the aggregation code, the judge versions
   and quantisation, and the reference scores, all with sha256.
5. Only then score the host. The pilot is the verdict run, not the calibration
   run; if the pilot itself is used for calibration, the verdict needs a second,
   independent run.

**Validation acceptance (instrument gate, before the host is scored).**

- human answers: all dimensions >= 4 and mean >= 4.5; if not, the rubric is too
  harsh or the anchors are wrong;
- salad: coherence and language <= 2, maximum <= 3; if not, the rubric is too
  lenient;
- fluent-but-incoherent: language >= 4 and coherence <= 2; this is the
  dissociation the instrument exists for;
- off-topic clean text: language >= 4, relevance <= 2, coherence >= 4;
- ordering: human > 100M/90MB > 3.62B on both the mean and the 10th percentile;
- inter-judge agreement: >= 70 % exact and >= 95 % within +/-1 per dimension;
- human read: the operator reads the 10 worst and 10 random samples blind and
  the judge-vs-human agreement is reported.

### 8.4 Falsification: the 2x2, not "the rubric is wrong"

Key 1 is measured on the val carve against a corpus 6-gram; key 2 is measured on
prompt generations. They are different data, and a disagreement between them is
a finding, not proof that the rubric is broken. The draft sentence "coherence
without statistical fit is not possible" is false as stated: a coherent model
can sit above a corpus-specific 6-gram on novel prompts, and a model below the
6-gram can still be incoherent (the section 18 salad). The 6-gram is a
corpus-specific comparison, not a law.

| key 1 | key 2 | verdict | action |
|---|---|---|---|
| pass | pass | pass | proceed to graft |
| pass | fail | fail (salad) | key-2 verdict stands; diagnose coverage |
| fail | pass | fail (gate) | register "coherent but off-anchor"; diagnose prompt OOD / carve representativeness |
| fail | fail | fail | diagnose |

The rubric is falsified by the validation set in 8.3, not by a cross-key
disagreement. A judge failure (NULL, JSON error, out-of-range) is "not
scoreable", not "failed"; re-run the judge pass.

### 8.5 Judge protocol: aggregation, dissent, NULL

The draft names two seats but no aggregation. Registered here:

- **Item score.** Dimension score = confirmed minimum of the judges (or the
  median of three when the third seat fires). Every item below the floor is
  re-scored blind before it counts.
- **Dissent.** A difference > 1 on any dimension between the two seats sends the
  item to the third seat. The third seat is a tie-breaker, not a second team.
- **NULL / JSON.** Retry once at the 4096 budget. If still NULL or unparseable,
  the item is a fail (conservative) or the run is "not scoreable" if the rate
  exceeds the registered cap. It is never silently dropped from the min.
- **Out-of-range / missing dimension.** Same rule as NULL: retry, then fail.
- **Agreement.** Report exact and +/-1 agreement per dimension over the gate
  items. Instrument gate: >= 70 % exact and >= 95 % +/-1, the same form as the
  4.4b stability criterion. Below that, the instrument is not stable enough for
  a floor gate.
- **Deepseek.** "Second team seat" is undefined. Either register it as the
  tie-breaker (local, model version, quantisation, when it fires) or remove it
  from the topology. The 4.4b registration says the cloud path is closed by
  provider policy.
- **Boxes.** Qwen on the second Spark, Gemma on the RTX 4090; judging does not
  share the training box (D8).

### 8.6 Count, stability, cost

- **Count.** Exactly 133 prompts: 50 explain + 50 describe in the gate, 33 argue
  diagnostic. The draft's "30 new items", "34 each" and "60 calls" are
  superseded; the D-count is re-registered from 100 to 133.
- **Calls.** 133 prompts x 2 judges = 266 calls per pass, not 60. Gemma is the
  bottleneck: the 4.4b certification measured median 63 s, mean 76 s, p95 159 s
  per call (n=480, 2048-token budget, single-score rubric). The key-2 rubric has
  a larger system message and three dimensions, so budget 1.5-2.5x: ~4-8 h for
  the 133-call Gemma pass, plus ~1-2.5 h for stability. Qwen measured median
  7 s, mean 12 s, so it is not the bottleneck. Plan 6-10 h per full pass and
  measure the first 10 calls to replace the estimate with the observed rate.
- **Stability.** 10 items x 3 repeats = 30 observations per judge; >= 29/30
  within +/-1 (96.7 %), exact agreement reported. The slice is stratified:
  3 items near the threshold, 3 at the floor, 4 random. The draft's 5 x 3 at
  >= 95 % is arithmetically 15/15 = 100 % and has no resolution between 80 %
  and 95 %. Stability measures the judge, because the model is greedy at t=0.
- **Authoring.** 133 prompts plus rubric plus the validation set is ~2-2.5 days,
  not 1 day.

### 8.7 Remaining corrections

- **256 B is local coherence.** ~45 words, ~3 sentences. It catches section 16
  salad but not "starts fine, derails at paragraph 2". Register the scope: key 2
  measures local coherence; long-range coherence is a separate, unbuilt
  instrument. Truncate at a word boundary and tell the judge the sample may end
  mid-sentence.
- **Anchors.** Define 2, 3 and 4 for every dimension, not only the endpoints.
  Coherence 1 is "no recoverable proposition", not "topic jumps" (that is 2).
  Language 1 is "broken morphosyntax", not "word salad": "Colorless green ideas
  sleep furiously" is language 5, coherence 1. The dimensions must be able to
  dissociate.
- **Prompt length.** The model is byte-level at block 512. Register prompt
  <= 128 B so prompt + 256 B generation fits with margin, or register the
  windowing rule explicitly.
- **Hash scope.** Hash the rubric text, the judge system message, the decoding
  parameters, the aggregation code, the judge versions/quantisation and the
  reference scores, not only the prompt list.
- **G0, not G1.** The plan's freeze point is G0 (data, carve, key-1 6-gram and
  margin, key-2 instrument, pilot shape, A/B/C). Key 2 is one field of G0.
- **Repetition.** Greedy decoding on an undertrained byte model loops. Add an
  objective repetition metric (longest repeated substring, distinct-4) with a
  hard fail above 64 B; a loop is locally fluent and can read as coherence 3.
- **Prompt-set sampling error.** The `min_d` floor over 100 is an extreme
  statistic. Report the second-worst item, the count of items within 0.5 of the
  floor, and a leave-one-out range. If the floor verdict hinges on one item,
  flag it.
- **Families.** Report per-family minima. Argue is a diagnostic, not a gate
  family; it measures a discourse mode the base host has not been trained for.
- **Relevance.** Define it as topical/mode consistency, not "does it answer the
  prompt". Instruction following is 4.4b's object; key 2 must not become a
  second 4.4b.
- **Collinearity.** After validation, report the dimension correlation matrix.
  If coherence and language correlate above 0.8, the third dimension is cost
  without information; merge it or keep language as a hard floor.
- **Contamination.** "Authored" is necessary but not sufficient. Check each
  prompt for an 8-gram overlap with the host corpus and each output for a
  50-byte verbatim overlap; flag the latter as memorisation, not coherence.
  Record who authored the prompts and when.

### 8.8 What this block does not do

- It does not change the operator decisions as decisions except the D-count:
  the D-count is re-registered at 133 (100 gate + 33 diagnostic), while
  authored, greedy/t=0, 256 B, threshold from a baseline and the stability
  slice stand. It changes the procedures that implement the length, threshold
  and stability decisions.
- It does not touch 4.4b. The certified set is read-only; the 20 English items
  are a judge-scale check under the 4.4b rubric, not a key-2 item pool. A drift
  check (> 0.4 against the frozen anchors Gemma EN 5.00 / Qwen EN 4.06) runs
  before any reuse.
- It does not freeze anything. G0 still requires the reference scores, the
  hashes and the operator's sign-off.
