# Sonde B - legal-leak window probe report

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: **COMPLETE**
Result of the pre-registered run of record: `docs/plans/2026-09-22_sonde-B-legal-leak-window-prereg.md`
Thread narrative: `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-thread-report.md`
Baseline it extends: `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-margin-report.md`

---

## 0. The question

The margin probe left two explanations for the one-sided legal leak: **H-short** (the 128-token scoring
window is too short to separate 12288 from 14336, so the tie-break lands arbitrarily) and **H-rule**
(the routing rule itself prefers the smaller prefix on faint evidence). This probe scores the same 200
legal crops at longer windows.

**Verdict in one line: neither hypothesis in its pure form - the leak *attenuates* with window length
but does not vanish, and it stays one-sided.**

## 1. The requested window, the declared substitution

The operator asked for windows 256 and 512. **512 is inadmissible before the fact:** the instrument
asserts `0 < window < block_size` and `block_size` is 512 on both legal cells, so window 512 exits the
process; window 511 is admissible but leaves a 1-token late window, which voids the local-correctness
read by construction.

**Frozen substitution (declared in the pre-registration before any run): windows 256 and 384.** 384 is
the largest window whose late span (`512 - 384 = 128`) equals the baseline scoring length, so the
local-correctness read keeps its baseline power there.

Also declared pre-run: the instrument's printed `routed`/`served` ppl and the served-ppl grid are **not
comparable across windows**, because `rl[:, :, window:]` changes length. Only routes, histograms,
margins and per-crop late losses are compared below.

## 2. Design and provenance

- Instrument unchanged and already pinned: `scripts/eval_router.py` @ `72399e12`, md5
  `70ddc5f31c0e3871c029f4f4f9dee7d2`, `--crop-dump legal:12288,14336`. No new instrument code.
- 2 ladders x 2 windows = 4 runs, crops 200, batch 4, `--route-grid` on, spec order identical to the
  margin probe. Baseline window-128 dumps reused, not re-run.
- Crop identity across windows holds by construction: crops are drawn from the corpus with
  `manual_seed(1234)` before `args.window` is used, so the 200 byte ranges are the same at 128, 256, 384.
- Checkpoints: seed-2 md5 `d94686ad9f90d4750ba8d02b88ffd9ea`, reference md5
  `8d89b2cabe0c0dccd595fc76bd74c822`. Corpus md5 `0135960429085039dbe5385f649e75fe`.
- GPU claimed exclusive `s_bdh-cl_000120_db292b`, run 07:46:24 - 07:56:47 local, released 204, card
  idle afterwards. Driver md5 `0acb65b86c531091342efcbd1c328648`. Four dumps written, 200 rows each.

## 3. Raw result - the leak attenuates, asymmetrically

Leaker count `L(window)` (routed < 14336) and route histogram:

| ladder | w=128 (baseline) | w=256 | w=384 |
|---|---|---|---|
| seed-2 | **9** (1@10240, 8@12288) | **11** (1@10240, 10@12288) | **7** (all @12288) |
| reference | **11** (all @12288) | **8** (all @12288) | **5** (all @12288) |

- **No upward leakage at any window** (no crop routes above 14336 at 128, 256 or 384, either ladder).
- The two ladders move in **different directions** from 128 to 256 (seed-2 up 9 -> 11, reference down
  11 -> 8), then both fall by 384.
- At 384 the leak is roughly **halved or better on both ladders** (seed-2 11 -> 7 from its 256 peak,
  reference 11 -> 5 from baseline) but **still present on both**.

## 4. D1' - persistence: my frozen threshold fires, and I qualify it

Frozen rule: `L(384) <= 2` on both ladders -> H-short; `L(384) >= 5` on both -> H-rule; otherwise partial.

- **L(384) = 7 (seed-2) and 5 (reference)** - both at or above 5, so the rule returns **H-RULE supported**.

**Qualification I owe the record, stated against my own threshold:** the observed pattern is not what a
pure H-rule predicts either. A rule-level asymmetry would leave the leak roughly unchanged by window
length; instead it **falls** (11 -> 7 and 11 -> 5 from the 128 baselines). What the data show is
attenuation without elimination - a leak that is *reduced* by more scoring evidence but not removed by
it. My binary thresholds had no middle for that, so I do not claim rule-level asymmetry; the honest
description is **partial attenuation**. The threshold outcome is reported as frozen; the reading is
reported as the data give it.

Secondary, reported and not promoted: leaker median `|margin|` stays far below the stayers' at every
window (seed-2 0.047 / 0.011 / 0.018 against stayers 0.086 / 0.089 / 0.086; reference 0.018 / 0.009 /
0.026 against 0.096 / 0.087 / 0.084). The near-boundary character of the leakers is stable across
windows even though the leaker *set* is not.

## 5. D2' - the shared core from the margin probe is REFUTED

The margin probe reported crops **114, 148, 161** as leaking on both ladders and called them "a small,
reproducible, genuinely-mis-routed set - the only part of the leak that behaves like a content
property rather than a boundary artifact". At longer windows that claim does not survive:

| crop | seed-2 w128 / w256 / w384 | reference w128 / w256 / w384 |
|---|---|---|
| 114 | 12288 / **14336** / 14336 | 12288 / **14336** / 14336 |
| 148 | 12288 / 12288 / **12288** | 12288 / **14336** / 14336 |
| 161 | 12288 / 12288 / **14336** | 12288 / 12288 / **14336** |

Frozen rule: "persistent core" only if all three leak on both ladders at 384. **Verdict: NOT a
persistent core.** Crops 114 and 161 stop leaking on **both** ladders once the window grows; 148
survives on seed-2 only. So the margin report's content-property reading of that trio **is withdrawn
here**: with more scoring evidence the shared core dissolves, which makes it a property of the short
window, not of the crops.

This is the second time in this thread that a claim of mine had to be withdrawn after a further test,
and both withdrawals are recorded additively rather than edited away.

## 6. D3' - local correctness: the one-sidedness survives the longer window

Per crop, is the late loss lower at the width the router chose? Frozen rule: `>= 50%` at 384 overturns
for that ladder; `< 25%` confirms; between is partial.

| ladder | w=128 | w=256 | w=384 | stayers locally right at 384 |
|---|---|---|---|---|
| seed-2 | 1/9 = 0.111 | 2/11 = 0.182 | 2/7 = **0.286** | 183/193 = 0.948 |
| reference | 1/11 = 0.091 | 0/8 = 0.000 | 1/5 = **0.200** | 189/195 = 0.969 |

**Verdict under the frozen rule:** the reference ladder falls in the confirm band (1 of 5 leakers
locally right = 0.200, below the 0.25 threshold, n=5); seed-2 lands between the bands (2 of 7 = 0.286,
n=7) and is reported as partial. Counts and denominators are on the line, not inferred.

What this means, stated plainly: **even with four times the early evidence, a legal crop that the router
routes downward is still usually served worse for it** - 5 of 7 remaining leakers on seed-2 (71%) and 4
of 5 on the reference ladder (80%) at window 384. A shorter *late* window (128 tokens instead of 384)
makes the 384 numbers the conservative ones. The one-sided error is not a short-window artefact: it attenuates in frequency and
survives in character.

## 7. Resolution against the pre-registered outcomes

- D1': frozen rule returns **H-rule**; the data actually show **partial attenuation**, as qualified in
  section 4. Not promoted to a rule-level asymmetry claim.
- D2': **refuted** - no persistent core; the margin probe's trio claim is withdrawn.
- D3': on the reference ladder 1 of 5 leakers is locally right = 0.200, below the 0.25 confirm
  threshold (n=5); on seed-2 2 of 7 = 0.286, between the bands (n=7), reported as partial. Local
  incorrectness persists at the longer window.
- Secondary: no upward leakage anywhere; leaker margins stay low at every window.

## 8. What this changes in the thread

1. **The fix is neither "widen the window" nor "fix the rule" alone.** Widening the scoring window
   removes roughly half the flips and leaves the rest; so the window length contributes causally, and
   something else contributes the remainder.
2. **The leak is a frequency effect, not a hard defect.** At 384, 7/200 and 5/200 crops mis-route, each
   costing on the order of the ~8% ppl penalty priced by the ablation.
3. **The margin probe's shared-core claim is withdrawn** (section 5). What remains stable across
   windows is not *which* crops leak but *what a leaker looks like*: a low-margin crop that usually is
   served worse at the width chosen.
4. **Untouched:** P1 remains falsified at 189 against band {191..199}; the grown-capacity ablation
   stands as reported (and corrected).

## 9. Provenance of record

- Raw dumps: `out_c/sondeB/harvest/leakdump_win256_seed2.txt`, `leakdump_win384_seed2.txt`,
  `out_c/sondeB/harvest_ref/leakdump_win256_ref.txt`, `leakdump_win384_ref.txt` (12138-12143 B each,
  200 rows each), plus the window-128 baselines from the margin probe.
- Analysis: `out_c/sondeB/window_analyze.py`, applying the frozen D1'/D2'/D3' rules verbatim; every
  number above is printed by it, not carried from memory.
- Pre-reg `494fe52`; instrument `72399e12`; driver `0acb65b8`; run 07:46:24 - 07:56:47 local;
  lease released 204; renewer stopped; guest GPU idle.
- Not covered: windows above 384 are inadmissible-by-late-window-length (511 leaves 1 token), so the
  "does it vanish near 512" question is not answerable with this instrument as written.
