# Judge certification countercheck: all report numbers verified, one report claim corrected, seven items repaired — recommendation: Qwen primary, Gemma cross-check, gate not ranking

**Date:** 2026-11-09
**Addressed to:** the operator (decision on judge topology per prereg §4.4a).
**Review of:** `docs/reports/2026-11-08_judge-certification.md` (6cab936, Quinn) —
per house rule, every check below is a recomputation from the raw rows
(`out_c/judge_calibration/cert.json`, `qwen_cert.json`), not a restatement;
items marked **found** are facts I verified that the report does not state.
**Bottom line for the operator:** both models can judge for §4.4a/4.4b, and the
right topology is a gate, not a ranking: primary judge = Qwen3.8-Flash-Next,
cross-check judge = Gemma-4-31b-it, agreement metric anchor-normalized. The five
open item defects named in the report are repaired in this commit (plus one
further defect **found** during the validation scan).

## 1. Verification method

criteria() and stability() were re-implemented from README §4's definitions and
run over the raw `rows` lists of each `*.json` (300 rows each, rep-1 slice for
the variant gates, repeats for the stability subslice). I did not rely on the
harness-precomputed `criteria_all`/`criteria_per_lang`/`stability` blobs except
to cross-check against them. First pass: my comparison script printed
`match-harness:False` per language — that was an artifact of my comparator
(key-name mismatch in the diff set), not a harness error; after alignment,
**every number in the report matches the raw rows exactly**.

## 2. The verified numbers

| check (README §4) | Gemma | Qwen |
|---|---|---|
| separation (gap, good ≥ 4) | **1.333 / 90.0 % — pass** | 0.867 / 60.0 % — fail |
| fact (planted ≤ 3, never 5) | 90.0 % ≤ 3 but **6.7 % = 5 — fail** | **100.0 % / 0 % — pass** |
| constraint (audience ≤ 3) | **50.0 % — fail** | 82.8 % — pass |
| brevity (long_wrong ≤ 2, mean) | 100 % / 1.0 — pass | 100 % / 1.0 — pass |
| floor (bad = 1, mean) | 100 % / 1.0 — pass | 100 % / 1.0 — pass |
| ordinal (per item) | 27/30 | 27/30 |
| stability (60 pairs) | 78.3 exact / 96.7 in ±1 — pass | **100 / 100 — pass** |

Per-language slices:

- **Gemma constraint fails in all three slices** — audience_violation rows ≤ 3:
  en 4/10, de 6/10, zh 5/10. This is not a language blind spot but a uniform
  leniency toward stated-audience/format violations.
- **Qwen passes constraint in all three slices**: en 9/10, de 8/9 valid
  (cert_de03 and cert_de04 got 4), zh 8/10 — the zh slice lands exactly on the
  80.0 % boundary.
- Qwen's two planted-5 **found** items for Gemma are `cert_de03` and
  `cert_en02` (2/30 = 6.7 %, matching the report).
- Ordinal failures — all six judge-level cells traced to item defects, fixed
  this round (section 4): Gemma `cert_de01` 2/3/1, `cert_de10` 3/4/1,
  `cert_en09` 2/4/1; Qwen `cert_de01` 2/3/1, `cert_en08` 2/3/1,
  `cert_zh05` 2/3/1.
- Latency **found**: Qwen mean 8.5 s (median 6.2) vs Gemma mean 76.1 s
  (median 60.9, max 320.3). Gemma additionally shows a cold/warm state effect
  (section 3.3).

## 3. Corrections to the report

### 3.1 "300 calls each, 0 failures" — wrong for Qwen

Gemma: 300 rows, all `finish_reason=stop`, 0 nulls, 0 retries — claim holds.
Qwen: 299 scored rows + **one NULL row** — `cert_de06`/`audience_violation`,
rep 1: `score=None`, empty `judge_content`, `finish_reason=length`,
`attempts=2`, and the full 4096-token completion budget was consumed by
reasoning tokens (`completion_tokens_details.reasoning_tokens=4096`). The row
was not recovered (there is no rep-2 row; non-stability items run a single rep).
Materially:

- the audience gate still passes: 24/29 valid = 82.8 % (report number);
- treating the NULL as a miss: 24/30 = **80.0 % — still passes** the ≥ 80 % band
  exactly, so the verdict is robust under the strictest reading.

### 3.2 The cert_de01 defect description quotes a claim the item does not contain

The report says the good variant "says *'Both require offer, acceptance, and
consideration'*" — consideration appears **nowhere** in `cert_de01` (found by
direct text check). The actual defect, visible in both judges' rep-1 rationales
(Qwen: *"Der notariell beurkundete Kaufvertrag ist bereits mit Beurkundung
wirksam, nicht erst mit Eintragung einer Auflassungsvormerkung."*), is that the
good variant claims the contract only becomes effective once the
Auflassungsvormerkung is entered — a false doctrine, correctly rejected by both
judges. The repair follows the rows, not the report quote.

### 3.3 Minor book-keeping: "four ordinal failures" is five

The §3 table lists five distinct items (de01, de10, en09 fail on Gemma; de01,
en08, zh05 on Qwen) = six judge-level failures. The substance of the section —
shared item defect, judge consensus, no judge defect — is verified as written.

## 4. Item repairs in this commit (round 2, pre-freeze)

Directly to `cert_items.json` / `cert_items_stage2.json` (the same defect class
the report's §5 asks for; each fix traced to a row-level rationale):

| cell | defect (source) | repair |
|---|---|---|
| cert_de01/good | contract-effective-only-with-Auflassungsvormerkung (qwen rep1, above; gemma rep1 caught it cold) | principle corrected: § 125 BGB nullity + § 311b Abs. 1 S. 2 BGB healing via completed transfer + entry; 4 plain sentences |
| cert_de01/audience_violation | "Übergabevertrag" is not an instrument **found** | word fix → "Übereignung"; legalese violation kept by design |
| cert_de10/good | literal corruption ("**undresponses**", gemma rep1 rationale) | two clean concrete hints (constraint: exactly two, no clichés) |
| cert_en08/good | overclaim: sale/warranty terms must sit in the notarial act (qwen rep1) | § 15 Abs. 3 GmbHG scoped correctly: the assignment of the share and the obliging clause require the form; price/warranty can be ordinary writing (practice bundles); notarization explained at first use (constraint) |
| cert_en09/good | listening failure attributed to the "writing system"/logography (gemma rep1) | two reasons, one = listening decoding (prosody/syllable-structure), one = morphology; no orthographic mechanism claim (constraint: exactly two reasons) |
| cert_zh05/good | false PIPL Art. 47 public-interest exceptions (qwen rep1 rationale verbatim: *“将《个保法》第47条误述为明确设有国家安全、公共卫生等删除例外”*) | correct GDPR Art. 17 grounds/exemptions vs PIPL Art. 47 (purpose fulfilled, service stopped, retention expired, statutory catch-all) grounds, scope contrast; citations annotated per constraint |
| cert_de02/long_wrong | kana + merged-token corruption ("einajer", "に関する") **found** in the round-2 validation scan — same class as de10 | junk removed, substantive words kept ("Erst ein Verwaltungsbescheid … ohne eine Genehmigung …") |
| cert_en16 + cert_en17 (stage 2) | planted_error without note (Quinn's review fcb7296 §2.1) | notes added — **Quinn's exact proposed texts** |

The diff is minimal: 7 cells in stage 1, 2 note blocks in stage 2. No re-run
was performed; the repaired cells' gold labels are expected to restore monotonic
ordering for both judges (all six ordinal failures were defect-driven), which
the merged-set run at freeze can confirm.

## 5. Anchor bands (rep-1 means) — the calibration input for §4.4b

| variant | Gemma | Qwen |
|---|---|---|
| good | 4.73 (de 4.50 / en 4.70 / zh 5.00) | 3.67 (de 3.50 / en 3.80 / zh 3.70) |
| short_correct | 3.40 | 2.80 |
| planted_error | 2.10 | 1.97 |
| audience_violation | 3.43 | 2.66 |
| bad | 1.00 | 1.00 |

Consequence for the §4.4a agreement metric: the same answer reads 4.5 on Gemma's
scale and 3.5 on Qwen's de-slice; **raw cross-judge agreement would be confounded
by the offset**. Normalize per-language against the judge's own good anchor
before comparing, or the metric measures the offset, not the disagreement.

## 6. Recommendation (prereg §4.4a)

The §4.4a gate is topology, not preference: *a judge is an HTTP endpoint, not an
agent session*. Both candidates satisfy it as-run (plain local endpoints, no
agent context, no agenda; neither model is GLM or LongCat, so the self-reference
caveat is moot).

**Primary judge: Qwen3.8-Flash-Next.** It is the only candidate that (a) catches
every planted fact in all three languages (100 % ≤ 3, zero 5-scores), (b) is
exactly self-consistent (100/100 on the 60 stability pairs), (c) passes the
constraint gate in all three slices, and (d) errs strict (good anchor 3.67,
planted anchor 1.97) — the right bias for the prereg's worst-case principle.
Its weakness (separation fail, good-anchor compression) disqualifies it only
from *ranking* — which is not what §4.4b defines.

**Cross-check judge: Gemma-4-31b-it.** Best quality separation (gap 1.333,
90 % of good ≥ 4). It must not be the primary verifier of facts: two planted
errors scored 5, and its stability misses are self-contradictory on identical
text — `zh04/planted` reps read "substantially incomplete … fails to explain
Value/Softmax" (rep 1, score 3) then "clear, accurate, and intuitive" (rep 2/3,
score 5); `de01/good` [2, 5, 5] runs cold-slow → warm-fast (173 s → 70 s), i.e.
the false doctrine was caught cold and missed warm. **found**: both misses are
judge-side drift under warm/cold state, not item defects.

**Can a second local model judge German?** Yes — verified on the de-slice:
Qwen de fact = 100 %, constraint = 88.9 % (valid rows), floor/brevity pass; its
only de misses were exactly the fixed anchor defects (de01, en08 resp. de01).
The §4.4a cross-check question from the prereg is answered by Qwen for German
and by Gemma for fine quality gradations (en/zh), with de spot-checks if wanted.

## 7. §4.4b acceptance threshold — draft for the freeze conference

Per the prereg the threshold is fixed *after* calibration, entering prereg
§4.4b at the freeze commit. Draft, derived from the measured bands above and
equally valid for either judge because it anchors on that judge's own values:

- **Fact gate (absolute):** any item judged factually wrong (≤ 2 on factual
  correctness) is a hard fail of the run — no averaging out. Mirror of the cert
  rule "an accepted planted error (5) fails the judge."
- **Constraint gate (absolute):** any accepted constraint violation (≤ 3
  judgment marked as a violation of a stated rule) is a hard fail unless the
  operator waives it explicitly.
- **Quality gate (anchor-normalized, per language):** mean over items ≥
  anchor_good − 0.5 and the worst item ≥ anchor_good − 1.5. On the measured
  anchors: Qwen de ≥ 3.0 mean / ≥ 2.0 worst; Qwen en ≥ 3.3 / 2.3; Qwen zh
  ≥ 3.2 / 2.2; Gemma de ≥ 4.0 / 3.0; en ≥ 4.2 / 3.2; zh ≥ 4.5 / 3.5.
- **Stability gate (absolute):** ≥ 95 % within ±1 on a scored-twice subset.
- **Anchor refresh rule:** if the merged-set run moves a judge's good anchor by
  more than 0.4, the gates re-derive from the new anchors before the freeze
  commit registers them.

These numbers are calibration input, not a pre-registered threshold; the
pre-registration step happens at the freeze conference per README §8.

## 8. Open items / freeze agenda

1. **Merged-set run** (stage 1 + stage 2, 60 items — Gemma ≈ 720 calls,
   Qwen ≈ 720 calls at observed rates): validates the seven repairs, gives
   stage-2 discrimination evidence (Quinn's "did not check" §5 item), refreshes
   anchors. Operator decision on compute.
2. **Stage-2 stability**: by design there is no stability subslice there
   (Quinn, fcb7296); document that design decision in the freeze note — merged
   runs then rely on the stage-1 ten only.
3. **Freeze commit** per README §8: merge stage 1+2, recompute hashes, register
   the two JSON hashes + threshold numbers in prereg §4.4b.
4. Pool C2/C3 remains open.
5. README §9 stage-status updated in this commit.

## 9. What I did not check

- No judge re-run on the repaired items (no compute burned pre-freeze).
- Other legal citations beyond those touched by the repairs — stage-2 citations
  were cell-by-cell verified by Quinn; stage-1 citations by his 83151bb review.
- `scripts/quinn/judge_calibration.py` code beyond the criteria()/stability()
  definitions used for the recompute (untracked working copy).

— asb (GLM agent), 2026-11-09
