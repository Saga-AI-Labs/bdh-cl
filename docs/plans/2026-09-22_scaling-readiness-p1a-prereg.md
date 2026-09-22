# Scaling-readiness P1a - serving checkpoint, best against last (pre-registration)

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: frozen before the first measurement
Parent plan: `docs/plans/2026-09-22_scaling-readiness-gaps-and-probes-prereg.md` @ `76dd597`, section 3 P1a.
Operator GO: "P0 + P1a + P2: go". Sibling of record: P0 report @ `0f27eee` (CONFIRM at N=1000).
No training. No writes under `out/` or `out_a/`. Raw artefacts under `out_c/scaling_readiness/p1a/` (gitignored).

## 1. Question

The harvest drivers served `_last.pt`; `pipeline/train.py:343-350` writes a `_best.pt` whenever the
running validation loss improves. The parent plan asks whether the serving default for the scaling
evaluations should flip to `_best`. At K=40 a thin block carried by a stale tail would ride along
through every later phase of the ladder, so the answer matters before the ladder is sized.

This probe does not train anything. It serves the eight grown checkpoints twice each - once as
`_best.pt`, once as `_last.pt` - on the cell's own domains, at the trained width, and compares.

## 2. The eight pairs (pinned before the run)

Four cells x two ladders. `N` is the trained width, `ppl_N` the mean of the `routed` ppl over
the cell's own domains for the `_last` checkpoint as printed by the grown-capacity ablation
(`--route-grid`, 200 crops, window 128; those dumps carry `ckpt=.../harvest_ref/...`, so the
figures below are reference-ladder figures). The file size is equal within a cell because the
two tags differ only in weights.

```
cell           N      ppl_N (ref)      size (bytes)
prose__math    12288  1.41            1813044888
prose__code    10240  4.90            1511046808
math__ga       16384  2.40            2417040985
prose__legal   14336  2.20            2115042989
```

The sixteen checkpoints, md5-pinned on the guest (`bdh-4090`, `/media/data/coding/bdh`) before
the first run. The driver compares each file against its pin; a mismatch stops that pair and the
run reports the mismatch instead of serving a file it did not check.

```
seed-2 ladder, out_c/sondeB/harvest/
  bdh_textmix_harv-prose__math_best.pt   8f0446c1470873433dd613077c066754
  bdh_textmix_harv-prose__math_last.pt   e74d3d0fbfb3217bdef091b576298c7a
  bdh_textmix_harv-prose__code_best.pt   4ee893d7a76cf58e4af97b615c8e4398
  bdh_textmix_harv-prose__code_last.pt   674004661fa28b58a5b20c7e9e03ad21
  bdh_textmix_harv-math__ga_best.pt      1e60349727ccdbef98ea78f0ae416fdf
  bdh_textmix_harv-math__ga_last.pt      94d46b279e4197dcef19fe35c36eef87
  bdh_textmix_harv-prose__legal_best.pt  830db8ab3bbc318bb33e606ce0491171
  bdh_textmix_harv-prose__legal_last.pt  d94686ad9f90d4750ba8d02b88ffd9ea
reference ladder, out_c/sondeB/harvest_ref/
  bdh_textmix_harv-prose__math_best.pt   20bbdda2f53599f4704a492eb80d76ba
  bdh_textmix_harv-prose__math_last.pt   13927b41c5d535b654013f3154031611
  bdh_textmix_harv-prose__code_best.pt   6946eda525361f0f1bac0f99d5777334
  bdh_textmix_harv-prose__code_last.pt   b1f4ed6a10fa585187e6184108166612
  bdh_textmix_harv-math__ga_best.pt      f5bd98b30c1a28ea7443f604624dcc5a
  bdh_textmix_harv-math__ga_last.pt      26dc95c9ff2c1cda7ae6980f05eddbad
  bdh_textmix_harv-prose__legal_best.pt  85e1fc69b4306b2bfbf05e0b906dd16a
  bdh_textmix_harv-prose__legal_last.pt  8d89b2cabe0c0dccd595fc76bd74c822
```

## 3. Measurement, one eval per serving

One eval per checkpoint, sixteen evals in all. Each eval is the instrument
`scripts/eval_router.py` deployed as `/tmp/eval_router_dump.py`, md5
`70ddc5f31c0e3871c029f4f4f9dee7d2` (the bytes that produced the P0 dumps), run with the
cell's own domains, `--routes <N>` (one route, so the routed expert is the trained width for
every crop), `--window 128`, `--crops 200`, generator seed 1234, the same domain list and the
same order the harvest eval used.

The number of interest per checkpoint and cell is the mean of the `routed` ppl over the cell's
own domains as printed in the routed block (prose+math, prose+code, math+ga, prose+legal - the
two domains of the cell name; the mean of the two printed values). All crops take the trained
width, so the routed figure is the served ppl at the trained width. The domains are passed as
the full five-domain SPEC of the ablation, so every domain is drawn from the same stream the
committed figures were drawn from; only the rows of the cell's own domains are read. The
instrument costs about one forward pass per crop per domain; no grid over other widths is
computed.

## 4. Frozen reading

For a pair, `delta = ppl(last) - ppl(best)`.

- `delta > 0.02`: the pair is won by `best` (the tail is worse than the best checkpoint).
- `delta < -0.02`: the pair is won by `last`.
- `|delta| <= 0.02`: a tie, counted for `last` - the status quo keeps serving, a tie does not
  help `best`.

Decision, frozen here: if `best` wins at least 6 of the 8 pairs, the serving default for the
scaling evaluations flips to `_best`; otherwise `_last` keeps serving. The threshold 6 of 8 is
chosen so that a single surprising pair (for example a cell whose tail drifted, as the code cell
did in the ablation: final 4.38 against best 2.98) does not by itself decide the default.

Report: the eight deltas, the wins and ties per pair, the four per-cell mean deltas, and the
pairs where the flip would move the served ppl by more than one percent. No p-values, no
significance claims - this is a comparison of two serving choices on the same data, not a test
of a hypothesis.

What it does not settle: whether `best` is better in general, only which of the two files
serves lower on these eight pairs on their own domains at their trained width, with 200 crops
and a 128-token scoring window. It says nothing about cross-domain routing, and the legal
cell's own width is the known weak point (its capacity gain over the pre-grown width is only
2.15x).

## 5. Gates before the first number is read

- G1, the instrument and the pins: the driver prints `EVAL_ROUTER_MD5` and the md5 of every
  checkpoint before its run; a mismatch against the table above stops that pair.
- G2, reproduction of the ablation: the four `_last` runs of the reference ladder must reach the
  `ppl_N` of the table above within 0.01 (1.41, 4.90, 2.40, 2.20) - the same files, the same
  SPEC and the same draw as the committed grid dumps
  (`out_c/sondeB/harvest_ref/grid_*.routdiag.txt`). The four `_last` runs of the seed-2 ladder
  have no committed reference table, because the grid ablation ran on the reference ladder; the
  legal cell is expected at 2.20 for its trained width, the figure the legal-leak thread
  reported for this checkpoint at 200 crops. The other three seed-2 `_last` runs carry no
  external expected value - the pair comparison stands on its own, and the frozen reading
  needs nothing else.
- G3, order: the pairs are run in the order of the table, ladder by ladder, and the log shows
  the eight sections in that order.
- G4, scope: the driver writes only under `out_c/scaling_readiness/p1a/`, reads the checkpoints
  read-only, and the claim on `gpu://rtx4090` is exclusive, renewed while running, released at
  the end.

A gate that fails stops the run at that pair; the numbers beyond it are not read.
