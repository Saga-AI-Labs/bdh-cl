# Pool cohort C3 review: structure clean, two false positives, coverage honest

**Date:** 2026-11-10
**Reviewer:** Quinn (a0-quinn) · **Author:** asb (GLM agent)
**Scope:** `data/evals/judge_set_v1/pool_instructions_c3.json` (180 items, DRAFT-for-review)
**Verdict:** LGTM with two false positives and no required fix. Not a full
cell-by-cell read — see §5.

## 1. Automated checks (all pass)

| check | result |
|---|---|
| JSON parse, schema, status | pass |
| IDs contiguous 81–140 per block, 180 unique | pass |
| lang/block integrity (60/60/60) | pass |
| domain vocabulary ≤ 2 per item | pass |
| difficulty vocabulary (11 easy / 29 medium / 20 hard) | pass |
| constraint ≤ 60 chars | pass |
| Mojibake / zero-width / ANSI scan (extended: U+FFFD, surrogates, bidi controls) | **0 hits** |
| repo wordlist scan | **2 hits** — see §2, both false positives |
| 6-gram Jaccard within C3 (> 0.40) | **0 pairs** |
| 6-gram Jaccard vs C1 and C2 (> 0.30) | **0 pairs** |
| zh quotation-mark pairs | **0 unbalanced** |
| CJK in de/en items | **0 hits** |

## 2. The two wordlist hits are false positives

| item | word | actual usage |
|---|---|---|
| `p_de95` | "variant" | "zwei Modellvarianten parallel" — model variants in an A/B test |
| `p_en95` | "variant" | "two model variants in parallel" — same scene |

**Neither is repo jargon.** The scene is a parallel A/B test of two model versions,
which is a legitimate technical usage, not a reference to the project's eval harness.
The zh counterpart (`p_zh95`) uses "模型版本" and does not trip the wordlist.

**No fix needed.** I record them because the wordlist is a filter, and a filter's
false positives are exactly what a cell read is for — the same lesson as the C1
review's four false positives.

## 3. Fact-feasibility (the eight slots GLM flagged)

All eight are `hard`, all answerable from general knowledge, no post-2024 events,
no statute numbers pinned as facts:

| idx | scene | assessment |
|---|---|---|
| 88 | procurement listing (政采目录) | the listing procedure and qualification thresholds are public-administration process; comparative, not regime-pinned |
| 90 | non-compete compensation | both systems' compensation requirements are settled; the question is comparative |
| 93 | impressum vs hosting prerequisites | the two obligations are different in kind and the question asks what each requires |
| 102 | customs valuation dispute | the dispute procedure and supporting documents are procedural; no pinned outcome |
| 119 | on-site service double taxation | the question asks what papers prevent double taxation, not which treaty applies |
| 120 | used-machine import gating | the import regime is procedural; the question asks what evidence and approvals |
| 124 | insolvency claim ranking | both regimes' ranking frameworks are settled; the question asks where the claim sits |
| 125 | border inspection conduct | the question asks for conduct and pre-trip protection, not legal advice |

**No contested item found.** Same conclusion as C2.

## 4. The `p_de124` constraint is justified — keep it

GLM discloses that `p_de124` uses the "Ohne Gesetzeszitate" class my C2 review
criticized on `p_de74`.

**My assessment: keep it, and here is the difference.** In C2, `p_de74` asked for
an explanation of a contractual concept, and the no-citation constraint removed the
most useful vocabulary. In C3, `p_de124` asks the **management** how a claim ranks
and what suspending shipments means — a ranking-and-consequences question for a
non-legal audience. The plain-language framing is the point of the scene.

**The constraint does not shadow the question.** It excludes the one thing a
non-legal audience cannot act on (a paragraph number), not the content.

## 5. zh register (10-item sample)

Scene-native occupation nouns are used correctly: 政采目录, 工伤, 企业年金, 备件,
大写金额. No translationese, no unbalanced quotes.

**One structural observation, not a finding:** two items (`p_zh88`, `p_zh134`)
open with "我们的…请给…" — a double-verb construction that is grammatical but
slightly heavy. It is consistent with the register of the other items and does not
affect answerability. Not a defect.

## 6. Coverage — what this review is and is not

**This is not a full cell-by-cell read of 180 items.** It is:

- the full automated scan (wordlist, extended mojibake, dupes, quotes, CJK)
- all 57 constraints read against their instructions
- the 8 fact-feasibility slots read in full
- a 10-item zh register sample
- the 4 asymmetric slots (116, 120, 124, 128) read in full

**Not covered:** the remaining ~160 items' instruction quality, domain-tag
correctness, and register.

**Recommendation:** accept C3 into the pool at the pool freeze. No fix required.

## 7. A note on method: a display artifact, not a data defect

While reading the zh sample, the terminal rendered `p_zh125` with three replacement
characters (`笔记���本`). A byte-level check shows **0 bytes of U+FFFD** in the file
and a character-level scan of all 180 items finds no replacement or control
characters. The file is clean; the artifact was in the terminal rendering of the
tool output.

**This is the same lesson as the C1 review:** the automated scan is a filter, and a
filter's output must be checked at the level that matters. Here the check was byte
level, and it cleared the item. A review that stopped at the rendered output would
have raised a false defect.

## 8. What I did not verify

- **The remaining ~160 items' instruction quality.** Not read.
- **The domain tags beyond the 4 asymmetric slots.** Not individually checked.
- **Whether the 180 C3 items are semantically novel or variants of C1/C2.** The
  6-gram audit found no near-dupes; a semantic-duplicate check was not performed.
- **The `p_zh125` rendering artifact beyond the byte and character scans.** I did
  not reproduce the display condition.
