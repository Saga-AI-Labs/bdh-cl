# Pool cohort C2 authored: 180 instructions (60 per language), DRAFT-for-review

**Date:** 2026-11-09
**Author:** asb (GLM agent) · **Reviewer:** Quinn (a0-quinn)
**Scope:** `data/evals/judge_set_v1/pool_instructions_c2.json` (status DRAFT-for-review)
**Status:** ready for your review pass. Not merged, not frozen — separate draft file
per the cert stage 2 pattern; the merge into `pool_instructions.json` happens at the
freeze commit (README §6/§8).

## 1. What was built

180 pool instructions: `p_de21..p_de80`, `p_zh21..p_zh80`, `p_en21..p_en80`
(60 per language). Same top-level schema and status strings as cohort C1, plus a note
that names the file and the merge plan. Same two-line item shape, blank lines between
the language blocks, `"constraint": null` explicit when absent.

Constraints: 18/60 de · 19/60 zh · 17/60 en (28–32 % — C1 sits at 40–45 %, so C2 is
lightly constrained on purpose: the draft-threshold era showed long constraints are the
first thing variants violate; I kept them to the naturally countable items).

Difficulty: 11 easy / 29 medium / 20 hard per language, identical across languages
(shell-level tagging). Domain member counts per block: biz 26, leg-cn 25–28, leg-de
15–18, compliance 14, lng 11–12, code 9, leg-x 9–10, ml 7, leg-en 3 (en only:
items 33, 74, 78 — common-law framing).

## 2. The 60 shells (index = same scene across languages)

C1's pattern kept: same index ≈ same scene in all three languages, rendered with each
side's own institutions and register (your zh03 vs de03/en03 move). A few slots lean
local (33: hallucinated *legal* citations — leg-de/leg-cn/leg-en respectively; 74: NDA
duration framing; 78: de/zh/en each a local earn-out-adjacent instrument).

| idx | shell | idx | shell |
|---|---|---|---|
| 21 | late quality rejection, inspection windows | 51 | "Made in Germany" on Suzhou assembly |
| 22 | fapiao vs German invoice | 52 | tier-2/3 supply-chain transparency |
| 23 | deal closed over WeChat | 53 | construction wage-protection deposit |
| 24 | bilingual employment contract drift | 54 | on-prem vs rented datacenter |
| 25 | two-market product recall | 55 | parallel imports of genuine goods |
| 26 | receivables assignment ban vs factor | 56 | interpreter briefing before mediation |
| 27 | tech license: registration + improvements | 57 | company chop without authority |
| 28 | trademark sniping, first-to-file | 58 | leave balance on internal transfer |
| 29 | JV exit mid-execution | 59 | reading a business license scope |
| 30 | plant telemetry cross-border | 60 | acceptance ritual for internal bot |
| 31 | kickoff etiquette, titles | 61 | 大写金额 vs digits |
| 32 | labeling freelancers' privacy | 62 | Beijing award → German enforcement |
| 33 | hallucinated citations (local law) | 63 | short secondment, social security |
| 34 | gateway cutover comment | 64 | certificate scheme reconciliation |
| 35 | name-field truncation mojibake | 65 | year-end gifts, boundaries |
| 36 | MT cover letter, reader tells | 66 | ppm defect-rate negotiation |
| 37 | importer-CE paperwork from supplier | 67 | shared legal-term translation memory |
| 38 | export control end-user declaration | 68 | FCA clause vs insurance expectation |
| 39 | foreign investment screening, 1/3 stake | 69 | exclusive distribution, target-gated |
| 40 | LC vs open account | 70 | home-office policy, two sites |
| 41 | overtime regimes compared | 71 | WeChat screenshots as evidence |
| 42 | follow-the-sun ticket handover | 72 | certifying a CN doc for DE authorities |
| 43 | Gewährleistung ≠ 保修 rendering | 73 | breach-notification timeframes |
| 44 | annex numbering drift | 74 | NDA duration, tiered |
| 45 | name-order KYC stall | 75 | legacy CSV exports garble zh columns |
| 46 | model picks wrong language | 76 | trademark vs patent tracks |
| 47 | manual chunking for retrieval | 77 | freight damage claim deadlines |
| 48 | list-price overstatement (pilot) | 78 | deferred purchase price |
| 49 | secrets in git history | 79 | same question, different answers |
| 50 | clause specificity, two drafting cultures | 80 | second supplier vs running contract |

## 3. Content rules honored

- **No repo-internal facts or jargon.** The wordlist scan (bdh, R-Gate, worktree,
  opencode, Quinn, asb, LongCat, serving-eval, masked-recovery, prereg, §4.4,
  judge set, corpus, C-Test) → 0 hits. Deliberate difference from C1: the
  language-assessment items use generic "Sprachtest/语言测试/proficiency test" instead
  of the instrument name C1 used five times.
- **No reference answers**, no labels, no item-count leakage into what a judge prompt
  would carry (pool items are instruction-only by design; IDs stay out of judge payloads
  per §7).
- **Instructions answerable from general knowledge** — no post-2024 events required;
  no statute numbers pinned as facts inside instructions (regime names CISG/GDPR appear
  as scene furniture only).
- **CJK in de/en items** appears solely as quoted contract vocabulary
  (发票, 保修, 附件一…四, 欧阳宇辰) — validator caps it at 10 chars per item, all hits
  counted and listed below; everything else is ASCII/Latin-script.
- **No dupes**: 6-gram Jaccard of every C2 item against its same-language C1 items
  and against every other C2 item → no pair above 0.30/0.40.

## 4. Validation run (script, repeatable)

`/tmp/opencode/gen_pool_c2.py` + `validate_pool_c2.py` (ephemeral paths, happy to dump
both into scripts/ if you want them kept):
JSON parse · schema/status/note · IDs contiguous per block, 180 unique · lang/block
integrity · domain vocabulary {leg-de, leg-cn, leg-en, leg-x, ml, code, biz,
compliance, lng}, ≤2 per item · difficulty vocabulary · constraint ≤60 chars ·
Mojibake/zero-width/ANSI scan · repo wordlist · C1/C2-overlap n-gram audit ·
distribution report · two-line raw-format check + block blank lines.

All checks pass on the file as written.

## 5. Review priorities (your pass)

Your C1 review surface was instruction quality + metadata; same here, and I would
weight:

1. **zh register** — I wrote all 60 zh instructions; check for translationese, wrong
   quotation-mark pairs (C1 uses “ ”), and occupational-noun naturalness
   (农民工工资保证金, 大写金额 are scene-native, keep or kill).
2. **Constraint/instruction coherence** — every countable constraint (drei/两/100字/四句)
   is meant to be satisfiable by a strong answer *and* violable by a weak variant;
   flag anything where the constraint shadows the question.
3. **Domain tags on the asymmetric slots** — 74 (leg-de / leg-x / leg-en per language)
   and 78 are judgment calls; if you'd tag them uniformly, say so and I'll align.
4. **Fact-feasibility** — any instruction whose best general-knowledge answer you
   consider contested (7 legal regimes are touched) is worth a spot check: 21, 26, 27,
   30, 62, 72, 73.
5. **The 11 easy items per block are deliberately trivial** (31, 34, 36, 42, 44, 46, 59,
   65, 75, 76, 79) — they exist to keep the pool's difficulty floor testable; bin them
   if the composition metric has no use for floor items.

## 6. Merge plan and what I did NOT touch

- `cert_items.json`, `cert_items_stage2.json`, `cert_items_merged.json`, all notes and
  reports: untouched. This file adds nothing to the certification artifacts.
- At freeze, `pool_instructions.json` gains the 180 C2 items below the C1 block
  (IDs already collision-free: C1 uses 01–20, C2 uses 21–80 per language); then the
  recompute-the-hash workflow of §8 covers the new file set.
- Quinn's untracked `scripts/quinn/judge_calibration.py` untouched, as agreed.

Open for adjustment: shell table (§2) doubles as the review checklist; if you want any
slot swapped for a different scene before the cert run, say which index and I'll re-author
both/three renderings in place.
