# Key-2 instrument gate failure: the cross-check seat cannot discriminate coherence

**Date:** 2026-11-23
**Addressed to:** the operator, for the G0 decision
**Status:** diagnosis and options. **No G0 sign-off.** Nothing below is frozen.
**Evidence:** `out/key2_calibration/{qwen,gemma}_scale.json` (108 rows each),
`stab_{qwen,gemma}_r{1,2,3}.json`, `probe_v2_{qwen,gemma,gemma_qat}.json`,
`disagreement_review.md` (blind sheet), `rubric_v2_system_prompt.diff`.

---

## 1. What happened

The 108-row scale set was scored by both registered seats on this host:

| judge | endpoint | model | rows | NULLs |
|---|---|---|---|---|
| primary | `192.168.178.51:8888` | `Qwen3.8-Flash-Next` | 108 | 0 |
| cross-check | `192.168.178.200:1234` | `gemma-4-31b-it` | 108 | 0 |

Both model ids match the 2026-11-09 certification records exactly, and the
system-prompt hash matched the registered value (`c996a247...d0b59c`), so this
is the registered instrument, not a drifted one.

The section 8.5 instrument gate then failed on coherence:

| dimension | exact | gate 70 % | within +/-1 | gate 95 % | verdict |
|---|---|---|---|---|---|
| coherence | **63.9 %** | fail | **90.7 %** | fail | fail |
| relevance | 78.7 % | pass | **94.4 %** | fail | fail |
| language | 71.3 % | pass | 100.0 % | pass | pass |

## 2. This is not judge noise

Each judge was re-run three times on a stratified 10-item slice
(`stab_slice.jsonl`), 30 observations each:

| judge | within +/-1 | cells identical across repeats |
|---|---|---|
| Qwen | 30/30 (100 %) | 30/30 |
| Gemma | 30/30 (100 %) | 30/30 |

Both seats are perfectly deterministic at temperature 0. The disagreement is
therefore systematic and reproducible; repeating the run cannot change it.

## 3. The failure is ten cells, and one judge's scale

Coherence has exactly 10 items with a gap greater than 1, and those same 10 are
the only `within +/-1` failures. The shape is uniform - Qwen lower, Gemma at 5:

| item | Qwen | Gemma |
|---|---|---|
| `cert_en01_long_wrong` | 3 | 5 |
| `cert_en03_long_wrong` | 3 | 5 |
| `cert_en03_planted_error` | 3 | 5 |
| `cert_en05_long_wrong` | 3 | 5 |
| `cert_en07_planted_error` | 3 | 5 |
| `cert_en14_planted_error` | 3 | 5 |
| `cert_en15_bad` | 3 | 5 |
| `cert_en13_audience_violation` | 3 | 5 |
| `cert_en17_audience_violation` | 1 | 5 |
| `cert_en17_long_wrong` | 3 | 5 |

If those ten agreed, coherence would be 79/108 exact (73.1 %) and 108/108
within +/-1 (100 %): both gates pass. The instrument is not broadly unstable.

The cause shows in the score distributions:

| judge | coherence | language |
|---|---|---|
| Qwen | 1:2 % 2:3 % 3:8 % 4:25 % 5:62 % | 4:29 % 5:71 % |
| Gemma | 2:3 % 3:1 % **5:96 %** | **5:100 %** |

Gemma uses essentially two values. On `good` both judges say 5.00, so the
seats agree at the anchor and diverge only where discrimination is needed.

## 4. Why the 2026-11-08 offset guidance does not apply

The certification report warned that raw cross-judge agreement is confounded by
a scale offset and recommended normalising against each judge's own `good`
anchor. That guidance is correct but does not cover this case:

- the anchors already coincide (`good` = 5.00 for both judges, all three
  dimensions), so normalising against them changes nothing;
- the disagreement is not a constant shift. Mean Gemma-minus-Qwen is +0.47 on
  coherence, and applying a -1 shift gives 26.9 % exact / 99.1 % within +/-1 -
  it fixes one metric and destroys the other.

On the 4.4b certification set the gap was a genuine offset (Gemma 4.73 vs Qwen
3.67 on `good`). Here it is a variance problem: one seat does not use the lower
half of the scale.

## 5. The fact-versus-contradiction ambiguity (now resolved)

On the 54 items the rubric says must stay high on coherence (`long_wrong`,
`planted_error`, `bad` - "key 2 does not score facts"):

| judge | mean coherence | scored <= 3 |
|---|---|---|
| Qwen | 4.31 | 9/54 |
| Gemma | 4.94 | 1/54 |

Qwen was importing factual judgement into coherence, which section 8.3 forbids.
The rubric also never said what a *single internal contradiction* costs, so
anchors 3 and 5 both read as defensible. The operator ruled on 2026-11-23:
**an internal contradiction is a coherence defect.**

A v2 system prompt was drafted to state that, to keep "false about the world"
unscored, and to state that register is not scored
(`out/key2_calibration/rubric_v2_system_prompt.diff`; system prompt
`c996a247...d0b59c` -> `9edfd92d...42124`, 2,588 -> 3,732 bytes).

## 6. The v2 draft fixes Qwen and does not fix Gemma

Both judges were probed on 12 disputed items with the v2 text (probe only, not
registered data):

| judge | exact | within +/-1 |
|---|---|---|
| Qwen v2 | 4/12 (33 %) | 7/12 (58 %) |
| Gemma v2 | 4/12 (33 %) | 7/12 (58 %) |
| Gemma QAT v2 | 4/12 (33 %) | 7/12 (58 %) |

Qwen moved where it should: its reasoning switched from "the law is wrong" to
"the passage contradicts itself", and it raised the dense-but-connected
register item from 3 to 4. It stayed low on the genuine word salad.

Gemma did not move. Under v2 it still scored **5 on
`cert_en17_audience_violation`**, the dense pseudo-legalese with no recoverable
proposition that Qwen scores 1-2, and it scored 5 on 10 of the 12 probe items.
`google/gemma-4-31b-qat` behaved identically. This is not prompt
non-compliance: Gemma's own reasoning states the passage "maintains a line of
thought". It does not detect the planted contradictions or the register
collapse.

## 7. Diagnosis

- The primary seat is usable after the v2 wording change; the ambiguity it was
  exploiting is a real rubric gap that v2 closes.
- The cross-check seat, as served (`gemma-4-31b-it`, and the QAT variant), has
  no coherence discrimination on this set. It cannot be fixed by wording, and
  it is deterministic, so it cannot be averaged away.
- With the min-of-two rule, Gemma currently contributes nothing to coherence:
  it never scores below Qwen, so Qwen alone decides that dimension while the
  record still claims two seats. That is the substantive problem, independent
  of the numeric gate.

## 8. Options

| option | what it does | cost / risk |
|---|---|---|
| 1. Probe independent candidates | Test a non-Gemma local model on the 12-item probe against 4 criteria (`good`=5, contradictions=3, word salad=1-2, dense register=4-5). | ~20 min per candidate. If one passes, seat change needs operator sign-off and breaks judge continuity with the 4.4b certification. Candidate pool is thin: see 8.1. |
| 2. Dimension-specific seats | Qwen owns coherence; Gemma keeps relevance and language, where it agrees (relevance 78.7 % exact; language 71.3 % exact, 100 % +/-1). | Coherence loses its second seat, which must be registered as a deviation, not a pass. |
| 3. Operator override | Freeze with the gate failure recorded as a known limitation. | Honest only if the record states that coherence is effectively single-judge; otherwise G0 would claim a stability it did not measure. |
| 4. Hold G0 | Decide elsewhere. | Nothing freezes; the 133 generations and reference rows stay valid because they are judge-independent. |

### 8.1 Candidate assessment (2026-11-23, operator input)

Both candidates suggested from the local endpoint were ruled out by lineage or
capability before any probe was run:

- **`ornith-1.0-35b`** is built on Qwen3.5 and Gemma 4. It carries the heritage
  of both registered seats, so it would not supply the independence a
  cross-check seat exists for. Excluded.
- **`mistralai/devstral-small-2-2512`** (Devstral 2, 24 B) fits on the RTX 4090
  but is over a year old and not strong enough to be the cross-check.

No candidate from the current pool is both independent and capable, so option 1
is deprioritised. The evidence used instead was a calibration read by an external
LLM (section 9), not a human read; the registered human blind read of 8.3 -
`out/key2_calibration/disagreement_review.md` with the key held separately -
remains available and would supersede it if the operator fills it in.

## 9. Calibration read by an external LLM (2026-11-23)

**Role: calibration input only. This is NOT a human read.** It is not a human
opinion, not a human judgement, and not the registered human read of section
8.3. It is an LLM's opinionated guess, used for one narrow purpose - ordering
the disputed cells - and it must never be cited as human assessment, as an
operator sign-off, or as ground truth.

The 20-sample blind sheet was scored by an external LLM (ChatGPT, OpenAI). The
rubric anchors were not supplied to it, so it used a conventional 1-5 scale; it
was a single pass with no stability check; and it is not a judge seat.

Results against the two seats over all 20 samples (calibration read vs judge):

| dimension | external vs Qwen | external vs Gemma |
|---|---|---|
| coherence | 45 % exact / **95 % +/-1** | 30 % / **55 %** |
| relevance | 45 % / 85 % | 50 % / 75 % |
| language | 65 % / 90 % | **85 %** / 90 % |

On the ten disputed cells the calibration read is closer to Qwen in 8/10, closer to
Gemma in 0/10 (2 ties). Cells S09 (`cert_en17_audience_violation`) is the
clearest: external 1, Qwen 1, Gemma 5.

Two limits on interpretation:

- **Relevance cannot be arbitrated by this read.** The calibration scores penalise
  samples that stay on topic but do not adequately answer (S01: external 2,
  both judges 5). Section 8.3 defines relevance as topicality and mode, "not
  whether the sample answers the prompt", so this is a definitional difference,
  not a judge error.
- **It is harsher on facts than v2 permits.** S01 and S02 are penalised for
  doctrinal confusion, which v2 classifies as a fact defect and does not score.
  Its support for Qwen is therefore support for the *ordering* of the disputed
  cells, not for its absolute values.

What the read can support: on coherence, the seat that tracks an independent
LLM reader within one point 95 % of the time is Qwen, and the seat that does so 55 %
of the time is Gemma. The same read shows Gemma is the stronger **language** seat
(85 % exact against 65 %), so the two seats are complementary per dimension
rather than one being uniformly worse.

## 10. Recommendation (updated)

Option 1 is unavailable: the only local candidates are lineage-linked (Ornith)
or dated (Devstral 2), so 8.1 applies.

Option 2, per dimension, on the evidence above:

| dimension | aggregation | basis |
|---|---|---|
| coherence | Qwen is authoritative; Gemma's score recorded but not binding | Qwen 95 % +/-1 vs external, Gemma 55 %; 8/10 vs 0/10 on disputed cells |
| language | two seats as registered | inter-judge 71.3 % exact / 100 % +/-1; Gemma 85 % exact vs external |
| relevance | two seats as registered, re-measured under v2 | inter-judge 78.7 % exact / 94.4 % +/-1 (0.6 pp short); the calibration read cannot arbitrate relevance |

This must be registered as a **deviation, not a pass**: coherence has one
effective seat. Option 3 (override) remains viable if and only if the frozen
record states: coherence was scored by one effective seat, the inter-judge gate
failed at 63.9 % / 90.7 %, and both seats were verified deterministic. A freeze
that omits this would overstate the instrument.

### 10.1 Approval and execution (2026-11-23)

Operator decisions taken on this note:

1. **Per dimension accepted** - Qwen authoritative on coherence, both seats on
   language and relevance, registered as a deviation.
2. **Rubric v2 registered** - `data/evals/key2_rubric_v2.json`, system prompt
   `9edfd92d...42124`, file sha256 `2c1b7972...f6626`, status DRAFT with the
   approval recorded in its `provenance` block. `key2_judge.py` now defaults to
   it.
3. **Re-score approved** - 283 samples per seat under v2 (108 scale, 18
   positive, 133 coherence negative, 24 relevance control).
4. **Analysis approved** - then `key2_analyze.py --coherence-seat-substr qwen_v2`
   for the `M_d`/`F_d` candidate, with the seat policy written into the candidate
   JSON.
5. **Calibration read labelled** - the ChatGPT read is calibration input only,
   explicitly not a human read, not a human opinion, not an operator sign-off.

G0 has **not** been held. The freeze still needs the v2 bands, the language
subset, and the operator's sign-off on the resulting `M_d`/`F_d`.

## 11. Reproduce

```bash
.venv/bin/python scripts/quinn/key2_judge.py \
  --base-url http://192.168.178.51:8888/v1 --model Qwen3.8-Flash-Next \
  --input out/key2_calibration/reference_scale.jsonl \
  --out out/key2_calibration/qwen_scale.json --log out/key2_calibration/qwen_scale.log
.venv/bin/python scripts/quinn/key2_judge.py \
  --base-url http://192.168.178.200:1234/v1 --model gemma-4-31b-it \
  --input out/key2_calibration/reference_scale.jsonl \
  --out out/key2_calibration/gemma_scale.json --log out/key2_calibration/gemma_scale.log
```

The agreement table is computed over the common ids of those two files, per
dimension, as `max == min` (exact) and `max - min <= 1` (within one).

## 12. Artifacts and provenance

| path | content |
|---|---|
| `out/key2_calibration/qwen_scale.json` | 108 rows, `Qwen3.8-Flash-Next`, 0 NULLs |
| `out/key2_calibration/gemma_scale.json` | 108 rows, `gemma-4-31b-it`, 0 NULLs |
| `out/key2_calibration/stab_{qwen,gemma}_r{1,2,3}.json` | 10-item stability slice, 3 repeats |
| `out/key2_calibration/probe_v2_{qwen,gemma,gemma_qat}.json` | v2 wording probes |
| `out/key2_calibration/disagreement_review.md` | 20-sample blind sheet, judge-free |
| `out/key2_calibration/disagreement_review_key.json` | answer key; open only after scoring |
| `out/key2_calibration/rubric_v2_system_prompt.diff` | v2 wording delta |
| `out/key2_calibration/calibration_read_chatgpt.json` | calibration-only LLM read of the 20 blind samples (S01-S20, 3 scores each); not a human read |

Positive band, for completeness: coherence 5.00, relevance 5.00, language 4.83
(min 4) over the 18 truncated `good` rows, 0 NULLs - the positive end of the
instrument is sound. The coercion rows (133 generations) were also scored by
Qwen with 0 NULLs and are judge-independent.
