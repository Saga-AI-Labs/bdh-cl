# Router Bias-Correction & Margin-Escalation — Preregistration v0.1 (draft)

**Status:** DRAFT v0.1 · drafted 2026-11-02 · asb (assistant-drafted; freezes only after both seats sign off)
**Position:** post-hoc *characterization and decision-rule change*, **not** a bridge gate.
It modifies neither the bridge protocol nor the adversarial prereg (`e288141`); its result
cannot invalidate any pre-registered gate.
**Trigger:** the running legal/code eval (score-vector, stage b) + the settled Sonde B
legal-leak thread (5 legs, complete through the window probe).

---

## 0. The story in one paragraph

The router's one known failure is directional and replicated: crops flip **downward only**
(legal→base, code→peer), the flip is **wrong ~90 % of the time** when it happens (D3:
leakers locally right 1/9 and 1/11, stayers 187/191 and 186/189), leakers sit at **small
margins** (D1), and **half the flips vanish** when the scoring window grows 128→384
(leg 5). Two candidate causes were named and never separated: (1) an **asymmetric bias** in
the routing rule, (2) a **too-short window**. This prereg separates them *offline* with the
already-collected score vectors, tests the cheapest fixes, and defers any training-level
change until the offline verdict is in.

## 1. Working hypothesis

**H1 (per-route bias).** Grown neurons are trained only on their own territory
(write-gating); on non-domain text they contribute noise. The early-window score
`S_r(c) = mean NLL of route r over positions 0..127` therefore contains a per-route
additive bias `τ_r > 0` for every route r beyond the base. The router compares raw `S_r`;
the bias pushes borderline crops toward the base/peer route — **always in the same
direction**, which is exactly the observed one-sidedness.

**H2 (window).** Independently of H1, 128 tokens under-determine the base-vs-own
comparison for a minority of crops; part of the flips is tie-break noise that longer
windows remove (leg 5: ~half).

H1 and H2 are not exclusive. The prereg measures both shares.

## 2. Data in hand vs. data needed (as of 2026-11-02)

| instrument | resolution | available for | needed for |
|---|---|---|---|
| `--score-vector` (running, stage b) | 25 routes × crop, early-128 **mean** | all 25 domains | A1–A3 (bias) |
| `--pos-dump domain:wA,wB` | 128 per-position margins, **exactly two widths** | legal (vs 8192), code (peers 53248/57344) | A5 (exploratory only) |
| `--crop-dump` | per-crop two-route scores + late losses | legal, code | A5, D-new |
| window-384 score vectors | — | **new run needed** (§4) | A4 (escalation) |
| per-position, all-route, top-2-auto dump | — | **instrument amendment** (§6, deferred) | universal flip-position features |

Explicitly **not** assumed: any position-resolved feature beyond the two dumped pairs.
The score vector's 25 values are early-window means; no "at how many positions does the
decision flip" feature is claimed outside those pairs.

## 3. Frozen offline analyses (no forwards)

Splits are by crop index, fixed before looking: **even indexes estimate, odd indexes
evaluate**, computed per domain (crop-index identity by construction, as in the margin
probe). Estimation and evaluation never share crops.

- **A1 — offset estimation.** For every route r: `τ_r = median over prose
  estimation-crops of S_r(c)` (prose = base/host domain; it is the one domain where no
  route has a domain advantage by construction). Robustness: recompute with mean; report
  split-half reliability of `τ` (even-vs-odd prose crops).
- **A2 — corrected routing.** `S'_r(c) = S_r(c) − τ_r`; re-argmin all evaluation crops.
  Freeze before running: overall accuracy, per-domain confusion, **direction histogram of
  every changed decision** (down / up / held).
- **A3 — one-sidedness discriminator (the H1 test).** After correction, is the flip
  direction still 100 % downward? H1 predicts the asymmetry collapses toward symmetry;
  a pure-window cause predicts no change. Report share of downward flips among all flips,
  before vs. after.
- **D-new — local correctness of upward flips.** If corrected routing creates *upward*
  flips, check them against the late-window served loss (crop-dump / route-grid where
  available): locally **right** upward flips support H1; locally **wrong** upward flips
  refute a pure additive-bias model.
- **A4 — margin-gated escalation (needs §4 run).** `τ_esc` = 10th percentile of margin
  on the *estimation* half only. For evaluation crops with margin < `τ_esc`, substitute
  the window-384 score vector; re-argmin. Pre-registered primary readout: changed-decision
  count and local correctness of each change.
- **A5 — exploratory pair profiles (no gate).** From the existing legal(↔8192) and
  code(53248/57344) position dumps: count per-crop flip positions; correlate with leak
  status. Characterization only; generalization waits for §6.

## 4. The one new run

Re-run `scripts/eval_router.py` on the identical crop set (same seed, same order, same
checkpoint) with `--window 384` and `--score-vector`, legal + code first, then the
remaining domains. Block size is 512 (cf. `1b0e4af` message), so 384 is the largest
window that keeps a 128-token late span — the same substitution logic as leg 5.
Cost: one forward pass per crop-route pair already budgeted in the stage-b run.
Pairing across windows is by crop index; any index mismatch aborts the analysis.

## 5. Predictions (first-guess bands; falsification is a result, not an embarrassment)

- **P1** Offset correction (A2) reduces legal misroutes on the evaluation half by ≥ 50 %
  relative, and increases no other domain's misroute count by more than 2 crops.
- **P2** Downward share of flips (A3) drops from 19/19 (legal, n=200 sample) into
  {50 % .. 80 %}. If it stays > 90 %, H1 is **falsified** as the dominant cause.
- **P3** Escalation (A4) removes ≥ 40 % of low-margin flips (leg-5 attenuation suggests
  ~50 %; band kept wide on purpose, cf. the P1 lesson from the replication leg).
- **P4** Code boundary cases (four at n=200, commit `2882e0e`) sit in the low-margin
  tail: ≥ 3 of 4 have margin below the overall median.

## 6. Deferred instrument amendment (nachziehen, separate commit)

`--pos-dump-auto PATH`: for **every** crop, after the early scores are filled, select the
top-2 routes automatically and dump the 128 per-position margins for that pair (plus the
late-window served loss at both widths) — zero extra forwards, same rl tensor. This
removes the two-fixed-widths limitation and makes flip-position features universal.
Format sketch: `crop, wA, wB, margin[128], late_loss_A, late_loss_B` per line/row.
Ship together with a regression check against the existing hand-paired legal/code dumps
(same crops, same margins, exact match).

## 7. What this does not establish

- Any claim about unseen crops — Stages 1–2 of the adversarial prereg (`e288141`)
  remain the instrument for that, unchanged.
- Any training-level fix. If A3/A4 leave a material one-sided residue **and** D-new
  comes back locally-wrong, the follow-up is a separate prereg (**RBC-2**): a
  margin-sharpening auxiliary loss inside the route-aware backward pass (per `1b0e4af`
  infrastructure), gradient-masked to the grown neurons only, so P5 bit-exactness is
  untouched by construction. RBC-2 is **not** registered here.
- Production routing policy. If H1 confirms, the shipping change is a per-route offset
  table + escalation rule in the serving path, recalibrated **per phase** on a small
  replay set — the continual-learning-native consequence (the bias is expected to drift
  with every growth step; the router needs its own replay).

## 8. Pointer index

| artefact | commit / path |
|---|---|
| margin definition | `docs/plans/2026-10-23_adversarial-router-test-prereg.md` (`e288141`) |
| leak thread narrative (legs 1–5) | `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-thread-report.md` |
| D3 one-sided error | `.../2026-09-22_sonde-B-legal-leak-margin-report.md` (`5f20c7e`) |
| window attenuation | `.../2026-09-22_sonde-B-legal-leak-window-report.md` (`9cd5df68`) |
| leak pricing (1.09× / 8 %) | `.../2026-09-22_sonde-B-grown-capacity-ablation-report.md` |
| legal n=200 = 19/200 | `docs/reports/2026-10-31_k25w1024-routing-matrix-results.md` L97–105 |
| code n=200 = 98.0 %, 4 boundary cases | same report, `2882e0e` |
| route-aware backward | `1b0e4af` (pipeline/train.py) |
| score-vector / crop-dump / pos-dump / route-grid | `06921e7`, `72399e1`, `2f0dc9d` + working tree |
