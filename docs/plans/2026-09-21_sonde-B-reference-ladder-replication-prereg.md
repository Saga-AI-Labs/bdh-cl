# Sonde B - reference-ladder replication pre-registration

Date: 2026-09-21 (UTC) - Seat: A0-Quinn (`saga`) - Status: **DRAFT** until frozen pre-run
Frozen design of record, written BEFORE any measurement on the reference ladder.

Companion (what this replicates): `docs/plans/2026-09-20_sonde-B-train-damage-pairs-prereg.md`
Result it replicates: `docs/reports/phase_2/2026-09-21_sonde-B-harvest-results-report.md`
External review the strategy follows: HAK `bdh-cl` #384 (operator), section 8.

---

## 0. Why this run exists

The 2026-09-21 harvest established the (a)/(b)/(c) mechanism at ladder scale on the **seed-2**
ladder (`out_a/bdh_textmix_ladA-A1-K5-seed2-*`). Every cell is single-seed; the legal boundary
leak (9/200, all downward) is the harvest's only directional signal and sits on the one domain
already known for boundary instability.

HAK #384 section 8 ruled the next major question is **replication of the mechanism**, not
another elaborate single-seed probe. The reference ladder (`out_a/bdh_textmix_ladA-A1-K5-*`,
seed 1337) is **complete and un-harvested** (section 1). Replicating the harvest on it costs
only the grown-cell step - no new ladder - and simultaneously tests the one open directional
signal. That is why this runs on the reference ladder rather than seed-3: a fresh seed-3 would
first rebuild an entire ladder to ask a question an existing ladder can already ask.

---

## 1. Run-site provenance (read-only pre-flight, 2026-09-21T19:22Z, SSH_RC=0)

- host alias `bdh-4090` (192.168.178.200), user `a0-quinn`, key `/root/.ssh/quinn_4090`
- run-site `/media/data/coding/bdh`, HEAD `e6bf359` (same HEAD as the seed-2 run)
- reference ladder **present and complete** - all six files the harvest needs:

| file (out_a/) | size (B) |
|---|---|
| `bdh_textmix_ladA-A1-K5-base_last.pt` | 1211147527 |
| `bdh_textmix_ladA-A1-K5-base_best.pt` | 1211147527 |
| `bdh_textmix_ladA-A1-K5-code_last.pt` | 1511046787 |
| `bdh_textmix_ladA-A1-K5-math_last.pt` | 1813044867 |
| `bdh_textmix_ladA-A1-K5-legal_last.pt` | 2115042968 |
| `bdh_textmix_ladA-A1-K5-ga_last.pt` | 2417040985 |

- completion evidence: `out_c/logs/ladA-A1-K5_analysis.txt` (5236 B), `..._routdiag_final.txt`
  (711 B), per-phase logs, and the done marker `ladder-ladA-A1-K5-done` present
- disk free on `/media/data`: 6.4 T of 15 T (54% used)

### 1a. Frozen hashes (md5, read 2026-09-21T19:24Z, SSH_RC=0)

The init artifact the run consumes is `base_last`; the four domain `_last` files are what a
reviewer needs to reproduce the harvest. All six pinned here so the freeze is hashed, not
size-only:

| file (out_a/) | md5 |
|---|---|
| `bdh_textmix_ladA-A1-K5-base_last.pt` | `4346dec144c1d44cc8155a67eb9623ce` |
| `bdh_textmix_ladA-A1-K5-base_best.pt` | `3c893c9eda91725d6ebd8dc808cb7af6` |
| `bdh_textmix_ladA-A1-K5-code_last.pt` | `f5c784fd4cfe7224a8fbd0e69931aa26` |
| `bdh_textmix_ladA-A1-K5-math_last.pt` | `f4fbf8827124c3f4563db7cec7485e8a` |
| `bdh_textmix_ladA-A1-K5-legal_last.pt` | `b79f0d52218156b0526bdda2fea15e9e` |
| `bdh_textmix_ladA-A1-K5-ga_last.pt` | `d401669769bb80b531d12a3adcfa8b7a` |

`base_last` stat: 1211147527 B, mtime `2026-09-18 05:07:20 +0200`.

Cross-check against the seed-2 ladder (same architecture, metadata bytes apart) - the twin-width
mapping transfers: ref base 1211147527 vs seed2 1211147753; ref code 1511046787 vs seed2
1511046913; ref math 1813044867 vs seed2 1813044993; ref legal 2115042968 vs seed2 2115043094;
ref ga 2417040985 vs seed2 2417041111.

---

## 2. Frozen design (identical to the seed-2 harvest - identity is the point)

- **Grown cells:** `prose__math`, `prose__code`, `math__ga`, `prose__legal` (the (a)-anchor).
- **Eval-only:** `ga__code`, `(b)`-only, **no flip** (operator ruling). Oracle = `code` at
  per-head width **10240**.
- **Widths** twin-matched to the measured A-ladder set `128/160/192/224/256` (n_embd 512,
  n_head 8 -> per-head `8192/10240/12288/14336/16384`); `grow_mult = twin - 128`.
- **`--block-size 512` MANDATORY** (pipeline default is 128; without it the run is
  silently wrong - the override-then-pin result, pre-reg 2026-09-20 section 5).
- **Training:** 10000 iters, route-aware alpha 0.9, `init_from` the reference `base_last`.
- **Measurement plane:** routed own-width, window 128, 200 crops/domain, batch 4, five-domain
  SPEC verbatim from the committed reference invocation (routed plane, not the cold table).
- **Instrument pristine:** `out/` and `out_a/` read-only; every artifact under `out_c/sondeB/`.

---

## 3. Frozen leak statistic (the thing pre-registered this time, not rediscovered)

Definition, fixed before the run:

- **Population:** focus rows only - the one newly-trained expert per cell. Homeless rows are
  expected diffusion (not boundary events) and are excluded.
- **Boundary-eligible:** a cell's focus row is boundary-eligible iff at least one column above
  AND at least one below the focus column exists in `{8192,10240,12288,14336,16384}` (so a
  top- or bottom-column cell cannot manufacture a one-way bias).
- **Measured:** self-count, and for leaks the destination columns split `up` vs `down`
  relative to the focus column.
- **Seed-2 observation (the signal under test):** `legal@14336`, self **191**, leaks **9**
  (`0` up, `9` down: `8->12288`, `1->10240`), boundary-eligible (16384 was available above).

**Pre-declared interpretation (fixed now, read after the run):**

| reference `legal` focus outcome | reading |
|---|---|
| leaks **down**, boundary-eligible, self < 200 | cross-seed confirmation of a lower-width boundary property |
| leaks **up**, or symmetric | no directional bias; the seed-2 signal was noise at n=9 |
| **self 200/200**, clean | the leak was a seed-local legal quirk, not a boundary property |
| a **non-legal** focus cell leaks | new signal - reported with its own cell and direction |

---

## 4. (a)/(b)/(c) predicates (frozen)

- **(a)** trained expert present -> tight diagonal + oracle-grade serving.
- **(b)** (`code` cell) served ppl equals its fixed-width oracle on the routed plane
  (delta `0.00`, or within the harness's printed resolution).
- **(c)** frozen regions (`encoder`, `encoder_v`, `decoder`, `embed_weight`, `lm_head`) unchanged
  vs init; new columns present at grown width; `failed_regions 0` every grown cell.
  - Tolerance: follow the seed-2 harvest's (c) procedure. If a frozen-region check fires,
    re-judge the **grown slice** by epsilon-relative tolerance (`8*finfo.eps`), **never**
    loosen the frozen-region check itself.

---

## 5. Predictions (falsifiable)

- **P1:** the four focus cells route self `200/200`; `legal` self in `{191..199}` (a clean
  200/200 for legal would falsify the seed-2 boundary story).
- **P2:** homeless domains scatter across neighbouring columns and serve 4-5x worse than with
  an expert (seed-2: code 72.67/85.89 vs 4.92/4.95; ga 27.72/25.52 vs 2.34/2.36).
- **P3:** the (b) equality holds for the `code` cell on the routed plane.
- **P4:** storage `failed_regions 0` for every grown cell.

---

## 6. Out of scope (explicitly not tested here)

- 100M scaling; seed-3 (ladder stability - stands at *no* on record).
- The learned/embedding router ceiling (Sonde C Arm 2, separate).
- reject/abstain as **necessary or beneficial** - #384 section 5 rules this not-yet-demonstrated;
  the harvest may motivate it, this run does not test it.

---

## 7. Gate before any GPU claim (order fixed)

1. Commit this pre-reg (bus intent + before-SHA, three-way read after).
2. md5-pin the reference `base_last` and write it back here (freeze the artifact).
3. Post a fresh `working_on` intent; claim `gpu://rtx4090` exclusive.
4. **Smoke first:** one single grow on the reference base at `bs=512`, width read back off the
   produced checkpoint.
5. Then the full grown-cell set; release the card at the end (readback, not the DELETE code).
