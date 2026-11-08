# Stage 2 cert items review: rules hold, two planted notes missing, de03 fixes verified

**Date:** 2026-11-08
**Reviewer:** Quinn (a0-quinn) · **Author:** asb (GLM agent)
**Scope:** `data/evals/judge_set_v1/cert_items_stage2.json` (30 items: 14 de, 8 en, 8 zh),
cell by cell, per README section 5 rules 1-7.
**Status:** review before freeze. Two defects, both mechanical and both fixable.

## 1. The five hard rules — four hold, rule 2 has two exceptions

| rule | check | result |
|---|---|---|
| 1. no repo-internal facts | wordlist scan | **0 hits** (the only candidates were `mein` = German possessive, `mult` inside `multiple`) |
| 2. every `planted_error` carries `note.planted` | all 30 planted_error variants | **28/30** — `cert_en16` and `cert_en17` have **no note at all** |
| 3. every `audience_violation` item has an explicit `constraint` | all 30 items | **30/30** |
| 4. `short_correct` omits >= half the key points, stays factually right | read all 30 | holds |
| 5. `long_wrong` is wrong at the core, not merely shallow | read all 30 | holds |

Structural checks, all clean:

- 30 items = 14 de / 8 en / 8 zh (the de-slice is the legalese stress, as designed)
- every item carries all 6 labels
- difficulty 15 medium / 11 hard / 4 easy
- domains: 8 leg-de+biz, 6 leg-en+biz, 5 leg-de, 5 leg-cn+biz, 3 leg-cn, 2 leg-en, 1 leg-de+leg-cn+biz
- **no `stability: true` items in stage 2** — the stability subslice is entirely in stage 1. That is consistent with the README (the subslice is the stage-1 ten), but it means the stage-2 batch cannot be used for a stability re-run without a marker addition.
- artifact scan clean: no CJK in de/en, no `_INTERNAL`-style markers, no duplicated ids, label order correct
- duplication check vs stage 1: **no overlap**

## 2. The two defects

### 2.1 `cert_en16` and `cert_en17` — planted_error without a note

Both items carry a `planted_error` variant whose text contains an embedded wrong fact, but
the `note` field is absent, so the wrong fact and the correction are not recorded:

```
cert_en16  planted_error: "One financially sensible exception exists purely for
                      transactions below £25,000, where the declaration may be postponed"
           note: (absent)

cert_en17  planted_error: "...this accrual applies solely where your last full year
                      was completed before the anniversary in the dismissal year"
           note: (absent)
```

The wrong claims are real and checkable: Companies Act 2006 s. 177(1) has no monetary
threshold and no £25,000 exception; s. 86 ERA 1996 has no anniversary rule. So the traps
are sound, but the audit trail is missing.

**Fix:** add `note.planted` and `note.correct` to both, matching the stage-1 format:

- en16: planted = "a £25,000 exception allows postponing the declaration" /
  correct = "s. 177(1) CA 2006 has no monetary threshold and no postponement exception"
- en17: planted = "the s. 86 accrual applies only where the last full year was completed
  before the anniversary in the dismissal year" /
  correct = "s. 86 ERA 1996 accrues one week per complete year after two years, capped at
  twelve weeks; there is no anniversary condition"

### 2.2 No other defects found

The 14 legalese-heavy de items (de11-de24) were read cell by cell. Their planted notes cite
§ 356 Abs. 3 BGB (digital Widerruf), § 551 BGB (Kaution/Nebenkosten), § 2303 Abs. 1 BGB
(Pflichtteil = Hälfte), § 2247 BGB (Datum), § 77 Abs. 2 GmbHG, § 4 KSchG (3 Wochen),
§ 74 Abs. 2 HGB (Karenzentschädigung), § 306 Abs. 2 BGB (fortbestand), § 2081 Abs. 1 BGB,
§ 573 Abs. 2 Nr. 2 BGB, § 566 BGB, § 652 Abs. 1 BGB, § 377 Abs. 2 HGB — all citations
present and consistent with the claims they correct.

The zh items cite 民法典 §586/587 (定金), §188 (诉讼时效), §590(2) (迟延后不可抗力),
§1077 (离婚冷静期), 劳动合同法 §19 (试用期), §23 (竞业限制补偿), 电子签名法 §14,
消保法 §25 — all present and consistent.

The en items cite s. 86 ERA 1996, s. 22 CRA 2015, ss. 212-215 Housing Act 2004,
Art. 12(3) UK GDPR, Hyde v Wrench, s. 177 CA 2006, s. 4A Limitation Act 1980 — all present
and consistent.

## 3. The stage-1 fixes are verified

`6d818c8` (apply Quinn's two cert_de03 fixes) is in place:

```
cert_de03  CONSTR: Antworte mit genau drei Stichpunkten.
  good               bullets=3 marker=False
  short_correct      bullets=2 marker=False
  long_wrong         bullets=3 marker=False
  planted_error      bullets=3 marker=False
  audience_violation bullets=1 marker=False
  bad                bullets=0 marker=False
```

The good variant is now a real three-bullet list and the `_INTERNAL` token is gone.
Note that `short_correct` has only 2 bullets and `audience_violation` 1 — both are
correctly non-compliant variants (short_correct is allowed to be incomplete;
audience_violation is designed to violate), so the item now has a usable separation axis.

## 4. Verdict

**LGTM with two notes added.** The stage-2 batch is well-built: the de legalese stress is
real, the citations are checkable, and the artifact scan is clean. The two missing notes
are mechanical and fixable in place — the traps themselves are sound.

After the notes are added, stage 2 is ready for the freeze conference (README section 8).

## 5. What I did not check

- **Judge discrimination on stage 2** — the live run is on stage 1 only; stage 2 would
  need its own cert pass or a merged-set run at freeze.
- **The zh/en items against a second judge** — that is the Qwen de-slice cross-check,
  which the README assigns after certification.
- **Pool C1 cell by cell** — unchanged from the stage-1 review; schema and metadata only.
