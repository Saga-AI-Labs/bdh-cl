# Scaling-readiness assessment and cheap-probe pre-registration

Date: 2026-09-22 (UTC) - Seat: Muse Spark (assistant) - Status: DRAFT until operator GO
Type: assessment + frozen probe design. Written BEFORE any new measurement beyond the committed record.

Companions (evidence this assessment rests on):
- `docs/reports/phase_2/2026-09-21_sonde-B-harvest-results-report.md` (seed-2 a/b/c)
- `docs/reports/phase_2/2026-09-22_sonde-B-reference-ladder-replication-report.md` (ref-1337, P1 falsified)
- `docs/reports/phase_2/2026-09-22_sonde-B-grown-capacity-ablation-report.md` (capacity causal)
- `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-{margin,window,content,position}-report.md` + `...-thread-report.md`
- `docs/reports/phase_2/2026-09-16_probe-b.md` (B-PASS), `2026-09-16_probe-c.md` (C0), `2026-09-16_probe-c-arms.md` (C-PARTIAL), `2026-09-17_probe-r-j.md`, `2026-09-17_probe-s-semantic-addressing.md` (S-PASS false)
- `docs/reports/phase_2/2026-09-20_sonde-D-hybrid-crop-addressing-report.md` (surface-follower, damage pairs)
- `docs/plans/2026-09-16_sondeA-scaling-probe.md` v0.3 (P-A1..P-A4, Gates A-PASS/PARTIAL/FAIL, TBD-K/TBD-GB still open)

---

## 0. Why this plan exists

Operator question (2026-09-22): behaviour across domains is mapped at ladder scale; scaling eval is TBD. Are the domain results good enough to base expensive follow-up (A1-K20 ~2.5-3d, A1-K40 +1-2d, A2-W1024 ~3-5d, PoC weeks) on, and did we miss cheap probes that must precede it?

Verdict up front: **yes, good enough to scale IF the scale-up is scoped to byte-distinct domains with the likelihood-scan router — after 3 cheap probes + 1 small pilot.** Not good enough for semantic/paraphrase, OOD-reject, or optimal growth sizing claims. The probes below cost minutes to ~hours, not days, and each has a frozen GO/NO-GO reading for A1-K20.

## 1. Assessment — where we stand

**Done and replicated (ladder scale, n_embd 512, 10k iters/phase, 200 crops/domain):**
- Storage thesis: P5 `BIT_EXACT 4/4` on B, C0, seed-2 harvest, ref harvest. F-V9 mechanism is base-composition-blind (prose-only vs multilingual ±0.02 ppl acquisition).
- Addressing: expert present → 200/200 + oracle serving; absent → scatter + 4-5x worse. (b) oracle equality `delta 0.00` both ladders (4.95=4.95, 4.90=4.90).
- Capacity causality: forced-width ablation `36.4x / 22.0x / 24.0x` (math/code/ga), legal `2.15x`. Homeless contrast was observational; ablation makes it causal.
- Leak bounded: only replicated directional signal (9/200 → 11/200, 20/20 down, 0 up), priced ~8% (2.39@12288 vs 2.20@14336), attenuates at w384 (7 and 5), `H-cancel ACCEPTED` (median R 0.0735/0.1139), no content/position separator. Not a capacity defect.
- Failure culture intact: P1 falsified at 189 vs {191..199}, shared-core 114/148/161 withdrawn, P-C1 falsifier triggered, S-PASS false, P-C4' FAIL. Retractions are additive, not edited away.

**Explicitly out of scope so far (do not claim):**
single seed per cell (two ladders total), 200 crops, ladder scale only, `no 100M pass`, `seed-3 off`, (c) check is author reconstruction post-hoc, O(K) scan at K=40 never run, `TBD-K/TBD-GB` still placeholders.

## 2. Gaps that must close before expensive runs

G1. **Eval power + dedup.** Leak claims rest on n=7/5, descriptive only. Ref crops 41/131 share 471/512B (92%) → effective n=4. No document-leakage audit. The 8% cost has no interval.
G2. **Growth-sizing + checkpoint rule.** Legal saturates by 12288 (final increment 1.09x) — over-grown. Code `final 4.38 vs best 2.98` drifts; harvest serves `_last.pt`. No stopping rule, no best-vs-last rule. At K=40 each block thins to ~12% width: waste compounds.
G3. **Harness hardening.** `block_size 512` footgun (default 128 silently wrong), driver once emitted 295B argparse stubs (`--domains` missing), storage check has no reusable harness. A 3-day ladder must not depend on eyeballing logs.
G4. **Scope fence.** Probe S oracle paraphrase 19.2%, routing 50% (tie-break); P-C4' agreement 104/576; J INCOMPLETE (iu blocked). Chat phases byte-identical to host are unsolved. PoC must exclude them or add a reject-layer probe first.
G5. **Boundary confound (paper note, not a blocker).** Down == adjacent (14336→12288); ga top has no upper, prose bottom no lower; one boundary pair tested. 20/20 down could be adjacency, not bias.

## 3. Frozen probe set (cheap first)

### P0 — Eval scale-up + dedup (CPU + short GPU, no training)
- Re-eval `prose__legal` both ladders at N=1000 crops, window 128, same routes/spec/order (seed 1234 extension — first 200 byte ranges identical by construction, assert overlap of first 200 vs archived dumps).
- Dedup: pairwise shared-bytes audit; drop/flag pairs sharing >256B; report effective N. Audit document leakage by offset histogram.
- Frozen reading: leak rate + served ppl of legal @14336 vs @12288 with Wilson 95% (crop-level, descriptive).
  - CONFIRM if leak 2-8% both ladders and cost 5-12% (consistent with 9-11/200 and ~8%).
  - UPDATE if leak <1% either ladder (200-crop noise) or >15% (underestimate) or cost outside 3-15%.
- Output: `leakcontent_N1000_{seed2,ref}.routdiag.txt` + overlap report. Cost: ~5x harvest eval ≈ 15-30 min. GO/NO-GO for citing the 8% figure in PoC budget.

### P1 — Growth-sizing + checkpoint rule (one short grow + re-evals, no ladder)
- P1a (no training): serve all 8 grown checkpoints (4 cells × 2 ladders) at `_best` vs `_last`; frozen rule: serving checkpoint = lower own-domain served ppl at trained width; report delta table. If `_best` wins ≥6/8, adopt `_best`-serves for all scaling evals.
- P1b (one grow, ~30-60 min): train reduced legal cell `prose__legal-gm64` (128→192, same protocol: bs512, α0.9, 10k iters, fresh opt, F-V9) on seed-2 base only. Compare legal served @12288 (gm64 trained) vs @14336 (gm96 trained, 2.20).
  - If gm64 within 0.10 ppl of gm96 → adopt stopping rule: stop growing a domain when forced-width final increment <1.15x (from `--route-grid`), and flag legal gm96 as over-grown in the manuscript.
  - Else (gap >0.25 ppl) → keep gm96 sizing, saturation reading withdrawn.
- Output: `grid_bestlast.txt`, `harv-prose__legal-gm64` checkpoint + routdiag. This is the only probe spending training GPU, bounded at one cell.

### P2 — Harness hardening + O(K) cost (no training)
- Build `scripts/storage_check.py` from the exact set `pipeline/train.py:197-203` + embed/lm_head; must PASS on all 8 existing grown checkpoints and FAIL on a synthetic corrupted copy (flip 1 weight in frozen region). Promote from author-reconstruction to harness before any K20 launch.
- Driver guards (assert pre-eval): `block_size==512`, `--domains` present, output >300B, checkpoint md5 pinned, `routes` contains per-head widths. Port the seed-2 stub trap into a failing test.
- O(K) projection: time `eval_router` scans at K=5 (existing) vs K=20/23 (RA2b-lt 23 routes, existing checkpoint, no training) across 50 crops; fit linear slope; project K=40 scan cost. If superlinear (>2.5x from K=5 to K=20 per crop), flag P-A1 risk before A1-K20 launches.
- Output: harness script + test log + cost slope. GPU: <15 min (evals only); rest CPU.

### P3 — Mixed K=8 pilot (small ladder, the only mid-cost item)
- One ladder, 7 grows: base prose + 3 Europarl (de, es, pl — includes a P-R3 hard cell) + code + math + legal + ga. Same B/C0 protocol (bs512, α0.9, +32, 10k/phase, F-V9). This mix (Europarl + code/legal crossing script/register) has never been grown together.
- Instruments per phase (Sonde A suite, reduced): acquisition, P5 every transition, full 8×8 confusion (200 crops), retention deltas, joint-vs-routed, wall-clock + bytes/phase.
- Frozen gates:
  - P3-PASS if P5 7/7 AND routing ≥0.95 AND first-phase retention |Δ|≤0.08 → GO A1-K20 unchanged.
  - P3-PARTIAL if storage holds but routing 0.85-0.95 or cost slope >2x first phase → GO A1-K20 with narrowed mix (drop hardest Europarl cell) + record knee.
  - P3-FAIL if P5 fails any transition → HALT, pivot to F-V9 audit (Gate A-FAIL path). Expected cost ~8-12h (scales from A1-K5 ≈12.3h/5 phases).

## 4. What this does and does not settle

- Settles: whether the 8% leak price, growth sizing, checkpoint choice, harness, and O(K) cost are trustworthy inputs to the PoC budget; whether a mixed register ladder survives (P3).
- Does not settle: paraphrase/semantic addressing (Probe S stands: S-PASS false — do not scale chat phases), OOD reject (needs fresh held-out calibration, P-C4' domains are now development data), K40 corpus inventory (still gated per Sonde A plan), 100M/W1024 behaviour (P-A3), second-boundary directionality (measure `math__ga` boundary opportunistically inside P3/A1-K20, no dedicated probe).
- Does not re-open: P1 (falsified), ablation H1/H0, H-cancel/H-few, C-PARTIAL scope.

## 5. Cost, outputs, gates to scaling

- P0 ~15-30 min GPU + CPU audit. P1a <15 min; P1b one cell ~30-60 min. P2 <15 min + CPU. P3 ~8-12h. Total before A1-K20: <1 day GPU, versus 2.5-3d for A1-K20 and weeks for PoC.
- Raw under `out_c/scaling_readiness/` (gitignored, md5-pinned in reports); reports under `docs/reports/phase_2/2026-09-2*_scaling-readiness-*.md`; bus intent before / done after per probe.
- Gate to A1-K20: P0 CONFIRM (or UPDATE with revised budget figure) ∧ P2 harness PASS + O(K) slope linear ∧ P3 ≥PARTIAL ∧ P1 serving rule frozen. A1-K40/W1024 remain gated on A1-K20 telemetry (P-A1..P-A4), not on this plan.

## 6. Provenance

- No new measurement taken to write this plan; every number quoted from the companions above.
- Checkpoints referenced (read-only): `out_c/sondeB/harvest/*_last.pt`, `out_c/sondeB/harvest_ref/*_last.pt`, `out_a/bdh_textmix_ladA-A1-K5-*-{seed2,ref}`, RA2b-lt `out/bdh_europarl_ladRA2b-lt_last.pt`. Corpus md5s as pinned in margin/window preregs (legal `0135960429085039dbe5385f649e75fe`).
- Operator GO required before P1b or P3 launch (training spend); P0/P1a/P2 are re-evals/hardening and may proceed under a single short claim.
