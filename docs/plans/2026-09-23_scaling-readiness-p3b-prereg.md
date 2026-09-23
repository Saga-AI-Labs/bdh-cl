# Scaling-readiness P3b pre-registration - leak-rate-vs-K and the window question (eval-only)

- Date: 2026-09-23. Seat: A0-Quinn. Status: frozen before launch.
- Operator GO 2026-09-23: "minimaler Zeitaufwand -> go fuer beide
  eval-only-Erweiterungen" (answering pi50 #442; bus reply #450).
- NO training. Evals only, on the existing checkpoints.
- Origin: pi50 #442 (Q1 leak-rate-vs-K, Q2 is the ~8% a window-128
  artifact?). P3 shipped the full 8x8 ONCE, at ga_last - the per-phase
  instrument was the own-width routdiag only. Q1 is unanswered by P3.

## Instrument

`scripts/eval_router.py` on the guest at HEAD `e6bf359` - md5
`73832ecd08f24eded93a98a74572be6e`, git-clean against that HEAD (the copy that
produced the P3 comparison base). The first pre-registration pinned
`ed9fd326...` (`2f0dc9d1`, the local build with the `--crop-dump`/`--pos-dump`/`--route-grid` flags) - that file was never on the guest path; the md5 gate
aborted the first launch, no measurement was taken, and the pin was corrected to
the guest reality additively. Both builds share every flag P3b uses (`--routes`,
`--window`, `--domains`, `--crops`, `--mb`, `--batch`); the dump flags are unused
here. Guest copy md5-pinned in the driver log. `--routes
8192,10240,12288,14336,16384,18432,20480,22528` (routes above a
checkpoint's width clamp to it - they are identical to full width),
`--crops 200 --mb 30 --batch 4`, the 8 domains as in P3.

## Run A (Q1: leak rate vs K)

The 8x8 at EACH of the eight checkpoints of the P3 ladder (base@8192,
de@10240, es@12288, pl@14336, code@16384, math@18432, legal@20480,
ga@22528 - widths of the P3 phases, the ga=8192+7*2048 form), window
128, 200 crops/domain. Output: `p3b_confusion_<tag>.txt` in
`out_c/scaling_readiness/p3b/`, verbatim confusion block parsed.
leak(tag) := off-diagonal share = (1600 - diagonal)/1600.
base (8192): all routes clamp to 8192 - one column, base has no leak
by construction; kept as the control.

## Run B (Q2: window of the leak)

ga_last, domains=legal only, window 128 (the 128 reading is on record:
8x8_final - 5@8192,195@20480) and window 384, crops 200, own width
22528 plus the 8192 route (the narrow column is the leak target).
Output `p3b_window_ga_legal_w128.txt`, `p3b_window_ga_legal_w384.txt`.
Caveat on Print: printed ppl are NOT comparable across windows (the late
span changes); the comparison quantity is the leak share and the 8192
column, not the printed ppl.

## Frozen verdicts (set before measurement, read only afterwards)

Q1:
- H-scalefree-decreasing: leak(ga_last) <= 0.50 * leak(de_last).
- H-flat: else leak(ga_last) within [0.50, 1.50] * leak(de_last).
- H-rising-or-other: else (report the curve verbatim).
- The pi50 thesis (relative damage shrinks with K) predicts
  H-scalefree-decreasing; scale-free routing error predicts H-flat.

Q2:
- H-window-dependent: legal leak share @384 <= 0.70 * share @128
  (attenuated, mirrors the harvest window probe 9->7 / 11->5).
- H-window-independent: else. If so: the 8% class cost is
  window-128-specific and the manuscript must state it window-conditional.

- n = 200/domain, descriptive, no p-value, no second seed.
- Single ladder, single seed - same scope limits as P3.
- The ~8.2/8.6% P0 cost figures: measured @128; Run B tests whether
  they hold at 384.

## Scope and side effects

- Writes only `out_c/scaling_readiness/p3b/`; `out/`, `out_a/`, the P3
  dirs untouched. GPU claim exclusive `gpu://rtx4090` + renewer; release
  when done. No training, no weight movement.
- Runtime: Run A ~8 x (effective ~2 non-clamped routes x 200 crops) +
  ckpt loads; Run B minutes. Total budget: minimal, target < 30 min.
