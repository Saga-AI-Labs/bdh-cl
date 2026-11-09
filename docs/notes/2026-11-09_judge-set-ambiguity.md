# Judge-set ambiguity: the ordinal gate measures agreement with gold labels, not truth

**Date:** 2026-11-09
**Trigger:** operator observation during the review of the five Qwen `2/3/1` items.
**Consequence:** the Ordinal criterion needs a per-item ambiguity flag, or it must be
applied only to uncontested items. The certification criterion set changes before the
Freeze commit, and §4.4b inherits the same limit.

## 1. The operator's point

> *"cert_zh05 kann ich nicht beurteilen, aber die anderen Items sind nicht-trivial. Das
> könnten Prüfungsfragen aus einem Jura-Examen sein, und die vertragsrechtlichen Items
> könnten echte Streitpunkte sein, bei denen man auch in der Realität von unterschiedlichen
> Rechtsanwälten unterschiedliche Antworten erhält. Ich denke, dass es in der Natur der
> Sache liegt, dass unterschiedliche Modelle unterschiedliche Meinungen haben."*

This is a methodological finding, not a note about three items. **The Ordinal gate
assumes a correct answer.** Where the gold label encodes one position among several
defensible ones, a judge that disagrees is scored as failing — even when the judge is
right. The gate then measures *agreement with the author's labels*, not correctness.

That is the same error class this project has hit repeatedly: measuring a property of
the instrument and attributing it to the object.

## 2. Classification of the five Qwen `2/3/1` items

| item | type | evidence | verdict |
|---|---|---|---|
| **cert_zh05** | **verifiable incompleteness** | PIPL Art. 47 lists five grounds; the good variant names (一), (二), (五) and omits **(三) 个人撤回同意** and **(四) 违反法律、行政法规或者违反约定处理个人信息**. The GDPR side states only Art. 3(1) territorial scope and omits Art. 3(2) extraterritoriality, while the PIPL side does state its extraterritorial limb. Both omissions are checkable against the statutory text. | **real defect, repaired** |
| **cert_de13** | **verifiable overgeneralization** | § 2303 BGB: grandchildren take a Pflichtteil only in the nachrückende Linie — when they step into the place of a deceased or disinherited parent. The good variant says Enkel "behalten einen Pflichtteilsanspruch" without the condition, and the question is a *specific* one ("Meine Großmutter hat mich enterbt"). | **real defect, repaired** |
| **cert_de18** | contested | § 305/306 BGB core is correct. The sentence "Vorformulierungen zählen trotzdem" is ambiguous, not clearly wrong; Qwen reads it as "rechtlich irreführend". | **judge strictness** |
| **cert_de20** | contested | Core correct for a three-sentence layperson answer (Art. 3 + Art. 23 PRC Company Law). Qwen demands Art. 54 acceleration, personal guarantees, one-person-company detail — completeness beyond the stated constraint. | **judge strictness** |
| **cert_en08** | contested | GLM deliberately chose the position that price/warranty terms can sit in ordinary writing; Qwen disputes it. Qwen additionally demands apostille/authority detail for the US holding. The scope question is genuinely disputed in the literature. | **judge strictness** |

**Two of five are real defects that Qwen caught and Gemma missed.** That is the
complementary-coverage argument, and it holds. **Three of five are differences of
judgment on contested questions.**

## 3. The zero-overlap finding, reinterpreted

The Merged-set run found **zero overlap** between Gemma's three Ordinal failures
(`cert_de16`, `cert_de24`, `cert_zh13`) and Qwen's eight (`cert_de13`, `de17`, `de18`,
`de20`, `de21`, `de23`, `en08`, `zh05`).

The first reading — "the judges disagree on different items, therefore they cover each
other" — is only half right. The correct reading:

- Where the failure is a **real defect** (zh05, de13), zero overlap means **Qwen catches
  what Gemma misses**. That is coverage.
- Where the failure is **strictness** (de18, de20, en08), zero overlap means **the two
  judges hold different positions on the same contested ground**. That is also coverage,
  but of a different kind: neither is "right" in an absolute sense, and the metric cannot
  tell them apart without an ambiguity flag.

## 4. Consequence for the Freeze

1. **Ordinal needs a per-item ambiguity flag.** Items whose gold label is contested must
   be marked at authoring time, and the gate must be computed over the uncontested subset
   only. Otherwise the certification score is a mixture of correctness and taste.
2. **The three contested items stay in the set but are marked.** They are not defects; they
   are legitimate disagreement. Marking them is what makes the remaining Ordinal failures
   interpretable.
3. **§4.4b inherits the limit.** The production judge metric measures agreement with gold
   labels. A contested item in the production set would score a legitimate disagreement as
   a failure. The prereg's §4.4b must state that its items are authored to be uncontested,
   or the metric is unsound.
4. **The Freeze note must record which items are contested** and which gate was computed
   over which subset. Without that, the registered thresholds are ambiguous.

## 5. Repairs in this commit

| cell | repair |
|---|---|
| `cert_zh05`/good | PIPL Art. 47(三) withdrawal of consent and (四) violation added; GDPR Art. 3(2) extraterritorial limb added, so both sides state their scope symmetrically |
| `cert_de13`/good | § 2303 BGB condition made explicit: children always, grandchildren only in the nachrückende Linie; compressed to stay within the four-sentence constraint |
| `cert_de18`, `cert_de20`, `cert_en08` | **not repaired** — marked contested in this note. Changing them to satisfy Qwen would move the gold label to one side of a real dispute. |

## 6. What I did not verify

- **cert_zh05's legal substance beyond the statutory text.** The operator noted they cannot
  judge it. My finding is that the omissions are verifiable against Art. 47 and Art. 3(2);
  whether the omission is *material* to the question asked is still a judgment.
- **The three contested items.** My classification of them as contested rather than
  defective is itself a judgment, and it is the kind of judgment the operator's point
  warns about. GLM should review it before the Freeze.
- **No judge re-run on the two repairs.** The repaired cells have not been scored.
