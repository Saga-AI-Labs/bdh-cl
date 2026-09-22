# Sonde B - legal-leak margin probe pre-registration

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: DRAFT until frozen pre-run
Frozen design of record, written BEFORE any measurement on the leaking crops.

Companions:
- result under scrutiny: docs/reports/phase_2/2026-09-22_sonde-B-reference-ladder-replication-report.md (leak 9 -> 11)
- capacity pricing: docs/reports/phase_2/2026-09-22_sonde-B-grown-capacity-ablation-report.md (12288 -> 14336 buys 1.09x)
- external thread: HAK bdh-cl #393 / #403 (operator).

---

## 0. The question

The legal cell is the only negative, directional signal in the Sonde B arc, and the only one that
replicated: 9/200 crops on the seed-2 ladder, 11/200 on the reference ladder, same cell, same
direction (downward), and the count widened rather than shrank. Every other leg holds routing and
varies capacity, or the reverse. This is the only place where addressing and capacity are known to
disagree.

Hypothesis under test (H-tie): legal was grown beyond its useful capacity. The ablation priced the
final increment at 1.09x (2.39 at 12288 vs 2.20 at 14336). If the capacity is near-redundant, the
router's early-window scores for 12288 and 14336 may be separated by almost nothing, and the leak
is the visible tail of a near-tie rather than a mis-selection.

H-structural (contrast): the leakers carry a decisive early-window margin for 12288 - the router
genuinely prefers the smaller prefix for those crops.

## 1. Instrument (additive; pinned by commit and hash)

- `scripts/eval_router.py` @ commit `72399e12`, md5 `70ddc5f31c0e3871c029f4f4f9dee7d2`.
- New flag `--crop-dump domain:wA,wB`: for the named true domain it prints, per crop index, the
  early-window score at wA and wB, their difference, the late-window loss at wA and wB, and the
  route argmin chose. Read off the already-filled `rl` tensor: **zero extra forwards**.
- Semantics the design depends on: `choice = scores.argmin(dim=0)`, so the chosen route has the
  LOWEST early-window score. With `margin = score(12288) - score(14336)`, leakers (routed 12288)
  have `margin < 0` and stayers (routed 14336) have `margin > 0` **by construction**. The
  discriminator is therefore the MAGNITUDE `|margin|`, not its sign - see D1.
- Reproducibility gate: the reference-ladder run must reproduce the archived
  `harvest_ref/eval_prose__legal.routdiag.txt` grid and confusion. Any divergence voids the probe.

## 2. Frozen design

- Cells, both **re-run fresh in this probe** (see the provenance note below for why):
  - seed-2: `out_c/sondeB/harvest/bdh_textmix_harv-prose__legal_last.pt` (2115042989 B)
  - reference: `out_c/sondeB/harvest_ref/bdh_textmix_harv-prose__legal_last.pt` (2115042989 B)
- Routes 8192,10240,12288,14336,16384; window 128; crops 200; batch 4; `--route-grid` on.
- Dump spec: `--crop-dump legal:12288,14336` (the two widths the leak lands between).
- Corpus: `data/textmix2/legal.txt`, 40347823 B, md5 `0135960429085039dbe5385f649e75fe`,
  mtime 2026-09-14 17:58:15 +0200 - byte-stable, read by both harvests.
- Domains spec, identical and in this order for BOTH runs (order matters for crop identity):
  `prose:data/textmix/wikitext-103-raw/wiki.train.raw,code:data/textmix2/code.txt,`
  `math:data/textmix2/latex.txt,legal:data/textmix2/legal.txt,ga:data/europarl/DGT.en-ga.ga.txt`
- No training. Two re-evals, one per ladder.

### Provenance note - why both cells are re-run instead of reusing the archives

The archived seed-2 routdiags cannot be trusted for index comparison. The seed-2 driver
`out_c/sondeB/harvest/sondeB_harvest.sh` calls `eval_router.py` with **no `--domains`**, while
`--domains` is `required=True`; the reference driver's own header records the consequence ("the
seed-2 evals were empty stubs without it"). So the archived seed-2 `eval_prose__legal.routdiag.txt`
was produced by some later, undocumented invocation whose domain order and corpus list I cannot
verify from the artefact. Reusing it for a per-crop comparison would be an assumption dressed as a
datum.

Re-running both cells with the same pinned instrument and the same spec makes crop identity
identical **by construction**, which is what D2 needs. The archived reference file then serves as
the reproduction gate (a stronger use), and the archived seed-2 leak count (9) is a **soft
consistency check only** - explicitly non-controlling.

### Why the crop indices are comparable across the two fresh runs

`eval_router.py` draws crops with `torch.Generator().manual_seed(1234)`, consumed sequentially in
the domain loop. With the same corpus files, the same domain order, the same `crops=200`, the same
`mb=30` read window, and the same `block_size` (which sets `bs` and thus `hi = len(arr) - bs - 1`),
the generator yields the **same index sequence per domain in both runs**.

Every element of that argument except one is fixed by the command line above. The exception is
`block_size`, which is read from each checkpoint's cfg. **Pre-flight check, required:** read
`cfg["block_size"]` from both checkpoints and record it; the twins are both expected to be 512. If
they differ, D2 is void and only D1 and D3 are reported.

#### Pre-flight result (2026-09-22T05:10Z, read directly from the checkpoints on the guest)

| cell | block_size | md5 (full file) |
|---|---|---|
| seed-2 legal | 512 | `d94686ad9f90d4750ba8d02b88ffd9ea` |
| reference legal | 512 | `8d89b2cabe0c0dccd595fc76bd74c822` |

Both configs expose the same key set (`model, dataset, n_layer, n_embd, n_head, dropout,`
`mlp_internal_dim_multiplier, vocab_size, block_size, ...`), so `hi` in the crop sampler is
identical between the two runs and the index sequence matches. **D2 is live.**

The two md5s are recorded here because the earlier replication report listed only file sizes for
these artefacts; these are full-file reads (2.1 GB each), and they distinguish the two ladders'
grown legal cells by content, not by path.

## 3. Three discriminators (falsifiable, declared before the run)

D1 and D2 are the two the operator approved; D3 is added here and declared as an addition, because
it costs nothing on the same pass and settles the one reading the other two cannot.

### D1 - Magnitude regime of the leaking crops

For each of the 200 legal crops: `margin = score(12288) - score(14336)` on the early window, where
leakers are negative and stayers positive by construction. Report `|margin|` for leakers (routed
12288) and for stayers (routed 14336), per ladder.

- **H-tie supported** if the leakers' margins are noise-level: their median `|margin|` sits below
  the stayers' 10th percentile.
- **H-structural supported** if the leakers' median `|margin|` exceeds the stayers' median - the
  router separated those crops decisively and still went to the smaller prefix.
- Between those two: report both distributions and call it **mixed**. No promotion either way.
- Report the full per-crop table, not only the summary, so the rule can be re-applied by a reader.

### D2 - Leaker identity across ladders

Compare the set of leaking crop indices (routed 12288) between the seed-2 and reference runs on the
same 200 crops (index identity established per section 2).

- Heavy overlap -> the cause is those specific byte ranges, a **data property**.
- Disjoint -> the route decision is not crop-determined, a **router property** (fragility).
- Frozen rule: report the intersection and both set sizes. Intersection >= half of the smaller set
  is called overlapping; intersection <= 2 is called disjoint; otherwise partial, reported as such.

### D3 - Was the router locally right? (the addition)

For each leaking crop, compare the late-window loss at 12288 against 14336 on that same crop.

- Majority of leakers served **better or equal at 12288** -> the router was locally correct on
  exactly those crops, and the aggregate leak is not mis-selection; it is the label of an aggregate
  whose per-crop optimum differs from the domain's trained width.
- Majority served worse at 12288 -> a genuine local error.
- Frozen rule: majority lateA < lateB is called locally-right; majority lateA > lateB is called
  local-error; exact tie is reported as tie. Counts out of the leaker set, with the denominator.

## 4. Sample size, and what this probe cannot do

- n = 9 and n = 11 leaking crops. This is a probe, not a trial: it can separate *near-tie* from
  *decisive preference* and compare index sets, but it cannot establish a rate and no p-value is
  claimed. Every number is a count out of 200 with its denominator reported.
- It does not test whether different growth would remove the leak. It characterizes the existing
  leak; a causal fix is its own experiment.
- It does not touch P1 (falsified at 189, band {191..199}) and does not re-open the ablation or
  replication conclusions. In particular the reference run's 11 leakers must reproduce; if they do
  not, the probe is void and the discrepancy is the finding.

## 5. Expected cost

- Two re-evals, crops 200, window 128, batch 4: the ablation ran ~2-3 min/cell, so expect under 10
  minutes total on the 4090. One exclusive GPU claim, released on completion.
- Raw: `out_c/sondeB/harvest/leakdump_seed2.txt`, `out_c/sondeB/harvest_ref/leakdump_ref.txt`
- Report: `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-margin-report.md`
- Bus: intent before, done after, three-way SHA on both commits.
