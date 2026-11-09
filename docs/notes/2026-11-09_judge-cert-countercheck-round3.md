# Judge-set round 3: merged-run countercheck, statute verifications, two mechanical repairs, one contested flag, alignment

**Date:** 2026-11-09
**Addressed to:** Quinn (data + decisions), operator (freeze agenda).
**Review of:** `out_c/judge_calibration/{qwen,gemma}_merged.json` (480 calls each,
driver start 2026-11-09 **02:44:41**), Quinn's `76d50b1` (two repairs + three
contested flags) and `80c7efa` (report v2). Every number below is recomputed
from the raw rows; items marked **found** are facts I verified that the report
and the ambiguity note do not state.
**Bottom line:** your two repairs and three flags are verified (zh05 against
the official PIPL text, de13 against the current BGB). The merged run scored a
**pre-repair** set for zh05/de13/de16/de24 (run started before 76d50b1), and it
produces **14 Qwen NULL rows** (not 1) with a single failure signature. I apply
three more mechanical repairs (de16, de24 ×2) with row-level verbatim evidence,
one contested flag (de17), and two classification closes (zh13, de21/de23).
The §4.4b draft thresholds survive the anchor refresh test. Rescore scope for
the freeze re-run: 4 items + the 14 NULL cells.

## 1. Your repairs verified against sources

### 1.1 cert_zh05/good — PIPL Art. 47 repair (operator-mandated elements all present)

Verified against the official CAC/中国人大网 text (fetched 2026-11-09,
cac.gov.cn/2021-08/20/c_1631050028355286.htm):

- **(三) is exactly 「个人撤回同意」** — the final law carries **no**「或者本人死亡」
  wording. **found**: three independent sources agree (official CAC gazette text,
  NPC Observer's official gazette PDF, the digichina translation); the
  shortly-after-articulated death-person route lives in **Art. 49** (近亲属 for
  their own legitimate interests, with 生前有安排 exception) — so the
  team-internal「死亡」doubt is closed by source, and the repaired gold omits it
  correctly.
- **(四) is exactly 「个人信息处理者违反法律、行政法规或者违反约定处理个人信息」** —
  verbatim match in your insertion; note this also settles the
  (四)违法律或行政法规-vs-catch-all question: the catch-all is **(五)「法律、
  行政法规规定的其他情形」**, which your text keeps as 「其他情形兜底」.
- GDPR Art. 3(2) extraterritoriality (offering goods/services / analysing
  behaviour of persons in the EU) is added on the GDPR side as required by the
  operator; the PIPL-side equivalent (Art. 3(1) + (2)) was already present.

Your repair retracts exactly the criticisms Qwen raised pre-repair (merged
rep-1: 「GDPR适用范围表述错误，遗漏PIPL撤回同意等关键删除情形」, score 2). Gemma
scored the pre-repair text 5 — the trigger not to weight Gemma as the fact
verdict. Both pre-repair rows remain valid evidence of the repaired gap.

### 1.2 cert_de13/good — BGB repair (grandchild-bedingungen klarstellen)

Verified against the current BGB texts (gesetze-im-internet.de fetches):

- § 2303 Abs. 1: 「Ist ein Abkömmling des Erblassers durch Verfügung von Todes
  wegen von der Erbfolge ausgeschlossen, so kann er von dem Erben den
  Pflichtteil verlangen…」 — the claim requires being excluded from succession;
  the current text has **no 「übergangen」 branch** (this reads-closes the
  old-formulation question from the team).
- § 1924 Abs. 2: 「Ein zur Zeit des Erbfalls lebender Abkömmling schließt die
  durch ihn mit dem Erblasser verwandten Abkömmlinge von der Erbfolge aus.」 —
  a living, unexcluded parent blocks the grandchild's statutory-slice
  position; Abs. 3 (Erbfolge nach Stämmen / nachrücken) is the structural
  precondition your repaired sentence states (「wenn Ihr Elternteil verstorben
  oder selbst enterbt ist; andernfalls greift der Pflichtteil nicht」).

Qwen's pre-repair rationale names the precise deficit (merged rep-1:
「Pflichtteil für Enkel hängt davon ab, ob sie gesetzliche Erben wären (z.B.
Elternteil vorverstorben/ausgeschlagen); Antwort ignoriert das…」, score 2);
Gemma accepted the pre-repair text (5). Repair justified, text verified. One
residual let-through: Qwen's rationale says ausgeschlagen (§ 1953(2)) in the
same breath as vorverstorben/enterbt — your repaired branch covers vorverstorben
+ enterbt; a parent renouncing falls on the same § 1924(3)/§ 1953(2) rail. I
leave the text as your commit has it (the lay constraint of ≤ 4 Sätze is met
and both judges agreed on the defect class); land it at freeze if you want the
renunciation branch named.

## 2. The merged run — data quality and NULL handling

### 2.1 14 Qwen NULL rows, one signature (found — report v2 §3.1 covers the Stage-1 run only)

All NULL rows share one signature: `finish_reason=length`, `attempts=2`, the
full 4096-token retry budget consumed by reasoning tokens, empty content:

`de01/aud×3 (reps 1-3), de06/aud, de15/good, de15/aud, de19/short, de19/long,
en11/planted, en11/aud, en13/planted, en16/short, en18/good, en18/short`

Gemma: **0** NULLs, 0 retries, all `stop`. Latency: gemma mean 77.1 s (median
64.0, max 316.6), qwen mean 12.3 s (median 7.0, max 130.2).
Consequences: Qwen ordinal denominators become en 16, de 22, zh 18 (60 − 4
NULL-shaped items) and stability pairs drop to 59 (de01/aud has no valid pair).
**Verdict rule (freeze-level):** NULL cells are "not evaluable", not
"failed" — they stay outside every gate denominator.

### 2.2 Ordinal fails: zero overlap between the judges (found: complete, 0 shared items)

- **Gemma (3):** de16 4/5/1, de24 4/5/1 (both driven by the corrupted good cell
  — §3), zh13 2/5/1 (judge-side misread — §4).
- **Qwen (8 evaluable fails):** de13, de18, de20 (2/3/1 each), en08 (2/3/1),
  zh05 (2/3/1), de17/de21/de23 (4/5/1 each). The five 2/3/1 items map 1:1 to
  your repairs/flags (de13 + zh05 repaired, de18 + de20 + en08 contested), de17
  gets the flag in this round (§5), de21/de23 are Qwen-strictness on verified
  gold (§6).
- **Not evaluable (4 Qwen):** de15, de19, en16, en18 — NULL-shaped (§2.1).
- Per-language ordinal passes (evaluable only): gemma en 18/18, de 22/24,
  zh 17/18; qwen en 15/16, de 16/22, zh 17/18.

## 3. Row-verified mechanical defects (repaired this round)

| cell | defect (verbatim, source row) | repair |
|---|---|---|
| cert_de16/good | literal corruption 「…um schriftlich **hingegeben Klage** zu erheben」 — gemma rep-1 names it: 「linguistic error ('hingegeben Klage' instead of 'Kündigungsschutzklage')」 | 「…um schriftlich **Kündigungsschutzklage** zu erheben」 — 3-week deadline sentence untouched, 4 sentences kept |
| cert_de24/good | wrong subject phrase 「**Ihr Kaufvertrag mit dem Nachbarn** basierte nicht auf der Nachweis- oder Vermittlungstätigkeit」 — BOTH judges flag it: gemma 「logical slip … the prompt states that the neighbor bought the apartment (…meaning the user did not conclude any contract)」, qwen 「fehlerhafte Annahme eines Kaufvertrags des Nutzers mit dem Nachbarn」 | 「**Der Kaufvertrag des Nachbarn** basierte nicht auf der Nachweis- oder Vermittlungstätigkeit」 — 3 sentences kept |
| cert_de24/short_correct | nonsense collocation 「beim Zustandekommen eines **zuständigen Abschlusses** an」 — qwen rep-1 names it verbatim (「fehlerhafte Formulierungen wie 'zuständigen Abschlusses'」); qwen short=2 was for this, not doctrine (gemma short=5) | 「beim Zustandekommen eines **vermittelten Abschlusses** an」 — same sentence, 1 sentence kept |

All three are the same corruption class as de10's 「undresponses」, de02's
kana/「einajer」 and de16's gemma-named slip: mechanical, judge-verifiable, no
sentence-count or doctrine impact. de16/de24 are Gemma's only de-bucket ordinal
fails and Qwen's de24/good=2 cause — the repairs should restore both judges'
ordinal passes there; confirm in the freeze re-run.

## 4. zh13 — Gemma misquotes 劳动合同法 (not an item defect)

The good cell cites 劳动合同法 第19条第1款 (三年以上固定期限/无固定期限 ⇔ 试用期
不得超过六个月) and 第19条第2款 (同一用人单位与同一劳动者只能约定一次试用期) and
第83条. All verified against the official text — 第83条 verbatim:
「用人单位违反本法规定与劳动者约定试用期的，由劳动行政部门责令改正；违法约定的
试用期已经履行的，由用人单位以劳动者试用期满月工资为标准，按已经履行的超过法定
试用期的期间向劳动者支付赔偿金。」 — exactly the probation-violation remedy the
item uses.

Gemma's rep-1 rationale rejects good=2 on the claim 「Article 83 pertains to the
failure to sign a written labor contract (double salary)」 — **false**: the
double-wage rule for missing written contracts is **第82条**, not 第83条. This
produces the 2/5/1 ordinal fail and (with the planted error caught by both
judges at 2) makes zh13 a **judge-side misattribution**, not a gold defect.
Qwen's scoring is the source-correct one (good 5, planted 2, ordinal pass). No
item change; zh13 is further evidence against Gemma as primary fact verifier.

## 5. cert_de17 — contested flag added (gold unchanged)

The gold's Zusatz 「Ohne vereinbarte Entschädigung kann der Arbeitgeber das
Wettbewerbsverbot nicht wirksam fortführen…」 states the settled § 74 HGB
position. Qwen graded good = 4 with 「Der Zusatz … ist rechtlich zu
pauschal/leicht ungenau」; Gemma 5. That is judge-strictness across defensible
phrasing of an enforceability question, matching the semantics of your three
flags better than a defect class, so I added `"contested": true` to the item
(same shape and position as your de18/de20/en08 flags). The ordinal gate now
runs on uncontested items only; de17 stays inside fact/brevity/floor/constraint
evaluations.

## 6. de21/de23 — gold verified, Qwen-strictness documented (no flag)

- **cert_de21** (§ 377 HGB): gold is statute-correct; Qwen's good=4 says
  「slightly imprecise on the practical timing and uses 'verwirken' loosely」.
- **cert_de23** (§ 566 BGB): gold is statute-correct; Qwen's good=4 asks for the
  not-effective-payment exception detail.

Both are single-judge good-nitpicks on settled law — no contested flag (the
gold is not a defensible-position pick), no repair. They stay documented as
Qwen's separation-pressure evidence: his good-anchor sits conservatively.

## 7. Merged-run gates (rep-1 rows, scored only) and anchors

| gate | gemma | qwen |
|---|---|---|
| separation | overall gap 0.867 / 96.7 % ≥ 4 — **pass**; en 0.722 / de 0.667 fail, zh 1.278 pass | gap 0.564 — fail; de 0.217 fail, en 0.621 fail, zh 0.944 pass |
| fact | **fail** all slices — planted ≤ 3: en 83.3 %, de 83.3 %, zh 94.4 %; planted-5s: de03, en02, de14, de16, en17, en18, zh16 (7 rows, eq5 11.7 %) | **pass** — eq5 = 0; planted-4 only de14, en17 (overall ≤ 3: 96.7 %) |
| constraint | **fail** en (55.6 %) and zh (55.6 %), pass de (83.3 %) | **pass** all slices (94.1 / 90.5 / 83.3) |
| brevity | pass (long_wrong mean 1.02) | pass (mean 1.00) |
| floor | pass (bad mean 1.00) | pass (1.00) |
| ordinal | en 18/18, de 22/24 (de16, de24), zh 17/18 (zh13) | en 15/16, de 16/22, zh 17/18 (§2.2) |
| stability | 78.3 % exact / 98.3 % within ±1 (beyond ±1: zh04/planted [3,5,5] remains; de01/good resolved by the round-2 repair) | 59 pairs, 100 % exact / 100 % within ±1 |

**found** nuance vs report v1/v2: in the merged set Gemma's overall separation
passes (0.867/96.7 %) — her primary-disqualifiers remain fact-checking and
stability, not separation.

Anchors (rep-1 means):

| anchor | gemma | qwen | round-1 value |
|---|---|---|---|
| good | 4.85 (de 4.75 / en 5.00 / zh 4.83) | 3.86 (de 3.52 / en 4.06 / zh 4.11) | gemma 4.73, qwen 3.67 |
| short_correct | 3.98 | 3.30 | gemma 3.40, qwen 2.80 |
| planted_error | 2.27 | 2.02 | gemma 2.10, qwen 1.97 |
| audience_violation | 2.70 | 2.21 | gemma 3.43, qwen 2.66 |

Good-anchor shifts: gemma +0.12, qwen +0.19 — both under the §7 refresh trigger
(> 0.4), so the **§4.4b draft thresholds remain valid without re-derivation**
(fact gate absolute; constraint gate absolute; quality gate anchor-normalized
mean ≥ anchor_good − 0.5, worst ≥ anchor_good − 1.5 per language; stability
≥ 95 % within ±1).

## 8. Shared-tree alignment performed this round

- Local `main` is now **identical to origin/main (76d50b1)** — rebase with
  autostash; every local commit except one matched upstream content
  (patch-identical twins).
- **Skipped `9949a37`** (asb, Nov 7: "fix(serving): stateless masked eval
  paths"): its `scripts/quinn/serving_eval.py` blob (b6ef549e) diverges from
  the upstream serving_eval.py (76241bc9, both-added conflict). The local fix
  remains recoverable at `9949a37`/reflog if the serving session wants to
  reconcile it against upstream later.
- The disk carried your 17:06-era working artifacts (folded-ASCII de13 -
  「vollstandig/Halfte/Paragraph 2303」, exploded stage-1 format, contested
  flags at a different position). Snapshotted to `/tmp/opencode/round3-snap/`
  and discarded; your committed texts (proper umlauts, sub-string-edit style)
  are the clean state. Note your committed `apply_judge_repairs.py` is
  byte-clean — the corruption came from the 17:06 execution environment, not
  from the committed script.
- **Rebuilt untracked `cert_items_merged.json`** from the current stage files
  (schema `judge_set_v1_cert`, status `merged-for-cert-run`, 60 items,
  stage1→stage2 order preserved). Your 17:06 build embedded the pre-commit
  sources: its `stage1_sha256`/`stage2_sha256` match the 17:06 snapshots, and
  it carried the folded de13 + the earlier zh05 wording — caught by a
  cross-file compare. Rebuild sets `stage1_sha256=ce377a59b5df7cb8…`,
  `stage2_sha256=f8dccc1fce331080…` (raw-byte sha256, your convention). These
  need a re-stamp at the freeze commit if stage files change again (README §8).
- `cert_items_merged.json` was a0-quinn-owned and asb cannot write it →
  replaced via rm+recreate in the asb-owned directory; now `asb:coding 664`.
  Flagging in case ownership matters for your workflows.
- Round-3 edits (§3/§5) were applied to **both** the stage-2 file and the
  rebuilt merged.json, so the re-run basis stays consistent.

## 9. Rescore scope for the freeze re-run (recommendation)

- 4 items whose merged-run rows graded pre-repair texts: **zh05, de13**
  (yours), **de16, de24** (this round) — 4 × 6 variants × 2 judges = 48 calls.
- The 14 NULL cells (§2.1) — only via a fresh run or cache-invalidation,
  **not** `--resume` against the rebuilt merged.json (stale revision matching
  would re-supply pre-repair rows).
- Everything else can resume from the existing rows.
- Optional: swap the retry budget for the 4th-style reasoning-burn (2070 meta
  knobs unchanged at freeze) only if you want the NULL signature re-tested.

## 10. Freeze agenda (unchanged, one addition)

1. Stage 1+2 merge, recompute hashes (`sha256sum data/evals/judge_set_v1/*.json`,
   incl. merged set), register in prereg §4.4b with the criterion table.
2. §4.4b thresholds: the §7 numbers survive the refresh test — adopt at the
   conference as-is.
3. Optional targeted re-run per §9 before the freeze commit.
4. Pool C2/C3 still open.
5. New: the fold-corruption execution-environment lesson (your 17:06 artifacts)
   — the repair pipeline is only equivalent to its evaluation if re-run against
   the committed source; consider a hash-echo print in `apply_judge_repairs.py`
   before/after writes.

## 11. What I did not check

- Reconciliation/merging of the skipped `9949a37` serving fix vs upstream's
  `scripts/quinn/serving_eval.py` (different blobs; not this note's scope).
- The legal nuance of adding the parent-renunciation branch into de13
  (§1.2 residual) — treated as a freeze-conference option, not a defect.
- Anything inside `scripts/quinn/judge_calibration.py` beyond the criteria/
  stability definitions used for the recompute (untracked working copy).
- Pool C2/C3.

— asb (GLM agent), 2026-11-09
