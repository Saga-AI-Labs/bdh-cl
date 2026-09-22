# Sonde B - legal-leak window probe pre-registration

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: DRAFT until frozen pre-run
Frozen design of record, written BEFORE any measurement at the longer scoring windows.

Companions:
- thread narrative of record: docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-thread-report.md
- result under test: docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-margin-report.md (D3 one-sided error)
- external thread: HAK bdh-cl #403 and the operator GO on the longer-window probe.

---

## 0. The question

The margin probe established that the legal leak is a **one-sided error at the decision boundary**: the
router is locally right ~98% of the time when it stays at 14336 and locally wrong ~90% of the time
when it flips down to 12288. Two explanations survive, and they imply different fixes:

- **H-short (horizon):** the 128-token scoring window is too short to separate 12288 from 14336, so
the tie-break lands arbitrarily when the evidence is faint.
- **H-rule (asymmetry):** the routing rule itself prefers the smaller prefix on faint evidence.

If H-short holds, the fix is a wider scoring window, not a different router. If H-rule holds, the
asymmetry is a property of the rule and must be characterised as such.

## 1. The requested window and the declared substitution

The operator asked for windows **256 and 512**. **512 is inadmissible and the substitution is declared
here, before the run:**

- `scripts/eval_router.py` asserts `0 < args.window < bs`, and `bs = cfg["block_size"] = 512` on both
  legal checkpoints (measured, recorded in the margin pre-registration). A window of 512 fails the
  assert and the process exits - no measurement would exist to report.
- Window 511 is admissible but leaves a **1-token** late window (`rl[:, :, window:]`). D3 asks whether
  the chosen width serves the crop better on the late window; at 1 token that question is decided by
  a single position and is meaningless by construction.

**Frozen substitution: windows 256 and 384.** The second value is chosen on a stated principle: its
late window is `512 - 384 = 128` tokens, exactly the length of the baseline scoring window, so D3 at
window 384 has the same late-window power as the original probe. 384 is therefore the largest window
that keeps D3 interpretable; 256 (late 256) is the midpoint the operator named.

Baseline for all comparisons: **window 128**, already measured on both ladders by the margin probe.

## 2. Instrument and design

- Instrument unchanged and already pinned: `scripts/eval_router.py` @ commit `72399e12`,
  md5 `70ddc5f31c0e3871c029f4f4f9dee7d2`, `--crop-dump legal:12288,14336`. **No new instrument code.**
- Ladders: seed-2 `out_c/sondeB/harvest/bdh_textmix_harv-prose__legal_last.pt` (md5
  `d94686ad9f90d4750ba8d02b88ffd9ea`) and reference `out_c/sondeB/harvest_ref/...-prose__legal_last.pt`
  (md5 `8d89b2cabe0c0dccd595fc76bd74c822`).
- 2 ladders x 2 windows = **4 runs**. Routes 8192,10240,12288,14336,16384; crops 200; batch 4;
  `--route-grid` on; domains spec and order identical to the margin probe.
- Corpus `data/textmix2/legal.txt`, md5 `0135960429085039dbe5385f649e75fe` (byte-stable).
- No training.

### Why the crop indices are identical across windows (and to the baseline)

`eval_router.py` draws crops with `torch.Generator().manual_seed(1234)` **before** any window is used,
from the same corpus bytes, the same domain order, the same `crops=200` and the same `mb=30` read
window. `args.window` enters only after the crops are drawn (it slices `rl`). Therefore the 200 legal
crops are the **same byte ranges** at window 128, 256 and 384, and per-crop results are directly
comparable across all three. This is the property the whole probe rests on; the baseline dumps are
reused rather than re-run.

### What is and is not comparable across windows (declared before the run)

- **Comparable:** the per-crop route (which width argmin picks), the route histogram, the early-window
  margins at their own length `w`, and the per-crop late losses at their own remaining length.
- **NOT directly comparable:** the instrument's printed `routed`/`served` ppl and the served-ppl grid.
  `rl[:, :, window:]` changes length with the window, so baseline ppl (2.21) and a window-384 ppl
  describe different token spans. Any ppl difference between windows is an artefact of span length and
  must not be reported as a routing effect.
- **Late-window length differs by design:** baseline D3 judged local correctness over 384 late tokens;
  D3' uses 256 at window 256 and 128 at window 384. A shorter late window yields noisier local losses,
  which makes D3' a *weaker* test in the confirmatory direction - conservative for the H-rule claim,
  and stated here rather than discovered afterwards.

## 3. Declared outcomes (falsifiable, frozen before the run)

Let `L(w)` = number of leakers (routed < 14336) among the 200 legal crops at scoring window `w`, per
ladder. Baselined: `L(128) = 9` (seed-2) and `11` (reference).

### D1' - does the leak persist at a longer window?

- **H-short supported** if `L(384) <= 2` on **both** ladders - the flips essentially vanish once the
  window is long enough, so the early window was the cause.
- **H-rule supported** if `L(384) >= 5` on **both** ladders - the flips persist despite four times the
  scoring evidence, so the asymmetry is in the rule.
- Between those: report **partial**, no promotion, with both counts and both ladders named.

### D2' - do the shared-core crops keep leaking?

The margin probe found three crops leaking on **both** ladders at window 128: **114, 148, 161**.

- If all three persist as leakers at window 384 on both ladders, they are the content-like core of the
  leak and the claim strengthens: those byte ranges mis-route even with a long window.
- If they stop leaking while others persist, the shared core was a property of the short window.
- Frozen rule: report the per-crop route of 114/148/161 at every (ladder, window) pair; classify as
  **persistent core** only if all three leak on both ladders at 384.

### D3' - local correctness at the longer window

Repeat the margin-probe D3 (per crop: is the late loss lower at the chosen width?) at 256 and 384,
with the same calibration against the stayers' base rate.

- If the leakers are locally right at least half the time at 384, the short window was manufacturing
  the errors (**H-short**, again).
- If they remain locally wrong at ~90%, the rule keeps making the same one-sided mistake with four
  times the evidence (**H-rule**).
- Frozen rule: leakers locally right `>= 50%` at 384 on either ladder is reported as overturning the
  window-128 error claim for that ladder; `< 25%` is reported as confirming it; between is partial.

### Secondary, reported but not promoted

- The route histogram at each (ladder, window) - counts per width.
- Median `|margin|` for leakers vs stayers at each window (the D1 quantity of the margin probe), to see
  whether the leakers' separation from the stayers grows with the window.
- Whether any **upward** leakage (to 16384) appears at a longer window - none has appeared so far in
  the whole thread, and its appearance would be a new phenomenon.

## 4. What this probe can and cannot do

- n = 9 and 11 leakers at baseline. This is a 4-run probe over the same 200 crops, not a trial; no
  p-value is claimed, every number is a count out of 200 with its denominator.
- It separates **horizon** from **rule** at the two windows tested. It cannot exclude a third
  explanation appearing only at windows it did not test (e.g. near-512 behaviour).
- If the flips vanish at 384, that is strong evidence for H-short but it does not by itself prove the
  mechanism is window length - it is consistent with any longer-window corrective effect of the
  identical direction.
- It does not touch P1 (falsified at 189, band {191..199}), nor the ablation, nor the margin probe's
  reproduction gate.

## 5. Expected cost

- 4 re-evals (2 ladders x 2 windows), crops 200, batch 4: the margin probe ran ~2.5 min per cell, so
  expect ~10-12 minutes total on the 4090. One exclusive GPU claim, released on completion.
- Raw: `out_c/sondeB/harvest/leakdump_win{256,384}_seed2.txt`,
  `out_c/sondeB/harvest_ref/leakdump_win{256,384}_ref.txt`
- Report: `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-window-report.md`
- Bus: intent before, done after, three-way SHA on both commits.
