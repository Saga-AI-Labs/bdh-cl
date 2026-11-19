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

**30 prompts, English, open-ended, requiring ~100-300 bytes of generation.**
Constructed so no gold answer exists and no single fact decides the score.

**Families (10 each, registered):**

1. **Explain** - "Explain how a bill becomes a law." / "Explain why the sky
   is blue." / "Explain what a router does."
2. **Describe a process** - "Describe how to bake bread." / "Describe how a
   compiler turns code into a program."
3. **Opinion/argue** - "Should cities ban cars in the centre? Argue your case."

**Contamination control:** prompts must be authored, not sampled from a corpus.
A prompt that appears in the training data would measure memorization, not
coherence. The prompt set gets a sha256 at freeze time; the hash is part of G1.

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
