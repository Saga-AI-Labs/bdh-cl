# Sonde B - legal-leak thread report (narrative of record)

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: **COMPLETE** through leg 5 (window probe run; one leg-4 claim withdrawn)
Purpose: preserve the whole legal-leak thread in one place - what was asked, what was measured,
what was corrected, what is open - with the artefacts and commits that carry each step.

This is a navigational and narrative document. The measurements live in the per-step reports;
every number below is copied from those, and the pointer index in section 5 names them.

---

## 0. The story in one paragraph

The legal expert is the only cell in the Sonde B program that produced a **negative, directional,
replicated** signal: on two independent ladders, a minority of legal crops route **downward** to a
smaller prefix than the one the cell was grown to (9/200 on seed-2, 11/200 on the reference ladder,
same cell, same direction, and the count widened rather than shrank). Everything else in the program
replicates cleanly. The thread then did three things: it **priced** the leak (the grown capacity
above 12288 buys only ~8% of serving ppl, so the leak is cheap), it **characterized** the leak's
mechanics (leakers sit at smaller early-window margins, but the error is one-sided: the router is
right ~98% of the time when it stays put and wrong ~90% of the time when it flips down), and it
**isolated** what is still unexplained (why the flip is one-sided). The outcome is a sharper claim
about the routing rule, not a defect in the grown capacity.

---

## 1. Leg 1 - the leak appears (seed-2 ladder, 2026-09-21)

First observation, in the seed-2 harvest. On the routed own-width plane, legal's route distribution
is not clean: most crops claim the trained width, a minority claim smaller ones.

- routed plane: 1 crop at 10240, 8 at 12288, 191 at 14336 - **9 leakers, all downward**
- served legal ppl on the routed plane: 2.21
- no upward leakage; the wider column exists and is not used

This was the only directional anomaly in an otherwise clean harvest, which is why it was carried
forward rather than noted and dropped.

## 2. Leg 2 - the leak replicates, and a numeric prediction fails (2026-09-22)

The reference ladder (seed 1337, independent of seed-2) re-ran the identical harvest design.

- routed plane: **11 at 12288, 189 at 14336** - the leak recurs, same cell, same direction
- the leaked count **widened** (9 -> 11) instead of shrinking
- served legal ppl on the routed plane: 2.21, i.e. unchanged to two decimals despite the wider leak
- pre-registered prediction **P1 failed**: legal self was 189 against the declared band {191..199}.
  The structure and direction replicated; the numeric band was too tight. P1 is reported as
  falsified and was **not** softened afterwards.

So the thread acquired a second, independent witness of the same anomaly - and one clean failure of
my own prediction to report alongside it.

## 3. Leg 3 - the leak gets priced (grown-capacity ablation, 2026-09-22)

Forced-width re-evaluation of the four grown cells answered a different question (is the grown
capacity load-bearing?) and, as a side effect, priced the legal leak.

Load-bearing ratios, trained domain, pre-growth width vs trained width:

| cell | pre-growth | trained | ratio |
|---|---|---|---|
| prose__math | 51.35 @ 8192 | 1.41 @ 12288 | 36.4x |
| prose__code | 107.95 @ 8192 | 4.90 @ 10240 | 22.0x |
| math__ga | 57.71 @ 12288 | 2.40 @ 16384 | 24.0x |
| prose__legal | 4.72 @ 8192 | 2.20 @ 14336 | 2.15x |

Legal is the outlier: it passes the pre-registered band only by the letter, and its **final increment
- the columns actually grown beyond 12288 - buys 1.09x** (2.39 at 12288 vs 2.20 at 14336). Legal's
serving has effectively saturated by 12288.

Consequence for the leak: crops that address 12288 instead of 14336 lose about **8%** of serving ppl.
The leak is real but cheap, and the cheapness has a measured cause (redundant top increment), not an
assumed one.

Two corrections were made to this report after its first commit, both additive:

- a **width mislabel** in the secondary section (legal's own width was printed as 10240, which is
  code's width; legal is grown 8192 -> 14336), and the universal-optimum sentence derived from it;
- the `prose__legal` grid's `ga` row, which is **flat-tied at 24.98 across 8192 and 10240**, now
  reported as an explicit tie rather than as an argmin.

## 4. Leg 4 - the leak gets characterized (margin probe, 2026-09-22)

Pre-registered probe with three frozen discriminators, run fresh on **both** ladders with a pinned
instrument (crop-index identity by construction rather than by assumption).

**Reproduction gate: passed exactly.** Fresh seed-2 gave 1@10240 + 8@12288 + 191@14336; fresh
reference gave 11@12288 + 189@14336 - both identical to the archived numbers. This also retired a
provenance doubt: the archived seed-2 routdiag could not be traced to a documented invocation (its
driver passes no `--domains`, which is required), so the archived figures are now independently
reproduced by a documented instrument instead of being trusted.

| discriminator | seed-2 | reference | verdict |
|---|---|---|---|
| D1 margin magnitude (median \|margin\| leakers vs stayers) | 0.0468 vs 0.0856 (p10 0.0318) | 0.0181 vs 0.0957 (p10 0.0320) | mixed / H-tie |
| D2 leaker identity across ladders | 9 leakers | 11 leakers | partial (shared 114, 148, 161) |
| D3 locally right at the chosen width | 1/9 | 1/11 | local-error, both |

D3 with its calibration is the load-bearing result:

- leakers locally right: **1/9** and **1/11**
- stayers locally right: **187/191 (0.979)** and **186/189 (0.984)**
- overall early-vs-late agreement: 188/200 and 187/200

The router is right about which width serves a crop ~98% of the time. When the early evidence goes
faint and it flips downward, it is wrong ~90% of the time. **That is a one-sided error at the
decision boundary, not an indifference region.**

My working hypothesis - that legal was over-grown and the leak was a benign near-tie tail - is
**half right**: the low-margin part is supported, the benign-indifference implication is refuted.

D2 keeps the claim honest: only 3 of 20 leakers are shared between ladders (114, 148, 161), so most
of the leak is ladder-specific fragility rather than crop content. That trio was read here as the one
part of the leak behaving like a data property. **Leg 5 withdrew the stronger half of that reading:**
at scoring window 384, crops 114 and 161 stop leaking on both ladders and only 148 survives, on seed-2
alone, so the shared trio was a property of the 128-token window rather than of the crops.

---

## 5. Pointer index (the artefacts that carry the thread)

| leg | artefact | commit |
|---|---|---|
| 1 | docs/reports/phase_2/2026-09-21_sonde-B-harvest-results-report.md | seed-2 harvest, 2026-09-21 |
| 2 | docs/reports/phase_2/2026-09-22_sonde-B-reference-ladder-replication-report.md | `178a4a33`, reframed in `ed9636d` |
| 2 | docs/plans/2026-09-21_sonde-B-reference-ladder-replication-prereg.md | pre-registration of leg 2 |
| 3 | docs/plans/2026-09-22_sonde-B-grown-capacity-ablation-prereg.md | `a33108f` |
| 3 | docs/reports/phase_2/2026-09-22_sonde-B-grown-capacity-ablation-report.md | `becf766`, corrected in `d96038c` + `19c7919` |
| 3 | scripts/eval_router.py `--route-grid` | `06921e7` |
| 4 | docs/plans/2026-09-22_sonde-B-legal-leak-margin-prereg.md | `3b43667` |
| 4 | docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-margin-report.md | `5f20c7e` |
| 4 | scripts/eval_router.py `--crop-dump` | `72399e12` |
| 5 | docs/plans/2026-09-22_sonde-B-legal-leak-window-prereg.md | `494fe52` |
| 5 | docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-window-report.md | `9cd5df68`, verdict lines corrected in `178978a8` |
| 5 | scripts/eval_router.py `--route-grid` + `--crop-dump`, unchanged | `72399e12` reused |

Raw per-run artefacts (gitignored, quoted in the reports): `out_c/sondeB/harvest/`,
`out_c/sondeB/harvest_ref/` - four grown cells, five routdiag tables, two leak dumps, two grid tables,
and six window-probe dumps (two ladders x windows 128/256/384).

---

## 6. What the thread establishes

1. **The anomaly is real and replicated**: a minority of legal crops route downward on two
   independent ladders, in the same cell, in the same direction.
2. **It is cheap**: about 8% of legal's served ppl, because the capacity above 12288 is redundant
   (final increment 1.09x).
3. **It is a boundary error, not indifference**: the router is ~98% right when it stays and ~90%
   wrong when it flips down; leakers sit at smaller margins but are served worse at the width chosen.
4. **It is mostly ladder-specific**: only 3 of 20 leakers coincide across ladders.
5. **It is not a capacity defect**: the same ablation shows the grown capacity is domain-specific
   and load-bearing in all four cells, legal included.
6. **It attenuates with a longer scoring window** (leg 5): about half the flips disappear at window
   384 on both ladders, no upward leakage appears at any window, and the remaining leakers are still
   usually served worse at the width the router chose.

Stated as one sentence: **the router's early-window estimate is reliable when it stays put and
unreliable when it flips, and the flip is downward-only.**

---

## 7. What is open, and the next probe

**Open:** why the flip is one-sided. Two candidates were named in leg 4. Leg 5 scored the same 200
legal crops on both ladders at windows 256 and 384 to separate them:

1. the routing rule is asymmetric (a bias toward the smaller prefix), or
2. the 128-token scoring window is too short to separate 12288 from 14336, so the tie-break lands
   arbitrarily.

**Leg 5 ran it (window 512 was inadmissible, substituted before the run):** the instrument asserts
`0 < window < block_size` and the checkpoints' `block_size` is 512, so window 512 exits the process;
511 would leave a 1-token late window and void the local-correctness read. The frozen substitution
was windows 256 and 384, the latter being the largest window whose late span (128 tokens) equals the
baseline scoring length.

What it found:

- Leaker counts **seed-2 9 / 11 / 7** and **reference 11 / 8 / 5** at windows 128 / 256 / 384.
- **No upward leakage** at any window, either ladder.
- The leak **attenuates but does not vanish**: roughly halved at 384 on both ladders, still present.
- Local correctness survives: at 384, **5 of 7** remaining seed-2 leakers (71 percent) and **4 of 5**
  reference leakers (80 percent) are still served worse at the width the router chose, while stayers
  remain about 95-97 percent locally right.
- The 114/148/161 shared-core reading from leg 4 is **withdrawn** (section 4).

So window length is part of the cause - about half the flips go away when the scoring window grows -
but not the whole of it, and neither leg-4 candidate is eliminated on its own.

**Not touched anywhere in this thread:** pre-reg P1 remains falsified at 189 against band {191..199}.
