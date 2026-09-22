# Sonde B - reference-ladder replication: grown cells, addressing readout, storage integrity

Date: 2026-09-22 (UTC 19:33-22:31). Seat: A0-Quinn (`saga`). Host: `bdh-4090` (192.168.178.200),
user `a0-quinn`, run-site `/media/data/coding/bdh`, HEAD `e6bf359`.
Status: **COMPLETE** - four grow cells `rc=0`, five eval passes `rc=0`, storage check `failed_regions=0`.

Design of record: `docs/plans/2026-09-21_sonde-B-reference-ladder-replication-prereg.md`
Committed at `0d30722` (parent `a63fe80`), md5-pinned.
Result replicated: `docs/reports/phase_2/2026-09-21_sonde-B-harvest-results-report.md` (seed-2 ladder).
External review that set the strategy: HAK `bdh-cl` #384 (operator), section 8 (replication over
another single-seed probe).

---

## 0. Design as applied, and provenance

Identical to the seed-2 harvest by construction - identity is the point of a replication.

- **Base ladder**: the REFERENCE ladder `out_a/bdh_textmix_ladA-A1-K5-*` (seed 1337), complete and
  un-harvested before this run. Pre-flight verified all six needed files present, md5-pinned in the
  pre-reg section 1a: `base_last 4346dec1...`, `base_best 3c893c9e...`, `code_last f5c784fd...`,
  `math_last f4fbf882...`, `legal_last b79f0d52...`, `ga_last d4016697...`.
- **Grow cells**: `prose__math` (128 -> 192, grow_mult 64), `prose__code` (128 -> 160, gm 32),
  `math__ga` (192 -> 256, gm 64), `prose__legal` (128 -> 224, gm 96, the (a)-anchor).
- **Eval-only**: `ga__code` (b), no growth, oracle = `code` at per-head route width **10240**.
- **Mandatory flags**: `--block-size 512` (pipeline default is 128; without it the run is silently
  wrong), `--route-aware --route-alpha 0.9`, `--no-freeze-attn`, `TORCHDYNAMO_DISABLE=1`,
  10000 iters, batch 1, warmup 1000, lr-decay 10000.
- **Instrument**: pristine `scripts/eval_router.py`, md5 `73832ecd08f24eded93a98a74572be6e`, asserted
  by the driver before any eval (so the author's uncommitted `--route-grid` working-tree edit cannot
  leak into the replication).
- **Isolation**: `out/` and `out_a/` read-only; every artifact under `out_c/sondeB/harvest_ref`.
- **Card**: `gpu://rtx4090` claimed exclusive as `s_bdh-cl_000102_5dd8f4` at 19:31:39Z, held by a
  detached renewer, released 22:33:26Z.

---

## 1. Run health

Driver `out_c/sondeB/harvest_ref_ladder.sh` (md5 `b77e3468...`), launched 19:33:19Z, done marker
`REF_HARVEST_DRIVER_DONE` at 22:30:35Z (guest-local 00:30:35, guest TZ `Europe/Berlin`, UTC+2).
Total wall time ~2h57m.

| phase | guest-local end | rc | produced `_last.pt` (B) |
|---|---|---|---|
| grow prose__math | 22:13:34 | 0 | 1813044888 |
| grow prose__code | 22:45:06 | 0 | 1511046808 |
| grow math__ga | 23:35:45 | 0 | 2417040985 |
| grow prose__legal (anchor) | 00:17:47 | 0 | 2115042989 |
| eval prose__math | -- | 0 | 733 B |
| eval prose__code | -- | 0 | 732 B |
| eval math__ga | -- | 0 | 730 B |
| eval prose__legal | -- | 0 | 734 B |
| eval ga__code_b | -- | 0 | 765 B |

No repair or re-run of any cell was needed (the driver carries a skip-if-present guard, so no
partial state could force a duplicate grow). GPU released; live scope list read back empty.

---

## 2. (a) Addressing readout - reference ladder

Routed own-width plane: window 128, 200 crops/domain, batch 4, five-domain SPEC verbatim.
Format: `domain | claim distribution | served ppl`.

**prose__math** (expert trained: math) - joint 24.28

| domain | distribution | served ppl |
|---|---|---|
| prose | 200 at 8192 | 2.46 |
| **math** | **200 at 12288 (its expert)** | **1.41** |
| code | 79 at 8192, 91 at 10240, 30 at 12288 | 62.70 |
| legal | 194 at 8192, 6 at 10240 | 4.79 |
| ga | 196 at 8192, 4 at 10240 | 24.67 |

**prose__code** (expert trained: code) - joint 7.60

| domain | distribution | served ppl |
|---|---|---|
| prose | 200 at 8192 | 2.46 |
| **code** | **200 at 10240 (its expert)** | **4.90** |
| math | 1 at 8192, 199 at 10240 | 14.91 |
| legal | 46 at 8192, 154 at 10240 | 4.15 |
| ga | 5 at 8192, 195 at 10240 | 20.18 |

**math__ga** (expert trained: ga) - joint 30.93

| domain | distribution | served ppl |
|---|---|---|
| prose | 200 at 8192 | 2.46 |
| code | 200 at 10240 | 4.90 |
| math | 200 at 12288 | 1.47 |
| **ga** | **200 at 16384 (its expert)** | **2.40** |
| legal | 46 at 8192, 154 at 10240 | 4.15 |

**prose__legal** - the (a)-anchor (expert trained: legal) - joint 14.94

| domain | distribution | served ppl |
|---|---|---|
| prose | 200 at 8192 | 2.46 |
| code | 7 at 8192, 82 at 10240, 74 at 12288, 37 at 14336 | 64.41 |
| math | 15 at 8192, 68 at 10240, 94 at 12288, 23 at 14336 | 38.29 |
| **legal** | **189 at 14336 (its expert), 11 at 12288** | **2.21** |
| ga | 101 at 8192, 87 at 10240, 10 at 12288, 2 at 14336 | 24.16 |

**ga__code** - the (b) cell, eval-only, oracle `code` at 10240 - joint 23.66

| domain | distribution | routed ppl | oracle ppl |
|---|---|---|---|
| prose | 200 at 8192 | 2.46 | nan |
| code | 200 at 10240 | 4.90 | **4.90** |
| math | 200 at 12288 | 1.47 | nan |
| legal | 200 at 14336 | 2.28 | nan |
| ga | 200 at 16384 | 2.37 | nan |

---

## 3. Cross-seed comparison - focus rows

The focus row of a cell is the one newly-trained expert. Served ppl on the focus row is
near seed-invariant.

| focus cell | expert @ col | seed-2 self | ref self | seed-2 leaks (up/down) | ref leaks (up/down) | upper col available |
|---|---|---|---|---|---|---|
| prose__math | math @ 12288 | 200 | 200 | 0 / 0 | 0 / 0 | yes |
| prose__code | code @ 10240 | 200 | 200 | 0 / 0 | 0 / 0 | yes |
| math__ga | ga @ 16384 | 200 | 200 | 0 / 0 | 0 / 0 | no (top col) |
| **prose__legal** | **legal @ 14336** | **191** | **189** | **0 / 9** | **0 / 11** | **yes (16384)** |
| ga__code (b) | code @ 10240 | 200 | 200 | 0 / 0 | 0 / 0 | yes |

Served ppl on the focus rows:

| focus | seed-2 | reference |
|---|---|---|
| math @ 12288 | 1.41 | 1.41 |
| code @ 10240 (prose__code) | 4.92 | 4.90 |
| ga @ 16384 | 2.36 | 2.40 |
| legal @ 14336 (anchor) | 2.21 | 2.21 |
| code @ 10240 (b cell) | 4.95 | 4.90 |

---

## 4. The leak statistic (frozen before the run)

Definition, fixed in the pre-reg section 3 before any reference measurement: population is focus
rows only; a focus row is boundary-eligible iff a column exists both above and below it; leaks are
split up/down relative to the focus column.

| seed | focus leaks | up | down | boundary-eligible? |
|---|---|---|---|---|
| seed-2 | 9 (legal only) | 0 | 9 | yes |
| reference | 11 (legal only) | 0 | 11 | yes |
| **combined** | **20** | **0** | **20** | - |

**Frozen verdict, applied as written:** the reference `legal` focus leaks downward, is
boundary-eligible, and has self < 200 -> *cross-seed confirmation of a lower-width boundary
property*. Exactly one focus cell leaks on each ladder, and it is the same cell.

**Where my own prediction failed.** Pre-reg P1 stated `legal self in {191..199}`. The reference
value is **189, outside the band - P1 is falsified.** The direction and structure replicated; my
numeric band was too tight. P1 and the interpretation table disagreed with each other, and reality
landed between them: the interpretation rule passes, P1 fails. The leak did not narrow across
seeds; it widened slightly (9 -> 11).

**Confounds, unchanged and stated:** n is small (9 and 11, one cell each); "down" from 14336 is
12288, the incrementally adjacent lower column, so proximity and direction remain confounded; and
legal is the one domain already known for boundary instability from the seed-2 work. The result is
a confirmed pointer, not a demonstrated general boundary bias.

---

## 5. (b) oracle equality - reproduced

On the routed own-width plane, the reference `code` expert serves **4.90**, and its fixed-width
oracle at 10240 is **4.90**: **delta 0.00**. The seed-2 harvest measured 4.95 = 4.95, delta 0.00.
The cleanest single mechanism readout in the set reproduces exactly on an independent ladder.

---

## 6. (c) storage integrity

Method and its provenance, stated precisely: the seed-2 run's storage check was ad-hoc (in-run for
one cell, in recovery for the others) and no reusable harness existed on the host. This report's
check is therefore an author-written reconstruction, `out_c/sondeB/storage_check_ref.py`
(md5 `b3d36b5c31260eca8c2d150539c64321`), run **CPU-only** (`CUDA_VISIBLE_DEVICES=""`) after the
harvest, with output at `out_c/sondeB/harvest_ref/storage_check_ref.txt`. The frozen set is **not
guessed**: it is the exact set `pipeline/train.py:197-203` snapshots and restores at step end -
`encoder[:, :, :n_old]`, `encoder_v[:, :, :n_old]`, `decoder.view(nh, n_new, -1)[:, :n_old, :]` -
plus `embed.weight` and `lm_head`, which are frozen by `requires_grad=False` rather than by restore.

| cell | frozen regions | new capacity | verdict |
|---|---|---|---|
| prose__math | 5/5 BIT_EXACT_OK (maxabs 0.000e+00) | 4096 new cols/rows, nonzero_frac 1.0000 | PASS |
| prose__code | 5/5 BIT_EXACT_OK | 2048 new, nonzero_frac 1.0000 | PASS |
| math__ga | 5/5 BIT_EXACT_OK | 4096 new, nonzero_frac 1.0000 | PASS |
| prose__legal | 5/5 BIT_EXACT_OK | 6144 new, nonzero_frac 1.0000 | PASS |

`STORAGE_CHECK_DONE failed_regions=0` (epsilon-relative tolerance recorded at 9.537e-07; every
region was bit-exact well inside it, so the tolerance was not needed). Capacity was added at grown
width without disturbing what had to remain unchanged - the (c) leg reproduces on the reference
ladder.

---

## 7. Training readouts (plumbing, secondary - no learning claim)

| cell | final val ppl | test ppl | best val ppl |
|---|---|---|---|
| prose__math | 1.51 | 1.45 | 1.30 |
| prose__code | 4.38 | 5.77 | 2.98 |
| math__ga | 2.33 | 2.42 | 2.28 |
| prose__legal | 2.16 | 2.19 | 2.03 |

These establish that the runs produced plausible checkpoints. They are not evidence about the
mechanism; the addressing and storage measurements above carry that, and they are independent of
these numbers.

---

## 8. What replicates, what does not, and limits

**Replicates on an independent ladder:** the mechanism chain. Trained expert -> tight diagonal and
oracle-grade serving; absent expert -> dispersed routing and 4-5x worse serving; the (b) oracle
equality at delta 0.00; the (c) frozen-region bit-exactness with growth present. These are
complementary readings of one chain, not three independent confirmations: (a) routing, (b) serving
and (c) storage are three views of the same grown checkpoints.

**Replicates and strengthens:** the legal boundary leak is present on both ladders, in the same
cell, in the same direction (20 of 20 leaks downward, 0 upward), with the upper column available.

**Does not replicate, and is reported as a failure:** pre-reg P1's numeric band {191..199} -
reference 189.

**Nuance worth recording:** the homeless-domain scatter is seed-stable in magnitude but not in
fine column distribution. Reference `prose__legal` homeless rows scatter 7/82/74/37 (code, ppl
64.41) and 15/68/94/23 (math, ppl 38.29); seed-2 gave 6/31/120/43 (85.89) and 6/84/59/51 (39.37).
Same order of degradation, different routing texture. Aggregate behaviour replicates; the exact
routing path does not.

**Limits:** single seed per ladder (two ladders total), 200 crops/domain, ladder scale. The
homeless-domain contrast is an observational counterfactual within trained pairs, not a randomised
causal intervention. The (c) check is an author reconstruction run after the fact, not a
pre-existing harness. Nothing here tests 100M scaling, seed-3 ladder stability (still "no" on
record), or the necessity/benefit of a reject layer.

---

## 9. Process ledger (what went wrong, kept rather than cleaned)

1. **A false lease-breach alarm, from me.** The watcher released the card at 22:33:26Z while the
done marker reads `2026-09-22 00:30:35`. The marker is **guest-local** (TZ `Europe/Berlin`, UTC+2),
so it corresponds to 22:30:35 UTC and the release came ~3 minutes after the run finished. Timezone
artefact, not a protocol failure - verified with `date` and `/etc/timezone` rather than explained
away.
2. **P1 falsified by my own run** (section 4). Recorded as a failure of prediction, not smoothed.
3. **The seed-2 driver's missing anchor is fixed here.** The seed-2 driver announced `prose__legal`
as the (a)-anchor but issued no grow for it; this driver includes it (grow_mult 96).
4. **The eval stub trap is closed.** The seed-2 evals were empty 295-byte argparse stubs because
`--domains` was omitted; this driver passes `--domains`, uses the route-width oracle
`code:10240` (not the `code:160` multiplier), and rejects any eval output under 300 bytes.
5. **One tool-format slip:** an emitted call lost its `runtime` field and was rejected before
executing; re-issued unchanged. No effect on the run.

---

## 10. Reproduction recipe

```
# pre-flight (read-only): reference ladder present and complete
ssh bdh-4090 'cd /media/data/coding/bdh && ls -la out_a/ | grep ladA-A1-K5 | grep -v seed2'

# claim the card (scope s_bdh-cl_000102_5dd8f4 was the lease for this run)
# post a working_on intent with the before-SHA, then:
ssh bdh-4090 'cd /media/data/coding/bdh && setsid nohup bash /tmp/harvest_ref.sh > /tmp/harvest_ref.log 2>&1 < /dev/null &'

# storage check (CPU-only, no card)
ssh bdh-4090 'cd /media/data/coding/bdh && CUDA_VISIBLE_DEVICES="" .venv/bin/python /tmp/storage_check_ref.py'
```

Driver: `out_c/sondeB/harvest_ref_ladder.sh` (md5 `b77e346873097dcf5870f4eb7f7270f8`).
Smoke: `out_c/sondeB/smoke_ref_ladder.sh` (md5 `5a5564f2d727c8602223c506eb3dd474`).
Storage: `out_c/sondeB/storage_check_ref.py` (md5 `b3d36b5c31260eca8c2d150539c64321`).

---

## 11. State

Card released, live scope list empty, no training or eval process live. `out/` and `out_a/`
untouched. All artifacts under `out_c/sondeB/harvest_ref` (gitignored, hence transcribed here).
This report is the version-pinned record of the reference-ladder replication and of the one
pre-registered prediction it falsified.
