# Judge topology limits: two local judges, no council — what the metric cannot do

**Date:** 2026-11-09
**Trigger:** operator observation that the cloud path is closed for judge work, and
that a council (three models) is therefore not available with the current hardware.
**Consequence:** the prereg's §4.4a agreement metric is a two-judge cross-check, not a
majority vote. Its limits are stated here so the Freeze note does not overclaim.

## 1. Why the cloud path is closed

The operator's test of a cloud judge for `cert_de20` produced a 58-second reasoning
trace and then a rate limit. This is not an isolated failure. The major western
providers now treat systematic multi-query evaluation of model outputs as
distillation-adjacent and throttle it. A judge that makes 200–480 calls per run is
exactly the pattern that triggers the limit.

**This is a hard constraint, not a budget problem.** Retry logic, exponential backoff,
and pacing do not fix it — the limit is a policy decision, not a capacity one. The
prereg's §4.4a draft anticipated retry logic; that draft is wrong for cloud endpoints
and should be retired.

## 2. Local inventory

| endpoint | model | state | role |
|---|---|---|---|
| `192.168.178.200:1234` | `gemma-4-31b-it` | UP | cross-check judge (separation) |
| `192.168.178.51:8888` | `Qwen3.8-Flash-Next` | UP | primary judge (fact-checking) |
| `192.168.178.50:8888` | `GLM-5.3-Flash-EXL3` | DOWN (host powered off) | was third seat |

**Two judges are available. Three are not.** A council with a simple majority requires
three independent seats; the GLM endpoint was the third and its host is off.

## 3. What the two-judge metric can and cannot do

**Can:**
- Detect disagreement: with two judges, any divergence is visible and no vote can
  average it away.
- Cover complementary blind spots: the Merged-set run showed zero overlap between
  Gemma's and Qwen's ordinal failures. Gemma missed `cert_zh05`; Qwen caught it.
  Qwen was too strict on `cert_de18`; Gemma passed it.
- Provide a reproducible primary verdict: Qwen's stability is 100 % exact across 59
  pairs, so its verdict is a stable measurement, not a sample.

**Cannot:**
- **Resolve disagreement.** With two judges there is no tiebreaker. The disagreement
  is reported, not decided. A council would decide it; this design documents it.
- **Estimate judge error rates.** Two measurements cannot separate "Qwen is wrong"
  from "the item is contested". The `contested` flag is the honest workaround, not a
  solution.
- **Claim independence in the statistical sense.** Both judges are evaluated against
  the same author-written gold labels. Agreement between them can reflect shared
  misreading of a label as easily as shared correctness. The zero-overlap finding
  mitigates this for the items where they differ, but not for the items where they
  agree.

## 4. The contested-flag workaround and its cost

The Merged-set run produced eight Qwen ordinal failures and three Gemma failures,
with zero overlap. Cell-by-cell review separated them into two verifiable defects
(repaired in `76d50b1`) and three contested items (flagged, not repaired).

**The flag shifts the problem, it does not solve it.** Marking an item contested
requires a judgment that the item is genuinely disputed — which is itself the kind of
judgment the operator's point warns about. The flag is defensible only because the
three items are marked with their reasoning in
`docs/notes/2026-11-09_judge-set-ambiguity.md`, not because the classification is
mechanical.

## 5. Consequence for the Freeze

1. **§4.4a registers a two-judge cross-check, not a council.** The prereg text must
   say so, and must state that disagreement is reported, not resolved.
2. **The agreement metric is divergence-based, not consensus-based.** With two
   judges the metric is "did they differ", and the divergence is the finding. That is
   a weaker claim than a majority verdict, and the prereg should not dress it up.
3. **The cloud-retry draft in §4.4a is retired.** Rate limits are policy, not capacity.
4. **The contested subset is recorded in the Freeze note**, with the three item IDs and
   the reasoning, so the registered thresholds are not ambiguous about which items
   they were computed over.
5. **If a third local judge becomes available**, the topology can be upgraded to a
   council without re-authoring the set — the set is model-agnostic. That is the
   contingency, not the plan.

## 6. What I did not verify

- **The GLM endpoint's status beyond "down".** The host was powered off by the
  operator; I did not check whether the model can be restarted on another host.
- **Whether any other local model could serve as a third seat.** The `.52` host has
  2.9 TB free and an idle GPU, but no third judge model is loaded or certified.
- **The cloud limit's exact policy.** The operator observed a rate limit after one
  test; I have not tested the boundary, and this note does not claim a specific
  threshold.
