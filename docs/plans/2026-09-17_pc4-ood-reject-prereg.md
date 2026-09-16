# P-C4′ — OOD Reject under Byte-First Routing (Prereg)

Status: PRE-REGISTERED · 2026-09-17 · Quinn · Operator GO: 2026-09-17 ("no-brainer, klares Go")
Position: closes the open Gate-C clause (P-C4) of `2026-09-11_sondeC-embedding-router-probe.md`.
No number below was measured before this file was committed.

## Object under test

The **byte-n-gram router** (per-class char 4-gram, add-1) — the operational
in-distribution candidate per the arms report §8 — NOT the retired residual head
(P-C1 falsifier) and NOT MiniLM. The two-axis reject rule (Stage A, X3) was
validated only for the likelihood router; this probe tests its byte-side
instantiation.

## Setup

- Model: `out/bdh_europarl_ladRA2b-lt_last.pt` (RA2b-lt, mult 736, 23 routes
  2048..47104 step 2048). Unchanged from the arms run.
- OOD set (6 languages, all absent from every training corpus by construction):
  lv (`data/europarl/europarl-v7.lv-en.lv.txt`, byte-near), ga
  (`data/europarl/DGT.en-ga.ga.txt`, Latin), zh/ja/hi
  (`data/europarl/xscript_{zh,ja,hi}.txt`, cross-script), iu
  (`data/europarl/xscript_iu.txt`, syllabics).
- Crops: 96/language × 512 B, tail slice of each artifact, seeds 9000+i
  (fresh stream; no overlap with trained-crop streams). iu: n = min(96,
  floor(bytes/512)).
- Likelihood side (reference): per OOD crop, NLL under all 23 territory-masked
  routes + one full-width (joint) forward; batch 1.
- Byte side: per-class 4-gram models fit on the EXISTING `c_arms_ra2b_r3.npz`
  train split (1340 crops, no refit tuning); per-language mean per-byte NLL and
  margin on OOD crops; calibration band from the 580 held-out trained crops.

## Two-axis rule, byte instantiation (preregistered construction)

Amendment 2026-09-17 (same day, before any OOD number was measured): the
relative axis originally read "mixture-NLL / best-class-NLL < 5". That
construction is wrong for the byte side — a likelihood mixture is max-dominated
(even trained languages would score ratio ≈ 1). The byte analogue of the
likelihood joint-vs-routed ratio is ONE pooled class-agnostic byte model vs the
best per-class model; direction as in Stage A (trained ⇒ high ratio, OOD ≈ 1).
Amended construction, frozen before any OOD scoring:

1. **Relative:** joint/best ratio per crop = NLL_joint / NLL_best_class, where
   NLL_joint is the pooled byte-4-gram model fit on all 1340 train crops (one
   model, byte analogue of the full-width model) and NLL_best_class is the best
   of the 20 per-class models. A language is accepted on the relative axis iff
   its mean crop ratio ≥ τ_rel, with τ_rel = min over the 20 trained languages
   of their language-mean ratio (calibrated on the 580 trained held-out crops
   only; the weakest trained language defines the bar).
2. **Absolute:** a language is accepted on the absolute axis iff its mean
   best-class per-byte NLL ≤ 10× the worst trained language mean (band from the
   580 trained held-out crops; the Stage A factor, frozen).

Accepted = both axes pass. Language-level means decide (as in Stage A X3);
crop-level rates are reported descriptively with Wilson intervals. Under this
calibration the trained-language falsifier direction is nearly vacuous by
construction (τ_rel is the weakest trained mean); the teeth of the test are on
the OOD side. Direction note for the record: Stage A rejected on LOW ratio
(byte-near unseen had ratio ≈ 1, trained ≈ 5.7×); this byte instantiation
keeps that direction — accept iff ratio ≥ τ_rel AND NLL within the band.

## Pre-registered predictions

- **P-C4′-1 (route agreement):** byte-router argmax class equals the
  likelihood argmin-NLL route on ≥ 0.90 of OOD crops overall (Wilson 95 %
  reported per language). Falsifier: any language < 0.50.
- **P-C4′-2 (the decisive clause):** the byte-side two-axis rule separates
  6/6 OOD languages from 20/20 trained languages (language-level means;
  crop-level rates reported with Wilson intervals). Falsifier: any OOD
  language accepted by both axes, or any trained language rejected.
- **P-C4′-3 (descriptive, mechanism check):** ratio-only acceptance admits at
  least one cross-script language (Stage A X3 mechanism, byte side).

## Verdict mapping

- P-C4′-2 PASS → Gate C closes **C-PARTIAL with OOD reject validated for the
  byte router**; byte-first routing remains the serving candidate.
- P-C4′-2 FAIL → byte router is OOD-unsafe; the A2 likelihood router (with its
  already-validated two-axis rule) remains the serving path, byte router
  demoted to in-distribution fast path behind a likelihood check.

## Budget and non-goals

~30–60 min GPU on .200 (576 crops × 24 forwards, batch 1) + minutes of CPU
fitting. No ladder training, no head refitting, no threshold tuning after
seeing OOD numbers. Any follow-up protocol needs a fresh preregistration.

— Quinn, 2026-09-17