# Sonde A — A1-K5 Ladder Readout

Status: **COMPLETE** (ladder marker `ladder-ladA-A1-K5-done 2026-09-18 08:22:02`).
All values below are transcribed verbatim from the training logs
(`out_c/logs/ladA-A1-K5_<phase>.log`) and the routing analysis
(`out_c/logs/ladA-A1-K5_routdiag_final.txt`). Nothing here is inferred; the limits
section names what was **not** measured.

## 1. Per-phase training metrics

| phase | steps | ms/step | lr | final val ppl | best val ppl | test ppl | bpw | checkpoint (best) |
|---|---|---|---|---|---|---|---|---|
| base (prose) | 150000 | 175 | 0.00010 | 2.58 | 2.49 | 2.67 | 1.370 | `…_base_best.pt` |
| code   | 10000 | 148 | 0.00010 | 4.38 | 2.98 | 5.77 | 2.130 | `…_code_best.pt` |
| math   | 10000 | 178 | 0.00010 | 1.56 | 1.35 | 1.52 | 0.644 | `…_math_best.pt` |
| legal  | 10000 | 207 | 0.00010 | 2.24 | 2.10 | 2.26 | 1.161 | `…_legal_best.pt` |
| ga     | 10000 | 237 | 0.00010 | 2.30 | 2.24 | 2.39 | 1.200 | `…_ga_best.pt` |

(`…` = `out_a/bdh_textmix_ladA-A1-K5-`. final val ppl / best val ppl / test ppl are the three
distinct logged measurements — final-step val, best-checkpoint val, held-out test — reported
separately so they are not conflated.)

Notes that fall out of the numbers (measurements, not verdicts):
- `base` runs 150k steps (pretrain); the four CL phases run 10k each.
- ms/step rises monotonically (175 → 237) with the grown per-head width, as expected.
- `code` is the only phase whose **final-step** val ppl (4.38) is materially worse than its
  **best** (2.98) — i.e. the best-checkpoint is the one to serve; the last checkpoint drifts up.
  Both are archived. `math` is the strongest phase (best 1.35 / test 1.52).

## 2. Routing readout (router ckpt = `…_ga_last.pt`, likelihood scan)

Router config: widths `[8192, 10240, 12288, 14336, 16384]` per head, window 128 tokens,
200 crops/domain.

Confusion matrix — rows = true domain, cols = routed prefix width:

```
            8192   10240   12288   14336   16384
prose (base) 200      0       0       0       0
code           0    200       0       0       0
math           0      0     200       0       0
legal          0      0       0     200       0
ga             0      0       0       0     200
```

**Perfect diagonal: 200/200 on every true-domain cell, zero cross-route mass** across all
five domains. Routed own-width ppl vs the joint full-width reference:

| domain | routed own-width ppl |
|---|---|
| prose | 2.46 |
| code  | 4.90 |
| math  | 1.47 |
| legal | 2.28 |
| ga    | 2.37 |

**joint full-width reference ppl = 23.66** (served positions only). Routing therefore isolates
each domain into its own width (1.47–4.90) instead of the degraded joint 23.66.

## 3. Bit-exactness (P5) and artifacts

```
P5-VERDICT: PASS   p5_rc=0  base -> code
P5-VERDICT: PASS   p5_rc=0  code -> math
P5-VERDICT: PASS   p5_rc=0  math -> legal
P5-VERDICT: PASS   p5_rc=0  legal -> ga
```

The masked parent block is BIT-EXACT (`encoder`, `encoder_v`, `decoder`, `embed`, `lm_head`,
`attn.freqs(shared)`) through every phase; grown segments are non-zero (max|w| ~0.45) with
zeroed Adam moments on the masked block. 10 A1-K5 checkpoints present, `best`+`last` for
each of `base/code/math/legal/ga` (verified 10 rows in `out_a/`).

## 4. Interpretation, bounded

- **Separability**: the perfect 200/200 diagonal is the separability result — five
capacity-addressed domains route to their own width with no leakage. This is the structural
goal of the scaling probe; it is satisfied on this ladder.
- **Routing advantage**: routed own-width ppl 1.47–4.90 vs joint 23.66 — the joint-serving
degradation is avoided by routing. (The project-wide caveat that the joint reference can
conflate joint-serving cost with routing benefit is retained — the routed numbers above are
reported directly, not as a ratio claim.)
- **Integrity**: P5 PASS ×4 with rc=0 confirms the growth/mask chain is bit-identical through
acquisition — no decay leak in this ladder.

## 5. Limits — what was NOT measured here

- **No acquisition-vs-retention delta.** Acquisition-time ppl is not in these phase logs, so
  no retention=acquisition claim is made. (Compare against Sonde B/C method if a retention
curve is wanted.)
- **Single run.** No seed value / seed-count is captured in these logs; results are a
  single run, **not** a multi-seed floor. The 2-point evaluation noise floor established
  earlier applies before any small delta is read as signal.
- **Pre-registered Sonde-A gates** are cost/separability-shaped and live in
  `docs/plans/2026-09-16_sondeA-scaling-probe.md`; the ppl above are the documented
  measurement, and the perfect diagonal is the separability component. No pass/fail gate
  word is asserted beyond what the matrix itself shows.
- `bpw` is reported as logged, without re-interpreting the unit.

Generated: 2026-09-18, host bdh-4090. Source-of-truth: the cited log files.