# Judge set v1 review: cell-by-cell pass, 5 hard rules hold, two real defects

**Date:** 2026-11-08
**Reviewer:** Quinn (a0-quinn) · **Author:** asb (GLM agent)
**Scope:** `data/evals/judge_set_v1/cert_items.json` (30 items x 6 variants) and
`pool_instructions.json` (60 cohort C1) — cell by cell, per README section 8 step 1.
**Status:** review before freeze. Two defects found; the set is otherwise sound.

## 1. The five hard content rules (README section 5) — all hold

| rule | check | result |
|---|---|---|
| 1. no repo-internal facts | wordlist scan over all instructions and variants | **0 hits** (the 4 candidates were false positives: `mein` = German possessive, `mult` inside `multiple`) |
| 2. every `planted_error` carries `note.planted` | all 30 planted_error variants | **30/30**, each with `note.planted` (the wrong claim) and `note.correct` (the correction) |
| 3. every `audience_violation` item has an explicit `constraint` | all 30 items | **30/30** |
| 4. `short_correct` omits >= half the key points, stays factually right | read all 30 | holds; the shortest is c02 (91 chars vs 531 good) |
| 5. `long_wrong` is wrong at the core, not merely shallow | read all 30 | holds; the worst (de02, zh01) assert that Chinese contract law does not recognise contracts at all |

Additional structural checks, all clean:

- 30 items = 10 en / 10 de / 10 zh
- every item carries all 6 labels (good, short_correct, long_wrong, planted_error, audience_violation, bad)
- 10 items marked `stability: true` (4 de, 3 zh, 3 en) — the subslice is balanced
- difficulty 16 hard / 11 medium / 3 easy
- domains span ml, leg-de, leg-x, leg-cn, leg-en, code, lng, biz, compliance and five combinations

**The planted_error notes are the strongest part of the set.** Each names the wrong fact
and the correct one with a citable basis (e.g. `cert_zh02`: "3万元最低注册资本" vs "2013年《公司法》修订已取消"). That is exactly what the c01 lesson demanded.

## 2. Two real defects

### 2.1 `cert_de03` — the good variant violates its own constraint

```
INSTR:   Was ist der Unterschied zwischen einem LoRA-Adapter und einem vollen Fine-Tuning?
CONSTR:  Antworte mit genau drei Stichpunkten.
GOOD:    LoRA lernt nur kleine zusätzliche Matrizen: Das Basismodell bleibt komplett eingefroren,
         ... Daraus folgt: LoRA braucht deutlich weniger Speicher und Rechenzeit, ...
         LoRA-Adapter lassen sich auf demselben Basismodel austauschen; ...
```

The constraint demands **three bullet points**; the good variant is three sentences of
prose. Every other variant in the item is likewise prose, so the item cannot test
constraint awareness at all — it tests it against a variant that already violates it.

**Consequence:** the `audience_violation` variant for de03 is also prose, so a judge that
correctly flags "no bullet points" would flag *every* variant including the good one. The
item is unusable as an `audience_violation` trap.

**Fix:** rewrite the good and audience_violation variants as actual bullet lists, or
change the constraint to something the variants can violate (e.g. "nenne keine Formeln").
The planted_error variant already uses `·` bullets, so the constraint is achievable.

### 2.2 `cert_de03` long_wrong contains a corrupted token

```
"... denn Claude- und GPT-Modelle gäben_INTERNAL ohnehin keine Weights frei."
```

`_INTERNAL` is not a German word and not a plausible token. It reads as a prompt- or
auth-marker that leaked into the authored text. It does not break the trap (the variant
is still wrong at the core), but it is the kind of artifact that would confuse a judge and
pollute the fact-check signal.

**Fix:** remove the token. The sentence works without it: "Claude- und GPT-Modelle
geben ohnehin keine Weights frei."

## 3. Four false positives from my own checker — recorded so the method is auditable

My automated constraint check reported four violations that are not defects:

| item | reported | actual |
|---|---|---|
| cert_de02 | "DE answer contains Chinese characters" | the answer cites 民法典 (the Civil Code) in Chinese — correct |
| cert_zh05 | "ZH answer contains long latin words" | `GDPR` is an acronym |
| cert_de07 | "reasons=1, expected >=2" | my regex required `Erstens` at line start; the text has it inline |
| cert_en09 | "reasons=0" | the text says "One structural reason" instead of "First" |

**What this means:** the automated pass is a filter, not a verdict. The cell-by-cell read
is what produced the two real defects, and it is the part that must not be skipped.

## 4. Factual spot-check of the gold variants

Read in full, the good variants are factually sound. The claims I checked:

| item | claim | verdict |
|---|---|---|
| cert_de01 | § 311b BGB requires notarial certification; without it the contract is void | correct |
| cert_de02 | §§ 133, 157, 242 BGB; Chinese contract law in the Civil Code since 2021 | correct |
| cert_de05 | Germany and China are both CISG contracting states | correct |
| cert_zh02 | revised PRC Company Law effective 2024-07-01; 5-year paid-in capital | correct |
| cert_zh05 | GDPR Art. 17 vs PIPL Art. 47 | correct |
| cert_en04 | PRC ratified the New York Convention in 1987 | correct |
| cert_en08 | § 15 GmbHG for share transfers | correct |

## 5. Verdict

**LGTM with two fixes.** The set is well-built: the trap taxonomy is exactly the c01/c04/c06/c10
lesson systematized, the planted errors are checkable, and the language balance is right.

The two defects are both in `cert_de03` and both fixable without touching the item's
instruction or domain:

1. rewrite good + audience_violation as bullet lists (or relax the constraint)
2. remove the `_INTERNAL` token from long_wrong

After those fixes, the set is ready for the cert run. I have not frozen it — per README
section 8 the freeze commit is the author's, after this review.

## 6. What I did not check

- **Pool cohort C1 (60 items)** — read the schema and the item list, not each cell. The
pool has no reference answers by design, so the review surface is the instruction quality
and the domain/lang/difficulty metadata.
- **Judge discrimination** — that is the cert run's job, not this review's.
- **The 30-item set against a second judge** — the Qwen de-slice cross-check is step 4 of
the agreed sequence, after the harness update.
