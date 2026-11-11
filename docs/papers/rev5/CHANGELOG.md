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

## Peer-review fix round (2026-11-11)

Applied after the external review in `docs/reviews/2026-11-11_bdh-paper-review-carbon.md`
(Priority 1 blockers, then Priority 2). Everything below is verified against the committed
reports and CSVs cited in place.

**Corrected figure (data bug).**
- `figures/f4_ood_scatter.pdf` regenerated: the rev4 PDF plotted the `ra2b_matrix.csv`
  lt-row *per-domain joint* values on the y axis (trained languages at 62–230 ppl). The
  trained languages now sit at their routed ppl 2.36–6.47 (`a4_routed_cost.csv`), with
  routing advantage = pooled joint reference 36.76 / routed (`a3` probe V4), reproducing
  the text's 5.7–15.6×. Unseen languages use report-verified axes
  (`data/ood_axes.csv`): lv (0.98×, 37.61), ga (1.39×, 50.54; DGT own-corpus joint 70.17),
  zh (3.87×, 417.28), ja (3.21×, 570.94), hi (5.74×, 732.27), iu-clean (1.90×, 303.61).
  In-plot convention note states the split: trained + lv divide the pooled Europarl joint
  reference (a3 V4); ga and the cross-script probes divide own-corpus joints (a3 V5, X3);
  lt's per-domain ratio is 1× by construction (9.1× pooled). Caption (fig:ood) and the
  Section 7.3 convention sentence state the same split.

**New provenance CSVs and figure generators.**
- `data/decay_cfits.csv` (measured per-segment c-fits: GR/sl 0.892636, G2/sv 0.634888,
  G/en 0.129460, G2/en 0.115561, RA2 es→en_best 0.579775 sd 2.2e-7) and
  `data/xscript_confusion.csv` (zh 31/6/3, ja 27/13, hi 10/30, iu-clean el 28 / bg 12 —
  likelihood-router census, pi-50 line 392).
- `decay_regimes.pdf` regenerated with corrected legends ("c=0.8927 (exact 0.892752)",
  "c=0.5798 (exact 0.579775)", target "es → en_best" restored).
- `f5_cross_script.pdf` regenerated with the real iu-clean split (was a fake 20/20 with
  "split not reported"); per-bar bg+el counts annotated.
- `f_architecture.pdf` regenerated: stray diagonal arrow removed, E→u⊙v and E_v→u⊙v arrows
  added with ReLU labels, LN between a(u) and E_v, update box reads x ← LN(x+LN(·)),
  write-back routed from D_c (below-route), right-panel arrows rerouted clear of boxes.
- `pareto_legacy_rev5.pdf`: in-plot source note moved into the LaTeX caption (it overlapped
  the bars).
- `figure_manifest.json` regenerated; now records ood/decay/cross-script summaries and the
  SHA-256 of every input CSV.

**Theory repairs (Priority 1).**
- thm:dissoc restated for the abstract shift-invariant class with an explicit
  "Implementation scope" remark (the literal bdh.py level ends with LN, the encoder read is
  not renormalized, so the literal level map does not satisfy the hypothesis and its
  zero-mean output cannot realize F_A + c·1 with c≠0 by appended neurons alone); B.2 proof
  rewritten accordingly.
- prop:soft statement and B.5 proof repaired: gates g1, g2 ∈ [0,1], ε, δ > 0, γ ≥ 0,
  identity specialist; the argument is now the constraint algebra under the gate domain
  (the trajectory never crosses the ReLU kink on the tested cone); negative-gate family
  spuriousness noted.
- thm:criterion: reachable set ∪_{0≤ℓ<L}, F_A(H_A) ⊆ H_A added; lem:zf sequential
  preservation clause + typo fix; prop:amp L_f → L_{F'} (statement and proof); \mathbb{1}
  → \mathbf{1}; B.3 emb(x) + fixed-L hypothesis.

**Protocol and wording repairs (Priority 2).**
- Route-mask slice vs cumulative-prefix disambiguation: α=0.9 training term is own-slice
  NLL (width interval [n_old, n_new); verified against RA2b-era commit 25d1340,
  `keep[n_old:] = 1.0`), "prefix" reserved for cumulative [0, k) at serving time; protocol
  table and attention note updated ("parameter-free, RoPE buffer prefix-preserved");
  RoPE right-associativity quirk recorded; a(u) linear-attention clarification sentence.
- Title "(Revision 5.0)" dropped; `\usepackage{placeins}` added; jargon "two seats"/"two
  scripts" replaced by plain wording (abstract, contributions, line 260 rewritten from the
  garbled rev4 sentence, bit-exactness subsection, Section 5.5 seats defined, line 760);
  "the operator" → first person; backticks → \texttt (or \path where the long path broke
  the line); "substantial" quoting fixed; `--init-from` escaping; 21×20 → 20×20 matrix.
- FCS family bands corrected from `fcs_matrix.csv`: fi belongs to the Western-Latin low
  band (en-column 11.31), ro to the Eastern-Latin/Slavic high band (22.48); the Finnic
  fi/et split (et 26.20 high) added to P-FCS-1 and P-FCS-3 discussions.
- Readout table: block-average/log-norm are "identity up to LN ε (≤0.04% ppl)", not
  bit-identical; leakage caption defines j ∈ [0,1] and the j ≤ 0.15 budget; f1 caption
  gains the RA2 mid-ladder ordering clause; fig:fcs moved inside Section 4, fig:expansion
  after the control paragraph, pareto [!ht] with source note in caption and \FloatBarrier;
  "Routed routed" duplication removed; all 10 figures + tab:predictions now \ref'd.
- AI-disclosure pointer made neutral (no "pending operator re-review").

Rebuild: 31 pages, 0 LaTeX errors, 0 overfull boxes, no unresolved references; float
placement and figure numbering (1–10) verified in the output PDF.

The final PDF is `rev5-bdh-manuscript.pdf`; the TeX source and the English Markdown sync are in the same directory.
