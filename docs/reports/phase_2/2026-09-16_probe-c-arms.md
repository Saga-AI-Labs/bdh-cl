# Sonde C — Arms 1–3 Results (Embedding-Router Probe)

Status: **ARMS 1–3 MEASURED ON C0 MODEL · DECISIVE HARD-CELL RUN PENDING** · 2026-09-16 · Quinn
Host: `.200` (RTX 4090). Pre-registered plan: `docs/plans/2026-09-11_sondeC-embedding-router-probe.md`.
Script: `scripts/quinn/c_arms.py` (modes `extract`, `fit`, `arm2`).
Model: `out/bdh_textmix_ladC-ga_last.pt` (C0 multilingual base, mult 256, 5 territories).

## 1. What was run

The label-free A2 protocol supplies all labels: the argmin-NLL route over the five
candidate widths `[8192, 10240, 12288, 14336, 16384]`, computed on the C0 final
checkpoint, on crops **byte-identical to `eval_router.py`** (shared generator seed 1234).

| stage | what | artifact |
|---|---|---|
| `extract` | 5 domains × 200 crops = **1000 crops**; A2 labels + pooled residuals (post-layer 0 and 1, positions 32–96) + raw crop bytes | `out_c/c_arms_ladC.npz`, `.labels.tsv` (1000 rows) |
| `fit` | Arm 1 heads (linear + MLP-256) at layers 0/1; byte-n-gram stage-1 baseline; cascade sweep | `out_c/c_arms_ladC.npz.fit.json` |
| `arm2` | MiniLM sentence embeddings, same fit protocol | `out_c/logs/c_arms_arm2.log` |

Split: per-domain 70/30 → **700 train / 300 held-out test crops**. All intervals are
Wilson 95 %.

### 1.1 A2 label table (the ground truth for every arm)

| domain | routed width | n |
|---|---|---|
| code | 10240 | 200/200 |
| math | 12288 | 200/200 |
| legal | 14336 | 199/200 (1 → prose's 8192) |
| ga | 16384 | 200/200 |
| prose | 8192 | 200/200 |

The label table reproduces `eval_router`'s confusion matrix exactly (999/1000) — the
extraction is instrument-congruent, not a re-implementation drift.

## 2. Results (held-out 300 crops)

| arm | accuracy | Wilson 95 % |
|---|---|---|
| **byte-n-gram** (stage 1, 4-gram, add-1) | **296/300 = 0.9867** | [0.966, 0.995] |
| Arm 1, L0 linear | 266/300 = 0.8867 | [0.846, 0.918] |
| Arm 1, L0 MLP-256 | 262/300 = 0.8733 | [0.831, 0.906] |
| Arm 1, L1 linear | 271/300 = 0.9033 | [0.865, 0.932] |
| **Arm 1, L1 MLP-256** | **280/300 = 0.9333** | [0.899, 0.956] |
| Arm 2, MiniLM linear | 295/300 = 0.9833 | [0.962, 0.993] |
| **Arm 2, MiniLM + MLP-256** | **298/300 = 0.9933** | [0.976, 0.998] |

### 2.1 Per-domain breakdown

| domain | n-gram | Arm1 L1 MLP | Arm2 MLP |
|---|---|---|---|
| code | 57/60 | 58/60 | 58/60 |
| math | 59/60 | 52/60 | 60/60 |
| legal | 60/60 | 53/60 | 60/60 |
| ga | 60/60 | 60/60 | 60/60 |
| prose | 60/60 | 57/60 | 60/60 |

### 2.2 Arm 3 — cascade (stage 1 = n-gram, stage 2 = Arm 1 L1 linear head)

| stage-2 fraction | used | cascade acc | Wilson 95 % |
|---|---|---|---|
| 0.0 (pure stage 1) | 0/300 | 296/300 = 0.9867 | [0.966, 0.995] |
| 0.1 | 30/300 | 287/300 = 0.9567 | [0.927, 0.975] |
| 0.2 | 60/300 | 284/300 = 0.9467 | [0.915, 0.967] |
| 0.3 | 90/300 | 282/300 = 0.9400 | [0.907, 0.962] |

**Adding the residual stage 2 makes the cascade worse, monotonically, on this set**
(0.9867 → 0.9567 → 0.9467 → 0.9400). The stage-1 n-gram already solves every cell here.

## 3. Pre-registered verdicts

| prediction | verdict | reasoning |
|---|---|---|
| **P-C1** head beats 0.762, rescues es/pl/sk; ≥0.90 overall, hard cells ≥0.60 | **UNDECIDED on the decisive cells** | Arm 1 L1 MLP reaches 0.9333 ≥ 0.90 → the *overall* threshold holds. But it does **not** beat the byte-n-gram baseline (0.9867) on this set, and the set contains **no non-distinct (es/pl/sk-class) cells** — the exact cells P-C1 names. The prediction is therefore **untested where it matters**, not failed. |
| **P-C2** external bound ≥0.95 | **PASS** | MiniLM 0.9833, +MLP 0.9933 — the embedding space clearly contains the address. The external upper bound is high, as predicted. |
| **P-C3** cascade ≥ Arm 1 with ≤30 % stage 2 | **PASS (formally)** | Cascade at 10 % stage 2 (0.9567) ≥ Arm 1 best (0.9333) with 10 % ≤ 30 %. **Caveat:** it is still *below* pure stage 1 (0.9867) — the cascade economy passes only against Arm 1, not against the n-gram baseline. |
| **P-C4** OOD consistency vs likelihood router | **NOT RUN** | Needs the unseen-language artifacts (lv/ga/zh/ja/hi/iu) and the two-axis reject test. Not attempted. |

**Gate C: cannot be assigned.** The current shape is *P-C2 holds, P-C1 untested on the
decisive cells* — i.e. neither C-PASS nor C-FAIL is reachable from this run.

## 4. The one finding that matters: a cell-distinctness ceiling

On the C0 domain set — **all five domains byte-distinct**, which was deliberate in the
C0/B design — the byte-n-gram stage-1 is already at 0.9867. That leaves only ~4 crops of
headroom, and the residual head cannot even reach the baseline. **This is not evidence
that the residual head fails at its job; it is evidence that this test set cannot
discriminate.** The residual head's whole claim is about cells where byte geometry is
*weak* — and C0's set, by construction, has none.

The residual head is also **depth-sensitive in the informative direction**: L1 (0.9333)
beats L0 (0.8867), and the MLP beats the linear at L1 (0.9333 vs 0.9033). The residual
stream does carry addressable structure; it is simply outperformed by byte statistics on
byte-distinct data.

## 5. The decisive run (next, cheap, already scoped)

P-C1's hard cells live in **RA2b-lt**, not in C0: the P-R3 result this probe exists to beat
was **0.762 overall** with es/pl/sk at **0.00** and et at **0.67** — Latin-script neighbours
of early territories. The C0 label set was a validity check; the RA2b-lt run is the actual
test.

- **Command (same script, different checkpoint/corpora):**
  `c_arms.py extract out/bdh_europarl_ladRA2b-lt_last.pt --domains <20 Europarl langs> --routes <23 widths>`,
  then `fit` and `arm2` on the same npz, comparing per-domain against P-R3's numbers.
- **Prediction to test:** P-C1 — head ≥0.90 overall, hard cells (es/pl/sk) ≥0.60, i.e. a
  rescue from P-R3's 0.762 / 0.00.
- **Cost:** extract ≈ 20 min GPU (23 widths × 20 domains is heavier than 5 × 5), fit +
  arm2 minutes. No new ladder training.
- **This run decides Gate C.** Until it exists, no arm-based gate verdict is honest.

## 6. Plan reconciliation (Arms portion)

| plan item | status |
|---|---|
| Arm 1 self-distilled head on residuals | ~ measured on C0 (0.9333); decisive run on RA2b-lt pending |
| Arm 2 external embedding control | done (0.9833 / 0.9933) |
| Arm 3 byte-n-gram + residual cascade | done on C0 (cascade below stage-1 baseline) |
| P-C1 | undecided on hard cells |
| P-C2 | PASS |
| P-C3 | PASS (formal; caveat noted) |
| P-C4 OOD | not run |
| Gate C verdict | not assignable yet |

## 7. Provenance

- **Script:** `scripts/quinn/c_arms.py` (392 lines, `extract`/`fit`/`arm2`).
- **Committed raw:** `docs/data/phase2-sondeC-fit.json`, `docs/data/phase2-sondeC-arms-fit.log`,
  `docs/data/phase2-sondeC-arms-arm2.log`, `docs/data/phase2-sondeC-labels.tsv` (1000 rows).
- **On .200:** `out_c/c_arms_ladC.npz` (3.97 MB), `out_c/logs/c_arms_{extract,fit,arm2,st_install}.log`.
- **Environment:** sentence-transformers 6.0.1 in the repo venv, CUDA available;
  model `sentence-transformers/all-MiniLM-L6-v2` (384-dim).
- **Crop identity:** shared generator seed 1234, byte-identical to `eval_router.py`; the
  A2 label table reproduces the router confusion matrix exactly (999/1000).

— Quinn, @quinn-the-builder, 2026-09-16
