# LR-schedule gap in expert-merge prereg v0.2: fix the selection rule before the probe logs are read

**Date:** 2026-11-05
**Addressed to:** Quinn (author of the LR probe, runner 764814, detached, arms running)
**Evidence:** `pipeline/config.py` (`learning_rate 1e-3`, `warmup_iters 30`, `lr_decay_iters 300`, **`min_lr 1e-4`**), `pipeline/train.py::get_lr` (linear warmup → cosine to `min_lr` → flat at `min_lr`), prereg v0.2 `cafdce2`
**Status:** amendment note — cycle step 1. The v0.3 edit follows when the probe logs land (`out_c/expert_merge/lr_probe_logs/`); predictions P1–P5 are unaffected.

## 1. The gap, and why this note is time-critical

v0.2 froze without an optimiser schedule. That is my miss in the freeze process: the
schedule is a design parameter, not an implementation detail — it shapes every
prediction the document makes. Your 3-arm probe is the right instrument, but for the
probe to stay preregistered rather than post-hoc, the **selection rule must be fixed
before any arm's log is read**. Hence this note, sent while ARM A is still running.

## 2. The arms as posted, with three source-backed caveats

| arm | peak rate | warmup | decay iters |
|---|---|---|---|
| A | 1e-4 | 500 | 20000 |
| B | 3e-4 | 1000 | 40000 |
| C | 1e-3 (ladder, unchanged) | 1000 | 10000 |

- **(a) Arm A's decay is a no-op under the current defaults.** `min_lr = 1e-4` equals
  A's peak rate, so after warmup the cosine sits flat at 1e-4 for the whole run.
  Constant-rate fine-tuning is defensible, but it should be a choice, not an accident:
  either confirm A as constant-rate, or set `min_lr` below the peak (e.g. 1e-5) so the
  schedule actually decays.
- **(b) Arm C is a two-regime run, not "hot all the way".** With the ladder schedule
  (decay 10000, `min_lr` 1e-4), C runs its 1e-3 phase for ~10k steps and then sits at
  1e-4 for the remaining ~9.5k of our 19.5k-step run. That is a legitimate shape for
  explore-then-settle, but it should be stated in v0.3 if C is chosen.
- **(c) The probe has a structural blind spot: at step 100 no arm has reached its
  regime.** Effective LR at step 100: A ≈ 2e-5 (warmup 100/500 of peak), B ≈ 3e-5,
  C ≈ 1e-4. All three arms are still in warmup; the probe measures early stability,
  not the compared regimes. Consequence: the probe can **disqualify** (divergence,
  loss climbing on a converged model) but cannot **optimise**. The selection rule
  below is built around that limitation instead of pretending 100 steps rank the arms.

## 3. Proposed selection rule (binding text for v0.3 §2.3)

- **R1 (disqualify):** any arm with NaN/inf, or with loss at the end of the probe
  above its own step-10 level — divergence on an already-converged model.
- **R2 (metric):** trailing mean of the training loss over probe steps 81–100, per arm.
- **R3 (choice):** among surviving arms, pick the **lowest peak rate** whose R2 value
  is within +5 % of the best surviving arm.
- **R4 (tie):** two arms within 0.5 % → the lower rate.
- **R5 (no arm survives R1):** the schedule becomes an open item; B1/B2 wait for a
  revised probe. A broken schedule is not picked just to proceed.

Rationale for the "lowest rate within band" shape: the warmup bias in (c) already
disfavours long-warmup arms, and a fine-tune of a converged model on a 20 MB corpus
wants the gentlest schedule that does not sacrifice progress. Requiring the *higher*
rate to prove superiority (not merely parity in a noisy 100-step window) is the
compensation.

## 4. Second gap found while checking: training seeds

v0.2 fixes the eval seed (1234, §2.5) but no training seed. Proposal for v0.3:
**seed 1234 for both B1 and B2** — matched data order, so the P4 comparison isolates
the fake-quant forward as the only difference (matched-pairs logic; the eval seed
being numerically equal is harmless, different generators).

## 5. Process

When the logs land: v0.3 gets a new §2.3 subsection "Optimiser schedule" (chosen arm,
the probe numbers, all three arms reported — not just the winner), the seed line, and
a changelog entry; then review and re-freeze per the usual cycle. Probe logs stay as
artefacts under `out_c/expert_merge/lr_probe_logs/`.

Freeze-checklist lesson for every future prereg: corpus, **schedule**, seeds, gates,
decision table, cost — all six before FROZEN. v0.2 had five of six.
