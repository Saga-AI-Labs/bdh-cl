# Sonde B — Train the damage pairs (read-only predecessor plan for a training probe)

Status: DRAFT, pre-registration. No GPU claimed, no run launched, no checkpoint touched. This file is the gate that must be frozen before any gpu://rtx4090 claim, exactly as A required freeze.json + functional_check rc=0 before its first crop.

Date: 2026-09-20 · Seat: A0-Quinn · Predecessor: A readout docs/reports/phase_2/2026-09-20_sonde-D-hybrid-crop-addressing-report.md (commit f39627b) · A pre-reg: docs/plans/2026-09-19_sonde-D-overlap-addressing-prereg.md

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

PIPELINE MECHANISM — read at the artefact, this answers §5's own open L-5 question (does config.py + train.py accept a bs=512 grown of an A-ladder checkpoint). Measured in git, not assumed: config.py:20 `block_size: int = 128` is the dataclass DEFAULT; the A ladder carries 512 only in its own checkpoint cfg, NOT in the pipeline. train.py:116-118 — with init_from + grow_mult the code reads `grow_src['cfg']['mlp_internal_dim_multiplier']` and sets `cfg.mlp_internal_dim_multiplier = base_mult + grow_mult`: it inherits the WIDTH from the checkpoint, it does NOT inherit block_size. The data stream is cut at cfg.block_size (train.py:40/49/249/292, data.get_batch(...cfg.block_size...)). Consequence, enforced: if B loads a bs=512 A-ladder checkpoint per init_from and does NOT pass `--block-size 512`, the model wants 512 while the stream feeds 128 — and that is not a crash, it is a silently-wrong training run, the exact silent-inconclusive class this session has caught four times. So `--block-size 512` is MANDATORY on the A base, override-then-pin, and the reason is the pipeline's own 128 default (not merely probe_s, which §3's first line over-attributed). Also measured: route_aware (config.py:64, zero old neurons in forward + loss on prefix-only logits) and grow_mult>0 (config.py:59, old neurons + embed/lm_head frozen) are the (c)-precondition, not style — the F-V9 guard (train.py:135-141) REFUSES an unfrozen init onto a grown checkpoint without --grow-mult unless allow_unfrozen_grown_init is passed. That guard is what makes 'storage stays intact' a checkable claim rather than a hope.

RUN-SITE IDENTITY — MEASURED on .200 through the documented access (a0-quinn@.200 with the container key ~/.ssh/quinn_4090; host prints ai, whoami a0-quinn; SSH_RC=0). The four pipeline files the run loads are BYTE-IDENTICAL to the local git read on which the PIPELINE MECHANISM above is based: config.py 904b6954…, train.py 3ad7848d…, data.py c45ea50d…, transformer.py b1d3e18e… — git porcelain lists none of the four as modified. So freeze.json CAN pin these four at the artefact and the MECHANISM above is the code the run will execute. The 255 earlier was MY access construction (root@ + no key loaded), not a .200 finding, and /var/tmp/chiara/bdh does not exist on .200 at all (the documented path is /media/data/coding/bdh only) — that was an address error in my command, the fifth instance this session of guessing where I should read.

SCOPE OF THAT COVERAGE, stated tight so the match is not over-read: byte-identical files is NOT the same claim as identical checkout. The .200 HEAD measured this turn is e6bf359; the preflight memory named 17032e94. The four files the run imports match across those two refs; that says nothing about the rest of the tree. freeze.json therefore pins the FOUR LOADED FILES by md5 (the run's true surface), not a whole-repo HEAD.

STILL OPEN — forbidden to enter from the head: the trained width per damage-pair cell and the grow_mult for a 2-domain hybrid. These are NOT in any of the four md5 (they are run parameters, not loaded code), and §3 already bound them to be pinned on the machine, not copied from probe_s. That pinning is a smoke run, which is GPU-mandatory and therefore lives behind the lease + freeze + operator-GO chain below, not behind this measurement.

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
2. CORRECTION (committed §5 said 'probe_s template reused for the training step' — that was wrong, read at the artefact). probe_s is BOUND to its own 128 window: block_size=128 is hardcoded in config() (probe_s_semantic.py:193); assert len(m['facts'])==512 (Z.121) is a FACT-COUNT not a block size; Z.114 asserts query+16<=128 and Z.327 asserts len(raw)<=128. Forcing bs=512 through probe_s is a CRASH, not a test. What probe_s transfers is the MECHANISM only — train_phase with init_from/base_path (Z.221), grown=base+grow_mult and route_aware=grown (Z.193), and the smoke-attestation gate (Z.544-547). Its DATA and its BLOCK are probe_s-own and must NOT be inherited. Consequence: the earlier out_c/sondeB/functional_check.py is a DEAD PROXY — it imports DataAdapter, a symbol that exists 0/0, and tests a get_batch arg; its PASS would not answer the 512 question, so it must not be trusted nor used to justify a claim. The REAL B gate is a pipeline question: does pipeline/config.py + train.py (Config(...), the loop config() delegates to) accept a bs=512 grown of an A-ladder checkpoint via init_from + grow_mult + route_aware? Read that, do not assume. AND §4's (b)/(c) criterion is corrected too: BIT-EXACT across a width change is UNACHIEVABLE (BLAS reduction-order changes), so judge the grown slice by an epsilon-relative tolerance (8*finfo.eps on logits), not bit_equal — a bit-exact (c) test would fire a false storage-break alarm. Only after the pipeline read + an epsilon gate: freeze, then claim the card.
3. Bus intent with ref BEFORE the gpu://rtx4090 claim (rule 7b), claim, run under the lease, RELEASE after (lapse is a protocol breach).
4. Operator GO on the open parameters (section 3) — the same loop that gated A's pre-reg.

## 6. What B is and is not

B trains a handful of small synthetic-to-real damage pairs on a ladder — minutes-scale, probe_s precedent, NOT the 100M target run. It answers where the capacity-addressing mechanism starts to fail, so the countermeasure is chosen before a real model is trained. It does not test a better router or a reject layer directly; it names which of (a)/(b)/(c) we are in, which is the decision that selects the countermeasure.

## 7. Resolution of the operator questions (delegated choice; operator GO 2026-09-21; corroboration HAK #371)

- Pairs: retain the three twin-growable pairs prose__math (+64), prose__code (+32), math__ga (+64); retain ga__code as the (b)-only cell (no growth; the back twin is narrower, so no positive grow_mult exists). ADD the near-free prose__legal (served ppl 4.94) as an (a)-anchor so a clean cell sits beside the damaged ones.
- Trained width: match each pair to the width its real-domain twin already holds (measured 128/160/192/224/256). Do NOT inherit probe_s's grow_mult 32 -- that value belongs to probe_s's own synthetic territories.
- Scale: B stays ladder-scale; a 100M-target sanity pass is a separate decision, not part of B.
- Freeze gate: freeze only after the functional_check pins each cell's trained width from the checkpoint (no width from memory); then the bus intent precedes the gpu://rtx4090 claim, and a smoke precedes the full harvest.
