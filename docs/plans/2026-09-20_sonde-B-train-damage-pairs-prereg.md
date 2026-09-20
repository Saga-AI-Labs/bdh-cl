# Sonde B — Train the damage pairs (read-only predecessor plan for a training probe)

Status: DRAFT, pre-registration. No GPU claimed, no run launched, no checkpoint touched. This file is the gate that must be frozen before any gpu://rtx4090 claim, exactly as A required freeze.json + functional_check rc=0 before its first crop.

Date: 2026-09-20 · Seat: A0-Quinn · Predecessor: A readout docs/reports/2026-09-20_sonde-D-hybrid-crop-addressing-report.md (commit f39627b) · A pre-reg: docs/plans/2026-09-19_sonde-D-overlap-addressing-prereg.md

## 1. Why B exists (read off A, not assumed)

A ran read-only over the existing ladder. All 20 hybrid crops routed 200/200 to their front-half width and carried served-ppl damage that is pair-specific. In every hybrid the oracle column read nan — correct, because a never-trained domain has no trained prefix expert, so there is nothing to grade against. A can show mis-routing damage but cannot grade it. B removes that ceiling the only way it can be removed: train the damage pairs so each gains a real width, then grade surface-vs-content against oracle.

## 2. Scope — the four pairs that hold the signal

From the A confusion and served-ppl table (md5 ef22c08889008d3a33eaf6c6ee959a7f), the damage concentrates in four pairs; training all 20 would be waste:

| pair (front__back) | A served ppl | rank |
| --- | --- | --- |
| prose__math | 805.47 | worst |
| prose__code | 157.67 | 2 |
| math__ga | 110.35 | 3 |
| ga__code | 80.97 | 4 |

The flipped control is built in: A already has code__prose 6.48 next to prose__code 157.67 — the same two domains, order flipped, factor ~24. B keeps both directions for the trained pairs so the asymmetry is measured, not quoted.

## 3. What is MEASURED vs what is OPEN (the bs lesson, enforced)

MEASURED at the artefact, two readings separated. A's ladder: block_size 512 from the checkpoint, window 128 (splice boundary), routes 8192/10240/12288/14336/16384, N_full 16384. probe_s's generator (the template B would inherit): block_size 128 HARDCODED at probe_s_semantic.py:193, and its 512 is a fact-COUNT (assert len(facts)==512 at Z.121), NOT a block size. Consequence, read from the code not assumed: B CANNOT inherit the template's block — it must override to 512 for the A-ladder, then pin it at the checkpoint. The 'fixed inputs' frame was wrong; these are override-then-pin, and I had written them as settled inputs. grow_mult is a phase FLAG (0 base / 32 grown, Z.193) not a constant, and route_aware=grown means the grown phase trains route-aware; both read at the artefact.

OPEN — must be pinned at the artefact before freeze, forbidden to enter from the head:

- trained width per damage-pair cell: NOT measured anywhere. The probe_s template trained its two synthetic territores to exactness (train_A 1.0, train_B 0.996) and recorded grow_mult, device cuda. B's per-cell trained width is that template's job to produce, then read back — writing it here unmeasured is exactly the bs=512 mistake.
- grow_mult / block plan for a 2-domain hybrid: probe_s used grow_mult 32; a real hybrid crop needs its own value, chosen on the machine, not copied.
- corpus source for the foreign tail: the real-domain tails come from data/textmix2/... (paths verified in A); the hybrid .bin form is A's corpora_hybrid/*.bin, 20 files at 514 bytes.

## 4. Design — the dissociation A could not run

Each damage pair is trained to a real width, then scored two ways at the SAME ladder:
- surface arm: router decides on the first window bytes (front half) → is the front half's width chosen?
- content arm: oracle uses the true width of the half that actually carries the served tail → does the router match the content's owner?

The signature is the routed-vs-oracle ppl gap at the tail, now computable because an expert exists. Three outcomes, each with a different countermeasure space, identical to the A decision table but now gradeable:
- (a) holds: oracle==routed → addressing survives real overlap, storage argument strengthens, no countermeasure needed
- (b) addressing breaks, storage intact: routed != oracle but the trained slice stays BIT-EXACT under p5 → fix the ROUTER (sondeC embedding router / P-C4 reject), not storage
- (c) storage breaks: the parent slice is no longer BIT-EXACT → the paper's core isometric claim does not transfer; genuine threat

p5 is a pure checkpoint pair-check (two checkpoint args, no crop/eval input); (c) is only observable where a real growth phase happened — i.e. the trained cells B produces, which is precisely why A alone cannot reach it and why B is not redundant.

## 5. Protocol gates before the card is touched

1. Freeze this plan: freeze.json + source_hashes + gates + functional_check (the A shape: it measured bs and verified the splice cell at the artefact before the run). functional_check must pin each cell's trained width from the checkpoint, not assert it.
2. probe_s template reused for the training step (it trained two synthetic domains to exactness); smoke-first (CPU, byte-parity copy into out_c/, pristine eval_router.py md5 preserved), then the card.
3. Bus intent with ref BEFORE the gpu://rtx4090 claim (rule 7b), claim, run under the lease, RELEASE after (lapse is a protocol breach).
4. Operator GO on the open parameters (section 3) — the same loop that gated A's pre-reg.

## 6. What B is and is not

B trains a handful of small synthetic-to-real damage pairs on a ladder — minutes-scale, probe_s precedent, NOT the 100M target run. It answers where the capacity-addressing mechanism starts to fail, so the countermeasure is chosen before a real model is trained. It does not test a better router or a reject layer directly; it names which of (a)/(b)/(c) we are in, which is the decision that selects the countermeasure.

## 7. Open questions for the operator (answer before freeze)

- Which four pairs confirmed, or add the near-free prose__legal 4.94 as a (a)-anchor so a clean cell sits next to the four damaged ones?
- Trained width: probe_s grow_mult 32 as the template, or match each pair to the width its real-domain twin already holds?
- Is a 100M-scale sanity pass wanted later, or does B stay ladder-scale (my read: ladder-scale is the point; scale is a separate decision)?

Pre-registration complete as a draft. Freeze only after the section 7 answers and the functional_check pins the trained widths at the artefact.
