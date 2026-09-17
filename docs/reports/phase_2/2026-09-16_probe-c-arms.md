# Sonde C — Arms 1–3 Results (Embedding-Router Probe)

Status: **RA2B-LT MEASURED · GATE C-PARTIAL (P-C1 FALSIFIER TRIGGERED FOR TESTED PROTOCOL; P-C2 PASS; P-C4′ REJECT FAILS) · 2026-09-16, updated 2026-09-17 · Quinn**
Host: `.200` (RTX 4090). Pre-registered plan: `docs/plans/2026-09-11_sondeC-embedding-router-probe.md`.
Script: `scripts/quinn/c_arms.py` (modes `extract`, `fit`, `arm2`; the `--crop-source tail|r3` patch was committed with the RA2b-lt update).
Models: C0 `out/bdh_textmix_ladC-ga_last.pt` (multilingual base, mult 256, 5 territories);
RA2b-lt `out/bdh_europarl_ladRA2b-lt_last.pt` (20 Europarl territories — the P-R3 hard-cell set).

Update (2026-09-17): the RA2b-lt hard-cell run has been measured; the earlier
"decisive run pending" framing is retired. Historical C0 numbers (§2) are
preserved unchanged. Two prior causal claims are retracted (§5). No new
experiments were launched for that reporting update; the historical report,
the `--crop-source` patch, and the RA2b-lt artifacts were committed together.

Update 2 (2026-09-17, later): P-C4′ — the separately pre-registered OOD reject
probe (`docs/plans/2026-09-17_pc4-ood-reject-prereg.md`, amended commit
3b7d24a) — has been measured on the RA2b-lt byte-4-gram router. The two-axis
reject accepts all six unseen-language domains based on their means; the agreement
prediction fails (Annex A). The original cascade-shaped P-C4 remains **NOT RUN**;
P-C4′ tests a different object and neither replaces nor closes that clause.
This report update and the new P-C4′ runner/artifacts are not yet committed.

## 1. What was run

The A2 protocol supplies route targets by argmin NLL over candidate widths on
each probe's own final checkpoint; it does not supply all supervision. The exact
byte-4-gram baseline is fit to domain classes, then mapped to modal A2 routes.
Both `c_arms.cmd_fit` and `pc4_ood.py` derive that map from all labels in each
domain, including held-out labels: this is not a strictly train-only or wholly
label-free baseline. C0 tail crops use seed 1234, shared with `eval_router.py`;
RA2b-lt `r3` crops use per-language seeds 5000 + sequence index. Per-crop identity
across the historical generators was not cryptographically verified (see §7).

| run | what | artifact / log (on `.200`) |
|---|---|---|
| C0 `extract` | 5 domains × 200 crops = **1000 crops**; A2 labels + pooled residuals (post-layer 0/1, positions 32–96) + raw crop bytes | `out_c/c_arms_ladC.npz`, `.labels.tsv` |
| C0 `fit` / `arm2` | Arm 1 heads (linear + MLP-256), byte-n-gram baseline, cascade; MiniLM control | `out_c/logs/c_arms_{fit,arm2}.log` |
| RA2b-lt `extract` | 20 domains × 96 crops = **1920 crops**; **23 routes** (2048…47104, step 2048); layers 0/1 pooled positions 32:96 | `out_c/c_arms_ra2b_r3.npz` |
| RA2b-lt baselines | hashed byte 1–4-gram (NB=262144, 200 epochs, lr 0.5) and exact byte 4-gram | `/media/data/coding/bdh/out_c/logs/c_arms_ra2b_r3_pr3.log`, `…_fit.log` |
| RA2b-lt `fit` / `arm2` | Arm 1 heads (L0/L1 linear + MLP-256); MiniLM control | `out_c/logs/c_arms_ra2b_r3_{fit,arm2}.log` |

Splits: per-domain 70/30 → C0 **700/300**, RA2b-lt **1340 train / 580 held-out**
(20 × 96 crops). All intervals are Wilson 95 %, descriptive and crop-level.

### 1.1 C0 A2 label table (historical)

| domain | routed width | n |
|---|---|---|
| code | 10240 | 200/200 |
| math | 12288 | 200/200 |
| legal | 14336 | 199/200 (1 → prose's 8192) |
| ga | 16384 | 200/200 |
| prose | 8192 | 200/200 |

The label table reproduces `eval_router`'s confusion matrix exactly (999/1000) —
instrument congruence, not a hash-level identity claim (see §7).

## 2. C0 results (historical, held-out 300 crops)

| arm | accuracy | Wilson 95 % |
|---|---|---|
| **byte-n-gram** (stage 1, 4-gram, add-1) | **296/300 = 0.9867** | [0.966, 0.995] |
| Arm 1, L0 linear | 266/300 = 0.8867 | [0.846, 0.918] |
| Arm 1, L0 MLP-256 | 262/300 = 0.8733 | [0.831, 0.906] |
| Arm 1, L1 linear | 271/300 = 0.9033 | [0.865, 0.932] |
| **Arm 1, L1 MLP-256** | **280/300 = 0.9333** | [0.899, 0.956] |
| Arm 2, MiniLM linear | 295/300 = 0.9833 | [0.962, 0.993] |
| **Arm 2, MiniLM + MLP-256** | **298/300 = 0.9933** | [0.976, 0.998] |

### 2.1 Per-domain breakdown (C0)

| domain | n-gram | Arm1 L1 MLP | Arm2 MLP |
|---|---|---|---|
| code | 57/60 | 58/60 | 58/60 |
| math | 59/60 | 52/60 | 60/60 |
| legal | 60/60 | 53/60 | 60/60 |
| ga | 60/60 | 60/60 | 60/60 |
| prose | 60/60 | 57/60 | 60/60 |

### 2.2 C0 cascade (stage 1 = n-gram, stage 2 = Arm 1 L1 linear)

| stage-2 fraction | used | cascade acc | Wilson 95 % |
|---|---|---|---|
| 0.0 (pure stage 1) | 0/300 | 296/300 = 0.9867 | [0.966, 0.995] |
| 0.1 | 30/300 | 287/300 = 0.9567 | [0.927, 0.975] |
| 0.2 | 60/300 | 284/300 = 0.9467 | [0.915, 0.967] |
| 0.3 | 90/300 | 282/300 = 0.9400 | [0.907, 0.962] |

On C0, adding the residual stage 2 made the cascade worse, monotonically; the
stage-1 n-gram already solved every cell of that set.

## 3. RA2b-lt results (the P-R3 hard-cell set)

### 3.1 Byte-n-gram baselines — corrected run

The first `pr3` invocation silently loaded a hardcoded OLD npz; the corrected
argv rerun is the result of record.

| baseline | held-out accuracy | Wilson 95 % |
|---|---|---|
| exact byte 4-gram | **580/580 = 1.000** | — |
| hashed byte 1–4-gram (NB=262144, 200 epochs, lr 0.5) | **574/580 = 0.9897** | [0.9776, 0.9953] |

Per-domain (hashed baseline): 29/29 on all 20 domains except **sk 23/29**. The
es/pl/sk-class failures that motivated this probe are solved by the byte
baseline at this sample size and split. Note: an earlier tail-source-NPZ
baseline (577/580 = 0.9948) is a distinct run, **not** this result.

### 3.2 Arm 1 — self-distilled residual heads

| head | held-out accuracy | Wilson 95 % |
|---|---|---|
| L0 linear | 524/580 = 0.9034 | — |
| L0 MLP-256 | 0.8810 | — |
| L1 linear | 0.9276 | — |
| **L1 MLP-256** | **540/580 = 0.9310** | [0.907, 0.949] |

Per-domain L1 MLP (of 29): bg 29, cs 25, da 27, de 26, el 29, en 27, **es 24**,
et 26, fi 26, fr 27, hu 29, it 24, lt 28, nl 29, **pl 29**, pt 26, ro 28,
**sk 25**, sl 29, sv 27. Hard cells: es 0.83, pl 1.00, sk 0.86 — all above the
preregistered 0.60 floor.

### 3.3 Arm 2 — MiniLM control

MiniLM and MiniLM+MLP both **578/580 = 0.9966**, Wilson [0.988, 0.999].

### 3.4 Arm 3 — cascade (log-verified)

Stage 2 is the Arm 1 L0 or L1 head behind the n-gram stage 1; fractions refer
to the 580 held-out crops. All numbers verified directly against
`docs/data/phase2-sondeC-ra2b-fit.log` (committed with this report).

| stage-2 head | fraction | used | cascade acc |
|---|---|---|---|
| L0 | 0.10 | 58/580 | 569/580 = 0.9810 |
| L0 | 0.20 | 116/580 | 562/580 = 0.9690 |
| L0 | 0.30 | 174/580 | 556/580 = 0.9586 |
| L1 | 0.10 | 58/580 | 572/580 = 0.9862 |
| L1 | 0.20 | 116/580 | 562/580 = 0.9690 |
| L1 | 0.30 | 174/580 | 559/580 = 0.9638 |

An earlier working summary reported "L1 → 0.9586 at 30 %"; the verified log
shows 0.9586 is the **L0** endpoint, while L1 ends at 0.9638. Either way the
cascade stays below pure stage 1 (exact 4-gram 1.000, hashed 1–4-gram 0.9897)
at every tested fraction: stage 2 adds no incremental utility in this regime.

## 4. C0 interpretation: a cell-distinctness ceiling (historical)

On the C0 domain set — all five domains byte-distinct, by design — the byte
n-gram stage 1 was already at 0.9867, leaving ~4 crops of headroom that the
residual head could not reach. That was evidence that the C0 test set could not
discriminate, not that the residual head fails at its job. The RA2b-lt set was
the discriminating test — and there too the byte baseline is at ceiling (§3.1),
so the C0 conclusion transfers: the limitation is not the lack of a hard-cell
set anymore; the head simply does not beat byte statistics on this task.

The reported L1 MLP outperforms L0 linear on both sets (C0 0.9333 vs
0.8867; RA2b-lt 0.9310 vs 0.9034, comparing L1 MLP with L0 linear), and MLP
beats linear at L1. These are readout comparisons, not an isolated depth effect
or evidence that the architecture lacks routing information.

**Unequal information budgets.** The byte baseline scores whole 512-byte crops.
`c_arms.py` uses checkpoint `block_size` for extraction; the completed P-C4′
runner enforces 512 bytes for the same RA2b-lt checkpoint. The residual head
receives pooled positions `32:96`; A2 scores only loss positions `:128` (also
the recorded P-C4′ window), although model forwards receive the whole crop.
Pooling positions are not a direct count of accessible input bytes. These
budgets and supervision differ, so the measured gap cannot establish an
architecture-level lack of information. A matched-information diagnosis is
approved, not yet run (§8).

## 5. Retractions

### 5.1 Crop-source claim (RETRACTED)

`out_c/logs/r3_original.log` independently reproduces the original P-R3
number: **0.762**, Wilson [0.659, 0.842], n=80 (16 crops/domain, global 75/25
split; es/pl/sk 0.00, et 0.67). The reproduction stands as a measurement of
that configuration. However, that configuration differs from the current one in
sample count (16 vs 96 per domain), split (global vs per-domain stratified),
and originally crop source — simultaneously. **No valid causal isolation
exists; the prior claim that crop source alone explains the 0.762 → ~0.99 gap
is RETRACTED.**

### 5.2 Inline density replicas 0.738 / 0.750 (RETRACTED as evidence)

Both replicas are excluded as causal or reproduction evidence. The first
misaligned labels and features (`y[tr]`/`y[te]` against `raw[idx]` instead of
`Y = y[idx]`). The second fixed the labels but still scored its per-domain
table against `dom[te]` instead of `dom[idx][te]`; that domain table is
invalid, and the 0.750 total was never validated as an exact reproduction. No
claim is made that the 0.750 aggregate is necessarily wrong — it is simply not
evidence.

## 6. Pre-registered verdicts

| prediction | verdict | reasoning |
|---|---|---|
| **P-C1** head > byte-n-gram; ≥0.90 overall, hard cells ≥0.60 | **FALSIFIER TRIGGERED (tested head/protocol)** | Absolute floors met: L1 MLP 0.9310 ≥ 0.90; es 24/29, pl 29/29, sk 25/29 all ≥ 0.60. But the prereg falsifier — head ≤ byte-n-gram — fired: 0.9310 vs 0.9897 (hashed 1–4-gram) / 1.000 (exact 4-gram) on the identical split. Scoped to shallow layers 0/1, pooled positions 32:96, and this fitting protocol; deeper heads untested. |
| **P-C2** external bound ≥0.95 | **PASS** | 0.9966 [0.988, 0.999] on RA2b-lt (0.9933 on C0). Foreign-competence control, not an own-AI candidate and not a mathematical upper bound; serving it would require an explicit operator change to the own-AI constraint. |
| **P-C3** cascade ≥ Arm 1 at ≤30 % stage 2 | formally met, no utility | Log-verified: at 10/20/30 % stage 2, L0 = 0.9810/0.9690/0.9586 and L1 = 0.9862/0.9690/0.9638 — all above Arm 1 (0.9310) but below pure stage 1 (exact 4-gram 1.000, hashed 0.9897). No incremental utility; not a deployment candidate. |
| **P-C4** original cascade OOD consistency | **NOT RUN** | Original clause: cascade routes agree with the likelihood router at ≥ the P-R3 level, and the two-axis reject still separates without false in-support confidence from the head. P-C4′ does not test this clause. |
| **P-C4′** OOD reject (byte router) | **FAIL** | Measured 2026-09-17 (Annex A): all six unseen-language domain means pass both reject axes; overall agreement with A2 is 104/576 = 0.1805556 [0.151, 0.214]. Verdict on the frozen construction, not on byte routing in general. |

**Gate C: C-PARTIAL**, per the plan's P-C1-fail / P-C2-pass mapping — the
address exists in representation space, but the tested self-distilled head does
not beat the cheap byte baseline. Scope: provisional, valid for the measured
in-distribution regime only; not serving-ready, not OOD-validated.

With P-C4′ now measured (Annex A), the pre-registered byte reject rule fails
OOD separation for the byte router as constructed. This does not retroactively
alter the original cascade-OOD preregistration.

## 7. What these results do not show

- **Legal depth.** Agreement with the A2 teacher cannot demonstrate that the
  teacher's legal-depth leakage is corrected. C0's legal label table (199/200
  routed to own width) and the legal-depth instrument (198/200) are different
  measurements. No demonstrated legal fix exists. Legal-depth choice, novelty
  detection, and same-language, same-style semantic memory retrieval are three
  distinct tasks; success on one does not establish either of the others.
- **Checkpoint depth.** Original checkpoint depth is not established here.
  The earlier `getattr` lookup on a dictionary returned `None`, which establishes
  neither six nor four layers. Readout layer indices 0/1 do not establish total
  checkpoint depth.
- **P-C4′ scope (Annex A).** The OOD run tests the byte reject rule as
  pre-registered. Agreement is measured against the A2 teacher — an instrument
  comparison, not ground truth — and the six unseen-language domains are now
  development data; any reject recalibration must use fresh held-out material.
- **Crop identity.** Generator/label concordance (999/1000 on C0) is instrument
  congruence, not cryptographic per-crop byte equality; "independently
  hash-verified" crop identity is not claimed.
- **Statistics.** Wilson intervals are descriptive and crop-level; crop
  overlap/document leakage was not audited; model selection used the same test
  split without correction; no paired significance tests; no latency
  measurements.
- **Operations.** No OOM in the completed fitting runs (an earlier
  extract-time batch-4 OOM was fixed with batch 1). No HF archival of active
  files is required.

## 8. Options and stopping criteria

### 8.1 How to use these results

- **Gate C-PARTIAL is scoped:** it rests on the tested P-C1 falsifier
  (triggered for shallow layers 0/1, pooled positions 32:96, this fitting
  protocol) plus P-C2 PASS, with the P-C4′ reject rule now measured and failing
  (Annex A). It is a verdict about
  the measured regime — not serving-ready and not OOD-validated.
- **The byte baseline is a candidate, not a validated deployment.** It is the
  best current in-distribution option; production validation is separate work.
- **No residual-cascade deployment.** Stage 2 adds no incremental utility at
  any tested fraction (§3.4).
- **MiniLM is a foreign-competence control only.** Serving it requires a new,
  explicit own-AI decision by the operator; it is also not a mathematical
  upper bound.
- **Agreement with the A2 teacher is NOT a Legal-leak fix** (see §7).
- **Document the errors and retractions (§5) rather than declaring the
  published 0.762 wrong:** it is reproduced as measured under its own
  configuration; what is retracted is causal attribution and the invalid
  inline replicas, not the original measurement itself.
- **Any new protocol — deeper heads, OOD tests, serving work — only after a
  fresh operator GO and a new preregistration.** The operator has now explicitly
  approved the three follow-ups below; their approval is not pending.

Preference order:

1. **Keep the byte baseline as the current in-distribution operational
   candidate** (exact 4-gram primary, hashed 1–4-gram fallback), with the A2
   likelihood router as reference/fallback — the latter is not validated for
   production.
2. **Do not deploy the cascade** — dominated by stage 1 in the measured regime.
3. **Do not adopt MiniLM for serving** — foreign competence; requires an
   explicit operator decision against the own-AI constraint.
4. **Preserve artifacts locally** (`out_c/*.npz` and logs on `.200`; C0
   fit/arm2 logs committed under `docs/data/`).
5. **Optional, only on new operator GO:** a separately pre-registered
   broader head search beyond the approved diagnosis. No unregistered hunting.

Stopping criteria — stop head-hunting while (a) the byte baseline is at or near
ceiling in-distribution and (b) no serving requirement fails under it. P-C4′
has now exposed a reject failure; semantic memory retrieval remains untested.
This motivates the approved targeted work, not open-ended head hunting.

### 8.2 Approved follow-ups — planned, NOT STARTED

Operator approval recorded 2026-09-17 covers:

1. **Matched-information readout diagnosis:** align byte/head/teacher input
   budgets and train-only supervision, then distinguish pooling/readout limits
   from information not demonstrated by this protocol. Verify checkpoint depth
   from valid configuration evidence rather than assuming it.
2. **New held-out reject calibration:** design and preregister a new reject
   construction with separate calibration and untouched evaluation material.
   The six measured OOD domains are development data, not a new test set.
3. **Controlled same-language semantic addressing:** compare oracle, A2, and
   byte routing on same-style memory retrieval with controlled lexical cues;
   score retrieval separately from teacher agreement, novelty, and legal-depth
   choice.

Implementation follows completion of this report review; no follow-up has
started. Freeze each measurement protocol before scoring. These follow-ups are
not prerequisites for Sonde A mechanics, and their approval
does not authorize deployment or unrestricted head searches.

## 9. Plan reconciliation (Arms portion)

| plan item | status |
|---|---|
| Arm 1 self-distilled head | measured on C0 (0.9333) and RA2b-lt (L1 MLP 0.9310); P-C1 falsifier triggered for tested protocol |
| Arm 2 external embedding control | done on both sets (0.9933 / 0.9966); foreign-competence control |
| Arm 3 byte-n-gram + residual cascade | done; below pure stage 1 at every tested fraction on both sets (RA2b numbers log-verified, §3.4) |
| P-C1 | FAIL for tested head/protocol (falsifier); absolute floors met |
| P-C2 | PASS |
| P-C3 | formally met; no incremental utility |
| P-C4 | NOT RUN (original cascade clause; not replaced by P-C4′) |
| P-C4′ | FAIL (separate byte-reject construction; Annex A) |
| Gate C verdict | **C-PARTIAL** (provisional, measured regime) |

## 10. Provenance

- **Script:** `scripts/quinn/c_arms.py` (modes `extract`, `fit`, `arm2`). The `--crop-source tail|r3` patch was committed with the RA2b-lt update.
- **C0 raw (committed):** `docs/data/phase2-sondeC-fit.json`, `docs/data/phase2-sondeC-arms-fit.log`, `docs/data/phase2-sondeC-arms-arm2.log`, `docs/data/phase2-sondeC-labels.tsv` (1000 rows).
- **RA2b-lt supporting artifacts (committed under `docs/data/`):** `phase2-sondeC-ra2b-fit.log`, `phase2-sondeC-ra2b-arm2.log`, `phase2-sondeC-ra2b-pr3.log`, `phase2-sondeC-ra2b-fit.json`, `phase2-sondeC-ra2b-pr3.json`.
- **On `.200`:** `out_c/c_arms_ladC.npz`, `out_c/c_arms_ra2b_r3.npz`; logs `/media/data/coding/bdh/out_c/logs/c_arms_ra2b_r3_{pr3,fit,arm2}.log`, `out_c/logs/r3_original.log`, plus the C0 `c_arms_{extract,fit,arm2,st_install}.log` set.
- **Environment:** sentence-transformers 6.0.1 in the repo venv, CUDA available; `all-MiniLM-L6-v2` (384-dim).
- **No new experiments were launched** for the Arms update; P-C4′ was a
  separate, separately pre-registered run (2026-09-17). All RA2b-lt numbers
  above are backed by the committed logs; all P-C4′ numbers by
  `docs/data/phase2-pc4-ood.json` and its log.
- **P-C4′ artifacts and runner (local, untracked):** `docs/data/phase2-pc4-ood.json`,
  `docs/data/phase2-pc4-ood.log`; script `scripts/quinn/pc4_ood.py` (sha256
  06cc7c06f5befbeda007f89eca0567d18d598b2aa3c8abe803de6c0312d320bf, identical
  local and deployed on `.200`); prereg
  `docs/plans/2026-09-17_pc4-ood-reject-prereg.md` (amended 3b7d24a); raw
  copies on `.200` at `out_c/pc4_ood.json` and `out_c/logs/pc4_ood.log`.

— Quinn, @quinn-the-builder, 2026-09-16 (updated 2026-09-17)

## Annex A: P-C4′ OOD reject — measurement record (2026-09-17)

**Prereg:** `docs/plans/2026-09-17_pc4-ood-reject-prereg.md` (amended commit
3b7d24a: relative axis re-specified as pooled-vs-best byte-4-gram NLL ratio;
τ_rel calibrated on trained languages; absolute band = 10× worst trained
mean). **Script:** `scripts/quinn/pc4_ood.py` (sha256
06cc7c06f5befbeda007f89eca0567d18d598b2aa3c8abe803de6c0312d320bf, identical
local and deployed on `.200`). **Router:** the RA2b-lt byte-4-gram router from
§3 — domain-class models with modal A2 route mapping, not an exclusively
label-free fit (recorded in the artifact).

**Registered input deviation (recorded before scoring):** the `iu` domain uses
the clean syllabic artifact `xscript_iu_syl.txt`, not the contaminated
`xscript_iu.txt` (Stage-A V6 erratum, 2026-09-11).

**Calibration (trained languages, held-out crops):** τ_rel = 0.8139 (weakest
trained: es); absolute band = 37.93 NLL/byte (10× worst trained cs, mean best
NLL 3.79). This multiplies NLL, not perplexity: for natural-log NLL, a 10×
perplexity allowance would add ln(10), not multiply NLL by 10.

**Decision unit:** language/domain means determine the registered verdict;
all 20 trained and all six OOD domain means pass both axes. Separately,
recalculation from the saved per-crop arrays confirms 96/96 individual crops
pass both thresholds in each OOD domain (576/576 total). This descriptive
crop-level count is not the definition of the domain-level decision.

| OOD domain | mean ratio | mean best NLL/byte | rel accept | abs accept | A2 agreement |
|---|---|---|---|---|---|
| lv | 0.877 | 4.947 | yes | yes | 96/96 = 1.000 |
| ga | 0.862 | 5.227 | yes | yes | 1/96 = 0.010 |
| zh | 0.998 | 5.500 | yes | yes | 0/96 = 0.000 |
| ja | 1.000 | 5.513 | yes | yes | 0/96 = 0.000 |
| hi | 1.000 | 5.512 | yes | yes | 1/96 = 0.010 |
| iu | 0.997 | 5.500 | yes | yes | 6/96 = 0.062 |

**Verdicts (as recorded in `docs/data/phase2-pc4-ood.json`):**

- **P-C4′-1 FAIL:** overall byte-vs-A2 agreement on unseen-language crops
  104/576 = 0.1805556 (Wilson [0.151, 0.214]).
- **P-C4′-2 FAIL:** the two-axis reject separates unseen from trained on
  neither axis — all six OOD domain means pass rel and abs.
- **P-C4′-3 (descriptive) TRUE:** the ratio axis alone admits all
  cross-script domain means. This is not a reject success or causal validation.

**Interpretation scope.** This is a verdict about the tested reject
construction, not about byte routing in general. Agreement with the A2 teacher
is an instrument comparison, not ground truth; a divergent route on unseen
input is not by itself a semantic error. A mechanism consistent with the
numbers is that unseen 4-grams/contexts yield similar smoothed class scores.
Their unseen fraction and causal contribution were not measured. The observed
cross-script pooled/best ratios cluster near 1, above τ_rel = 0.814; the
absolute band (37.93) is ~6.9× the highest OOD mean NLL (5.51). These are
descriptive observations, not an isolated mechanism. No post-hoc threshold
tuning was performed; any fix belongs to a fresh
pre-registered recalibration probe with new held-out material, since these six
domains are now development data.
