# Judge calibration review: the run's real headline is not 6/10 — it is that every scored failure traces to the label set or the token budget, not the judge

**Date:** 2026-11-08
**Addressed to:** the author of `scripts/quinn/judge_calibration.py` and
`out_c/judge_calibration/calibration.json` (10-item first run)
**Evidence:** raw JSON + log read in full; script read; Kendall/gate statistics recomputed
from the raw rows; prereg v0.2 §4.4a/4.4b as of `d341f75`
**Status:** review before any scale-up. The calibration-first path and the third-party
judge choice are right. One framing correction, four fixes, two label traps, one process item.

## 1. The bias rule: agree with the practice, but the stated ground is the wrong one

Excluding both agent-owned models (LongCat under Agent Zero, GLM under Opencode) from
judging is the right operational rule — a third-party local model removes the question at
zero cost. But the ground is not "self-preference bias": the judged answerer in §4.4 is
the **BDH-CL chat model**, and neither LongCat nor GLM is that model or its training
lineage — self-preference applies when a judge grades its own family's outputs, which is
not this situation. The real contamination ground is the one §4.4a already names and
should stay authoritative: *a judge is an HTTP endpoint, not an agent session* — an agent
has context, agenda, and can bend the rubric prompt; an endpoint cannot. State it that way
in §4.4b, or the rule invites misgeneralization later ("no judge may belong to any agent"
→ "therefore no local endpoint is usable", which is false and expensive).

Practical consequence I endorse: **primary judge = the third-party local endpoint
(gemma-4-31b-it on :1234); cross-check judge (subset, per §4.4a) = a second third-party
model.** Under the symmetry of the agreed rule that cross-check should not be mine; a
cloud-frontier subset or a second local model are both legitimate — the operator picks,
per §4.4a's "commits infrastructure" note.

## 2. What the run actually measured — read the four "failures" before quoting 6/10

Recomputed from the raw rows: strict rank order `good > mediocre > bad` holds on 6/10
(c02, c03, c05, c07, c08, c09); pairs concordant 15/19 (0.79); gate at score ≥ 4 accepts
**8/9 scored good rows and 0/20 non-good rows** (max non-good score = 3). The four misses,
individually:

| item | failure | whose fault |
|---|---|---|
| c01 | good=2 < mediocre=3 | **the label.** The "good" answer claims both systems "require … consideration" — consideration is a common-law doctrine, civil-law systems do not require it. The judge caught exactly this, with a legally correct reason, and scored 2. The judge out-performed the label. |
| c06 | good=null | **the token budget** (plus a label defect, see §4). reasoning_tokens=509 against max_tokens=512, finish_reason=length, empty content: the reasoning channel ate the entire budget before emitting the score — on precisely the row with the most to wrestle with. |
| c04 | mediocre==bad==1 | rubric compression, arguably correct. The mediocre answer ("Chinese has fewer characters, so clauses are short") is near-tautological; the judge's reason says so. |
| c10 | mediocre==bad==1 | same pattern — the mediocre variant's literacy claim is crude enough that a strict judge's 1 is defensible. |

**No demonstrated judge error exists in this run.** The correct headline is not "6/10
discriminative" but: *o discrimination failures attributable to the judge; two label
traps it handled better than the labels did; one infra-trap row; two rubric-compressed
ties.* As an **accept/reject gate** the run already supports the model; as an **ordinal
ranking instrument** (model-vs-model comparison) it does not yet — that needs anchors and
repeats below.

## 3. Four fixes before the 20-item / scale-up run

1. **Reasoning budget:** `max_tokens: 512` is below a reasoning judge's needs (observed
   111–509 reasoning tokens on *every* row). Set ≥ 2048 and auto-retry once on
   `finish_reason=length` before recording a null. The c06 null is the bad case exactly:
   nulls cluster on *hard* rows, so a silent drop loses the rows you most need. Also:
   `judge_reasoning` is truncated at 400 chars in the log — do not truncate the one
   field needed to diagnose a null.
2. **Disentangle brevity from correctness:** every mediocre variant is *short-correct*
   and every bad variant is *wrong* — the design cannot distinguish "the judge grades
   correctness" from "the judge punishes brevity", and verbosity bias in LLM judges is
   well documented. Add a fourth variant: **long-wrong** (assertive, detailed, factually
   wrong). Prediction: a brevity-biased judge scores it near the good answers; a
   correctness-grading judge scores it 1–2. This single row decides whether the judge can
   be trusted on verbose confabulation — which is precisely the failure mode a small
   byte-level model will produce post-SFT. Note the current data already hints at it:
   the short-correct mediocre variants are the ones compressed to 1.
3. **Full anchor rubric:** the system prompt defines only 5/3/1 ("excellent", "adequate",
   "wrong or irrelevant") and the judge improvises 2s and 4s unprompted. Write all five
   anchors (suggested: 5 = correct, complete, meets stated audience/format constraints;
   4 = correct with a minor gap; 3 = correct but substantially incomplete; 2 = partially
   flawed or a serious gap; 1 = wrong or ignores the instruction). Without shared anchors,
   the §4.4a cross-check agreement metric cannot be interpreted — two judges with
   different anchor conventions will disagree in ways that are protocol artifacts, not
   signal.
4. **Measure the stability the docstring promises:** the docstring lists "does
   temperature=0 give the same score on repeat?" as measured — the run contains exactly
   one sample per (item, variant), so it is not measured. Temp-0 is not automatically
   deterministic across serving stacks. Cheap version: 3 repeats × 10 rows (~25 min
   serial at the observed 45 s mean), report exact-match rate and ±1 rate. This also
   calibrates how the 20 % cross-check threshold should be read against same-judge
   noise.

## 4. Label audit before this set becomes the §4.4b trap set

Two of the ten "gold" labels are defective as constructed: c01's good variant carries a
planted factual error (§2) and c06's good variant **ignores its own instruction's audience
constraint** — an instruction "for a Chinese-speaking engineer" answered entirely in
English is not good instruction-following. A calibration set with wrong gold labels
poisons every future judge comparison and every trap-based re-certification; it needs an
audit pass (I can do the cross-review of all 10 items), corrected variants or documented
defects, and a **freeze**. Also undersized for the per-language claim: en=5 items,
de=3, zh=2 — the "judges German and Chinese as reliably" claim has n=2–3 per language
behind it. For the 20-item set minimum 7/7/6 per language, discriminative rate reported
per language.

## 5. Topology and bookkeeping

- The measured candidate must enter §4.4a's table: the current table lists GLM local
  (192.168.178.50:8888), LongCat cloud, Qwen local — the endpoint actually calibrated
  (192.168.178.200:1234,
  gemma-4-31b-it) is in neither the prereg nor the logs' meta. Add the row with measured
  numbers attached (mean 45.2 s, max 87.6 s serial ⇒ 30 rows ≈ 23 min; a 200-item
  composition probe ≈ 2.5 h serial, acceptable for a local judge).
- **Record the model fingerprint** (file hash / quantization tag from the serving stack)
  in the calibration meta. A local endpoint is only an auditable judge if its identity
  is pinned: re-quantization or a swapped file shifts scores silently, and a threshold
  fixed in §4.4b would inherit the shift invisibly.
- Docstring says "20 cross-domain instructions"; the run has 10 (`meta.items: 10`). The
  user asked for a 10-item first run, so the run is right and the docstring is stale.
- Score-parse nit: the regex `\{\s*"score"\s*:\s*(\d)` captures only one digit —
  harmless at a 1–5 scale, worth a bounded range check once, not urgent.

## 6. What this unblocks, when the fixes land

With (1)–(4) plus the label audit and freeze, the §4.4b decision can be frozen as:
*third-party local primary judge, one cross-check on a subset, agreement threshold
(≥ 80 %) with a handle on same-judge repeat noise, thresholds fixed after — not before —
the enlarged calibration run.* That ordering is exactly what §4.4b already states; this
run is the right first brick under it.

— asb, 2026-11-08
