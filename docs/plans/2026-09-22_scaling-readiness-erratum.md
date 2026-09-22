# Scaling-readiness pre-registration - erratum (Quinn)

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: **COMPLETE**
Target of this erratum: `docs/plans/2026-09-22_scaling-readiness-gaps-and-probes-prereg.md` @ `76dd597`
This document is ADDITIVE. It does not edit the pre-registration; the original stays as written.
Operator instruction that triggered it: "P0 + P1a + P2: go" after a review that flagged defects.

Note on quotation: quotes from the pre-registration are transcribed to ASCII so this file stays
ASCII (>= for >=, <= for <=, -> for ->, D for the delta sign). No other change to the quoted text.

---

## 0. Why this exists

The pre-registration was reviewed before running P0/P1a/P2. Four defects were found that are
backed by code evidence already on disk, and one defect I had asserted in chat was re-checked and
found to be my own error, so it is retracted below. Nothing here changes a measurement; it fixes
two things that would have broken a run and flags two ambiguities, and records a retraction.

## 1. E1 - P0: "first 200 byte ranges identical by construction" is FALSE for the target domain

Pre-reg line 46 reads:

```
Re-eval prose__legal both ladders at N=1000 crops, window 128, same routes/spec/order
(seed 1234 extension - first 200 byte ranges identical by construction, assert overlap of
first 200 vs archived dumps).
```

Code evidence (all on disk, no new measurement):

- `scripts/eval_router.py:76` creates ONE generator, `g = torch.Generator().manual_seed(1234)`,
  BEFORE the domain loop; `:82-83` draws exactly ONE `torch.randint(hi, (args.crops,), generator=g)`
  per domain. The stream is therefore consumed sequentially across domains.
- This is already stated in `docs/plans/2026-09-22_sonde-B-legal-leak-content-prereg.md:36-38`:
  the generator is "created once and consumed sequentially in domain order (prose, code, math,
  legal, ga). Legal is the fourth draw, so the map must be rebuilt by consuming the three preceding
  draws first." That pre-registration and its content probe were checked with MISMATCH_COUNT 0
  across guest torch 2.13.0+cu130 and local torch 2.4.0+cpu.
- Consequence: at `--crops 200` each domain draws 200; at `--crops 1000` each domain draws 1000.
  The target domain `legal` is the fourth draw, so in the 1000-run it starts only after prose,
  code and math have consumed 3x1000 draws instead of 3x200. It therefore starts at a different
  stream position than in the archived 200-run.
- So the 1000-run's first 200 `legal` crops are NOT the archived 200 `legal` crops. The
  pre-registered overlap assertion ("assert overlap of first 200 vs archived dumps") would FAIL on
  the target domain. Only the FIRST domain (prose, drawn first on a fresh stream) is a prefix.

Correction to run, before P0:
- The overlap must be asserted against an archived-comparable baseline. Two admissible options:
  (a) run a dedicated `--crops 200` pass with the SAME shared generator, SAME domain order and
      SAME per-draw size as the archived run, and assert that pass reproduces the archived dumps
      first, THEN run `--crops 1000`; or
  (b) if per-domain independence is wanted, give EACH domain its OWN generator seeded 1234, and
      state explicitly that the 1000-run is then NOT the same shared stream as the archived
      run, so the archived 200 dumps may not be reused as its prefix.
- Either way the frozen reading is bound to the baseline it is compared against. Do not mix a
  1000-crop stream with a 200-crop archive and call them "identical by construction".

## 2. E2 - P0: Wilson 95% at crop level understates the interval

Pre-reg line 48: "leak rate + served ppl ... with Wilson 95% (crop-level, descriptive)."
Wilson intervals assume independent crops. My own committed content probe
(`docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-content-report.md:101`) found a reference
leaker pair sharing "471 of 512 bytes, 92 percent", merging which "the reference ladder's 5
leakers cover only 4 distinct" byte ranges. The crops are not independent, so the effective n is
below the nominal crop count and a crop-level Wilson interval is too narrow. The interval must be
declared on the effective (deduped) count, or widened, or reported as descriptive only.

## 3. E3 - P2: "all 8 existing grown checkpoints" is ambiguous (16 files match)

Pre-reg line 61: "must PASS on all 8 existing grown checkpoints". On the guest
(`out_c/sondeB/harvest` and `harvest_ref`) each of the four cells exists as BOTH `_best.pt` and
`_last.pt`, i.e. 16 files match, checked by `ls` in this session (identical sizes per pair,
legal 2115042989 B). "The 8 checkpoints" does not pin which set. State explicitly whether the
PASS set is the 8 `_last.pt` (the ones the ladder actually serves), the 8 `_best.pt`, or all 16.

## 4. E4 - P3: expected cost is internally inconsistent

Pre-reg line 72: "Expected cost ~8-12h (scales from A1-K5 =12.3h/5 phases)." The stated basis
12.3h/5 phases = 2.46h/phase; P3 is 7 phases, so the same basis gives ~17.2h, not 8-12h. Either
the 8-12h figure or the 12.3h/5 basis is wrong. Left as an open question, not resolved here
(P3 is not run under this instruction).

## 5. E5 - retraction: the "truncated P3 gate" defect I claimed is FALSE (my error)

In chat I asserted the P3 gate was broken because it read "first-phase retention |D|<=0. remain
gated on A1-K20 telemetry", i.e. a threshold that never terminates. I re-checked the file. The
gate (line 70) reads verbatim and complete:

```
P3-PASS if P5 7/7 AND routing >=0.95 AND first-phase retention |D|<=0.08 -> GO A1-K20 unchanged.
```

The threshold `<=0.08` is present; "remain gated on A1-K20 telemetry" belongs to line 84 and
describes A1-K40/W1024, not P3. The two lines are not one statement. This defect was NOT in the
file; the claim was a misreading on my part and is retracted. No change to the file results.

## 6. What this erratum does and does not do

- Does: fix two run-breaking defects before P0 (E1 overlap, E2 interval), flag one ambiguity (E3)
  and one internal inconsistency (E4), and retract one false claim of mine (E5).
- Does not: run any probe, take any measurement, or edit the pre-registration. It adds no data
  that was not already on disk.
- Consequence for the agreed run: P0 is run only after the E1 overlap fix is in place, with the
  E2 interval treated on the effective count. P1a and P2 run as planned. P1b and P3 are not run
  (training spend needs a separate operator GO).
