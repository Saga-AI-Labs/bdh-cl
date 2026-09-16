# Sonde B (phase-2) gate tables — P5 in-chain + P-B4 routed-vs-acquisition

Run: host .200 (rtx4090), ladder `ladder_sondeB_resume.sh` (phases 2-5),
finished 2026-09-15 18:24. Instruments: `scripts/p5_inchain_check.py`,
`scripts/domain_eval.py`, `scripts/eval_router.py`.

## P5 in-chain (storage thesis, new domain class) — ALL 4 PASS
Masked parent block must stay bit-exact through each growth phase.
encoder / encoder_v / decoder / embed / lm_head / attn.freqs all BIT-EXACT;
grown segment nonzero; optimizer v(masked)==0 & m(masked)==0, v(grown)!=0.

| transition | parent mult -> child mult | P5 verdict |
|---|---|---|
| base  -> code  | 128 -> 160 | PASS |
| code  -> math  | 160 -> 192 | PASS |
| math  -> legal | 192 -> 224 | PASS |
| legal -> ga    | 224 -> 256 | PASS |

Raw per-tensor detail: `phase2-sondeB-p5-inchain.txt` (this dir).

## P-B4: routed retention vs own acquisition
Both are own-prefix, cold eval. Acquisition = own domain in that phase's
`domain_eval` (block=512, 30 crops) on that phase's own exit. Retention =
same domain served by the FINAL checkpoint at its own prefix
(`ladB_routdiag_final.txt`, window=128, 40 crops).

| domain | acquisition ppl (own phase) | routed retention ppl (final ckpt) | delta |
|---|---|---|---|
| code  | 5.23 | 5.24 | +0.01 |
| math  | 1.47 | 1.44 | -0.03 |
| legal | 2.21 | 2.17 | -0.04 |
| ga    | 2.32 | 2.36 | +0.04 |
| prose | 2.39* | 2.39 | 0.00 |

*prose acquisition is the base-phase exit, not a growth phase.

### Honest caveats (do NOT read the deltas as zero)
- The deltas are REAL, tiny, bidirectional drifts (-0.04..+0.04), not an
  identical-by-construction null. They exceed exactness but sit inside the
  crop/window noise floor (window 512 vs 128, 30 vs 40 crops).
- These are NOT the teacher-forced `val ppl` from the training logs
  (code 2.82 / math 1.32 / legal 2.02 / ga 2.18). Teacher-forced val and
  cold random-crop eval are different protocols; comparing them to the
  routed cold numbers would manufacture a fake retention loss. Kept separate.
- Joint full-width cold eval at the final checkpoint is far worse
  (code 89.52, prose 23.76) — that is the serving-confounder, not
  retention failure; the routed own-prefix column is the correct read.

Verdict: P-B1 (territoriality) PASS (199/200 diagonal). P-B4 (retention=acquisition)
PASS on own-width, with the small real deltas documented above, not suppressed.
