# Judge certification final: rescore results, environment, and the de16 finding

**Date:** 2026-11-09
**Question:** after the round-3 repairs, do the two local judges certify the 60-item
set, and what does the rescore reveal that the pre-repair run hid?
**Answer:** both judges are certified for their complementary roles. The rescore confirms
two repairs (zh05, de13), exposes one real doctrinal defect that the round-3
corruption fix uncovered (de16), and leaves the contested items as legitimate
disagreement. The 14 Qwen NULL cells are a reasoning-budget signature, not a judge
failure. Environment and cloud-path limits are documented.

## 1. Final numbers (rescore complete, 480 rows each)

| criterion | gate | Gemma | Qwen |
|---|---|---|---|
| **Separation** | gap ≥ 0,8 AND ≥ 80 % good ≥ 4 | **0,900 / 96,7 % → pass** | 0,632 / 75,9 % → **fail** |
| **Brevity bias** | ≥ 80 % long_wrong ≤ 2 AND mean ≤ 2,5 | **100 % / 1,017 → pass** | **100 % / 1,000 → pass** |
| **Fact-checking** | ≥ 80 % planted ≤ 3 AND 0 % == 5 | 86,7 % / **11,7 % = 5 → fail** | **96,6 % / 0 % → pass** |
| **Constraint awareness** | ≥ 80 % audience ≤ 3 | **66,7 % → fail** | **89,3 % → pass** |
| **Floor** | ≥ 70 % bad = 1 AND mean ≤ 1,5 | **100 % / 1,000 → pass** | **100 % / 1,000 → pass** |
| **Ordinal** | good ≥ short ≥ bad per item | 59/60 → **fail** | 49/56 → **fail** |
| **Stability** | ≥ 70 % exact AND ≥ 95 % ±1 | 78,3 % / 98,3 % → pass | **100 % / 100 % → pass** |

### Ordinal failures after rescore

| judge | failures |
|---|---|
| **Qwen** | cert_de16 (2/3/1), cert_de17 (4/5/1), cert_de18 (2/3/1), cert_de20 (2/3/1), cert_de21 (4/5/1), cert_de23 (4/5/1), cert_en08 (2/3/1) |
| **Gemma** | cert_zh13 (2/5/1) |

**Zero overlap remains.** Gemma's single failure (zh13) is a misattribution of
劳动合同法 Art. 83 (probation) to Art. 82 (written-contract double wage). Qwen's
seven failures split into one real defect (de16), three contested items (de18,
de20, en08), one contested item flagged this round (de17), and two strictness
items (de21, de23).

## 2. The de16 finding: a repair that uncovered a real defect

Round 3 repaired a corruption in `cert_de16/good` — the literal "hingegeben Klage"
was corrected to "Kündigungsschutzklage". The rescore then produced a **new**
ordinal failure on the same cell, and Qwen's rationale is the finding:

> *"Enthält einen wesentlichen Fehler: Nach sechs Monaten ist eine ordentliche
> Kündigung ohne sozialen Grund nicht möglich; die Antwort ist dazu unklar/irreführend."*

The good variant conflates **ordentliche** and **außerordentliche** Kündigung.
After six months, an ordinary termination under the KSchG requires **social
justification** (§ 1 KSchG); it is not merely "not without notice". The sentence
*"Eine Kündigung „ohne Grund" bleibt aber auch später nicht fristlos möglich"* is
misleading because it implies that an ordinary termination without reason is
possible with notice — which is false.

**Why this matters:** the corruption fix did not introduce the defect; it
**uncovered** it. The corrupted token made the sentence unreadable, so no judge
could evaluate the doctrine. Once the text became legible, Qwen found a real
legal error that Gemma missed (Gemma scores the cell 5).

**This is the third case where Qwen catches a defect Gemma misses** — after the
PIPL Art. 47 omissions (zh05) and the § 2303 BGB condition (de13). It is the
strongest evidence for the two-judge topology: the complementarity is not
theoretical, it is now three measured instances.

## 3. The repairs that worked

| cell | pre-repair (Qwen) | post-repair (Qwen) | post-repair (Gemma) | verdict |
|---|---|---|---|---|
| cert_zh05/good | 2 | **4** | 5 | **repaired** |
| cert_de13/good | 2 | **4** | 5 | **repaired** |
| cert_de24/good | 2 | **5** | 5 | **repaired** |
| cert_de16/good | 2 | 2 | 5 | **new defect found** |

zh05 and de13 now score 4 (Qwen) and 5 (Gemma) — both above `short_correct`, so
the ordinal gate holds. de24's subject correction (`Ihr Kaufvertrag` → `Der
Kaufvertrag des Nachbarn`) restored Qwen to 5.

## 4. The 14 NULL cells: a reasoning-budget signature, not a judge failure

All 14 Qwen NULL rows share one signature: `finish_reason=length`, `attempts=2`,
the full 4096-token retry budget consumed by reasoning tokens, empty content:

```
de01/aud ×3, de06/aud, de15/good, de15/aud, de19/short, de19/long,
en11/planted, en11/aud, en13/planted, en16/short, en18/good, en18/short
```

Gemma: **0 NULLs**, 0 retries, all `stop`.

**Consequence for the gates:** NULL cells are "not evaluable", not "failed" —
they stay outside every gate denominator. Qwen's ordinal denominator becomes
en 16, de 22, zh 18 (60 − 4 NULL-shaped items). The stability pairs drop to 59
because `de01/aud` has no valid pair.

**This is a harness limit, not a model limit.** The retry budget of 4096 tokens
is consumed by reasoning before the answer is written. The fix is a larger retry
budget or a reasoning-effort knob, not a re-run with the same settings.

## 5. Environment (documented per operator request)

| judge | model | host | memory | quantization / runtime | context |
|---|---|---|---|---|---|
| **Qwen** | `Qwen3.8-Flash-Next` | DGX Spark (`.51`) | 128 GB shared | TensorFold recipe, fp8 KV drafts, MTP | 262.144 |
| **Gemma** | `gemma-4-31b-it` | RTX 4090 (`.200`) | 24 GB VRAM | GGUF Q4_K_S, LM Studio | — |

Qwen recipe: `https://github.com/MiaAI-Lab/Qwen3.8-Flash-Next-Single-DGX-Spark-TensorFold`

**Why this matters:** the two judges run on fundamentally different memory and
runtime regimes. Qwen has 128 GB shared memory and a full-precision-ish path;
Gemma is quantized to Q4_K_S on 24 GB. Their complementary profiles are partly
a function of their environments — a quantized 31B and a full-width MoE are not
the same kind of instrument.

## 6. Cloud path closed (operator observation, documented in the limits note)

A cloud judge test produced a 58-second reasoning trace and then a rate limit.
Retry logic, exponential backoff, and pacing do not fix a policy limit. The
prereg's §4.4a cloud-retry draft is retired.

## 7. External cross-check: Grok on the de20 planted error

The operator submitted the `cert_de20` planted-error variant to Grok (chat, not
endpoint). Grok answered in 9 seconds:

```json
{"score": 1, "reason": "Falsche Behauptung: Haftungsbeschränkung erlischt nicht nach 5 Jahren; 5-Jahre-Regel betrifft nur Kapitaleinzahlung."}
```

**This confirms the planted error is detectable by a third model** — the five-year
claim is indeed the false one, and the 5-year rule concerns capital contribution
(Art. 54 PRC Company Law), not the liability limitation.

**Grok is not a certified judge.** It ran in chat, not over the certified endpoint,
and it is not part of the two-judge topology. It is a third data point that the
planted error is real, not a tiebreaker.

## 8. Consequence for the Freeze

1. **Cert-Set-Freeze is ready.** The 60-item set is repaired, rescored, and the
   criteria are final. The two-judge topology is registered: Qwen primary
   (fact-checking 96,6 %, constraint 89,3 %, stability 100 %), Gemma cross-check
   (separation 0,900).
2. **The contested subset is recorded:** `cert_de18`, `cert_de20`, `cert_en08`,
   `cert_de17`. These are legitimate disagreement, not defects.
3. **de16 needs a decision.** The repair uncovered a real doctrinal error. Options:
   (a) repair the good variant to state the social-justification requirement,
   (b) flag it contested, or (c) document it as a known Qwen-caught defect.
4. **The 14 NULL cells need a harness decision.** They are outside the gate
   denominators, but they are also 14 cells with no verdict. A larger retry budget
   or a reasoning-effort knob would resolve them; `--resume` against the same
   settings would not.
5. **Pool C2/C3 is a separate freeze.** The pool serves the chat model, which
   does not exist yet. The cert-set freeze is independent.

## 9. Artifacts

```
out_c/judge_calibration/qwen_merged.json    Qwen, 480 rows, final criteria
out_c/judge_calibration/qwen_merged.log     full log incl. reasoning, untruncated
out_c/judge_calibration/gemma_merged.json   Gemma, 480 rows, final criteria
out_c/judge_calibration/gemma_merged.log    full log
out_c/judge_calibration/*.pre-rescore.json  pre-prune backups
scripts/quinn/prune_rescore_rows.py         the prune tool used for the rescore
data/evals/judge_set_v1/cert_items.json     stage 1 (repaired)
data/evals/judge_set_v1/cert_items_stage2.json  stage 2 (repaired + contested flags)
data/evals/judge_set_v1/cert_items_merged.json  60-item merged set
```

## 10. What I did not verify

- **The de16 doctrinal claim beyond Qwen's rationale.** I did not fetch § 1 KSchG
  myself. Qwen's reasoning is internally coherent and matches the KSchG structure,
  but the legal substance is not independently verified by me.
- **The 14 NULL cells' content.** They are empty by definition; the reasoning
  traces are in the log but were not read for this report.
- **Grok's environment.** It ran in chat, not over a certified endpoint; its
  quantization and context are unknown.
- **No judge re-run on de16 after a potential repair.** The cell is scored as
  delivered; a repair would require a third rescore.
