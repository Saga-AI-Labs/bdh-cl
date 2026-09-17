# Sonde A — Scaling Probe (Territories × Model Size)

Status: PRE-REGISTERED v0.3 · drafted 2026-09-16, updated 2026-09-17 · Quinn · Operator GO: granted (v0.3)
Revision: v0.3 folds in the measured Sonde C arms and probes R/J/S/P-C4′. The serving
router is fixed (likelihood scan); the head and the cascade are dismissed. Remaining
placeholders: only `TBD-K` (PoC charter) and `TBD-GB` (A's own disk telemetry).
Position in roadmap: between Sonde C and the PoC full pretrain (first mentioned in
the 2026-09-11 roadmap conversation; B plan: "Sonde A (scaling probe) is drafted
separately"). Depends on: Sonde B (**B-PASS**) and Sonde C (**C0 complete; arms
measured, Gate C-PARTIAL**). No probe outcome is a silent prerequisite of A's gates.

## Preconditions (one sentence each)

- **Sonde B (2026-09-15/16, host .200):** growth+selection works outside the language
domain — all five pre-registered predictions P-B1..P-B5 PASS, the storage thesis held
bit-exact through 4 growth transitions on non-language classes (P5 4/4), routing
199/200 with the one legal leak confirmed real at 200-crop depth
(`docs/reports/phase_2/2026-09-16_probe-b.md`, commits `6f6368d`/`b17de39`).
- **Sonde C0 (2026-09-16 06:54-13:00, host .200):** the prerequisite multilingual-base
  ladder is **complete** - base 2.33 ppl, 5/5 phases, P5 in-chain 4/4 PASS, routing
  **999/1000** (200 crops/domain), legal depth **198/200**
  (`docs/reports/phase_2/2026-09-16_probe-c.md`, commit `d8c2fe0`). Headline: the
  multilingual base did **not** close legal’s leak (Sonde B 197/200 -> C0 198/200),
  so the leak is **byte-geometry-intrinsic, not base-composition** - A’s hard cells
  are therefore base-independent and the C0 label set is a valid anchor.
- **Sonde C Arms 1-3: MEASURED (v0.3).** On RA2b-lt, **23 widths**, 580 held-out crops:
  byte 4-gram **580/580 = 1.0000**; best self-distilled residual head (L1-mean-mlp256)
  **540/580 = 0.9310**; MiniLM control **578/580 = 0.9966**; both cascade families fell
  monotonically below the stage-1 baseline (`2026-09-16_probe-c-arms.md`, `0095ece`).
- **Probe R (independent matched-input replication, v0.3):** 96-byte crops, matched
  train crop set, 480 held-out: byte **479/480 = 0.9979**, best head **456/480 =
  0.9500**, McNemar **23:0** — same conclusion as the arms under a different split and
  crop length; the two protocols are not pooled (`2026-09-17_probe-r-j.md`, `3108ea7`).
  Gate C is **C-PARTIAL**: the pre-registered P-C1 falsifier (head ≤ byte baseline)
  triggered in both, so the serving-side configuration is no longer open — it is the
  **likelihood scan** (`eval_router`); the head and the cascade are dismissed. A
  stronger head may be re-armed only by new measurement, never by assumption.

## Purpose (the M4 bet)

B proved the mechanism **exists** outside language; C proves the addressing **generalizes**
beyond byte-distinctness. Neither says anything about **scale**: the PoC is planned at
`TBD-K` territories on a model larger than the ~100 M research ladder. Sonde A measures
where the mechanism's cost and accuracy curves bend, so the PoC config is chosen from
measured curves instead of extrapolated hope. If territories stay separable and phase cost
stays near-linear in `K`, the PoC proceeds at full planned scale; if either curve turns
superlinear, A localizes the knee and the PoC scope adjusts **before** spending weeks on
the full pretrain.

## Design

Two axes, each with its own ladder arm; all arms reuse the exact B/C0 protocol
(route-aware α=0.9, grow +32, batch 1, fresh optimizer, F-V9 step-end restore) so every
difference is attributable to scale, never to protocol drift.

**Axis 1 — territory count (`K` sweep, fixed size ≈ 100 M).**
- Arm A1-K5: five domains, identical to Sonde B's set (the known-good anchor; re-running
  it is the protocol-identity check, not a repeat experiment).
- Arm A1-K20: twenty byte-distinct domains — the Europarl-20 set already proven on RA2b,
  **plus** the B/C classes (code/math/legal/ga) so the mix crosses script and register.
  Router config at 20 widths is **fixed to the likelihood scan** (`eval_router`, O(K)
  scans per crop). Arm 3's cascade measured **dead** — monotonic degradation below the
  stage-1 baseline in both pooling families — and is not part of any A arm. The O(K) eval
  cost is still a measured quantity here: at K=40 the scan cost doubles and has never
  been run at that width (see Budget).
- Arm A1-K40: PoC planning value (double the 20; `TBD-K` from the PoC charter if it
  differs). Falsifier-relevant: at +32/phase, block 40 adds 40×32 neurons; at mult 128→256
  the grown block is ~12 % of width — A1 measures whether routing survives that thinning.

**Axis 2 — model size (fixed `K = 20`).**
- Arm A2-W512: as B (n_embd 512, nh 8) — size anchor.
- Arm A2-W1024: n_embd 1024, nh 16 (params ≈ 4×100 M, still far from the PoC target);
  growth stays +32 **per head**, i.e. absolute block bytes double — tests whether
  territory separability is width-neutral.
- **Arm A2-B: DISARMED (v0.3).** Its activation precondition — `TBD-C1` showing the
  residual head dominates — was **falsified** twice (Arms and Probe R, both head < byte
  baseline). Running it would re-train a dismissed object; it stays in the plan as a
  disabled arm, re-armable only by new measurement.

**Per arm (identical instrument suite, same invocation as B/C0):**
- acquisition: best val ppl per phase (teacher-forced; logged, never compared across
  protocols — the B §7 rule);
- territory: P5 in-chain **every** transition (the storage claim must hold at every scale
  step, not be spot-checked);
- routing: `eval_router` full K×K confusion, 200 crops/domain, window 128;
- retention: routed own-width vs own acquisition, deltas reported as measured (B §3.4
  convention — no noise-floor smoothing);
- joint-vs-routed two-axis: every phase-end checkpoint (the serving confounder must stay
  separated at scale);
- **cost telemetry (new, PoC-relevant):** wall-clock + GPU-seconds per phase vs position
  in ladder (slope of growth cost in `K` is the PoC budget's single most important unknown);
  checkpoint bytes per phase (disk projection: the PoC ladder at `TBD-K` × PoC size is
  `TBD-GB`, and .200 `/media/data` currently shows 6.1 T free).

## Pre-registered predictions

- **P-A1 (cost near-linearity):** per-phase GPU-seconds grow sub-quadratically in `K`; at
  `K ≤ 40` and ≈ 100 M, each phase stays ≤ 2× the first phase's cost. Falsifier: superlinear
  rise (masking/restore costs across all prior blocks) → PoC ladder re-planned with
  grouped-growth or wider blocks per step.
- **P-A2 (separability at thinning):** own-prefix routing accuracy stays ≥ 0.95 at `K=20`
  (byte-distinct mix) even when each grown block is ≤ 15 % of width. Falsifier: drops →
  the +32 quantum is scale-bound; growth schedule must widen (e.g. +32→+64 at large mult),
  which feeds back into `TBD-K`.
- **P-A3 (storage size-neutral):** P5 stays bit-exact on all transitions at W1024. A
  failure would be the roadmap's worst-case (masking mechanism itself is size-sensitive);
  expected PASS since F-V9 is structural, but it has never been measured at this size —
  this is the arm's load-bearing gate.
- **P-A4 (retention at length):** the routed retention delta of the **first** phase stays
  within B's noise floor (|Δ| ≤ 0.05 ppl) by `K=20`/`K=40` — length does not erode old
  territories through accumulated float-adjacent drift. Falsifier: monotone widening of
  deltas with ladder depth → PoC needs periodic re-anchor (restore) steps; that mechanism
  exists (F-V9) but its end-to-end cost is PoC budget.
- **P-A5 (addressing scalability, placeholder) — SUPERSEDED (v0.3).** It registered the
  cascade endorsed by `TBD-C-GATE` keeping its accuracy at `K` × sizes, with stage-2
  fraction ≤ `TBD-C3`. That condition was falsified before A ran: Arm 3 measured the
  cascade **dead** (monotonic degradation below the stage-1 baseline, both pooling
  families), so it cannot be endorsed. The registered text is kept verbatim for audit;
  the addressing-scalability question now attaches to the **likelihood scan** (see Design).
  Re-arm this prediction only by new measurement, never by assumption.

## Gates

- **Gate A-PASS:** P-A1 ∧ P-A3 hold (and P-A2/P-A4 within stated tolerances). → The PoC
  proceeds at planned `TBD-K` × target size with the B/C0 protocol unchanged; growth
  quantum +32 stays the default.
- **Gate A-PARTIAL:** storage holds (P-A3) but cost bends (P-A1 fails) or separability
  thins (P-A2 fails). → PoC re-configured from the measured curves: fewer territories per
  growth step, or grouped phases per block, or size kept below the knee. Documented as a
  **design-space boundary**, not a failure of the mechanism.
- **Gate A-FAIL:** P-A3 fails (storage is size-sensitive). → The mechanism does not scale
  as theorised; PoC pivots (re-audit F-V9 masking at depth, or cap PoC size); the
  manuscript records the boundary. This is the one outcome that blocks the PoC outright.

## Budget (draft; final config after C)

- Axis 1: A1-K5 ≈ 13 h (B protocol, same cost); A1-K20 ≈ 2.5–3 days on .200/RTX 4090
  (per-phase cost rise is exactly what A1 measures — the range bounds that unknown); A1-K40
  ≈ +1–2 days, **run only after K20's cost telemetry projects ≤ the PoC window**.
- Axis 2: A2-W512 anchors free (reuses A1-K20 exits); A2-W1024 ≈ 3–5 days (≈4× compute
  per step, eager; 4090 24 GB holds the 400 M model with checkpoint headroom).
- Evals/telemetry: included per phase (≤ 1 h/arm overhead); P5 is CPU-only and
  overlaps the upload/other ladders.
- Hardware: **.200 / RTX 4090 is the primary and sufficient host for A1 (K5, K20) and
  A2-W512.** These arms are router-free for training; per B/C0 they fit the 24 GB card.
  **The gx10 is NOT required to start A1 — the local Qwen3.8-Flash-Next serving on it
  stays up, and no cloud (Deepseek) switch is needed for A1 or A2-W512.** gx10 becomes
  relevant only for **A2-W1024** (~400 M, ~4× per-step compute) as the documented fallback
  if the 4090 VRAM or queue binds; taking gx10 down (stopping Qwen, moving to a cloud
  model) is an operator decision that will be requested **before** that arm launches, not
  assumed. P5 is CPU-only and overlaps other ladders. No cloud, no API cost — all local,
  matching the roadmap constraint (and the review-cost lesson).
- **A1-K40 launch precondition (unmet, must not be skipped):** the K40 mix needs ~20
  byte-distinct corpora beyond Europarl-20 plus the B/C classes. On `.200` the available
  non-Europarl corpora (`textmix`, `textmix2`, `wikitext2`, `tinyshakespeare`) have not
  been audited for count or byte-distinctness against the K20 set. **K40 must not launch
  until that inventory is verified**; the `TBD-C-GATE` removal below does not remove this
  gate.
- **Total: 1–2 working weeks if A1 is gate-clean; A arms can be interleaved with PoC prep.**
- Token note: **FULFILLED (v0.3)** — Sonde C0 is done and read out, and the A1-K20
  serving config is fixed to the likelihood scan. Axis 1 K5/K20 ladders remain
  router-free for training; the routing **eval** config is settled rather than pending.

## Relationship to prior work

Scaling studies (e.g. Kaplan/Rozado-class curves) model loss vs parameters/data; none
models **per-territory growth cost in a masked-expert CL ladder** — the quantity the PoC
budget needs. A contributes that measured curve and its knee location. Positioned as the
roadmap's resource-planning leg; no overlap with B (existence) or C (addressability).

## Non-goals

- No chat phases (their byte-identity is C's subject; A's K20 mix deliberately excludes
  them so a C-FAIL cannot contaminate A's reading).
- No hyperparameter search (cost model uses the fixed B protocol).
- No full PoC pretrain (that is the next gate's consumer).
- No new addressing mechanisms — A **scales** what C's gate endorses, it does not design it.

## Open placeholders (fill after Sonde C Arms 1-3)

**Settled by C0 already (no longer pending):** the hard-cell target set is fixed - the legal leak is byte-geometry-intrinsic (Sonde B 197/200 -> C0 198/200 despite the multilingual base), so A’s `K=20`/`K=40` mixes exercise a base-independent regime. The C0 label table (`out_c/logs/ladC_routdiag_labels.txt`, 999/1000) is the anchor for any head-vs-n-gram comparison.

**Resolved by the measured arms and probes (v0.3):**

- `TBD-C1` = **0.9310 (head) vs 1.0000 (byte baseline)** on the RA2b protocol — head does
  not dominate; falsifier fired, head dismissed (re-armable only by new measurement).
- `TBD-C3` — **moot**: the cascade was never endorsed (measured dead in both pooling
  families), so no stage-2 fraction governs anything.
- `TBD-C-GATE` = **likelihood scan (`eval_router`)** — the only surviving router; A2-B is
  disarmed above.

**Still open (do not block the A1 ladders on these):**

- `TBD-K` — PoC planning territory count (PoC charter).
- `TBD-GB` — PoC ladder checkpoint volume projection (A's own bytes/phase telemetry,
  filled at end of A1-K20).

**Probe context — recorded, explicitly NOT A gates or prerequisites:** R/J/S/P-C4′
(`docs/reports/phase_2/`). J supports a calibrated byte-NLL reject rule for fresh text
(ID 1919/1920; OOD false-accept 0/5 available cells; iu blocked). S records a paraphrase
transfer failure (oracle-reader A 157/512, B 40/512; byte "always-A" was a tie-break under
equal scores, S-PASS false) under its small scratch-model recipe. Neither is a
prerequisite of any A gate; treating them as such re-imports exactly the silent
prerequisite creep this plan prohibits.

— Quinn, @quinn-the-builder, 2026-09-16
