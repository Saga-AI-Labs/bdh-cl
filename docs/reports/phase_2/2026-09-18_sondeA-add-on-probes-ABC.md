# Sonde-A Add-On Probes C / B / A — Measured Readout

Date: 2026-09-18 (campaign `ALL_DONE 20260918T182527Z`). Author: Quinn.
Pre-registration: `docs/plans/2026-09-18_sondeA-add-on-probes-prereg.md`.
Predecessor (separately committed): `2026-09-18_sondeA-A1K5-readout.md` (commit 8f1ce25).

## 0. Provenance

All figures are transcribed from the seven run logs produced on host
`bdh-4090` under `/media/data/coding/bdh/out_c/logs/`: `fullC.log`, `fullB.log`,
`fullA_{base,code,math,legal,ga}.log`, each closed with `RC=0` and wall-clock
stamps. Those seven logs, the `ALL_DONE` marker and the runner script are
curated byte-for-byte into this repo at `docs/data/sondeA-abc-run/`, with
`MANIFEST.sha256` giving each file's digest so the copies are checkable against
the host originals without a re-fetch; the figures below are transcribed from
those committed copies, not from a host path. Runner: `out_c/run_abc_full.sh`
(its bytes are the committed `docs/data/sondeA-abc-run/run_abc_full.sh`). Script: staged copy
`out_c/eval_router_grid.py` (md5 `8d76a3…`); the committed
`scripts/eval_router.py` was never run and its md5 (`73832e…`, pre-edit) is
unchanged — the `--route-grid` mechanism exists only in the staged copy.

Frozen routing argv, identical across all seven stages (verbatim from
`scripts/quinn/ladder_sondeA.sh` A1-K5, the run that produced the committed
readout):

```
--routes 8192,10240,12288,14336,16384
--domains prose:data/textmix/wikitext-103-raw/wiki.train.raw,
           code:data/textmix2/code.txt,
           math:data/textmix2/latex.txt,
           legal:data/textmix2/legal.txt,
           ga:data/europarl/DGT.en-ga.ga.txt
--window 128  --crops 200          # --mb left at its default 30 (not passed)
--batch 1
```

## 1. Determinism + flag-inertness gate (prerequisite, passed)

Probe C and probe A's `code` stage are the same checkpoint under the same
frozen argv, differing only by the `--route-grid` flag. Their routed rows are
byte-identical:

```
fullC     prose 2.46 code 5.51 math 15.78 legal 4.46 ga 21.28
fullA_code prose 2.46 code 5.51 math 15.78 legal 4.46 ga 21.28   == identical
```

Two facts from one comparison: the evaluator is run-to-run deterministic under
fixed argv (an independent re-run of the p20 determinism check), and
`--route-grid` is numerically inert — an extra reduction over the resident
`rl` tensor that perturbs the routed/oracle path by zero bits.

## 2. Probe C — code anomaly, localised (not resolved as the old binary)

`--ckpt …code_best.pt` serves the code domain at routed ppl **5.51**, where the
same domain under `ga_last.pt` (the readout / probe B) is **4.90**. The
code-best checkpoint is therefore *worse at serving code than the later
checkpoints are*. The pre-registered read was `2.98 (drift) vs 4.90
(intrinsic)`; the measured 5.51 is on neither branch, so the binary was too
crud — reported as measured, not forced: the anomaly is specific to
`code_best.pt`'s own forward, and the number is slightly *higher*, not lower,
than the downstream value. This is the single number from #338 that needs no
further run to state; resolving *why* needs a retrain and is out of scope here.

## 3. Probe B — [domain × forced-width] served-ppl grid (F-B untriggered)

`ga_last.pt`, 200 crops/domain, full run, printed inside one pass from the
already-filled `rl` (zero extra forwards):

```
rows = true domain, cols = forced prefix width
              8192    10240    12288    14336    16384
  prose      2.46     4.33    14.37     5.27    34.52
   code    107.96     4.90    28.87    18.97   103.38
   math     51.35    14.79     1.47     6.90    47.21
  legal      4.72     4.03    11.86     2.28    18.60
     ga     24.98    20.07    57.71    22.65     2.37

  routed (own home width): prose 2.46  code 4.90  math 1.47  legal 2.28  ga 2.37
  joint full-width reference: ppl 23.67 (served positions only)
```

- **F-B untriggered:** in every row the diagonal (home width) is the row
  minimum; no off-diagonal cell is lower than its own home by any amount,
  so the capacity-addressing reading is not broken by this grid.
- **G-B parity (reproduces the committed readout):** diagonal
  `2.46 / 4.90 / 1.47 / 2.28 / 2.37` is the committed routed set exactly, and
  joint `23.67` vs the committed `23.66` is Δ0.01 — the frozen-argv parity
  requirement is met.
- Allocation-vs-routing note: forcing an *already-introduced* domain through a
  wrong width raises ppl sharply for `code`/`math`/`ga` (e.g. ga home 2.37 vs
  57.71 at 12288) but weakly for `prose`/`legal` at one neighbour
  (legal@10240 4.03 < legal@8192 4.72). Where forcing is weak, the two
  domains' expert columns overlap; where it is sharp, the width is the
  address. This is the allocation-vs-routing split #338 asked for.
- The smoke's earlier flat rightward rows were a `crops=4` artifact; the
  200-crop full run resolves them into real structure (this is why a smoke was
  not allowed to stand as green).

## 4. Probe A — behavioural-retention matrix (F-A untriggered)

Routed ppl of each domain under each phase checkpoint. Cells marked `NA*` are
*before that domain was introduced* — the value there is 'serving an unlearned
domain' and is excluded from the retention matrix (see §5):

```
checkpoint \ domain   prose     code      math      legal     ga
base_best            2.46     NA*140.78 NA*60.23  NA*4.84   NA*26.38
code_best            2.46     5.51      NA*15.78  NA*4.46   NA*21.28
math_best            2.46     4.90      1.48      NA*4.15   NA*20.18
legal_best           2.46     4.90      1.47      2.36      NA*20.19
ga_best              2.46     4.90      1.47      2.28      2.38
```

Post-introduction deltas versus each domain's own intro value:

| domain | intro ppl | last ppl | Δ | reading |
|---|---|---|---|---|
| prose | 2.46 (base) | 2.46 (ga) | +0.00 | exact constant |
| code  | 5.51 (code) | 4.90 (ga)   | −0.61 | serves better later; 5.51 is the code_best anomaly (§2) |
| math  | 1.48 (math) | 1.47 (ga)   | −0.01 | flat |
| legal | 2.36 (legal)| 2.28 (ga)   | −0.08 | flat |
| ga    | 2.38 (ga)   | 2.38 (ga)   | —     | intro only |

No domain's ppl rises after its introduction; the largest movement is −0.61 and
it is a *decrease*. **F-A untriggered** → the behavioural retention is supported
by the P5 bit-exactness of the same ladder (readout 8f1ce25), not merely
alongside it. Prose is the cleanest evidence: one value, 2.46, across all five
checkpoints.

## 5. Secondary observation (not a pre-registered gate)

The `NA*` cells are not noise: under a checkpoint that has not yet seen a
domain, the likelihood scan routes that domain's crops into the nearest known
expert (e.g. under `base_best`, code → width 8192 at ppl 140.78; under
`code_best`, ga → 10240 at 21.28). The scan never refuses — it always picks a
known width. This is the same no-reject behaviour probe J characterised; it is
noted here because the A grid happens to display it across the full
introduction chain, not because A was designed to measure it.

## 6. Measured cadence (this run's own stamps; no estimated ETA)

| stage | start→RC | secs |
|---|---|---|
| C     | 180921→181117 | 116 |
| B     | 181117→181417 | 180 |
| A base  | 181417→181544 |  87 |
| A code  | 181544→181728 | 104 |
| A math  | 181728→181944 | 136 |
| A legal | 181944→182227 | 163 |
| A ga    | 182227→182527 | 180 |

Whole seven-stage campaign: 966 s ≈ 16.1 min, serialised on one 4090. (Cadence
here supersedes a chat-line figure from earlier in the session; these are
recomputed from the stamps, which are the authority.)

## 7. Limits — what this does NOT measure

- **Single run, single seed.** No multi-seed noise floor was computed, so the
  ≤0.61 movements are 'no visible rise', not a quantified 'retention ≥ x'. A
  claim needing a floor needs a seed sweep.
- **`code`'s 5.51 anomaly is located, not explained.** §2 states where it is;
  the cause needs a retrain, out of scope.
- **Probe A measures served ppl through the own-width slice, not held-out
  accuracy.** It is a perplexity readout on the same frozen crops the committed
  run used, not a separate benchmark score.
- **The joint full-width reference climbs again at `ga_best` (24.01)** because
  by then all five expert columns are grown — that is the joint-serving case,
  consistent with B's 23.67; it is not a second measurement of anything new.
- **No gate words beyond §1 and the named F-A/F-B/G-B outcomes.** #338's
  remaining asks (a router-stability matrix, a behavioural benchmark beyond ppl)
  are non-goals here.

## 8. Standing of the mechanism

The `--route-grid` addition is validated for numerics (§1) and used as-is for §3.
The flag lives only in the staged copy `out_c/eval_router_grid.py` and in the
still-uncommitted working-tree edit of `scripts/eval_router.py`; the evaluator
committed to this repo was never run and is byte-identical to its pre-edit
state (md5 `73832e…`). What is published here is the validated measurement and
its provenance, not a committed code change to the evaluator.
