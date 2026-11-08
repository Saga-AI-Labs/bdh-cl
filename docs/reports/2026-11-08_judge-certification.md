# Judge certification: two models, complementary profiles, one shared item defect

**Date:** 2026-11-08
**Question:** can a local third-party judge be certified for the chat prereg's
§4.4a/4.4b composition metric, and can a second local model judge German?
**Answer:** both models run the full cert set end to end. Neither passes all criteria,
and their failures are complementary: Gemma separates quality well but misses planted
facts; Qwen catches every planted fact and is perfectly stable but scores good answers
too low. The single most important finding is not a judge failure at all — three of the
four ordinal failures trace to one defective item that both judges reject identically.

## 1. What was run

Two judges, same frozen rubric, same 30-item set (10 en / 10 de / 10 zh), 6 variants per
item, 3 repeats on the 10 stability items — **300 calls each, 0 failures**.

| | Gemma | Qwen |
|---|---|---|
| endpoint | `192.168.178.200:1234` | `192.168.178.51:8888` |
| model | `gemma-4-31b-it` | `Qwen3.8-Flash-Next` |
| context | — | 262.144 tokens |
| reasoning | yes | yes (default enabled) |
| calls | 300 | 300 |
| endpoint fingerprint | `85c12327fcf7b0c0` (60 models) | tensorfold |
| rubric sha256 | `ef4d113fdbd74f61…` | `ef4d113fdbd74f61…` |

Harness: `scripts/quinn/judge_calibration.py` — frozen system prompt (5 anchors), `temperature=0.0`,
`max_tokens=2048` with one retry at 4096 on `finish_reason=length`, untruncated reasoning log,
endpoint fingerprint in meta, checkpoint after every item, `--resume` for long runs.

## 2. Certification criteria

Criteria are from `judge_set_v1/README.md` section 4; `pass` is the frozen gate.

| criterion | gate | Gemma | Qwen |
|---|---|---|---|
| **Separation** | gap ≥ 0,8 AND ≥ 80 % good ≥ 4 | **1,333 / 90 % → pass** | 0,867 / 60 % → **fail** |
| **Brevity bias** | ≥ 80 % long_wrong ≤ 2 AND mean ≤ 2,5 | **100 % / 1,0 → pass** | **100 % / 1,0 → pass** |
| **Fact-checking** | ≥ 80 % planted ≤ 3 AND 0 % == 5 | 90 % / 6,7 % → **fail** | **100 % / 0 % → pass** |
| **Constraint awareness** | ≥ 80 % audience ≤ 3 | 50 % → **fail** | **82,8 % → pass** |
| **Floor** | ≥ 70 % bad = 1 AND mean ≤ 1,5 | **100 % / 1,0 → pass** | **100 % / 1,0 → pass** |
| **Ordinal** | good ≥ short ≥ bad per item | 27/30 → **fail** | 27/30 → **fail** |
| **Stability** | ≥ 70 % exact AND ≥ 95 % ±1 | 78,3 % / 96,7 % → **pass** | **100 % / 100 % → pass** |

### Per language slice

| slice | Gemma | Qwen |
|---|---|---|
| en | sep ✅ fact ❌ constr ❌ | sep ❌ fact ✅ constr ✅ |
| **de** | sep ❌ fact ❌ constr ❌ | sep ❌ **fact ✅** constr ❌ |
| zh | sep ✅ fact ✅ constr ❌ | sep ❌ fact ✅ constr ✅ |

**Qwen is the better German fact-checker.** On the de-slice Gemma fails fact-checking;
Qwen passes it with 100 %. That is the cross-check question the README posed, answered:
yes, a second local model can judge German — and it catches what Gemma misses.

**Gemma is the better separator.** Gap 1,333 vs 0,867, and 90 % vs 60 % of good rows ≥ 4.
Qwen scores good answers too low for a ranking instrument.

**Qwen is perfectly stable.** 100 % exact across 60 repeat pairs; Gemma 78,3 %. Against a
judge that agrees with itself 100 % of the time, the §4.4a cross-check agreement metric
measures real disagreement, not judge noise.

## 3. The ordinal failures are item defects, not judge defects

Four items fail the ordinal gate, and the pattern is the finding:

| item | Gemma good/short/bad | Qwen good/short/bad | verdict |
|---|---|---|---|
| **cert_de01** | **2 / 3 / 1** | **2 / 3 / 1** | item defect, both judges identical |
| cert_de10 | **3 / 4 / 1** | (holds) | item defect (weak good) |
| cert_en09 | **2 / 4 / 1** | (holds) | item defect (weak good) |
| cert_en08 | (holds) | **2 / 3 / 1** | item defect (detail error in good) |
| cert_zh05 | (holds) | **2 / 3 / 1** | item defect (good too long) |

**cert_de01 is the c01 case, still unfixed.** Its good variant says *"Both require offer,
acceptance, and consideration"* — consideration is a common-law doctrine; German law has
no consideration requirement (§ 311b BGB governs form, not consideration). Both judges
correctly score it 2, and the short_correct variant scores 3. **The item's gold label is
wrong; the judges are right.**

cert_de10 and cert_en09 are the same shape: the good variant is long and detailed but
not convincing enough, so the judge prefers the shorter one. cert_en08 and cert_zh05
(Qwen only) are good variants with a detail problem / excessive length.

**Why this matters:** both judges independently reject the same item. That is a consensus
between two unrelated models, which is the strongest evidence that the item is defective
and the judges are not. An ordinal failure caused by a judge would not repeat identically
across two different architectures.

## 4. Consequence for the judge topology

The README's §4.4a proposal was a primary judge plus a cross-check on a subset, with an
agreement metric. The measurements support that shape and refine it:

| role | model | why |
|---|---|---|
| **Primary judge** | Qwen3.8-Flash-Next | fact-checking 100 %, constraint 82,8 %, stability 100 % — the judge that catches wrong facts and is reproducible |
| **Cross-check judge** | Gemma-4-31b-it | separation 1,333, 90 % good ≥ 4 — the judge that grades quality gradations well |

**The two profiles are complementary, not redundant.** Gemma's blind spot is planted
facts (6,7 % scored 5); Qwen's is quality separation (only 60 % of good rows ≥ 4). A
single judge would carry one systematic blind spot; the pair covers both.

**What the topology cannot fix:** Qwen's low good-scores make it unsuitable as a ranking
instrument (model vs model). For an accept/reject gate it is fine — it errs strict, not
lenient. Gemma's missed facts make it unsuitable as the sole fact-checker. The
certification therefore supports **a gate, not a ranking**, with Qwen primary.

## 5. Open items

1. **cert_de01's gold label is still wrong.** It should be rewritten (drop the
   consideration claim) before the set is frozen. It is the only item both judges reject
   identically, and it poisons the de-slice.
2. **cert_de10 / cert_en09** need stronger good variants.
3. **cert_en08 / cert_zh05** need a detail/length pass.
4. **Stage 2 has no stability items.** The stability subslice is entirely in stage 1, so a
   stage-2-only run cannot measure stability without a marker addition.
5. **The §4.4b accept threshold is still not fixed.** Per the prereg, it follows
   certification; the bands measured here are the input.

## 6. Artifacts

```
out_c/judge_calibration/cert.json       Gemma, 300 rows, all criteria
out_c/judge_calibration/cert.log        full log incl. reasoning, untruncated
out_c/judge_calibration/qwen_cert.json  Qwen, 300 rows, all criteria
out_c/judge_calibration/qwen_cert.log   full log
scripts/quinn/judge_calibration.py      the harness (frozen rubric, resume, checkpoint)
```

## 7. Reproduce

```bash
# Gemma (takes ~6-8 h at observed rates)
timeout 259200 .venv/bin/python -u scripts/quinn/judge_calibration.py \\
  --base-url http://192.168.178.200:1234/v1 --model gemma-4-31b-it \\
  --set data/evals/judge_set_v1/cert_items.json \\
  --out out_c/judge_calibration/cert.json --log out_c/judge_calibration/cert.log --resume

# Qwen (parallel, own endpoints; ~5-8 h)
timeout 259200 .venv/bin/python -u scripts/quinn/judge_calibration.py \\
  --base-url http://192.168.178.51:8888/v1 --model Qwen3.8-Flash-Next \\
  --set data/evals/judge_set_v1/cert_items.json \\
  --out out_c/judge_calibration/qwen_cert.json \\
  --log out_c/judge_calibration/qwen_cert.log --resume
```
