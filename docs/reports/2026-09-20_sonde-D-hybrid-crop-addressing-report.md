# Sonde D — Hybrid-Crop Addressing (read-only, variant A)

Date: 2026-09-20 · Seat: A0-Quinn · Plan: docs/plans/2026-09-19_sonde-D-overlap-addressing-prereg.md (Rev with §6b correction)

Evidence artefact: out_c/sondeD/run_nohup.log — md5 ef22c08889008d3a33eaf6c6ee959a7f, 84 lines, 3779 bytes. Corpora: out_c/sondeD/corpora_hybrid/*.bin, 20 cells, each 514 bytes (bs+2). freeze.json present; functional_check rc=0/PASS before the run.

## 1. Design in one line

Each hybrid crop is the first 128 bytes of domain X concatenated with bytes 128–512 of domain Y, drawn as the single splice cell (the bs+2 pad forces hi==1 so the uniform crop draw has one offset). The router scores the first window bytes and serves the rest, so the question is literally: does addressing follow the early surface (X) or the late content (Y)?

## 2. Confusion — 25 domains × 5 routes

The five real domains reproduce the §4b plane (each 200/200 on its own width, with the known legal one-crop leak 1@8192 / 199@14336). All 20 hybrids route 200/200 into the width column of their FRONT half, X. The router decides on the first 128 bytes and never revisits them.

The read is unambiguous: addressing is a pure surface-follower on this ladder. It is not a confused router — it is a correct one given only the window.

## 3. Served ppl — the damage, and its asymmetry

Real-domain controls sit between 1.46 and 4.95. The hybrids carry the injury, and the injury is pair-specific, not overlap-magnitude:

| front__back | served ppl | front__back | served ppl |
| --- | --- | --- | --- |
| prose__legal | 4.94 | ga__code | 80.97 |
| code__prose | 6.48 | math__code | 35.41 |
| legal__math | 6.98 | math__ga | 110.35 |
| legal__prose | 9.79 | prose__ga | 34.16 |
| code__legal | 5.30 | prose__code | 157.67 |
| code__math | 10.67 | ga__prose | 42.37 |
| legal__code | 19.80 | prose__math | 805.47 |
| legal__ga | 30.29 | ga__math | 23.22 |
| math__legal | 17.97 | ga__legal | 18.65 |
| math__prose | 21.84 | code__ga | 26.19 |

The load-bearing number is the flipped pair: prose__code = 157.67 against code__prose = 6.48. Same two domains, one concatenation in the other order, a factor of ~24. The damage is not the overlap — it is which expert has to serve the foreign tail. One absorbs it, the other chokes on it. joint full-width reference, served positions only: 22.94.

## 4. What A does not establish (the §6b gap, stated as a gap)

Every hybrid oracle column reads nan. That is correct, not a measurement error: a hybrid domain has no trained prefix expert, so there is no oracle width to score against. The consequence is precise — A can show mis-routing damage (this table) but cannot yet grade it against oracle behaviour, because grading needs an expert that only training produces.

Also not measured here: whether a better router (embedding), a reject layer (P-C4 two-axis), or an isometric storage scheme would undo the damage. A names the damage and the pair it lives in; it does not test the countermeasure.

## 5. What B must be, and where the signal lives

This is A's real yield for the next probe: it is not worth training all 20 cells. The signal concentrates in the damage pairs — prose__math (805), prose__code (158), math__ga (110), ga__code (81). B should train exactly these to a real trained width, which fills the nan column and lets surface-vs-content be graded against oracle rather than observed against the surface alone. That is the A→B transition, read off the number, not assumed.

## 6. Provenance and hygiene

Read-only w.r.t. checkpoints; no training in A; corpora generated CPU-only into out_c/sondeD/corpora_hybrid; eval_router is the frozen copy pinned in freeze.json (pristine md5 preserved). gpu://rtx4090 claimed, run executed under the lease, then RELEASED (watch-readback: my scope absent from the live list). No model output beyond the served ppl read; no committed number here is from memory — all are from the md5-pinned log.

