# Probe S — Semantic Addressing and Paraphrase Transfer

Status: **MEASURED; S-PASS = false**. Date: 2026-09-17. Author: Quinn.

## 1. Scope and execution

Probe S tests whether two protected fact territories support recall under withheld query templates, and whether answer-free routing selects the appropriate territory. It is not a test of arbitrary unseen factual bindings or general conversational memory.

Protocol: [Probe S, premeasurement amendment](../../plans/2026-09-17_probe-s-semantic-addressing.md). Runner: `scripts/quinn/probe_s_semantic.py`.

The run on `bdh-4090` completed with exit status 0. Raw run path, relative to `/media/data/coding/bdh`: `out_c/probe_s/run-20260917T043829Z/`. The grown-model query log contains 2,048 evaluations: 512 per territory and split. The base-model log contains another 1,024 A evaluations. Each split contains two templates; repeated queries over the same facts are not independent factual observations.

The protocol was amended before scientific execution to use identical answer-free queries for both routers, explicit old-only and new-only oracle masks, and full-answer evaluation. Compositional queries were deferred. The frozen protocol and source hashes identify the executed version rather than the superseded draft. The execution handover reports a synthetic smoke-test precision correction and no scientific retries; this report does not independently establish the absence of other runs.

## 2. Instrument and configuration

- Small BDH trained from scratch: two layers, embedding dimension 256, four heads, block size 128, dropout 0.
- Base multiplier 128; growth increment 32; final multiplier 160. Oracle A selects old neurons and oracle B selects the new block. Full-width serving is a separate descriptive condition.
- Fixed training budgets: 4,000 base steps and 2,000 growth steps, batch size 8, learning rate 0.001, weight decay 0.1. Base/growth seeds: 17092027/17092028. This is one experimental run, not a replicated seed study.
- Growth uses route-aware training with alpha 1.0 and frozen attention. This differs from the alpha 0.9 language-ladder setting.
- The data adapter invokes `pipeline.train.train` with synthetic dataset substitution and verification hooks. Reusing that training implementation does not mean the original corpus-loading pipeline was used unchanged.
- A2 compares query-only likelihood under the two territorial masks. Both A2 and the byte comparator see the same answer-free query; neither receives the target answer for route selection.
- The byte comparator is an order-5 byte model with four-byte context, not the historical byte-4-gram classifier used in R.
- After routing, the same grown BDH generates the answer under the selected mask. Exact success requires the complete answer, with generation stopping at the first period or at the registered 16-byte cap. This is not next-byte accuracy. Full-answer NLL is recorded separately.

## 3. Results

All exact-answer and routing counts below have denominator 512 per row. Counts are obtained from the recorded rates and denominators; verification against query records is described in Section 6.

| Query condition | Oracle exact | A2 route correct | A2 exact | Byte route correct | Byte exact | Full-width exact |
|---|---:|---:|---:|---:|---:|---:|
| A, seen templates | 512/512 | 512/512 | 512/512 | 512/512 | 512/512 | 356/512 |
| B, seen templates | 510/512 | 512/512 | 510/512 | 0/512 | 6/512 | 9/512 |
| A, withheld paraphrases | 157/512 | 512/512 | 157/512 | 512/512 | 157/512 | 53/512 |
| B, withheld paraphrases | 40/512 | 0/512 | 5/512 | 0/512 | 5/512 | 3/512 |

On withheld paraphrases:

- Oracle exact: A **30.6641%**, B **7.8125%**, pooled **197/1024 = 19.2383%**.
- Both routers select A for every query: pooled route accuracy **512/1024 = 50%**.
- Both routed readers achieve **162/1024 = 15.8203%** exact answers.

The identical paraphrase routing does not imply identical behavior on all inputs: on seen B templates, A2 selects B correctly on 512/512 queries, whereas the byte comparator selects A on all 512.

Independent inspection of all 2,048 grown-model query records found exactly equal recorded A/B byte-NLL scores on every query. The runner resolves ties lexicographically (`min(scores, key=lambda k: (scores[k], k))`), selecting A. Thus the byte comparator's always-A behavior is a deterministic tie-break, not confident evidence favoring territory A. Its 50% paraphrase routing accuracy is a non-discriminating baseline under this setup. The equal aggregate A2/byte outcomes do not imply equal mechanisms or a general limit on byte-based addressing; the cause of the score equality was not isolated by this report.

Before growth, A oracle recall was 512/512 on seen templates and 156/512 on withheld paraphrases. After growth these values are 512/512 and 157/512. The one-answer increase is descriptive, not evidence of improved generalization.

## 4. Registered gates and protection checks

| Criterion | Result | Interpretation |
|---|---|---|
| Acquisition: oracle exact >=0.80 in each territory on seen templates | PASS | A 512/512; B 510/512 |
| P-S1: oracle paraphrase exact >=0.80 in each territory | FAIL | A 157/512; B 40/512 |
| P-S2: pooled A2 route accuracy >=0.85 | FAIL | 512/1024 |
| Conditional routing falsifier: route accuracy <=0.60, provided acquisition and P-S1 pass | NOT TRIGGERED | P-S1 prerequisite fails |
| P-S3: byte comparison | No A2 advantage on paraphrase route/exact scores | Descriptive equality, not equivalence across tasks |
| P-S4: post-growth A seen-template oracle exact >=0.75 | PASS | 512/512 |
| S-PASS | false | Required transfer and routing gates fail |

`grown_checks.json` records 2,000 masked-gradient checks, 2,020 exact protection checks, observed decay before restoration, and changes in the new encoder. These are runner-recorded assertions, not an independent checkpoint-tensor audit performed for this report.

The separate functional check on four prefixes records maximum absolute difference **5.7220458984375e-06**, with absolute and relative tolerances of 1e-4. Numerical functional agreement within tolerance is not bit-identical output. It must not be conflated with exact frozen-tensor checks.

## 5. Interpretation and next-step boundary

The supported failure label is **paraphrase transfer failure under the tested recipe, not demonstrated storage destruction**. Seen-template acquisition succeeds in both territories and A retention is preserved. However, even the oracle mask fails to recover most answers when the query template changes. Routing alone therefore cannot account for the low paraphrase answer accuracy.

The observed always-A routing is a real result. It does not trigger the conditional routing falsifier, because adequate oracle paraphrase recall was a prerequisite. The result neither establishes general BDH semantic incapacity nor isolates a cause such as layer depth, training budget, or representation location.

Important limitations:

- Synthetic facts, a small scratch-trained model, one seed pair and a narrow template family; no broad language competence was established first.
- Shared language and style do not eliminate lexical or template shortcuts. Successful seen-template recall does not establish semantic-only addressing.
- Multiple templates query the same facts. Query counts are not independent sample sizes for population-level significance.
- No compositional-query, novelty-detection, natural-conversation or production-serving result is available.
- No post-result retraining or template search is needed to record this negative result faithfully.

**Implication for Sonde A:** mechanism scaling can proceed as a separate question, with oracle routing used to isolate growth and retention and A2 routing reported separately. Probe S does not justify claiming that chat-memory addressing is solved. Any follow-up aimed at paraphrase competence should be separately scoped and authorized, rather than silently becoming another prerequisite for mechanical scaling.

## 6. Evidence and verification scope

Curated summaries belong in `docs/data/probeS-run/`: score tables, gates, configurations, frozen-source metadata, execution checks and completion status. Raw corpora, query records and checkpoints remain in the run directory; they are not included in this small summary bundle.

All reported exact-answer and routing counts were independently recalculated from the 2,048 grown-model query records and matched `scores.json`. The 1,024 base-model records reproduced `base_scores.json`; base oracle scoring uses the full-model reading. Exact-answer flags were also checked against the recorded prediction bytes and the complete target answer plus period. An initial recount script incorrectly assumed an A reading existed in the base records; after correcting that schema assumption, the base recount passed. This was an analysis-script correction, not a model rerun or a change to measured results. All 2,048 grown-model records had exactly equal A/B byte scores, confirming the tie-break finding above. Eleven curated source files were compared byte-for-byte with their copies, and all entries in `SHA256SUMS` passed verification. Source hashes identify the recorded runner and protocol version; these checks are not an independent rerun of training or model evaluation.

No new scientific run was launched to prepare this report. Commit, push and external notification status are separate from the saved report and are not implied by its existence.
