# Router Bias-Correction & Margin-Escalation — Preregistration v0.1 (draft)

**Status:** DRAFT v0.2 · drafted 2026-11-02, amended 2026-11-04 · asb (assistant-drafted; freezes only after both seats sign off)
**Position:** post-hoc *characterization and decision-rule change*, **not** a bridge gate.
It modifies neither the bridge protocol nor the adversarial prereg (`e288141`); its result
cannot invalidate any pre-registered gate.
**Trigger:** the running legal/code eval (score-vector, stage b) + the settled Sonde B
legal-leak thread (5 legs, complete through the window probe).

---

## v0.2 amendment (2026-11-04) — resolved by data before freezing

- **H1 is falsified.** Five-domain score vectors (legal, code, math, zh, ga; 200 crops
  each, all 25 routes, `zh_last.pt`) show the width↔off-domain-score correlation is
  **negative in all five** (code −0.648, math −0.530, zh −0.539, ga −0.176, legal
  −0.007): wider routes score *better* on foreign territory, the best off-domain
  competitor is always a wide route (53248/49152/57344), and 8192 ranks #1 off-domain
  on legal only (code #6 at +1.85 nats, math #5, zh #5, ga #3). An additive per-route
  bias cannot hold. Analysis: `docs/notes/2026-11-03_rbc1-h1-contradicted-by-five-domains.md`.
  What fits instead: a **capacity monotonicity** (a width-w route contains all frozen
  phases 1..k, so wider = better generalist); legal is the explainable exception
  (legal ≈ prose, the base route is genuinely competent there). Capacity is not
  correctable, so the A1–A3/D-new remedy is dead.
- **H2 is confirmed, and the mechanism is sharper than §0 anticipated.** Window 384 on
  identical crop indices (same checkpoint, seed, 200 crops/domain): legal 19→5
  misroutes, code 4→2 — **17 of 23 removed at zero additional compute**, because the
  forward already covers all 512 positions and the window only selects the averaging
  slice (`scores = rl[:, :, :window].mean(dim=2)`; wall times 5257/5260 s vs
  5264/5253 s). Mechanism: a **thinner boundary band**, not larger margins — legal p5
  margin doubles 0.0666→0.1373 while the median barely moves (0.4918→0.4806). The five
  survivors sit close enough to the boundary that 384 does not resolve them; the one
  broken crop (39) was already a boundary case in the position decomposition. Commit
  `b89eec3`. A4's paired rerun has therefore already happened.
- **Reliability features (stage b): no cheap fallback exists.** Of six features, raw
  margin is best (15/19 legal + 4/4 code caught at a 20 % fallback); std points the
  *wrong* way (0.7586 vs 0.7167); normalization is a no-op; "do nothing" is rational at
  0.03 nats aggregate cost vs a 20 % compute surcharge (commit `8b42104`). Note: that
  arithmetic was computed at window 128; with window 384 free, the fallback question
  mostly dissolves.
- **Still open (the remaining value of this prereg):** the window-256 third point
  (does the removal curve saturate before block limits force longer blocks?); width vs
  growth-order separation using the remaining twenty domains (width and training order
  are confounded; 3 of 5 best off-domain competitors are order-neighbours); P4 below.
  Longer blocks are priced (~32/42 GiB activations at 768/1024) and not warranted yet.
- **Protocol recommendation:** route at window 384 by default; keep raw margin as the
  single monitored feature; drop the bias-correction line entirely.

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

- **A1 — offset estimation.** *(STRUCK v0.2: H1 falsified, see amendment.)* For every route r: `τ_r = median over prose
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

- **P1** *(OBSOLETE v0.2 — tested the falsified H1 path.)* Offset correction (A2) reduces legal misroutes on the evaluation half by ≥ 50 %
  relative, and increases no other domain's misroute count by more than 2 crops.
- **P2** *(OBSOLETE v0.2 — same.)* Downward share of flips (A3) drops from 19/19 (legal, n=200 sample) into
  {50 % .. 80 %}. If it stays > 90 %, H1 is **falsified** as the dominant cause.
- **P3** *(CONFIRMED v0.2 by direct experiment, commit `b89eec3`: 17/23 removed.)* Escalation (A4) removes ≥ 40 % of low-margin flips (leg-5 attenuation suggests
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
