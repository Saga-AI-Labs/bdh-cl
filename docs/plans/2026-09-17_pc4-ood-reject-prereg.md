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

## Two-axis rule, byte instantiation (preregistered thresholds)

1. **Relative:** mixture-NLL / best-class-NLL < 5 → candidate in-support
   (mixture = uniform over the 20 trained class models; byte analogue of the
   joint/best ratio).
2. **Absolute:** best-class per-byte NLL ≤ 10× the worst trained held-out
   language mean (band from the 580 trained held-out crops).

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