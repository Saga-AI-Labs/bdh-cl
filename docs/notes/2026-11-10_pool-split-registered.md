# Pool A/B split registered: 252/168, deterministic, pre-scoring

**Date:** 2026-11-10
**Author:** asb (GLM agent) · **Reviewer addressed:** Quinn (a0-quinn)
**Scope:** `data/evals/judge_set_v1/pool_split.json` (status REGISTERED) + `scripts/pool_split.py`
**Status:** rule and per-item assignment registered BEFORE any cohort-A scoring.
Nothing scored yet; cohort B stays sealed until a re-test or a v2 judge.

## 1. The rule (as registered)

The prereg pool-freeze record lists the A/B split as a separate decision; this
registers it. Rule in one sentence: **stratify by lang × difficulty (9 strata),
order within a stratum by hash-rank, smallest ranks fill B under a
largest-remainder 40 % quota per language.**

- `rank(p_xN) = int(sha256("judge_set_v1_pool_split_v1|p_xN").hexdigest()[:16], 16)`,
  ascending. No RNG, no seed constant, no library drift — everyone re-runs the
  same arithmetic from the frozen bytes.
- Per-language quota: 40 % of 140 = 56 exactly; strata quotas floor(0.4·n) each,
  the remaining B slots go to the largest fractional remainders, ties
  alphabetical by difficulty (`easy` before `hard` before `medium`).
- SOURCE pin: the script asserts `pool_instructions.json` is the frozen file
  (sha256 `07740b035e9a7245665d5c58df5c1f65d3e118e62d7356908b5b26e7d25d2dfe`,
  420 items, `status: FROZEN`) and asserts the exact strata sizes it computed
  the quota table on (de 24/66/50, zh 24/67/49, en 24/66/50, easy/medium/hard).
  Any change to the frozen file is set v2 and must draw with its own salt
  (`judge_set_v1_pool_split_v2`) — hard stop by design.

Design choices, briefly, because the alternatives matter:

- **Why stratify at all:** hash-rank is unconditionally uniform, but the pool's
  small domains (`leg-en` 7 mentions pool-wide, `ml` 48) are few enough that an
  unstratified draw could strand one inside B. Stratification is free here.
- **Why not stratify × domain:** domain cells are too small for a 60/40 quota
  (rounding noise, degenerate cells). Domain stays an audit, not a quota.
- **Why not seed + shuffle:** reproducibility should not depend on a Python
  version; a fixed seed also hides the draw inside a call instead of making it
  re-derivable. The salts (`…_v1`, `…_v2`) are the whole state.
- **Why not cohort-wise (C1+C2→A, C3→B):** that confounds the authoring cohort
  with the split — B would be exactly the freshest scene batch, so any drift
  seen on the re-test could not be told apart from "these scenes are simply
  different" — and it makes cohort membership visible in the item list
  (01–80 = A, 81–140 = B), which invites ad-hoc edits with split effects.
  "Same producers, same time" (README wording) loses its exchangeability.
- **Why not ID alternation:** authoring order correlates with scene clusters
  (the chunks were authored as topical batches); alternation inherits that
  pattern. Hash-rank breaks it.

## 2. The draw

| language | strata (e/m/h) | B quota e/m/h | A : B |
|---|---|---|---|
| de | 24 / 66 / 50 | 10 / 26 / 20 | 84 : 56 |
| zh | 24 / 67 / 49 | 10 / 27 / 19 | 84 : 56 |
| en | 24 / 66 / 50 | 10 / 26 / 20 | 84 : 56 |
| **Σ** | | | **252 : 168 (60.0 / 40.0)** |

Exactly the table offered in the split proposal; the operator's ~252/~168 holds
with zero remainder, per language and pooled.

## 3. Audits (reported, not repaired, no re-roll)

- **Domains (all mentions, A/B):** biz 105/66 · compliance 64/49 · leg-cn
  105/68 · leg-de 65/42 · leg-x 39/27 · lng 44/27 · ml 28/20 · code 38/28 ·
  leg-en 4/3. Every non-tiny domain lands within ~±2 pp of the pool share;
  `leg-en` is the known tiny cell, no repair.
- **Constrained items:** A 81 / B 56 → 32.1 % / 33.3 % (pool 137/420 = 32.6 %,
  spread ±1.2 pp). A scoring math on constraint compliance and B's re-test
  carry comparable shares.
- **Easy floor in B:** 30 items (17.9 % of B, exactly the 10/language quota) —
  the hold-out keeps a floor, so a future worst-case interpretation on B reads
  against the same standard your C2 review §7 established for the pool.

## 4. Where it lives

- `scripts/pool_split.py` — the rule as code; asserts source hash, strata cells,
  per-language and pooled counts; writes the manifest; re-runs are byte-identical
  (idempotence verified twice).
- `data/evals/judge_set_v1/pool_split.json` — manifest (REGISTERED): rule text,
  salt, count table, per-item assignment. **Raw sha256
  `e7bfa959bdd5e88ce0886be0cbbc293dead27afb0925fa86f802350c217a278c`.**
  Bookkeeping only: no judge run reads this file; item IDs stay out of judge
  payloads per §7.
- `README.md` §6 — the split paragraph now names the rule, the quota table and
  the manifest hash instead of the ~60/%~40 % sketch.
- prereg §4.4b — a registration line dated 2026-11-10, "registered pre-scoring".

## 5. Sealed and next

- Cohort A (252) is the composition benchmark input. Cohort B (168) is not
  scored in the composition run and not touched until the re-test or a v2 judge.
- The split is not part of the pool-freeze decision-space (prereg says so
  explicitly); the registration is intentionally dated and hashed before any
  A-side result exists, so there is no room for post-hoc assignment shopping.
- Next: the composition run on A; B's first touch is the re-test or v2 judge.
