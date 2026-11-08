# Stage 2 cert items ready for review: 30 new traps in a separate file, live run untouched

**Date:** 2026-11-08
**Addressed to:** Quinn (`scripts/quinn/judge_calibration.py` author, running the 72 h cert
run started 16:13:12)
**Evidence:** `data/evals/judge_set_v1/cert_items_stage2.json` pushed as `4ada77a`;
README §5 rules 1–7, §8 freeze procedure, §9 stage status updated in the same commit.
**Status:** DRAFT-for-review. No action needed on the live run — it snapshots
`cert_items.json` at start and never reads this new file; merge happens at the freeze
commit (§8), not before your LGTM.

## What the file is

30 new cert items as a separate batch: **cert_de11–de24** (14 de, heavy-legalese stress:
Kontakt-/Erb-/Miet-/AGB-/GmbH-Vertretung/KSchG-§-HGB-Karenz/Handelskauf-Rüge PR-C law on
German, §§-dense audience variants), **cert_en11–en18** (unfair dismissal, CRA 2015
s. 22, tenancy deposit s. 212–215, UK GDPR Art. 12(3), Hyde v Wrench, Companies Act
2006 s. 177 as a format item, ERA s. 86 notice, defamation 1-year limitation), and
**cert_zh11–zh18** (民法典 §586/587 定金, §188 诉讼时效, 劳动合同法 §19 试用期, §23 竞业
限制 compensation, 电子签名法 §14, §590(2) 迟延履行后不可抗力, 消保法 §25 七天无理由,
§1077 离婚冷静期). All diffs target the same six labels per item (good,
short_correct, long_wrong, planted_error, audience_violation, bad) with planted-correct
citations in the `note` field, same as stage 1.

## What I want your eyes on (priority order)

1. **Planted-correct facts:** every `planted_error.note.correct` — check the citation,
   not just the gist. The German corpus leans on § 551 (Kaution), § 356 (digital),
   § 2303 (Pflichtteil), § 2247 (Datumsangabe), § 77 GmbHG, § 23 KSchG, § 74 HGB,
   § 377 HGB, § 566 BGB, § 652 BGB, § 306 BGB, §§ 2078/2081/2082 BGB, § 573 BGB.
   The zh corpus is 民法典/劳动合同法-heavy; the en corpus is ERA/CRA/Housing/UK GDPR/CA.
   If any "correct" is itself wrong, that plant falls with it.
2. **Rule 6 compliance by role:** only `audience_violation`/`bad` may violate the item
   constraint; good/short_correct/long_wrong/planted must satisfy it (sentence-count
   caps, §-citations where asked, en16 = exactly three bullets for all four of those
   roles).
3. **Rule 7 artifact scan:** this batch was written in pieces and repaired; I ran a
   mechanical scan (CJK-in-de/en, markup tokens, duplicated ids, label order, planted-
   note presence) and fixed ~35 spots — a second pair of eyes on the rewritten de
   variants (esp. de11/de14–de18 audiences) would close the residual risk properly.
4. **Duplication check vs stage 1:** none of these 30 are intended to overlap topics
   in `cert_items.json`; flag if any reads as a near-duplicate.

## Not in this review

The live run's early signal — `cert_de01/good` in the restart reads rep1=2 (173 s,
first call after startup) then rep2=rep3=5 (~70 s each). Whether that is a cold-state
effect or my suspected gold defect (Trennungsprinzip sentence in de01/good) gets
disentangled post-run against the full rep-latency table, per README §4 decision rules;
not a stage-2 question.

**After your LGTM:** pool C2 (~180 instructions, 60/lang) as a separate draft, then the
freeze conference (§8: merge stage 1+stage 2, recompute hashes, prereg §4.4b commit).

— asb, 2026-11-08
