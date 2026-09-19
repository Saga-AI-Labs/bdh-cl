# Sonde D — Semantic-Overlap Addressing Probe (Pre-Registration)

Date: 2026-09-19 · Supervising seat: A0-Quinn (Saga) · Status: PROPOSED, not run, no lease
Operator framing this responds to: *introduce domains with substantially greater semantic
overlap or deliberately ambiguous routing boundaries and see where the capacity-addressing
mechanism starts to fail — so we can think about countermeasures before we start training an
actual model.*

Name note: Sonde A (scaling), B (domain CL), C (embedding-router) are taken; probes S / J / R
are add-on probes. This is a distinct probe and is numbered **D** to keep the roadmap line clean.

---

## 0. What this is and is not

**Is:** a pre-registration for a small controlled probe that turns one sentence the manuscript
already concedes into a measurement. It is read-only on existing checkpoints plus a small
synthetic data build; it takes **no** training of any real target model and reserves **no** GPU
until the operator fires it.

**Is not:** a model, and not a substitute for one. A 100M network with synthetic overlap answers
*"where does my router break"*, not *"where does a real model break".* This distinction is the
point of running it before a model, so it must survive into any reporting.

---

## 1. Why (the argument for doing it at all)

### 1.1 It fills a gap the manuscript itself names (anchors held to lines this pass)

The positive storage result is explicitly scope-bounded in the manuscript, not asserted
unconditionally: *"Storage is exact for the tested growth construction"* (tex:34) and *"We answer at
the bit level for the tested configurations"* (tex:47). The tested configurations are the five
ladder domains `prose / code / math / legal / ga` (the §4b report's own column set), which are
near-disjoint by construction. The manuscript then concedes the open edge in its own words: the
*"untested ``domain'' notion for chat-level continual learning"* (tex:931). So the architecture
claim is bounded to domains that do not compete, and the manuscript says the domain notion beyond
that is untested — never yet stressed on domains that genuinely overlap. That is the
highest-value untested edge, and it is untested **inside the existing regime**, so it is cheap
relative to a model.

> *Provenance note, stated plainly.* An external reviewer (HAk #349) summarised this gap as
> domains that are not *"as cleanly separable as these five".* That phrasing is theirs, not the
> manuscript's — the tex contains no such line. It is used here only as a pointer to the gap the
> tex does state at :34/:47/:931, never as a quoted claim of the paper.

### 1.2 Seed 3 is the wrong next run; this is the right one

A third seed sharpens a noise band around a result already held by two seeds (the report's own
line: *"would mostly sharpen the noise band"*). Overlap tests the architectural hypothesis
itself. The two answers differ: seed 3 widens confidence in "it replicates"; this asks
"what does 'replicates' even mean when domains are not clean".

### 1.3 The reason to probe before a model — three break-domains, three different countermeasures

The addressing mechanism can fail in three structurally different places. Which one fires
**determines which countermeasure is the correct one to build**, and building a real model
without knowing this means picking one of three blind:

| Break-domain | Signature | Correct countermeasure |
|---|---|---|
| **(a) holds entirely** | routing stays correct, P5 `BIT-EXACT`, served own-width ppl constant across the overlap axis | no countermeasure; overlap was never the limiter — the architectural argument simply strengthens |
| **(b) breaks at addressing** | router picks the wrong slice **but** the mis-selected slice is still P5 `BIT-EXACT` (the right data is present, mis-routed) | the problem is **routing**, not storage → Sonde C embedding router / P-C4 two-axis reject |
| **(c) breaks at the storage layer** | overlap changes the parent slice → P5 **no longer** `BIT-EXACT` | the paper's core storage claim does **not** transfer → a genuine risk, not a periphery |

Only (c) threatens the paper's spine. (b) is interesting and survivable. The whole value of a
pre-model probe is to learn **which letter** we are in while the experiment is still cheap, and
(b) versus (c) is decidable **only** by running the two signatures together (§4).

---

## 2. Why the prior evidence (Probe S) does **not** already answer it

This is the most important section, and it corrects my own prior reading. On 2026-09-19 I put
Probe S forward as evidence that the break sits at addressing, citing "agreement ~0.5 = chance".
Opening the committed run (`out_c/probe_s/run-20260917T043829Z/`) shows that reading was too
strong, and the correction is itself the design constraint this probe must obey.

**What the artifacts actually say (verbatim from the run, not from this file's memory):**

| field | value | file |
|---|---|---|
| `acquisition` | `true` | `gates.json` |
| `P_S1` (oracle paraphrase) | **`false`** | `gates.json` |
| `P_S2` (routing falsifier) | `false` | `gates.json` |
| `P_S4` (retention) | `true` | `gates.json` |
| `routing_falsifier` | `false` | `gates.json` |
| `failure_labels` | `[paraphrase_transfer_failure_not_storage_failure]` | `gates.json` |
| `pooled a2_route` / `byte_route` | `0.5` / `0.5` | `gates.json` |
| `test_A oracle` / `a2_route` | `0.3066` / `1.0` | `scores.json` |
| `test_B oracle` / `a2_route` | **`0.0781`** / `0.0` | `scores.json` |
| `train_B a2_exact` vs `test_B oracle` | `0.996` **vs** `0.078` | `scores.json` |
| `functional_check max_abs` vs `atol` | `5.72e-06` < `1e-04`, `prefixes=4` | `functional_check.json` |
| `checks.passed` / `smoke` | `true` / `false` | `checks.json` |

**Reading.** The `0.5` is a **pooled descriptive** over territories A and B; A holds perfectly
(`a2_route=1.0`), B collapses **even under oracle** (`oracle=0.078 < 0.80`). `functional_check`
passing and `checks.smoke=false` say the harness was sound and B's failure is real, not a bug.

**The load-bearing consequence** comes from Probe S's own gate logic (`probe-s-semantic-addressing.md`):
Z.128 — the routing falsifier is prespecified *"ONLY if acquisition and P-S1 pass"*; Z.124-*126* —
if acquisition passes but P-S1 fails, *"label paraphrase transfer failure, NOT storage failure …
not interpreted as an addressing failure despite available recall."* Since `P_S1=false`, the
routing number was **disqualified at the gate**: Probe S never adjudicates addressing. (For B it
did not even have "available recall" — oracle is 0.078.)

**Therefore, and this is the design rule for Sonde D:** a per-domain routing number is
interpretable **only if that same domain passes its own acquisition **and** recall gates first**.
Otherwise the probe reproduces Probe S — a `0.x` that reads like "router broken" and proves
nothing, because the domain cannot answer even when routed correctly. Sonde D is only worth
running if it enforces this per-domain precondition up front, so it does **not** inherit an
inconclusive. My earlier "addressing breaks" lean is withdrawn; the honest prior is **neutral**,
and the probe is what resolves it.

---

## 3. What is measured (the design)

### 3.1 The overlap axis (a knob, not a flag)

Each territory pair is built at a controllable semantic-overlap fraction, stepped
(e.g. **10 / 20 / 40 / 70 / 90 %**) of content that is interchangeable with its neighbour. Binary
"overlap / no overlap" cannot find where it breaks; a swept axis can.

Construction hook already exists: `pipeline/config.py` `text_mix` = comma-separated
`"name:path"` byte-corpus pairs, `text_mix_mb` default 30. Synthetic corpora are dropped in as
`name:path` pairs with no pipeline change.

### 3.2 The dissociation cells — the actual payload

The two cells that carry information are the crossed ones, because the byte / likelihood router
(82 % two-byte; the manuscript's own *"no linguistic reading is required"*) is structurally blind
to exactly one of the two overlap types:

| cell | surface (bytes) | meaning | what it isolates |
|---|---|---|---|
| **D1** | **different** | **high overlap** | can a byte-invisible meaning collision still be addressed? (likelihood-router stress) |
| **D2** | **high overlap** | **different** meaning | is the router fooled by shared surface where meaning differs? (the byte-router's known weakness, quantified) |

Plain same-both cells are controls, not results.

### 3.3 The dual signature (this is what decides (b) vs (c))

Measured on the **same** ladder, together — neither alone is decidable:

1. **Addressing signature** — `eval_router` routed own-width ppl + `--oracle-routes name:width`.
   The a2-vs-oracle gap is precisely the Probe-S B-diagnostic: it separates "mis-routed" from
   "cannot recall even if routed".
2. **Storage signature** — `scripts/p5_inchain_check.py`: `encoder`, `encoder_v`, `decoder`,
   `attn.freqs` `BIT-EXACT` over `W = mult*64`, `core = all(encoder, encoder_v, decoder)`.

Decision: a2 route degrades **with** P5 still `BIT-EXACT` → **(b)**. a2 route degrades **with**
P5 no longer `BIT-EXACT` → **(c)**. Both hold across the axis → **(a)**.

---

## 4. How it is measured (instrument, discipline, freeze)

- **Instrument:** `scripts/eval_router.py` (`--routes … --domains name:path --window 128 --crops
  200 --batch 4`) with `--oracle-routes name:width,…` to emit the oracle served-ppl arm. Flags
  copied verbatim from the committed ladder's own routing call, as §4b did, so the measured plane
  is the plane the ladder reports.
- **Storage verifier:** `p5_inchain_check.py` at each phase exit, same call shape that produced
  the seed-2 `BIT-EXACT` lines.
- **Held-out discipline (inherited, load-bearing):** `data.py::_europarl_blocks` holds the last
  2 MB of each stream (1 val + 1 test) **before** the train cap. Synthetic overlap corpora must
  copy that: probe crops never appear in any training stream, or the addressing number is void.
- **Gate-first ordering:** build corpora → **selftest** (a tiny end-to-end pass) → **smoke** run →
  then the full axis. (Note: the Probe-R selftest needs `import torch`; the container has no
  torch, so selftest/smoke execute on the GPU host at run-time, not in this plan check.)
- **Freeze + provenance, on the Probe-S pattern:** record `freeze.json` + `source_hashes`
  (`bdh.py`, `pipeline/*.py`, `scripts/eval_router.py`, the synthetic generator, this plan),
  a `functional_check.json` (rtol/atol, prefixes), `gates.json` per domain, `status.txt` /
  `exit_status.txt`. `checks.passed=true`, `smoke=false` gate any scientific claim.
- **Countermeasures run alongside, on the same ladder** (so the break is not walked twice):
  Sonde-C-style embedding router (Arm 2 external upper bound, P-C2 ≥0.95 target) and the P-C4
  two-axis reject (`accept iff ratio ≥ τ_rel AND within band`; τ_rel = min over trained languages;
  direction trained ≈ 5.7×, byte-near-unseen ≈ 1). A countermeasure earns its place only if it
  **moves the break-point up** the overlap axis relative to the byte/likelihood baseline.

---

## 5. Decision rules and what each verdict licenses

- **(a)** — *S-D holds:* addressing + recall correct **and** P5 `BIT-EXACT` across the axis.
  Licenses: overlap was never the binding constraint; strengthens the architecture claim. Does not
  license: scaling, real-corpus, or "no forgetting" as a bound.
- **(b)** — *addressing-bound:* recall available (oracle would be good) but a2 routes wrong,
  P5 intact. Licenses: the fix is in the router, storage is exonerated; motivates C / C4.
- **(c)** — *storage-risk:* recall available but the overlap phase perturbs the parent, P5 not
  bit-exact. Licenses nothing soft — this is a result that must reach the paper as a scope limit
  on the storage claim.
- **Inconclusive** (the Probe-S outcome): any domain whose own acquisition or recall gate fails.
  Reported as **data**, labelled by which gate failed, **never** re-read as an addressing result.

All failures are results, not retry triggers.

---

## 6. Known limits (stated so the probe is not over-asked)

- 100M, synthetic overlap. Answers "where does **my** router break", not "where does a real model
  break". It is a scout, and should be read as one.
- The likelihood router is the one under test; this is not evidence about a future learned
  embedding router's ceiling — Sonde C Arm 2 (external bound) is the separate question.
- A single overlap scalar; adversarial or graded-ambiguity beyond one fraction is a later axis.
- Cross-seed: the point here is the break-**point**, not variance, so this runs on one seed and
  does **not** pre-empt the seed-3 decision (which stands at *no*).

---

## 7. Boundary of this document

No GPU is claimed or reserved for this plan. Nothing is launched; the card stays as it is; seed 3
stays unlaunched per operator. This is the map, not the run. On operator GO it becomes a frozen
run (freeze + gates + `functional_check`) executed serially and read-only on checkpoints, and
the pre-registration above is the version that gets frozen before the first crop is seen.

*Sources for the Probe-S numbers above, verbatim from this pass: `out_c/probe_s/run-20260917T043829Z/gates.json`,
`scores.json`, `functional_check.json`, `checks.json`; gate logic from
`docs/plans/2026-09-17_probe-s-semantic-addressing.md` Z.23, Z.119, Z.123–135; countermeasure forms
from `docs/plans/2026-09-11_sondeC-embedding-router-probe.md` and
`docs/plans/2026-09-17_pc4-ood-reject-prereg.md`; instruments `scripts/eval_router.py`,
`scripts/p5_inchain_check.py`, corpus hook `pipeline/config.py::text_mix`. The operator-facing
claim "Probe S showed addressing breaks", made by me on 2026-09-19 before opening these files,
is retracted here and superseded by §2.*
