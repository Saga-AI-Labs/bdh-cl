# Scaling-readiness P0 - eval scale-up and dedup (pre-registration)

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: **FROZEN before any new measurement**
Parent: `docs/plans/2026-09-22_scaling-readiness-gaps-and-probes-prereg.md` @ `76dd597`, section 3 P0.
Erratum this pre-registration implements: `docs/plans/2026-09-22_scaling-readiness-erratum.md` @ `ac6d046`
(E1 overlap fix, E2 effective-n).
Operator GO: "P0 + P1a + P2: go".

Design-before-measurement is the house rule: every reading below is fixed BEFORE the run, and
nothing is promoted here that is not backed by the controls named in sections 3 and 6.
No training. No writes under `out/` or `out_a/`.
Raw artefacts under `out_c/scaling_readiness/` (gitignored per .gitignore line 20), md5-pinned
in the report.

---

## 1. Question

The 8% legal-leak price and the 9/200 vs 11/200 leak rates rest on n=200 crops. Do they hold
when the same two legal cells are re-evaluated at N=1000 crops, and are the crops independent
enough for a crop-level interval to mean anything?

## 2. Instrument and command (verbatim, so the archived baseline is reproducible)

- `scripts/eval_router.py`, run on the guest as `/tmp/eval_router_dump.py`, md5
  `70ddc5f31c0e3871c029f4f4f9dee7d2` (the instrument that produced the archived window-128
  dumps; md5-gated in-run, a mismatch is fatal).
- Command per ladder, identical to `out_c/sondeB/leakdump_driver.sh:40-42`:
  `$PY $EV <ckpt> --routes 8192,10240,12288,14336,16384 --domains "$SPEC" \
   --crops <N> --window 128 --batch 4 --route-grid --crop-dump legal:12288,14336`
  with `SPEC = prose,code,math,legal,ga` in that order (legal is the FOURTH draw; the generator
  `torch.Generator().manual_seed(1234)` is created once and consumed sequentially across domains).
- Checkpoints (md5 checked on the guest this session by one read-only ssh `md5sum`, the three
  values below): seed-2
  `out_c/sondeB/harvest/bdh_textmix_harv-prose__legal_last.pt` = `d94686ad9f90d4750ba8d02b88ffd9ea`;
  reference `out_c/sondeB/harvest_ref/bdh_textmix_harv-prose__legal_last.pt` =
  `8d89b2cabe0c0dccd595fc76bd74c822`; legal corpus `data/textmix2/legal.txt` =
  `0135960429085039dbe5385f649e75fe`.

## 3. Gate G0 - reproduction (the E1 fix), the single most important control

Because the crop draw is a single shared generator consumed in domain order, raising `--crops`
from 200 to 1000 moves the fourth draw: the 1000-run's first 200 legal crops are NOT the archived
200 and must not be called "identical by construction". Therefore:

- **G0-a (200 reproduction pass):** run the EXACT command with `--crops 200` on both ladders.
  The legal `CROP_DUMP` block of each output must equal the archived baseline BYTE-FOR-BYTE.
  Archived targets (md5sum of the archived files, verified this session): seed-2
  `168504a92d0c5b44243dfb93d64d5b3b`, reference `51dd88cc0d9358ca061e9326e51e2465`. The gate is
  on the legal `CROP_DUMP` block (header + 200 rows), not the whole file, because the in-run
  instrument also carries `--route-grid`; the grid block's presence is recorded, not compared.
  A mismatch is a **STOP**: the 1000-run does not proceed against an instrument that cannot
  reproduce its own archived baseline, and no 1000-crop figure is reported.
- **G0-b (1000 run):** only after G0-a passes on both ladders, run `--crops 1000` on both ladders.

## 4. Readings (frozen)

- R1 leak set: a crop is a leaker iff its chosen route is NOT the trained width (14336), using
  the window-analyser convention `chosen < 14336` is the leaker test already established for this
  cell. Report leaker count and rate per ladder, and the Wilson 95% interval **on the effective
  count** (E2: the reference ladder contains crop pairs sharing up to 92% of bytes, so the nominal
  n is not the independent n). The interval is not widened by hand; the dedup audit R3 sets the
  effective n.
- R2 served ppl of legal at 14336 vs at 12288, per ladder, at N=1000; leak price = the ratio,
  with the effective-n caveat stated beside it.
- R3 dedup audit: pairwise shared-byte count over the 1000 legal crops (the content-probe method,
  byte features only, no tokenizer); report the count of pairs sharing > 256 bytes and the number
  of distinct byte-ranges after merging pairs that overlap > 256 bytes. Effective n = distinct
  classes.
- R4 document-leakage audit: histogram of the 1000 legal crop offsets (the leakmap method, guest
  run, same SPEC so the offsets are the instrument's own), binned by 100 kB; a spike that repeats
  the same offset region across both ladders is reported, not hidden.

## 5. Reading of the gate (frozen before the run)

- **CONFIRM** if leak rate stays in [2%, 8%] on both ladders AND the 14336/12288 cost stays in
  [5%, 12%]: the 8% figure is citable in the PoC budget.
- **UPDATE** if either ladder is < 1% (the 200-crop figure was noise) or > 15% (it underestimated),
  or the cost leaves [3%, 15%]: the budget figure is revised, and the 200-crop number is marked
  as not reproducible at N=1000 rather than deleted.
- The n=200 baseline is never overwritten; both are reported.

## 6. Cost and stop

- 4 evals (2 ladders x {200,1000}); the ablation ran ~2-3 min/cell, so under ~30 min GPU plus
  CPU for the audits. Exclusive `gpu://rtx4090` claim, released when done; the card is not held
  idle.
- STOP conditions: G0-a mismatch; instrument md5 mismatch; corpus md5 mismatch; missing checkpoint.
- This probe claims no measurement beyond the dumps. It settles only the scale-up and the interval
  width. It does not touch the P1 falsification or the H-cancel acceptance.
