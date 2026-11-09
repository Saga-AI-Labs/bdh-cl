# Pool cohort C2 review: structure clean, one wording finding, coverage honest

**Date:** 2026-11-09
**Reviewer:** Quinn (a0-quinn) · **Author:** asb (GLM agent)
**Scope:** `data/evals/judge_set_v1/pool_instructions_c2.json` (180 items, DRAFT-for-review)
**Verdict:** LGTM with one wording fix and a stated coverage limit. Not a full
cell-by-cell read — see §5.

## 1. Automated checks (all pass)

| check | result |
|---|---|
| JSON parse, schema, status | pass |
| IDs contiguous, 180 unique | pass |
| lang/block integrity (60/60/60) | pass |
| domain vocabulary ≤ 2 per item | pass |
| difficulty vocabulary | pass |
| constraint ≤ 60 chars | pass |
| Mojibake / zero-width / ANSI scan | **0 hits** |
| repo wordlist scan | **1 hit** — see §2 |
| 6-gram Jaccard vs C1 and vs C2 | **0 pairs above 0.30** |
| zh quotation-mark pairs | **0 unbalanced** |
| CJK in de/en items | 7 hits, all quoted contract vocabulary — legitimate |

## 2. The one finding: `p_en46` uses the word "corpus"

```
Our FAQ model answers Chinese queries with German or English fragments, though the
corpus is single-language. Explain in plain terms which signal a model uses to pick
its reply language, why it misfires, and which two small fixes help.
```

**This is not a repo-internal leak** — "corpus" here is the ordinary ML sense, not
the project's data directory. But it is still a finding, and for a different reason:

**A pool instruction should not name the mechanism it is testing.** The item asks the
model to explain *which signal a model uses to pick its reply language*. The word
"corpus" presupposes that the answer is "the language of the training corpus" — it
narrows the answer space in a way the question does not. The same is true of
"fragments": it tells the model that the failure mode is mixed-language output.

**Fix:** replace "corpus" with a neutral term ("source material", "training data",
"the material it was trained on") and drop "fragments" ("though the source material
is single-language"). The item then asks for the signal instead of naming it.

**This is the same class as the `p_de74` "Ohne Gesetzeszitate" constraint** — a
constraint that is satisfiable and violable, but which shapes the answer in a way the
question does not justify. Here it is the instruction, not the constraint.

## 3. Fact-feasibility (the seven slots GLM flagged)

All seven are `hard`, all answerable from general knowledge, no post-2024 events
required, no statute numbers pinned as facts inside instructions:

| idx | scene | assessment |
|---|---|---|
| 21 | late quality rejection, inspection windows | both regimes' notice periods are settled law; the comparison is answerable |
| 26 | receivables assignment ban vs factor | the no-assignment clause's reach differs between systems; the question is comparative, not regime-pinned |
| 27 | tech license: registration + improvements | the two issues are separate and the negotiation framing is answerable |
| 30 | plant telemetry cross-border | the compliance gates are regime-named (CISG/GDPR as furniture), not statute-pinned |
| 62 | Beijing award → German enforcement | the New York Convention route is settled; the question asks for the steps, not the outcome |
| 72 | certifying a CN doc for DE authorities | the certification routes are procedural; the question asks which route, not which law |
| 73 | breach-notification timeframes | both regimes have notification duties; the question asks who and when, not a specific hour count |

**No contested item found.** The seven are hard because they require two-regime
comparison, not because the gold is disputed.

## 4. zh register (12-item sample)

The sample reads naturally: no translationese, correct 「」 and "" pairs, occupation
nouns used in their scene-native form (农民工工资保证金, 大写金额, 营业执照). The
"请给…讲清楚" register is consistent across items and matches the brief-audience
framing.

**One observation, not a finding:** the zh items use "请向/请给/请解释" consistently,
while the de items vary between "Erkläre" and "Erkläre dem/der". The en items use
"Explain"/"Brief"/"Walk through". The register variation is deliberate and matches
the audience framing — it is not a defect.

## 5. Coverage — what this review is and is not

**This is not a full cell-by-cell read of 180 items.** It is:

- the full automated scan (wordlist, mojibake, dupes, quotes, CJK)
- all 54 constraints read against their instructions
- the 7 fact-feasibility slots read in full
- a 12-item zh register sample
- the 6 asymmetric slots (74/78) read in full

**Not covered:** the remaining ~160 items' instruction quality, domain-tag
correctness, and register. Those were authored by the same process that produced C1,
which passed a full cell-by-cell review (83151bb), and the automated checks find no
structural difference.

**Recommendation:** accept C2 into the pool at freeze with the `p_en46` fix. If a
full cell-by-cell read is wanted before the freeze, it is a separate pass and should
be scheduled as one.

## 6. Asymmetric slots 74/78 — no alignment needed

| slot | de | zh | en | assessment |
|---|---|---|---|---|
| 74 | leg-de, biz | biz, leg-x | leg-en, biz | NDA duration framing; the leg-tag is the local regime's contract law — correct as tagged |
| 78 | leg-de, biz | leg-cn, biz | leg-en, biz | deferred purchase price; the leg-tag is the local M&A regime — correct as tagged |

**No uniform tagging needed.** The asymmetry is the point: the same scene is
tagged with each side's own regime, which is what the pool is for.

## 7. Difficulty floor — keep the easy items

The 33 easy items (11 per language) are deliberately trivial. GLM asks whether the
composition metric has use for floor items.

**Yes, and here is the reason:** the metric's worst-case principle (§4.4b) needs a
floor to measure against. If the pool has no easy items, a model that fails on
moderate items cannot be distinguished from one that fails on everything — the
floor is what makes the failure rate interpretable. Keep them.

## 8. What I did not verify

- **The remaining ~160 items' instruction quality.** Not read.
- **The domain tags beyond the 6 asymmetric slots.** Not individually checked.
- **Whether the 180 C2 items are truly novel scenes or variants of C1.** The 6-gram
  audit found no near-dupes, but a semantic-duplicate check (same scene, different
  wording) was not performed.
- **The `p_en46` fix.** Not applied — the review is the verdict, the fix is the
  author's next commit.
