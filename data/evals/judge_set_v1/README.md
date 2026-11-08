# Judge set v1 — certification traps + composition benchmark pool

**Status:** DRAFT for four-eyes review. NOT frozen. This directory becomes the frozen
judge set only after the review pass and the freeze commit (see §8).
**Designed by:** asb (GLM agent) · **To be reviewed cell-by-cell by:** Quinn (a0-quinn)
· **Judge under certification:** `gemma-4-31b-it` (192.168.178.200:1234) primary ;
`Qwen3.8-Next-Flash` German-capability check secondary.
**Governance note for the operator:** per the agreed rule no agent-owned model
(LongCat, GLM) judges. This set is authored by excluded agents, judged by a third-party
endpoint, and cross-checked by Quinn — authorship of items does not contaminate a
scored answer, and every gold label here is checkable against bedrock domain facts.

## 1. Why two populations

All four defects in the 10-item first run (c01, c04, c06, c10) were **label/variant
defects**, not instruction defects — and c01/c06 were executed better by labels that
weren't there. Therefore the set is split along the defect axis:

| population | contents | purpose | when judged |
|---|---|---|---|
| `cert_items.json` | instructions **with** 6 labeled variants each | certify a judge: separation, brevity-bias, fact-checking, constraint awareness, stability | **now**, pre-SFT, repeatedly (re-certification after endpoint changes) |
| `pool_instructions.json` | instructions **without** reference answers | the §4.4b composition benchmark: real model answers post-SFT, scored under the frozen rubric | post-SFT |

## 2. Frozen judge prompt (rubric)

Every judge run — certification and §4.4b — uses exactly this system prompt. Changing
it requires a new set version:

```
You grade chat answers strictly. Reply ONLY with a JSON object
{"score": <integer 1-5>, "reason": "<short string>"}. No other text, no markdown.
Anchors:
5 = correct, complete, and satisfies every stated constraint (audience, language, format)
4 = correct with a minor gap or a slight constraint miss
3 = correct but substantially incomplete
2 = partially flawed or contains a notable error
1 = wrong, misleading, or ignores the instruction
```

## 3. Frozen protocol knobs for the certification run

- `temperature = 0.0`, `max_tokens = 2048` (the 10-item run showed reasoning budgets of
  111–509 tokens/call; 512 produced a null on the hardest row).
- On `finish_reason = length`: one retry at 4096 before recording a null. Nulls must stay
  rare **and** correlated only with the hardest rows, not silently dropped.
- Log the full `judge_reasoning` (untruncated) — it is the failure-diagnosis field.
- No labels flow to the judge: payload is system prompt + instruction + one answer.
- `seed` and call order fixed in the script; three full repeats on the stability
  subslice (items marked `"stability": true`), one pass over everything else.
- Record the model fingerprint (served file hash or quantization tag from the endpoint)
  in the run meta. Endpoint identity is part of the judge's audit trail; a re-quantized
  endpoint is a different judge until re-certified.

**Run logistics (observed 2026-11-08):** the full cert pass is **300 judge calls**
(20 non-stability items × 6 × 1 + 10 stability items × 6 × 3). At the observed
186–222 s/call on the certificate endpoint that is ~17–20 h wall clock — a 6 h timeout
is insufficient, and `cert.json` is written only after the last row, so an interrupted
run leaves only the log (rows are recoverable from the log). Budget the timeout,
or slice the run; never shorten the protocol knobs to fit a schedule.
**Cert-status interim (while the 2026-11-08 run was live):** early judge reads
(cert_de01/good, first repeats) landed borderline-4 with slow, self-checking reasoning —
watch the 3/4-boundary in the analysis rather than pre-deciding.

## 4. Certification criteria (the judge passes if all rows hold)

Aggregated over the cert run per variant, per language slice where stated:

| check | criterion | verdict it renders |
|---|---|---|
| separation | mean(good) − mean(short_correct) ≥ 0.8, AND ≥ 80 % of good rows ≥ 4 | discrimination exists at all |
| brevity bias | ≥ 80 % of long_wrong rows ≤ 2, AND mean(long_wrong) ≤ 2.5 | punishes wrongness, not length |
| fact-checking | ≥ 80 % of planted_error rows ≤ 3 (0 % may be 5) | catches embedded single-fact errors |
| constraint awareness | ≥ 80 % of audience_violation rows ≤ 3 | notices stated audience/language/format rules |
| floor | ≥ 70 % of bad rows = 1, mean(bad) ≤ 1.5 | floor is calibrated |
| ordinal order | per item: mean(good) ≥ mean(short_correct) ≥ mean(bad) | monotonic use of the scale |
| stability | ≥ 70 % exact-match across the 3 repeats of the subslice; ≥ 95 % within ±1 | scores are reproducible |
| per-language | every criterion holds on the en-, de-, and zh-slices separately | no silent language blind spot |

**Decision rules:** gemma passes → primary judge candidate confirmed; fails any
fact-checking or stability row → judge rejected, model choice re-opened. Qwen3.8-Next-Flash
runs the same cert set; its **de-slice result answers "can a second local model judge
German"** — that is the cross-check-judge decision input. The §4.4b accept-threshold is
fixed only AFTER certification, against these measured bands (prereg already commits to
that ordering).

## 5. Variant semantics and the six traps

Each cert item carries up to 6 variants. Labels are role names, not quality claims:

| label | design | expected band |
|---|---|---|
| `good` | complete on all key points, constraint-compliant | ≥ 4 |
| `short_correct` | correct but **substantially** incomplete (no tautologies — the c04 lesson) | ~3 |
| `long_wrong` | assertive, detailed, verbose, **wrong at the core** (the brevity-bias control; the c10 lesson: no crude sunglasses like "Chinese people can't read") | ≤ 2 |
| `planted_error` | otherwise complete and correct, **exactly one wrong fact integrated** (the c01 lesson, systematized) | ≤ 3, never 5 |
| `audience_violation` | content correct, but violates the item's stated constraint (wrong language / wrong audience register / wrong format — the c06 lesson) | ≤ 3 |
| `bad` | wrong or off the task | 1 |

Hard content rules baked into the authoring checklist (Quinn verifies these):

1. **No repo-internal facts.** Item facts must be bedrock domain knowledge an external
   31B judge knows (legal articles, ML basics, culture). Project-internal claims would
   make certification unfalsifiable.
2. **Every `planted_error` carries `note.planted`** naming the wrong fact AND the correct
   fact (checkable). No planted errors on debatable/interpretive claims.
3. **Every item with an `audience_violation` variant has an explicit `constraint`** in
   the instruction — the judge must be able to read the constraint in the prompt.
4. `short_correct` must omit ≥ half the key points while staying factually right.
5. `long_wrong` must be factually wrong at the core — not merely shallow.
6. **Constraint-compliance is part of the role, not an accident.** Every variant whose
   defect is *not* the constraint miss (`good`, `short_correct`, `planted_error`,
   `long_wrong`) must satisfy the item's stated constraint — otherwise a low score is
   ambiguous between the designed defect and a format violation, and the
   `audience_violation` row loses its discriminating power (the cert_de03 lesson: its
   first draft had a prose `good` next to a "three bullet points" constraint). Only the
   `bad`/`audience_violation` roles may violate the constraint.
7. **No leaked authoring artifacts.** Variant text must contain no prompt/auth markers,
   no mojibake, no zero-width characters, no stray tokens (the cert_de03 `_INTERNAL`
   lesson). An automated token-artifact scan runs pre-commit; it is a filter, the
   cell-by-cell read remains the verdict (Quinn 2026-11-08 §3: automated pass = filter,
   not verdict).

## 6. Pool design and staging

Pool items are the benchmark instructions: cross-domain composition tasks the chat model
will face (German-Chinese business/legal/tech mix mirrors the project's domain pairs).
Each has `lang`, `domains[]`, `difficulty`, optional `constraint`. **No reference
answers** — pool items are judged on real model answers post-SFT, so they cannot leak
labels. Cohorts, committed in stages to keep the four-eyes quality loop honest:

| cohort | size | status |
|---|---|---|
| C1 | 60 (20/lang) | this commit, review target |
| C2 | ~180 | asb authors next, after C1 review |
| C3 | ~180 | fills to ~500; ~15 % discard expected in review |
| C4 | reserve | optional top-up only if freeze-survivor count < 400 |

At freeze the pool splits into cohort A (~60 %, the scored benchmark) and cohort B
(~40 %, held out — same producers, same time; used for a re-test or a v2 judge without
restale risk).

## 7. Anti-contamination

- This directory is **never training data**. No corpus script reads it (verified: the
  corpus builder fetches explicit Gutenberg IDs, no directory scan); the hold-out stays
  procedural: SFT paths must not reference `data/evals/`.
- Pool/cert items are graded in judge memory per request; item sets are not fine-tuning
  material for the judged model by construction, and are committed only after review so
  the SFT corpus authoring did not see them (authorship predates SFT anyway).
- Judges never see labels; item IDs never enter judge prompts.

## 8. Freeze procedure (after Quinn's pass)

1. Quinn's per-cell verdicts → my fixes → his LGTM comment on the review commit.
2. Freeze commit: set `STATUS: FROZEN` here, drop any item whose gold was corrected,
   recompute content hash `sha256sum data/evals/judge_set_v1/*.json` and record it in
   prereg §4.4b together with the cert-criteria table (§4).
3. Report for the cert run goes to `docs/reports/` (Quinn's harness). Any post-freeze
   item change = new set version (v2), old hashes stay historical.

## 9. Stage status (this commit)

- [x] README/spec (this file)
- [x] cert stage 1: 30 items (10 en / 10 de / 10 zh), all 6 variants, notes incl. planted-fact citations
- [x] pool cohort C1: 60 instructions (20 en / 20 de / 20 zh), 0 reference answers
- [x] Quinn cell-by-cell review (83151bb): LGTM with two fixes, both cert_de03
      (prose `good` under a bullet-constraint; `_INTERNAL` token in `long_wrong`)
- [x] author fixes: cert_de03 rewritten (good/short_correct/long_wrong now
      constraint-compliant bullets, single-defect attribution preserved), leaks ruled out
- [ ] cert run pass + report (2026-11-08 run in flight; timeout math in §3)
- [x] cert stage 2: 30 items (14 heavy-legalese de / 8 en / 8 zh) authored as a
      SEPARATE draft file `cert_items_stage2.json` (status DRAFT-for-review), so
      the in-flight run's `cert_items.json` snapshot stays untouched; merge into
      the frozen set happens at the freeze commit per §8. Rules 1-7 (§5) apply,
      incl. rule 6 (constraint compliance by role) and the artifact scan (rule 7).
- [ ] cert stage 2 review (Quinn): cell-by-cell, incl. fact checks in de/zh/en
- [ ] pool C2/C3
- [ ] Qwen de-slice cross-check (only if gemma cert passes)
- [ ] freeze commit + hash into prereg §4.4b

**One protocol change Quinn's harness needs before the cert run:** the system prompt
above (§2), `max_tokens: 2048`, retry-on-length, untruncated reasoning log, endpoint
fingerprint in meta — the 10-item run's harness predates these; its null/`c06` lesson
is fixed here.

— asb, 2026-11-08
