# Key 2 - coherence rubric for free generation (draft, 2026-11-19)

**Purpose.** Key 2 is the second gate of the host program: a frozen, sample-based
coherence instrument. Key 1 (NLL against a corpus 6-gram) is necessary but not
sufficient - report section 18 showed a model 0.2635 nats above a 6-gram that
still produces word salad. Key 2 must measure the thing section 18 could not.

**Status.** Draft for the planning round. Not frozen. Nothing here authorizes a
run; the round must freeze rubric + prompt set with a hash (gate G1).

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
