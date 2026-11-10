# Pool cohort C3 authored: 180 instructions (60 per language), DRAFT-for-review

**Date:** 2026-11-10
**Author:** asb (GLM agent) · **Reviewer:** Quinn (a0-quinn)
**Scope:** `data/evals/judge_set_v1/pool_instructions_c3.json` (status DRAFT-for-review)
**Status:** ready for your review pass. Not merged, not frozen — separate draft file
per the cert stage 2 pattern (same as C2); the merge into `pool_instructions.json`
happens at the pool freeze, and the hashes get registered then — together with C1
and C2, not as part of the cert-§4.4b registration of 2026-11-09.

## 1. What was built

180 pool instructions: `p_de81..p_de140`, `p_zh81..p_zh140`, `p_en81..p_en140`
(60 per language). Same top-level schema (`judge_set_v1_pool`) and status string as
C1/C2, same note pattern that names the file and the merge plan. Same two-line
item shape, blank lines between language blocks, `"constraint": null` explicit
when absent.

Composition per language (shell-level, identical across languages):

- Difficulty: 11 easy / 29 medium / 20 hard. The easy slots keep the pool floor
  your §7 asked to keep (list in §5.5).
- Constraints: 19/60 (32 %), same slot set in all three languages: 81, 85, 89, 92,
  97, 103, 110, 112, 117, 121, 124, 129, 130, 131, 133, 136, 137, 138, 139.
  Types follow the C2 mix: word limits (92, 139), audience fixing (136), reply
  language (110), bullets (112), sentence counts (131, 133), everyday analogy
  (117), count/list constraints (81, 85, 89, 97, 103, 121, 129, 130, 137, 138),
  no-status (124).
- Domain member counts per block (de / zh / en): leg-cn 25/29/25, biz 23/23/23,
  leg-de 16/14/16, compliance 20/19/20, leg-x 11/10/11, code 10/10/10,
  lng 10/10/10, ml 5/5/5. **leg-en: 0 by design** — the common-law framing stays
  in C2's 33/74/78; C3 scenes pair leg-de/leg-cn/leg-x with the operational
  domains.

## 2. The 60 shells (index = same scene across languages)

C1/C2 pattern kept: same index ≈ same scene in all three languages, rendered with
each side's own institutions and register. All 60 scenes are fresh — none of the
90 C1/C2 shells is redone (audit in §4 backs this mechanically).

| idx | shell | idx | shell |
|---|---|---|---|
| 81 | late, higher-priced order acknowledgment | 111 | FAT/SAT acceptance gates |
| 82 | supplier-hall fire, insurer subrogation | 112 | whistleblower channel, kickback tip |
| 83 | distributor swap, full-price buy-back demand | 113 | CN subsidiary → group ERP access |
| 84 | factory-direct vs HK trading company | 114 | pension top-up for CN staff |
| 85 | "as new" refurb claim, yardsticks | 115 | model name sounds wrong abroad |
| 86 | forwarder handovers, documents error | 116 | employee representation under acquisition |
| 87 | chip shortage vs penalty clause | 117 | source-code escrow, triggered release |
| 88 | public-procurement catalog listing | 118 | free samples must declare value |
| 89 | machine vibration data resold | 119 | on-site training billed DE→CN |
| 90 | sales chief → direct competitor | 120 | nine-year-old machine import approval |
| 91 | first consumer e-commerce, returns | 121 | capstone prototype IP, two clauses |
| 92 | late payment, FX risk placement | 122 | safety labels: pictogram vs text |
| 93 | one hosting, two market site requirements | 123 | image copies to unpicked serving nodes |
| 94 | font licensing across media/markets | 124 | biggest customer in restructuring |
| 95 | parallel A/B with real customer queries | 125 | business-data laptop at the border |
| 96 | controller end-of-support, five more years | 126 | component list with provenance |
| 97 | two audits, opposite verdicts | 127 | customer list as trade secret |
| 98 | seconded technician injured on site | 128 | repair shipments zig-zag, double formalities |
| 99 | reseller parallel brand, collisions | 129 | staff survey anonymity, both cultures |
| 100 | vulnerability report via wrong form | 130 | meeting transcription, customer data |
| 101 | group-wide signing authority table | 131 | DST asymmetry in scheduling |
| 102 | customs disputes the transfer prices | 132 | campaign photos, faces and releases |
| 103 | server wipe before resale | 133 | ten-year spares promise vs five-year plan |
| 104 | manual warnings drift zh vs de | 134 | one analytics stack, two consent flows |
| 105 | probation exit for an underperformer | 135 | both holiday sets in one calendar |
| 106 | Arbeitszeugnis vs graded reference | 136 | regional accents vs speech recognition |
| 107 | rounding up vs down moves volumes | 137 | end-of-life take-back duties |
| 108 | cold-chain excursion, curve questioned | 138 | coverage evidence across the package |
| 109 | certified translations for a German court | 139 | bilingual statement, second-language risks |
| 110 | unregistered design shown at a fair | 140 | bilingual disclaimer that holds in both markets |

Closest lane neighbors were checked by hand and shifted: 107 is order-rounding
operations, not C2's 61 (大写金额 digit rendering); 114 is staff-side pension top-up,
not C2's 90 (non-compete); 109 formalizes what C2's 72 only implied (certifying a
CN doc for DE authorities); the 6-gram audit keeps all lanes below threshold.

## 3. Content rules honored

- **No repo-internal facts or jargon.** Wordlist scan (bdh, R-Gate, worktree,
  opencode, Quinn, asb, LongCat, serving-eval, masked-recovery, prereg, §4.4,
  judge set, C-Test) → 0 hits. Plus the lesson from your p_en46 review §2 applied
  systematically: **no instruction names the mechanism it tests**. "Corpus" and
  "fragments" are completely absent; the two ML-language-adjacent items (115, 136)
  ask about effects and countermeasures, not mechanisms.
- **No reference answers**, no labels, no item-count leakage into what a judge
  prompt would carry (pool items are instruction-only; IDs stay out of judge
  payloads per §7).
- **Instructions answerable from general knowledge** — no post-2024 events, no
  statute numbers pinned as facts (regime names appear only as scene furniture).
- **CJK in de/en items: 0 hits.** No scene in this cohort called for quoted
  contract vocabulary; all de/en text is Latin-script, zh items stay zh-only.
- **zh punctuation**: 3 items carry curly “ ” pairs (85, 99, 134), all balanced;
  no 「」 corner quotes (consistent with C1/C2 usage).
- **No dupes**: 6-gram Jaccard of every C3 item against same-language C1 and C2
  items (0.30 bound) and against every other C3 item (0.40 bound) → clean.

## 4. Validation run (script, repeatable)

`/tmp/opencode/gen_pool_c3.py` + `validate_pool_c3.py` (ephemeral paths; happy to
dump both into `scripts/` if you want them kept):
JSON parse · schema/status/note block · IDs contiguous 81–140 per block, 180
unique · language-block integrity · domain vocabulary {leg-de, leg-cn, leg-en,
leg-x, ml, code, biz, compliance, lng}, ≤2 per item · difficulty vocabulary ·
constraint ≤60 chars · mojibake/zero-width/ANSI scan · repo wordlist · 6-gram dup
audit vs C1 file AND C2 file plus within-C3 (bounds 0.30/0.40) · per-language
distribution report · two-line raw-format check + block blank lines (2).

**ALL CHECKS PASS** on the file as written. Raw sha256 of the DRAFT file (bytes):
`993ebbb95cada741071a3bd0cbb521f4c0862dcb72e5f2a1d6c468fba5f4695f`.

## 5. Review priorities (your pass)

Same surface as C1/C2 (instruction quality + metadata), weighted:

1. **zh register** — all 60 zh instructions are fresh this cohort; check
   translationese and quote pairs. Scene-native occupation nouns this time:
   政采目录 (88), 工伤 (98), 企业年金 (114), 备件 (133) — prune anything
   that reads translated.
2. **Constraint/instruction coherence** — the 19 constrained slots are listed in
   §1. Each countable constraint is meant to be satisfiable by a strong answer
   and violable by a weak variant; flag anything where the constraint shadows
   the question. One disclosure: **124 uses the "Ohne Gesetzeszitate" class your
   review §2 criticized on p_de74** — in C3 the scene's management-audience,
   plain-language framing is the justification (the question asks for ranking
   and consequences, not law). If you disagree, I'll drop the constraint from
   124; it is the only member of the class in this cohort.
3. **Domain tags on the asymmetric slots** — deliberate, not uniform: 116
   (de/en leg-de vs zh leg-cn-first: the works-council scene is asked from the
   acquirer's home base in zh), 128 (per-side customs framing), 124/120/88
   (CN-side regimes tagged leg-cn on all languages). If you'd tag any of them
   uniformly, say which and I'll align.
4. **Fact-feasibility** — regime items worth the same spot check you did for C2:
   88 (procurement listing steps), 90 (non-compete compensation requirement),
   93 (impressum vs hosting prerequisites), 102 (customs valuation dispute
   flow), 119 (on-site service double taxation), 120 (used-machine import
   gating), 124 (insolvency claim ranking), 125 (border inspection conduct).
   General-knowledge answerable by design; no statute numbers, no post-2024
   events. If any is contested as a general-knowledge answer, name it and I'll
   re-author in place.
5. **The 11 easy items per block are deliberately trivial** (84, 106, 107, 115,
   118, 122, 129, 131, 132, 135, 139) — pool floor, same rationale as your §7
   keep; bin them if the composition metric has no use for floor items.

## 6. Merge plan and what I did NOT touch

- `cert_items.json`, `cert_items_stage2.json`, `cert_items_merged.json`, all
  notes and reports: untouched. The cert freeze (416336d) stands as frozen;
  nothing in this file touches the certification artifacts or their prereg
  registrations.
- At the pool freeze, `pool_instructions.json` gains the 180 C3 items below the
  C2 block (IDs already collision-free: C1 uses 01–20, C2 21–80, C3 81–140 per
  language), then the recompute-the-hash workflow re-registers the merged pool
  file: C1 + C2 + C3 = **420 pre-discard**, ~15 % discard expected in review
  (C4 stays reserve per §6).
- The reviewed `p_en46` fix is applied in the C2 draft in the same push; the
  fix record is `docs/notes/2026-11-10_pool-c2-en46-fix.md`.
- Quinn's untracked scripts untouched, as agreed.

Open for adjustment: shell table (§2) doubles as the review checklist; if you
want any slot swapped for a different scene before the pool freeze, say which
index and I'll re-author the renderings in place.
