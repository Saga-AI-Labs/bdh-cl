# Revision 5 Figure Decision

**Basis:** the exact `c240a3f706058b44619e2a182a57e59c1b174665` manuscript, its committed figures, and the primary reports cited by the paper.

| Source artifact | Decision | Revision 5 treatment | Rationale |
| --- | --- | --- | --- |
| `decay_regimes.pdf` | Integrate in the main text | Included after the closed-form decay verification. | It directly visualizes the optimizer confound that the paper derives and repairs. |
| `leakage.pdf` | Integrate in Theory | Included after the soft-activity remark. | It supports the scoped soft-gating/LayerNorm leakage discussion; it is not presented as a proof. |
| `pareto.pdf` | Regenerate and integrate as a scoped legacy appendix | `pareto_legacy_rev5.pdf` is generated from the source table and included in `app:legacy`. | The experiment predates K20 and addresses consolidation, not the K20 gates. The old PDF is archived as a source-only artifact. |
| `forgetting.pdf` | Do not integrate | Archived under `figures/unreferenced/`. | The current FCS heatmap and `sec:fcs` provide the primary source-backed forgetting evidence; this older three-language plot is redundant. |
| `grid.pdf` | Do not integrate | Archived under `figures/unreferenced/`. | It concerns an older sparsity-composition side line, not the storage/serving/addressing claims of Revision 5. |

## Corrected Revision 5 figures

- `f3_retention_bars.pdf` is regenerated from `a4_routed_cost.csv` and the final RA2b matrix. Routed values are approximately 2--4 PPL, not the 20--230 PPL bars in the previous figure; joint values remain 20--230 PPL.
- `f6_expansion_control.pdf` separates free-width joint PPL from masked PPL. The real-ladder arm is shown as `31.07` free and `2.31` masked, rather than plotting only the masked value on a joint axis.
- `f_architecture.pdf` is a schematic, not a quantitative result, and is labeled as such.

All committed files in this revision are written in English. The review's reported `\\texttt` defect was checked against the exact c240a3f source: the active rev5 source contains the correct `\\texttt{...}` command, and the built PDF is the final authority.
