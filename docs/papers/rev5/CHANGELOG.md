# Revision 5.0 Change Log

**Date:** 2026-09-28
**Source baseline:** `c240a3f706058b44619e2a182a57e59c1b174665`

- Corrected Figure 3 from the committed A4 routed-cost table and final RA2b matrix. Routed values are shown near acquisition; joint values remain in the elevated 20--230 PPL range.
- Corrected Figure 6 to show free-width joint PPL and masked PPL separately, including real-ladder values 31.07 and 2.31.
- Added the corrected architecture schematic in the introduction.
- Added a complete pre-registered prediction/outcome register, preserving PASS, FAIL, PARTIAL, SUPPORTED, NEGATIVE, REFUTED, and NOT STARTED outcomes.
- Added `decay_regimes.pdf` to the decay-confound section.
- Added `leakage.pdf` to the soft-gating theory discussion.
- Added a regenerated, explicitly non-K20 `pareto_legacy_rev5.pdf` appendix figure.
- Archived `forgetting.pdf`, `grid.pdf`, and the original `pareto.pdf` under `figures/unreferenced/`; their inclusion decision is documented in `figure_decision.md`.
- Repaired the malformed `\\texttt{...}` source reference and verified the final LaTeX build with no unresolved references or overfull boxes.

The final PDF is `rev5-bdh-manuscript.pdf`; the TeX source and the English Markdown sync are in the same directory.
