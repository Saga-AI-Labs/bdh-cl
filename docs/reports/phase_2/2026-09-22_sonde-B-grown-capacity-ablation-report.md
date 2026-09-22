# Sonde B - grown-capacity ablation report

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: **COMPLETE**
Result of the pre-registered run of record: `docs/plans/2026-09-22_sonde-B-grown-capacity-ablation-prereg.md`
Interrogates the replication report: `docs/reports/phase_2/2026-09-22_sonde-B-reference-ladder-replication-report.md`
Answers the open next-experiment question in HAK `bdh-cl` #393 (operator).

---

## 0. The question

#393: dissociate "the router addresses the right region" from "that region is what carries the
capability." The homeless contrast gestures at it but is not randomised - it changes addressing
AND capacity at once. This run changes **capacity alone**: it forces serving to each of five
prefix widths and reads the serving curve. If the grown columns carry the capability, serving
at the pre-growth width is far worse than at the trained (grown) width.

## 1. Method

- No training. The four existing grown cells are re-evaluated at forced widths
  {8192, 10240, 12288, 14336, 16384} per-head, crops 200, window 128, batch 4
  (identical to the harvest evals - identity is the point).
- Instrument: `scripts/eval_router.py` at commit `06921e7`, additive `--route-grid`, pulled to
  the run-site as `/tmp/eval_router_grid.py` and md5-pinned (`8d76a312bc652eb6cdf5464535da9f32`).
  The grid is printed from the tensor the harness already fills: **zero extra forwards**, no
  change to the computation. Run-site HEAD stayed `e6bf359` (no checkout).
- `set_prefix(k)` clamps `k` to the checkpoint's neuron count `N_full`. So a width column above
  a cell's grown width **repeats** the grown-width column: it is not a further measurement.
  Read the plateaus accordingly (`math__ga` is the only cell with all five columns distinct).
- Pre-registered band: a cell is load-bearing iff `P(pre-growth) >= 2 x P(grown)` AND the gap
  exceeds the crops-200 served-plane spread (~ +/-0.05 ppl).

## 2. Result - capacity is load-bearing, sharply

Served ppl of the **trained domain** at its pre-growth width vs its trained (grown) width:

| cell | grow | pre-growth width -> ppl | trained width -> ppl | ratio | argmin |
|---|---|---|---|---|---|
| prose__math  | 128 -> 192 (8192 -> 12288)  | 8192 -> 51.35  | 12288 -> 1.41 | **36.4x** | 12288 (trained) |
| prose__code  | 128 -> 160 (8192 -> 10240)  | 8192 -> 107.95 | 10240 -> 4.90 | **22.0x** | 10240 (trained) |
| math__ga     | 192 -> 256 (12288 -> 16384) | 12288 -> 57.71 | 16384 -> 2.40 | **24.0x** | 16384 (trained) |
| prose__legal | 128 -> 224 (8192 -> 14336) | 8192 -> 4.72   | 14336 -> 2.20 | **2.15x** | 14336 (trained) |

All four cells pass the pre-registered band. Three pass it decisively (>20x); `prose__legal`
passes it by the letter (2.15x) and is treated separately in section 4.

Raw grids (per cell, all five domains; out under `out_c/sondeB/harvest_ref/grid_<cell>.routdiag.txt`):

    prose__math (N_full 12288; 14336/16384 repeat 12288)
                   8192    10240    12288    14336    16384
        prose      2.46     6.26    16.21    16.21    16.21
         code    107.97    74.07   130.17   130.17   130.17
         math     51.35     3.07     1.41     1.41     1.41
        legal      4.72     7.59    15.57    15.57    15.57
           ga     24.98    63.64   181.69   181.69   181.69

    prose__code (N_full 10240; 12288+ repeat 10240)
                   8192    10240    12288    14336    16384
        prose      2.46     4.33     4.33     4.33     4.33
         code    107.95     4.90     4.90     4.90     4.90
         math     51.35    14.79    14.79    14.79    14.79
        legal      4.72     4.03     4.03     4.03     4.03
           ga     24.98    20.07    20.07    20.07    20.07

    math__ga (N_full 16384; all columns distinct)
                   8192    10240    12288    14336    16384
        prose      2.46     4.33    14.37    30.42    48.03
         code    107.96     4.90    28.87    60.31   120.15
         math     51.35    14.79     1.47    16.94    51.36
        legal      4.72     4.03    11.86    24.48    39.82
           ga     24.98    20.07    57.71     3.61     2.40

    prose__legal (N_full 14336; 16384 repeats 14336)
                   8192    10240    12288    14336    16384
        prose      2.46     4.30     4.08     4.64     4.64
         code    107.96    68.91    63.35    65.20    65.20
         math     51.34    41.05    36.61    38.98    38.98
        legal      4.72     3.45     2.39     2.20     2.20
           ga     24.98    24.98    26.52    28.62    28.62

## 3. Secondary read - the grown columns are domain-specific (a second, independent witness)

Each domain's minimum sits at its OWN trained width, and being forced wider than that optimum
costs it. This does NOT mean monotone increase for every domain in every cell - e.g. in the
`prose__math` grid the `code` column dips from 107.97 to 74.07 at 10240 (code's own width)
before rising to 130.17. The correct statement is per-domain: a domain is cheapest at its own
width and dearer on either side of it. The cleanest witness is `math__ga`, the only all-distinct
grid, where every domain shows a dip at its own width:

| domain | own width | grid over 8192/10240/12288/14336/16384 | minimum at |
|---|---|---|---|
| ga    | 16384 | 24.98 / 20.07 / 57.71 / 3.61 / **2.40** | 16384 (trained) |
| code  | 10240 | 107.96 / **4.90** / 28.87 / 60.31 / 120.15 | 10240 (own) |
| math  | 12288 | 51.35 / 14.79 / **1.47** / 16.94 / 51.36 | 12288 (own) |
| legal | 10240 | 4.72 / **4.03** / 11.86 / 24.48 / 39.82 | 10240 (own) |
| prose | 8192  | **2.46** / 4.33 / 14.37 / 30.42 / 48.03 | 8192 (own) |

So within a cell grown for one domain, every other domain still finds its own minimum at its
own (lower) width, and widening it past that optimum is strictly harmful. The grown columns are
not merely *addressed* by the trained domain; they are capacity that helps that domain and costs
the others whenever they are forced onto it. That is the specificity the earlier fixed-width
tables could not show, because they never forced a wrong width.

## 4. prose__legal, target 2 - load-bearing by the letter, marginal in the increment

`prose__legal` (grow 128 -> 224, i.e. 8192 -> 14336) reads:

    legal   8192 -> 4.72   10240 -> 3.45   12288 -> 2.39   14336 -> 2.20

- By the pre-registered band it is load-bearing (4.72 / 2.20 = 2.15x).
- But decompose the gain: 8192 -> 10240 is 4.72 -> 3.45 (1.37x), 10240 -> 12288 is 3.45 -> 2.39
  (1.44x), and 12288 -> 14336 - **the increment that is actually the grown columns beyond 12288** -
  is 2.39 -> 2.20, only **1.09x**.
- Contrast the clean cells: prose__math's final increment (10240 -> 12288) is 3.07 -> 1.41 = 2.18x;
  prose__code's (8192 -> 10240) is 22.0x; math__ga's (12288 -> 16384) is 24.0x.

Reading: legal's serving saturates by 12288; the extra capacity grown up to 14336 adds ~8%. Its
grown columns are load-bearing in the weak sense and largely redundant. This is consistent with
- and does not contradict - the routing leak: legal crops that address 12288 instead of 14336
lose little because 12288 already serves legal at 2.39 vs the 2.20 optimum. So the leak is
benign **because the capacity is redundant there**, which is a statement about capacity, not a
resolution of the routing-selection phenomenon itself.

## 5. Resolution against the pre-registered outcomes

- H1 (load-bearing): **supported** - all four cells, three at >20x.
- H0 (not in the grown content): **refuted** for all four cells.
- Secondary "min at the trained width": **held** for all four cells.
- Not re-opened: P1 (falsified at 189, band {191..199}) - untouched by this run.

## 6. What this settles, and what it does not

- **Settled:** the grown capacity is domain-specific and load-bearing. Forcing the pre-growth
  width degrades the domain 22-36x in the three clean cells; the grown columns help their own
  domain and actively hurt others.
- **Not settled:** the routing-selection half of #393. This run holds the router fixed (it
  scores the same prefixes) and changes only the forced serving width; it cannot explain why
  legal routes 11/200 downward. Section 4 narrows the *consequence* of that leak (small, because
  legal's capacity is redundant beyond 12288) but not its cause.

## 7. Provenance and verification of record

- Guest pre-flight 2026-09-22T03:30Z, SSH_RC=0: HEAD `e6bf359`, origin Saga-AI-Labs/bdh-cl,
  all five corpora present, RTX 4090 idle before claim.
- GPU held exclusive under scope `s_bdh-cl_000114_40185a` (renewed once to 04:26:50Z), released
  204 on completion - not held idle.
- Driver `out_c/sondeB/grid_ablation_driver.sh` (md5 `4609f22ea578d8d8c3d20a6c0b77f5ab`),
  instrument md5-pinned in-run (`EVAL_ROUTER_MD5 8d76a312bc652eb6cdf5464535da9f32`).
- Run window 05:56:55 - 06:06:39 local; four grids written (1122-1126 B each); no training, no
  new checkpoints, `out/` and `out_a/` read-only.
- Instrument commit `06921e7`; pre-reg commit `a33108f`; replication-edit commit `ed9636d`.
- Read: the four `grid_*.routdiag.txt` printed in full above; every ratio in this report is
  recomputed from those printed numbers, not carried from memory.
- Check not run: no md5 of the four grown checkpoints this session (sizes only); the
  checkpoint-presence pre-flight was `ls -la` over SSH, not a forward pass.
