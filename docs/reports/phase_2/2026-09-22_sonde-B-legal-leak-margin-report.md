# Sonde B - legal-leak margin probe report

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: **COMPLETE**
Result of the pre-registered run of record: `docs/plans/2026-09-22_sonde-B-legal-leak-margin-prereg.md`
Prices the capacity half: `docs/reports/phase_2/2026-09-22_sonde-B-grown-capacity-ablation-report.md`
Answers the open thread from HAK `bdh-cl` #403.

---

## 0. The question, and the answer in one line

The legal leak is the only negative, directional, replicated signal in Sonde B. My hypothesis was
that legal was over-grown, so the router's early-window margin between 12288 and 14336 would be
near-zero and the leak would be the tail of an indifference region.

**Verdict: half right, and the wrong half is the interesting one.** The leakers do sit at smaller
margins than the stayers - but the failure is not symmetric noise. A small margin pointing at 14336
is right ~98% of the time; a small margin pointing at 12288 is wrong ~90% of the time. The leak is
a **one-sided error at the router's decision boundary**, not an indifference region.

## 1. Instrument, design, provenance

- Instrument: `scripts/eval_router.py` @ commit `72399e12`, md5 `70ddc5f31c0e3871c029f4f4f9dee7d2`,
  new additive `--crop-dump domain:wA,wB`, md5-gated in-run. Read off the already-filled tensor:
  zero extra forwards.
- Both legal cells re-run **fresh** with the identical spec and order, because the archived seed-2
  routdiag could not be traced to a documented invocation (its driver passes no `--domains`, which
  is `required=True`). Crop-index identity is therefore established by construction.
- Pre-flight recorded: `block_size` 512 on both cells; checkpoint md5s `d94686ad9f90d4750ba8d02b88ffd9ea`
  (seed-2) and `8d89b2cabe0c0dccd595fc76bd74c822` (reference).
- Corpus `data/textmix2/legal.txt` md5 `0135960429085039dbe5385f649e75fe` - byte-stable across both
  harvests, read by both runs.
- GPU claimed exclusive `s_bdh-cl_000117_578231`, run 07:12:55 - 07:18:07 local, lease released 204.
  No training. Driver md5 `6888ec2088cda6813358c7a880aa784f`.

### Reproduction gate: PASSED exactly, both ladders

| ladder | archived confusion (8192/10240/12288/14336/16384) | fresh run |
|---|---|---|
| seed-2 legal | 0 / 1 / 8 / 191 / 0 | 1@10240, 8@12288, 191@14336 |
| reference legal | 0 / 0 / 11 / 189 / 0 | 11@12288, 189@14336 |

Both reproduce digit-for-digit. This also retires the provenance worry from the pre-registration:
those archived seed-2 numbers are now independently reproduced by a documented instrument.

## 2. D1 - margin magnitude: partially supported, ladder-dependent

`margin = score(12288) - score(14336)` on the early window; leakers are negative and stayers positive
by construction, so the quantity read is `|margin|`.

| ladder | leakers |median \|margin\|| stayers median | stayers p10 | verdict |
|---|---|---|---|---|
| seed-2 | 0.0468 | 0.0856 | 0.0318 | **MIXED** |
| reference | 0.0181 | 0.0957 | 0.0320 | **H-tie supported** |

The pre-registered rule fires differently on the two ladders. On the reference ladder the leakers
sit below the stayers' 10th percentile - the near-tie reading. On seed-2 they sit above p10 but far
below the median - between the thresholds, which the rule calls mixed.

**Reading:** the leakers are systematically low-margin on both ladders (medians 0.047 and 0.018
against stayer medians 0.086 and 0.096), so "near the decision boundary" is supported. But the
thresholds disagree, so the strong H-tie form is **not** established, and any claim that the leak is
pure indifference would overstate it.

## 3. D3 - and the calibration that makes it sharp

The pre-registered rule asks, per leaker, whether the chosen width serves that crop better on the
late window. Answer on both ladders: almost never.

| ladder | leakers locally right at chosen width | base rate: stayers locally right |
|---|---|---|
| seed-2 | 1 / 9 = 0.111 | 187 / 191 = **0.979** |
| reference | 1 / 11 = 0.091 | 186 / 189 = **0.984** |

Overall early-window-versus-late-window agreement is 188/200 and 187/200 (0.940 / 0.935).

This is the load-bearing number of the probe. The router's early-window choice is right ~98% of the
time when it lands on 14336 - and wrong ~90% of the time when it flips to 12288. It is not picking
noise-level differences; it is making a **one-sided error**, and it is making it on crops where the
chosen prefix is measurably worse for that crop.

**My hypothesis does not survive in the form I proposed it.** A near-tie region predicts symmetric
mis-selection: some leakers right, some wrong, roughly evenly. The observed 2-for-20 is not that.

## 4. D2 - leaker identity: partial, with a consistent core

| ladder | leaker indices |
|---|---|
| seed-2 (n=9) | 18, 30, 91, 114, 122, 148, 151, 161, 164 |
| reference (n=11) | 20, 38, 41, 59, 107, 114, 131, 148, 161, 169, 171 |

Intersection: **114, 148, 161** (3). Seed-2-only 6, reference-only 8. Frozen rule: intersection of 3
against a smaller set of 9 sits between the two thresholds (>= 4.5 overlapping, <= 2 disjoint) -
reported as **partial**, no promotion.

Two things follow, and they point the same way as D3:

1. **Most leakers are ladder-specific**, so most of the leak is not crop-determined. A routing
   decision that moves between ladders on the same 200 bytes is fragility, not content.
2. **Three crops leak on both ladders, and all three are locally mis-served on both** (114: +0.078 /
   +0.074 late-loss penalty; 148: +0.005 / +0.046; 161: +0.041 / +0.019). That is a small,
   reproducible, genuinely-mis-routed set - the only part of the leak that behaves like a content
   property rather than a boundary artifact.

## 5. Resolution against the pre-registered outcomes

- D1: **mixed** - near-tie supported on the reference ladder, inconclusive on seed-2. Not promoted.
- D2: **partial** - 3 shared indices, 6 and 8 ladder-specific. Not promoted either way.
- D3: **local-error on both ladders**, against a ~98% base rate. The strongest and cleanest verdict.
- Reproduction gate: **passed exactly**, both ladders.

## 6. What this settles, and what it changes

**Settled.** The legal leak is a **one-sided router error at the decision boundary**, not an
indifference tail. It costs the served ppl ~8% (12288 serves legal at 2.39 against 2.20 at 14336),
so it is real but bounded. The router is not confused about which width is better in general - it is
right 98% of the time - it fails specifically when the early-window evidence is faint and points
downward.

**Changed.** The paper sentence I would now write is not "legal sometimes routes downward because
the capacity is redundant". It is: **the router's early-window estimate is reliable when it stays
put and unreliable when it flips, and the flip is downward-only.** That is a statement about the
routing rule, testable independently of capacity.

**Not settled.** Why the flip is one-sided. The obvious candidate - a prior toward the smaller
prefix, or an asymmetry in how the early window scores a prefix it has less evidence for - is
outside what this probe measured: both dumps report the early-window scores and the late-window
losses at the two widths only, at the harvested window of 128 tokens. The probe that would settle
it: score the same crops with the window lengthened (256, 512). If the flip survives a longer
window, the asymmetry is in the rule; if it disappears, the early window is simply too short to
separate these two prefixes, and the fix is a wider scoring window rather than a different router.

This does not touch P1 (falsified at 189, band {191..199}) and does not re-open the ablation.

## 7. Provenance of record

- Raw dumps: `out_c/sondeB/harvest/leakdump_seed2.txt`, `out_c/sondeB/harvest_ref/leakdump_ref.txt`
  (12139 B / 12146 B, 200 rows each).
- Analysis: `out_c/sondeB/leakdump_analyze.py`, applying the frozen rules verbatim; every number above
  is printed by it, not carried from memory.
- Pre-reg `3b43667`; instrument `72399e12`; driver `6888ec20`; probe run 07:12:55 - 07:18:07 local.
- Read: both dump files in full, the analyzer output in full, the archived reference routdiag for the
  gate. GPU released 204; renewer stopped; card idle at 287 MiB / 0%.
- Check not run: no leave-one-out or window-length sweep; the window-length probe above is proposed,
  not executed.
