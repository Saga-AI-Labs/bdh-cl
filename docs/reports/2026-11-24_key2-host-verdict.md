# Key 2 host verdict - 3.62B mixed checkpoint

- Date: 2026-11-24
- Status: **verdict recorded. Key 2 fails on all three dimensions. Key 1 is not
  measured.**
- Frozen instrument: `docs/notes/2026-11-24_key2-g0-freeze.md` (G0, signed
  2026-11-24), rubric v2 `data/evals/key2_rubric_v2.json`.
- Machine record: `out/key2_calibration/verdict_3.62b.json`, sha256
  `3cd917be6e32378d79869991f39d67c70752ffa1caf875a2e57fe79834912c20`.

## 1. Object and inputs

| object | value |
|---|---|
| host checkpoint | `out/routed_probe/bdh_textmix_p3_mixed_best.pt`, 38,657,073,228 B, sha256 `ce24e0fd...0e1874` |
| generations | `out/key2_calibration/gen_3.62b.jsonl`, 133 rows, sha256 `e763dd32...00d1f8e5` |
| decoding | greedy argmax, 256 new bytes, one sample per prompt |
| prompts | `data/evals/key2_prompts_v1.json`, sha256 `c1d9c62c...bf12e23c`; 100 gate + 33 argue |
| rubric | v2 FROZEN, system prompt `9edfd92d...42124` |
| thresholds | `thresholds_candidate_v2.json`, sha256 `c341edb4...c0d957`; `F_d` 2/2/3, `M_d` 4.50/4.50/4.33 |
| verdict pass | fresh blind scoring, 133 rows x 2 seats, both completed with 0 NULLs |
| seats | Qwen3.8-Flash-Next (sole coherence seat), gemma-4-31b-it Q4_K_S |

The verdict pass is a separate scoring run made after the freeze. It is not a
relabel of the calibration scores, and section 4 shows the two agree exactly.

## 2. Result

Gate, 100 items. Rule: `mean_d >= M_d` and `min_d >= F_d` per dimension, no
cross-dimension mean.

| dimension | mean | `M_d` | min | `F_d` | result |
|---|---|---|---|---|---|
| coherence | 1.00 | 4.50 | 1 | 2 | **fail** |
| relevance | 1.01 | 4.50 | 1 | 2 | **fail** |
| language | 1.49 | 4.33 | 1 | 3 | **fail** |

Diagnostic, 33 argue items (not gated):

| dimension | mean | min |
|---|---|---|
| coherence | 1.00 | 1 |
| relevance | 1.00 | 1 |
| language | 1.49 | 1 |

Every dimension fails on both the mean and the floor, by 3.5 points on the mean
(coherence, relevance) and 2.8 on language. There is no near miss to argue
about.

The material is degenerate repetition. `k2_explain_01` against "Explain why the
sky changes color at sunset." begins:

```
[nb] substance of the provisions of the provisions of the provisions of the
provisions of the provisions of the provisions of the provisions of the provisions
of the provisions of the provision of the provisions of the provisions of ...
```

The first byte sequence is non-ASCII; the rest is the loop itself.

Qwen's verdict reason: "The text is repetitive, broken, and unrelated to the
prompt, with no recoverable proposition." Gemma's on `k2_describe_44`:
"degenerate repetition and starts with a non-English word; it fails to form a
coherent thought".

## 3. Floor breaches and the 8.5 re-score

Items below `F_d`: coherence 100/100, language 100/100, relevance 99/100 (one
item scores 2). Rubric 8.5 requires an item below the floor to be re-scored
blind before the breach counts.

The re-score is the verdict pass itself. The calibration pass scored these
samples before the freeze; the verdict pass scored them again after it, without
either pass seeing the other. The two agree on every cell (section 4), so the
breach is confirmed twice. A third pass would add no information: the seats are
deterministic at temperature 0 and the replication is exact.

## 4. Replication

Fresh verdict pass against the calibration pass, per seat:

| seat | cells identical | reasons identical |
|---|---|---|
| Qwen | 399/399 | 133/133 |
| Gemma | 399/399 | 133/133 |

Consensus agreement is 100 % exact on all three dimensions. This is stronger
than the stability slice required by 8.5 and it is the first time the two seats
have been shown to reproduce an entire 133-row pass, not a 5-item sample.

## 5. What each dimension's failure does and does not prove

This is the part of the verdict that must not be overstated.

| dimension | negative band | independence of this failure |
|---|---|---|
| coherence | these same 133 generations | **calibration-consistent, not independent** |
| language | language-broken subset of these generations | **calibration-consistent, not independent** |
| relevance | dissociation-B off-topic passages | **independent** |

`F_d` was set one point above the maximum of the material that is now being
scored, so the coherence and language failures follow from the calibration by
construction. They confirm that the instrument rejects the distribution it was
calibrated against; they are not an out-of-sample measurement.

Relevance is the exception. Its band is 24 clean off-topic passages, not these
generations, and the host still scores 1.01 against `M_d` 4.50. That limb is a
genuine out-of-sample failure.

Under the frozen protocol a genuinely independent second generation cannot be
constructed: greedy decoding, one sample per prompt, same checkpoint and same
prompts reproduce identical bytes. An independent verdict needs either a
protocol amendment (for example sampled decoding at a fixed seed) or a different
checkpoint. That decision is not taken here.

## 6. Judge-free corroboration

The registered repetition rule (rubric 8.7) is a hard fail above 64 B of longest
repeated substring. It does not use the judges or the thresholds.

| measure | host | positive band |
|---|---|---|
| longest repeated substring, max | 180 B | 19 B |
| longest repeated substring, median | 107 B | 9 B |
| rows at or above 64 B | **133/133** | 0/18 |
| distinct-4, mean | 0.154 | 0.913 |

The host triggers the hard fail on every sample. This is the independent
corroboration that the verdict is not an artefact of a band calibrated on the
same material: the text is degenerate by a measure that knows nothing about the
rubric.

## 7. Diagnostics required by 8.7

| dimension | second worst | items within 0.5 of floor | leave-one-out mean |
|---|---|---|---|
| coherence | 1 | 100 | 1.000 - 1.000 |
| relevance | 1 | 100 | 1.000 - 1.010 |
| language | 2 | 100 | 1.485 - 1.495 |

Per-family minima are 1 for both gate families (explain, describe) on all three
dimensions. The floor verdict does not hinge on one item: removing any single
item leaves the mean unchanged to two decimals.

Dimension correlation is not computable on coherence, which has zero variance
(all 1s). Relevance and language correlate at 0.103, so there is no collinearity
signal here; the samples are too degenerate to support one.

## 8. Position in the 8.4 table

Key 1 has not been measured (the host train/val carve is not built), so the 2x2
row cannot be completed. The key-2 half is not ambiguous: rubric 8.4 states that
a model which fails key 2 is rejected on the coherence verdict regardless of key
1. The pending action is the coverage diagnosis named in that table, not a re-run
of this pass.

## 9. Not measured

- **Key 1** (6-gram against the val carve): carve not built.
- **Contamination**: prompt 8-gram against the host corpus and output 8-gram
  against the corpus are both blocked on the same carve.
- **Human read**: substituted by the GPT calibration read at the freeze, as
  registered. No human judgement of these 133 samples exists.
- **Independent generation**: see section 5.

## 10. Decision required

1. Accept the verdict as a **calibration-consistent fail** on coherence and
   language plus an **independent fail** on relevance, with the repetition hard
   fail as corroboration; or
2. amend the protocol to allow a second, independent generation (sampled
   decoding at a fixed seed, or a different checkpoint) and score that before
   treating the coherence verdict as out-of-sample.

Either way the host is rejected on this evidence. The difference is what the
record is allowed to claim later.

## Reproduce

```
.venv/bin/python scripts/quinn/key2_verdict.py \
  --verdict out/key2_calibration/qwen_verdict_v2.json \
  --verdict out/key2_calibration/gemma_verdict_v2.json \
  --compare out/key2_calibration/qwen_negative_v2.json \
  --compare out/key2_calibration/gemma_negative_v2.json \
  --out out/key2_calibration/verdict_3.62b.json
```
