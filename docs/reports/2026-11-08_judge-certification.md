# Judge certification: two models, complementary profiles, one shared item defect

**Date:** 2026-11-08 (rev. 2026-11-09 after the countercheck)
**Question:** can a local third-party judge be certified for the chat prereg's
§4.4a/4.4b composition metric, and can a second local model judge German?
**Answer:** both models run the full cert set end to end. Neither passes all criteria,
and their failures are complementary: Gemma separates quality well but misses planted
facts; Qwen catches every planted fact and is perfectly stable but scores good answers
too low. The single most important finding is not a judge failure at all — the ordinal
failures trace to defective items that both judges reject identically.

**Revision note (2026-11-09):** a countercheck by GLM recomputed every gate from the raw
rows and found three errors in the first version of this report. All three are corrected
here; the corrected text is marked **CORRECTED**. GLM's note is
`docs/notes/2026-11-09_judge-cert-recommendation.md`.

## 1. What was run

Two judges, same frozen rubric, same 30-item set (10 en / 10 de / 10 zh), 6 variants per
item, 3 repeats on the 10 stability items — **300 calls each**.

| | Gemma | Qwen |
|---|---|---|
| endpoint | `192.168.178.200:1234` | `192.168.178.51:8888` |
| model | `gemma-4-31b-it` | `Qwen3.8-Flash-Next` |
| context | — | 262.144 tokens |
| reasoning | yes | yes (default enabled) |
| calls | 300 | 300 |
| endpoint fingerprint | `85c12327fcf7b0c0` (60 models) | tensorfold |
| rubric sha256 | `ef4d113fdbd74f61…` | `ef4d113fdbd74f61…` |

Harness: `scripts/quinn/judge_calibration.py` — frozen system prompt (5 anchors),
`temperature=0.0`, `max_tokens=2048` with one retry at 4096 on
`finish_reason=length`, untruncated reasoning log, endpoint fingerprint in meta,
checkpoint after every item, `--resume` for long runs.

## 2. Certification criteria

Criteria are from `judge_set_v1/README.md` section 4; `pass` is the frozen gate.

| criterion | gate | Gemma | Qwen |
|---|---|---|---|
| **Separation** | gap ≥ 0,8 AND ≥ 80 % good ≥ 4 | **1,333 / 90 % → pass** | 0,867 / 60 % → **fail** |
| **Brevity bias** | ≥ 80 % long_wrong ≤ 2 AND mean ≤ 2,5 | **100 % / 1,0 → pass** | **100 % / 1,0 → pass** |
| **Fact-checking** | ≥ 80 % planted ≤ 3 AND 0 % == 5 | 90 % / 6,7 % → **fail** | **100 % / 0 % → pass** |
| **Constraint awareness** | ≥ 80 % audience ≤ 3 | 50 % → **fail** | **82,8 % → pass** |
| **Floor** | ≥ 70 % bad = 1 AND mean ≤ 1,5 | **100 % / 1,0 → pass** | **100 % / 1,0 → pass** |
| **Ordinal** | good ≥ short ≥ bad per item | 27/30 → **fail** | 27/30 → **fail** |
| **Stability** | ≥ 70 % exact AND ≥ 95 % ±1 | 78,3 % / 96,7 % → **pass** | **100 % / 100 % → pass** |

### Per language slice

| slice | Gemma | Qwen |
|---|---|---|
| en | sep ✅ fact ❌ constr ❌ | sep ❌ fact ✅ constr ✅ |
| **de** | sep ❌ fact ❌ constr ❌ | sep ❌ **fact ✅** constr ❌ |
| zh | sep ✅ fact ✅ constr ❌ | sep ❌ fact ✅ constr ✅ |

**Qwen is the better German fact-checker.** On the de-slice Gemma fails fact-checking;
Qwen passes it with 100 %. That is the cross-check question the README posed, answered:
yes, a second local model can judge German — and it catches what Gemma misses.

**Gemma is the better separator.** Gap 1,333 vs 0,867, and 90 % vs 60 % of good rows ≥ 4.
Qwen scores good answers too low for a ranking instrument.

**Gemma's constraint failure is uniform, not a language blind spot** (CORRECTED, GLM
found): audience_violation rows ≤ 3 are en 4/10, de 6/10, zh 5/10 — the same leniency
in all three slices. Qwen passes constraint in all three: en 9/10, de 8/9 valid,
zh 8/10 (the zh slice lands exactly on the 80 % boundary).

**Qwen is perfectly stable.** 100 % exact across 60 repeat pairs; Gemma 78,3 %. Against a
judge that agrees with itself 100 % of the time, the §4.4a cross-check agreement metric
measures real disagreement, not judge noise.

## 3. Corrections from the countercheck

### 3.1 CORRECTED — "300 calls each, 0 failures" is wrong for Qwen

Gemma: 300 rows, all `finish_reason=stop`, 0 nulls, 0 retries — the claim holds.

Qwen: **299 scored rows plus one NULL row** — `cert_de06`/`audience_violation`, rep 1:
`score=None`, empty `judge_content`, `finish_reason=length`, `attempts=2`, the full
4096-token completion budget consumed by reasoning tokens. There is no rep-2 row
(non-stability items run a single rep). Materially the audience gate still passes at
24/29 = 82,8 %; treating the NULL as a miss gives 24/30 = **80,0 % — still passes** the
≥ 80 % band exactly, so the verdict is robust under the strictest reading.

### 3.2 CORRECTED — the cert_de01 description quoted a claim the item does not contain

The first version of this report said the good variant "says *'Both require offer,
acceptance, and consideration'*" and treated that as the defect. **That quote is not in
`cert_de01`.** It belongs to the 10-item calibration phase's `c01`, an English contract
item; `cert_de01` is a German notarization item and contains no "consideration". I
carried a diagnosis from one item onto a different item and wrote a plausible quote
instead of reading the file. GLM caught it by direct text check.

The actual defect, visible in both judges' rep-1 rationales, is that the good variant
claims the contract "wird in der Regel erst wirksam, wenn die Auflassungsvormerkung ins
Grundbuch eingetragen ist" — the contract only becomes effective once the
Auflassungsvormerkung is entered. That is a false doctrine: the notarial contract is
effective upon notarial certification (§ 311b BGB); the Vormerkung protects the buyer's
expectation but does not condition the contract's effectiveness. Qwen's rationale:
"Der notariell beurkundete Kaufvertrag ist bereits mit Beurkundung wirksam, nicht erst
mit Eintragung einer Auflassungsvormerkung." Both judges correctly score it 2.

### 3.3 CORRECTED — "four items fail the ordinal gate" is five items, six judge-level cells

The table below lists five distinct items; `cert_de01` fails on both judges, so there are
six judge-level failures. The substance of the section — shared item defect, judge
consensus, no judge defect — is verified as written.

### 3.4 A further defect the countercheck found (not in the first version)

`cert_de02`/`long_wrong` contained kana and merged-token corruption ("einajer",
"に関する") — the same corruption class as `cert_de10`, found in the round-2 validation
scan and repaired in the same commit as the other seven cells.

### 3.5 Latency (CORRECTED, GLM found)

| | mean | median | max |
|---|---|---|---|
| Qwen | **8,5 s** | 6,2 s | — |
| Gemma | 76,1 s | 60,9 s | 320,3 s |

Gemma additionally shows a **cold/warm state effect**: `de01/good` scored [2, 5, 5] with
the rationale running 173 s cold and 70 s warm — the false doctrine was caught cold and
missed warm. `zh04/planted` reads "substantially incomplete … fails to explain
Value/Softmax" (rep 1, score 3) then "clear, accurate, and intuitive" (rep 2/3, score 5).
**Both Gemma misses are judge-side drift under cold/warm state, not item defects.**

## 4. The ordinal failures are item defects, not judge defects

Five items fail the ordinal gate, and the pattern is the finding:

| item | Gemma good/short/bad | Qwen good/short/bad | verdict |
|---|---|---|---|
| **cert_de01** | **2 / 3 / 1** | **2 / 3 / 1** | item defect, both judges identical |
| cert_de10 | **3 / 4 / 1** | (holds) | item defect (good corrupted: "undresponses") |
| cert_en09 | **2 / 4 / 1** | (holds) | item defect (good claims a logographic/writing-system mechanism) |
| cert_en08 | (holds) | **2 / 3 / 1** | item defect (good overclaims the notarial act) |
| cert_zh05 | (holds) | **2 / 3 / 1** | item defect (good claims false PIPL Art. 47 public-interest exceptions) |

**cert_de01 is the shared failure** (see §3.2 for the corrected description). Both judges
independently reject the same item, and both give it the same scores. That is a consensus
between two unrelated architectures — the strongest evidence that the item is defective
and the judges are not. An ordinal failure caused by a judge would not repeat identically
across two different models.

The other four are item-side for different reasons: a corrupted token (de10), a good
variant that attributes the difficulty to the writing system instead of listening
decoding (en09), a good variant that overclaims what must sit in the notarial act
(en08), and a good variant that invents public-interest exceptions to PIPL Art. 47
(zh05). All four were repaired in the same commit.

## 5. Anchor bands (rep-1 means) — the calibration input for §4.4b

| variant | Gemma | Qwen |
|---|---|---|
| good | 4,73 (de 4,50 / en 4,70 / zh 5,00) | 3,67 (de 3,50 / en 3,80 / zh 3,70) |
| short_correct | 3,40 | 2,80 |
| planted_error | 2,10 | 1,97 |
| audience_violation | 3,43 | 2,66 |
| bad | 1,00 | 1,00 |

**Consequence for the §4.4a agreement metric:** the same answer reads 4,5 on Gemma's scale
and 3,5 on Qwen's de-slice. **Raw cross-judge agreement would be confounded by the
offset.** Normalize per language against the judge's own good anchor before comparing, or
the metric measures the offset, not the disagreement.

## 6. Consequence for the judge topology

The README's §4.4a proposal was a primary judge plus a cross-check on a subset, with an
agreement metric. The measurements support that shape and refine it:

| role | model | why |
|---|---|---|
| **Primary judge** | Qwen3.8-Flash-Next | fact-checking 100 %, constraint 82,8 %, stability 100 % — the judge that catches wrong facts and is reproducible |
| **Cross-check judge** | Gemma-4-31b-it | separation 1,333, 90 % good ≥ 4 — the judge that grades quality gradations well |

**The two profiles are complementary, not redundant.** Gemma's blind spot is planted
facts (6,7 % scored 5) and it drifts under cold/warm state; Qwen's is quality separation
(only 60 % of good rows ≥ 4). A single judge would carry one systematic blind spot; the
pair covers both.

**What the topology cannot fix:** Qwen's low good-scores make it unsuitable as a ranking
instrument (model vs model). For an accept/reject gate it is fine — it errs strict, not
lenient. Gemma's missed facts make it unsuitable as the sole fact-checker. The
certification therefore supports **a gate, not a ranking**, with Qwen primary.

## 7. §4.4b acceptance threshold — draft for the freeze conference

Per the prereg the threshold is fixed *after* calibration, entering prereg §4.4b at the
freeze commit. Draft, derived from the measured bands in §5 and equally valid for either
judge because it anchors on that judge's own values:

- **Fact gate (absolute):** any item judged factually wrong (≤ 2 on factual correctness)
  is a hard fail of the run — no averaging out. Mirror of the cert rule "an accepted
  planted error (5) fails the judge."
- **Constraint gate (absolute):** any accepted constraint violation (≤ 3, judgment marked
  as a violation of a stated rule) is a hard fail unless the operator waives it
  explicitly.
- **Quality gate (anchor-normalized, per language):** mean over items ≥
  `anchor_good − 0,5` and the worst item ≥ `anchor_good − 1,5`. On the measured anchors:
  Qwen de ≥ 3,0 mean / ≥ 2,0 worst; Qwen en ≥ 3,3 / 2,3; Qwen zh ≥ 3,2 / 2,2;
  Gemma de ≥ 4,0 / 3,0; en ≥ 4,2 / 3,2; zh ≥ 4,5 / 3,5.
- **Stability gate (absolute):** ≥ 95 % within ±1 on a scored-twice subset.
- **Anchor refresh rule:** if the merged-set run moves a judge's good anchor by more than
  0,4, the gates re-derive from the new anchors before the freeze commit registers them.

These numbers are **calibration input, not a pre-registered threshold**; the
pre-registration step happens at the freeze conference per README §8.

## 8. Open items

1. **Seven cells repaired, not re-run.** The repairs (five gold rewrites, one word fix,
   one corruption cleanup) are in commit `2920bd8`; no judge re-run was performed. The
   repaired cells' gold labels are expected to restore monotonic ordering for both
   judges, which the merged-set run at freeze can confirm.
2. **Merged-set run** (stage 1 + stage 2, 60 items — Gemma ≈ 720 calls, Qwen ≈ 720 calls
   at observed rates): validates the seven repairs, gives stage-2 discrimination
   evidence, refreshes anchors. Operator decision on compute.
3. **Stage 2 has no stability items.** By design the stability subslice is entirely in
   stage 1; document that design decision in the freeze note — merged runs then rely on
   the stage-1 ten only.
4. **Freeze commit** per README §8: merge stage 1+2, recompute hashes, register the two
   JSON hashes + threshold numbers in prereg §4.4b.
5. **Pool C2/C3 remains open.**

## 9. Artifacts

```
out_c/judge_calibration/cert.json       Gemma, 300 rows, all criteria
out_c/judge_calibration/cert.log        full log incl. reasoning, untruncated
out_c/judge_calibration/qwen_cert.json  Qwen, 299 scored rows + 1 NULL row, all criteria
out_c/judge_calibration/qwen_cert.log   full log
scripts/quinn/judge_calibration.py      the harness (frozen rubric, resume, checkpoint)
data/evals/judge_set_v1/cert_items.json          stage 1 (repaired)
data/evals/judge_set_v1/cert_items_stage2.json  stage 2 (planted notes added)
```

## 10. Reproduce

```bash
# Gemma (takes ~6-8 h at observed rates)
timeout 259200 .venv/bin/python -u scripts/quinn/judge_calibration.py \
  --base-url http://192.168.178.200:1234/v1 --model gemma-4-31b-it \
  --set data/evals/judge_set_v1/cert_items.json \
  --out out_c/judge_calibration/cert.json --log out_c/judge_calibration/cert.log --resume

# Qwen (parallel, own endpoint; ~5-8 h)
timeout 259200 .venv/bin/python -u scripts/quinn/judge_calibration.py \
  --base-url http://192.168.178.51:8888/v1 --model Qwen3.8-Flash-Next \
  --set data/evals/judge_set_v1/cert_items.json \
  --out out_c/judge_calibration/qwen_cert.json \
  --log out_c/judge_calibration/qwen_cert.log --resume
```
