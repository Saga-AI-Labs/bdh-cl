# Sonde-A Add-On Probes (A/B/C) — Pre-registration

Date: 2026-09-18. Author: Quinn. Basis: committed Sonde-A readout
`docs/reports/phase_2/2026-09-18_sondeA-A1K5-readout.md` (commit 8f1ce25)
and the operator review #338. **Nothing here is pushed; this is a plan + a
gated execution order.**

## Ground facts from `scripts/eval_router.py` (verified, not assumed)

- Routed ppl = `exp(rl[choice, crops, window:].mean)` with `choice =
  scores.argmin(dim=0)` (lines 105–107, 110).
- Oracle ppl = `exp(rl[oi, crops, window:].mean)` for the pinned true width
  index `oi` (lines 111–114). **Consequence:** under a perfect diagonal
  (`choice == oi` for every crop), routed ppl and oracle ppl read the SAME
  tensor slice and are therefore **exactly equal**, not approximately. The
  Sonde-A readout measured a perfect diagonal (200/200 × 5), so on this ladder
  the operator's 'correct→correct' and 'oracle-no-router' arms coincide and the
  oracle column adds no new information — the genuinely new arm is wrong-width.
- The route loop (lines 92–103) already fills `rl[ri]` for **every** route
  `ri`. The full [true_domain × forced_width] ppl grid is therefore **already in
  memory** and merely discarded except at the argmin and the one oracle index.
  Probe B re-reads that tensor; it needs no extra forward passes over what a
  normal run already costs.
- Crops are drawn with a re-seeded generator (`manual_seed(1234)`, line 70)
  from the **first `mb*1_000_000` bytes, last 2_000_000 window** of each
  `--domains` path. Reproducible across runs only if `--mb`, `--crops`,
  `--window`, and every `--domains` path are byte-identical between runs.

## Shared protocol (applies to A, B, C)

- **Gate G0 (crop-parity).** All comparisons share one frozen arg-string:
  fixed `--mb`, `--window`, `--crops`, `--routes`, and an identical
  `--domains name:path,...`. A probe that changes any of these invalidates its
  own deltas. **Falsifier F0:** if two runs with the *same* ckpt and args give
  different `routed_ppl`, the harness is non-deterministic — STOP, do not
  report any delta.

**Frozen routing argv** (verbatim from `scripts/quinn/ladder_sondeA.sh` A1-K5,
the run that produced the committed 200/200 readout — this is the single
arg-string every A/B/C cell must reuse):

```
--routes 8192,10240,12288,14336,16384
--domains prose:data/textmix/wikitext-103-raw/wiki.train.raw,
           code:data/textmix2/code.txt,
           math:data/textmix2/latex.txt,
           legal:data/textmix2/legal.txt,
           ga:data/europarl/DGT.en-ga.ga.txt
--window 128  --crops 200        # --mb omitted => default 30; do not pass it
router ckpt = out_a/bdh_textmix_ladA-A1-K5-ga_last.pt
```

`--mb` is load-bearing for crop parity (it truncates each file to `mb*1e6`
bytes before the last-2MB window), and the committed call left it at its
default **30** — passing any other value silently re-derives a different crop
set and voids every delta. Same rule for `--window`/`--crops`/`--routes`.
- **Compute fit:** batch=1, eager mode (Sonde-A precedent; batch=4 OOMed on the
  largest 2.4 GB ckpt). This is the proven profile, not a guess.
**Batch is numerically inert here, so it is parity-neutral:** the route loop
tiles disjoint crops through the forward call and stores each loss to its own
row, so `--batch` only groups the iterator; the `argmin`, the served slice, and
the `--route-grid` reduction all index by crop, never by batch. The committed
200/200 run itself used `--batch 4` on the 2.4 GB `ga_last`, so batch is a
throughput/memory knob, not a correctness one. We still run **batch=1** for
headroom beside the live upload, and that is byte-parity to the batch=4
baseline; the earlier batch=4 OOM belonged to the wider c_arms/RA2b prefix
family (widths to ~47104), not this 16384-topped K5 set.
- **GPU idle is a precondition to verify at smoke time, not a claim:** in this
  venv `nvidia-smi` is off-PATH, so 'free' is currently only process-evidence
  (no training-python on .200; the HF upload job is CPU/IO-bound). Confirm
  idle via the correct binary before A. The still-running phase-2/legacy upload
  hammers `md0` (~300 MB/s); schedule A's disk reads aware of that.
- **ETAs are measured, never estimated** (this repo has retracted estimated
  ETAs before). Report steady-state it/s from a wall-clock sample; the base
  phase has no MLP growth so it is the reliable segment.
- **Language:** plan/report committed in English (repo rule).

## Probe A — Behavioural-retention matrix (no code change)

Definition: for each phase checkpoint `ck_k` (best) in
`{base,code,math,legal,ga}`, run the existing `eval_router.py` over the five
domains it should have seen by phase `k`; read `routed_ppl` (self-routed).
Define `retention_loss(D,k) = routed_ppl@ck_k − routed_ppl@ck_at_intro(D)`.
This is the behavioural counterpart to the already-held P5 bit-exactness.

- **Gate G-A:** the lower-triangle 5×5 ppl grid + the 5 retention curves land;
  each diagonal cell (`k == intro(D)`) must equal the readout's own routed ppl
  within G0 noise.
- **Falsifier F-A:** if a domain's ppl rises vs its intro value by more than
  the G0 noise floor **while P5 said the masked parent block was bit-exact**,
  the two disagree — the behavioural claim is NOT supported by the structural
  one; flag rather than average it away.
- Reuses the fixed-capacity-matrix eval harness where possible so numbers are
  comparable to the published knowledge-destruction result.
- Cost: 5 ckpts × 5 domains forward passes, sequential, batch=1. No new code.

## Probe B — Wrong-width forcing `--route-grid` (single-pass, zero new forwards)

Add `--route-grid`, a flag that emits the full [true_domain × forced_width]
served-ppl grid **inside the existing pass**: the route loop (lines 92–103)
already fills `rl[ri]` for every route of every crop, so grid cell
`(D, ri) = exp(rl[ri, crops, window:].mean)` costs no extra forward and no
second crop-draw — it is a reduction over a resident tensor.

Why single-pass rather than a per-run `--force-routes name:width` mirror of
`--oracle-routes`: that form needs five invocations to fill 25 cells, each
re-running the whole route loop (5× the forwards) and each re-drawing crops,
so cross-run parity would rest entirely on F0 catching a bad crop-draw. The
grid flag makes it moot by construction — all 25 cells share one process, one
crop-draw, one numerics context — and it is five times cheaper on a box whose
disk the still-running upload is occupying.

- **Gate G-B:** diagonal of the grid (forced==home) reproduces `routed_ppl`;
  the joint column reproduces the 23.66 reference.
- **Falsifier F-B:** if `ppl(D @ wrong width)` is *lower* than `ppl(D @ home)`
  by beyond the G0 floor, the 'capacity-addressing' reading is wrong — a crop
  is better served through another domain's slice, which breaks the address
  metaphor. Report as a defect, do not bury it.
- Decodes allocation-vs-routing: high wrong-width ppl ⇒ routing-decision value;
  flat across widths ⇒ the 23.66 gap was mostly capacity-allocation, and the
  '23.66 vs 1.47' should be phrased as *avoiding joint-serving degradation*,
  not as an X× routing win.

## Probe C — `code_best.pt` re-route (cheapest discriminator, no code change)

Re-run `eval_router.py` with `--ckpt …code_best.pt` (not `ga_last`) on the code
domain.

- **Gate G-C:** one routed ppl number.
- **Read:** ≈2.98 ⇒ the readout's 4.38 final-val was **checkpoint drift**;
  stays ≈4.90 ⇒ **intrinsic** to code-as-domain. Discriminates three of the
  four code hypotheses from #338 with a single forward pass. Distinguish
  training-time val (4.38) from routing-time served ppl (4.90); do not conflate.

## Non-goals

- No retraining, no push, no history rewrite. Additive-only.
- Item 'D' (the 23.66 framing) is a wording fix already held as a standing
  caveat — 0 GPU, tracked here only so the #338 list stays whole.

## Execution order once approved

1. Patch `--route-grid` into `scripts/eval_router.py` (guarded, one file).
2. Smoke A/B/C on **one** domain, batch=1, on .200 (verify GPU idle first).
3. Full A 5×5, full B grid, full C — each reported with measured it/s and the
   G/F gate verdicts. Results to a dated English report; push only on ask.