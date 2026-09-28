# Review: rev4-bdh-manuscript.tex

**Reviewer:** LongCat 2.5 Preview (Free)
**Date:** 2026-09-28
**Manuscript:** `docs/papers/rev4-bdh-manuscript.tex` (Revision 4.7, September 19, 2026)
**Figures reviewed:** All PDFs in `docs/papers/figures/`

---

## Summary

This is a well-structured, honestly-scoped manuscript that makes a clear contribution: separating **storage** (bit-exact preservation under masked growth), **serving** (joint vs. routed degradation), and **addressing** (label-free selection) in a depth-recurrent language model with additive neuron growth. The writing is unusually transparent about limitations, failed experiments, and self-caught errors.

However, the review identified **one major figure-text discrepancy** (Figure 3) and **one misleading figure presentation** (Figure 6), plus a LaTeX compilation error. The remaining four figures match their captions accurately.

---

## 1. Figure-by-Figure Verification

### Figure 1: `f1_ladder_curves.pdf` — Ladder Acquisition

**Caption claims:** RA2b (fixed regime, blue, all 20 phases): 2.25–5.99 band, position cost gone. RA2 (leaky regime, red, 12 documented phases): acquisition tracked ladder position. Green arrows: lt 9.94 to 3.72 (-63%), sl 9.45 to 3.36 (-64%). Residual spread is alphabet difficulty (bg/el), not chain state.

**What the figure shows:** Blue line ranges from ~2.25 to ~5.99 across 20 phases, relatively flat with two spikes at bg (~5.86) and el (~5.99). Red dashed line increases monotonically with phase position, reaching ~15.5 at phase 20. Green arrows highlight lt and sl improvements.

**Verdict:** MATCHES description. The blue line is flat (position cost gone), the red line tracks position (leaky regime), and the green arrows correctly highlight the same-position improvements. The residual spread at bg/el is visible and consistent with "alphabet difficulty."

---

### Figure 2: `f2_fcs_heatmap.pdf` — FCS Forgetting Matrix

**Caption claims:** FCS forgetting matrix (log10 ppl). Each row is the 20-domain cold eval after that phase; blue box marks the diagonal. Latin-script languages fall to their English-only zero-shot level (nine of sixteen fully displaced, seven partial retention; en, lt, bg, el excluded); bg/el collapse by four orders of magnitude at row 20; family-structured oscillation survives throughout.

**What the figure shows:** A 21x20 heatmap with log10 ppl color scale (0-7+). Blue boxes mark the diagonal. The bg and el columns show dark red (log10 ppl approximately 7, i.e., ~10^7 ppl) at later rows. Family-structured patterns are visible: Romance/Germanic languages (es, fr, de, it, pt, da, sv, nl, fi) show similar forgetting trajectories, while Slavic/Uralic languages (pl, cs, sk, sl, hu, et) show different patterns.

**Verdict:** MATCHES description. The heatmap clearly shows the family-structured forgetting, the diagonal marking, and the catastrophic collapse of bg/el at row 20 (four orders of magnitude). The color scale and values are consistent with the manuscript's claims.

---

### Figure 3: `f3_retention_bars.pdf` — Retention Bars

**Caption claims:** RA2b final checkpoint: routed serving (blue) vs joint serving (orange) vs acquisition exit (black tick), per domain, log scale. **Routed tracks acquisition for every domain (median +4.3% over the acquisition exit, range -0.8% to +8.0%, worst case hu)**; joint serving erodes 1.0-37.8x (median 11x).

**What the figure shows:** For each of 20 domains, three elements:
- **Black tick (acquisition exit):** positioned at ~2-6 ppl (bottom of chart)
- **Blue bar (routed serving):** positioned at ~20-60 ppl
- **Orange bar (joint serving):** positioned at ~20-200 ppl

**Verdict:** MAJOR DISCREPANCY. The caption states "Routed tracks acquisition for every domain (median +4.3% over the acquisition exit)" — this means the blue bars should be within 4.3% of the black ticks (i.e., ~2.1-6.3 ppl). Instead, the blue bars are at ~20-60 ppl, which is **~10x higher** than the acquisition exit, not 1.043x. On a log scale, this is a full order of magnitude difference.

The figure as drawn contradicts the manuscript's central claim that "retention equals acquisition." If the figure accurately represents the data, then routed serving is ~10x worse than acquisition, not 4.3% worse. If the text is correct, then the figure is plotting the wrong values (perhaps joint serving values in both bars, or some other error).

**This is the most serious finding of this review.** The paper's headline result — that prefix-masked serving reproduces acquisition quality — is not supported by the figure that is supposed to demonstrate it.

---

### Figure 4: `f4_ood_scatter.pdf` — Two-Axis OOD Separation

**Caption claims:** Two-axis OOD separation. Blue: 20 trained languages (ratio >= 5x, absolute ppl <= 6.5). Diamonds: 6 unseen — byte-adjacent (lv, ga) collapse on the ratio axis; cross-script (zh, ja, hi, iu) sit orders above on the absolute axis. hi breaches the trained ratio floor (5.74x): the one-axis rule fails informatively; both axes together separate all 26.

**What the figure shows:** Scatter plot with routing advantage (joint/best-route ppl) on x-axis (log scale) and best-route ppl (absolute) on y-axis (log scale). Blue dots (trained) cluster in the lower-left. Red diamonds (unseen) are in the upper-right. Vertical dashed line at ~5x (trained floor), horizontal dotted line at ~6.5 (~10x acquisition band).

**Verdict:** MATCHES description. The trained languages (blue) are correctly positioned below the horizontal line and mostly left of the vertical line. The cross-script unseen languages (zh, ja, hi, iu) are above the horizontal line. hi is correctly shown breaching the vertical floor at ~5.74x. The byte-adjacent unseen (lv, ga) are shown with low routing advantage (~1x), collapsing on the ratio axis.

---

### Figure 5: `f5_cross_script.pdf` — Cross-Script Routing

**Caption claims:** Cross-script routing on the fixed-regime chain (40 crops per probe). zh 37/40, ja 40/40, hi 40/40 and the decontaminated iu 40/40 concentrate on the only two territories with substantial multi-byte training exposure (bg/el: 82% 2-byte characters vs 11.7% next-highest); no Latin-route attraction remains after the iu correction.

**What the figure shows:** Stacked bar chart for zh, ja, hi, iu-clean. Orange = to el (Greek), Purple = to bg (Cyrillic), Gray = other routes.
- zh: ~31 orange + ~6 purple + ~3 gray = 40 -> ~37/40 to bg+el
- ja: ~27 orange + ~13 purple = 40 -> 40/40 to bg+el
- hi: ~10 orange + ~30 purple = 40 -> 40/40 to bg+el
- iu-clean: ~20 orange + ~20 purple = 40 -> 40/40 to bg+el

**Verdict:** MATCHES description. The visual counts are consistent with the claimed routing concentrations. zh has 37/40 to bg+el (3 to other), and the other three probes have 40/40. The figure supports the claim that cross-script inputs route to high-byte territories.

---

### Figure 6: `f6_expansion_control.pdf` — Expansion Control

**Caption claims:** Expansion control on the en base (one growth step; instrument gate reproduces matrix exit at 2.33 vs 2.31, PASS). Random Gaussian blocks cost 4.1x; inert zeros cost nothing — the zero-init convention is load-bearing; the real ladder's joint damage is 83% arithmetic on the log scale at the English-era checkpoint (62% in linear perplexity; six of seven eras reproduce the mechanism, fraction range 0.60-1.47).

**What the figure shows:** Three bars:
- Random (A): 9.57
- Inert zeros (C): 2.33
- Real growth (B): 2.31

**Verdict:** MISLEADING. The manuscript's own table (Section 5.1) reports the real ladder's English free-width perplexity as **31.07**, not 2.31. The value 2.31 is the **prefix-masked** perplexity, not the free-width (joint) perplexity. The figure plots the masked value for "Real growth (B)" while the caption discusses "the real ladder's joint damage" — which is the free-width value of 31.07.

The figure as drawn shows real growth (B) at 2.31, which is actually *slightly better* than the base (2.33). This gives the false impression that real growth causes no damage. The actual joint damage (31.07, a 13.3x increase) is not visualized at all. The 83% arithmetic claim is unsupported by the visual because the real damage bar is missing.

---

## 2. Unreferenced Figures

The following figures exist in `docs/papers/figures/` but are **not referenced** anywhere in the manuscript:

| File | Description | Status |
|------|-------------|--------|
| `decay_regimes.pdf` | Closed-form decay curves (c^k) for prediction vs. measurement | Not cited; content is described in Section 2.3 (decay confound) |
| `forgetting.pdf` | Catastrophic forgetting: sequential EN->DE->ES bar chart | Not cited; appears to be a simple 3-language illustration |
| `grid.pdf` | Sparsity at fixed capacity (volume/registers/languages) | Not cited; appears to be from an earlier version |
| `leakage.pdf` | Soft-regime leakage: budget j <= 0.15, relative logit drift | Not cited; relates to Proposition 3.5 (soft gating counterexample) |
| `pareto.pdf` | Merge->prune->replay reaches joint parity at original width | Not cited; relates to the replay baseline (Section 6.5) |

These figures may be from earlier manuscript revisions or supplementary material. If they are no longer needed, they should be moved to an archive directory. If they should be cited, references should be added.

---

## 3. LaTeX/Compilation Issues

### 3.1 Broken `\texttt` command (Line 415)

There is a **tab character** before `exttt` instead of a backslash. This should be:

```latex
(\texttt{docs/reports/2026-09-13\_quinn\_tier1-router-split-report.md}, bdh/2166c24).
```

This will cause a LaTeX compilation error.

### 3.2 Cross-references

All internal cross-references (Section~\ref{...}, Figure~\ref{...}, Table~\ref{...}) appear to be correctly formed and should resolve properly.

---

## 4. Content Review

### 4.1 Strengths

1. **Exceptional honesty about limitations.** The manuscript explicitly states what it does not claim, what would falsify its framing, and what it cannot explain (Section 9). This is rare and commendable.

2. **Clear separation of concerns.** The storage/serving/addressing decomposition is a genuine contribution to the continual-learning literature.

3. **Self-caught errors are disclosed.** The decay confound (Section 2.3), the iu contamination (Section 6.3), and the calibgain withdrawal (Section 6.2) are all reported transparently.

4. **Prior art engagement is substantive.** Each prior work is discussed with agreement/divergence/verdict, not just cited.

5. **Pre-registered predictions.** The manuscript references pre-registered hypotheses (H-decay-1/2/3, P-FCS-1/2/3, P-R1/R2) and reports their outcomes honestly (including a FAIL on P-FCS-3).

### 4.2 Concerns

1. **Figure 3 discrepancy (see above).** This is the most serious issue. The figure does not support the headline claim.

2. **Figure 6 misleading presentation (see above).** The real growth bar shows the masked value, not the free-width value that would demonstrate the claimed damage.

3. **Single seed.** All results are from single runs with a measured 2-4% seed floor. The manuscript acknowledges this, but it means all quantitative claims have uncertainty that is not visualized in any figure.

4. **N=6 for OOD detection.** The out-of-support detection thresholds are fit and evaluated on the same 6-language probe set. The manuscript is transparent about this ("a measured separation, not held-out validation"), but it means the two-axis rule is not validated on truly unseen languages.

5. **Architecture vs. objective confound.** The manuscript acknowledges (Section 9, item iv) that the fixed-capacity floor vs. growth ladder comparison moves two variables at once (capacity mechanism + route-aware auxiliary loss). This is a real confound that is disclosed but not resolved.

6. **Scale.** All results are at 100M-579M parameters on two GPUs. The addressing question at 2,000+ territories is acknowledged as open, but the gap between 20 and 2,000 territories is vast.

### 4.3 Writing Quality

The writing is dense but generally clear. The manuscript is long (~1200 lines of LaTeX) and could benefit from:
- A table summarizing all pre-registered predictions and their outcomes
- A figure in the introduction showing the BDH architecture (currently only described in text)
- Moving some proofs to a supplementary document (the appendix is substantial)

---

## 5. Summary of Findings

| Finding | Severity | Location |
|---------|----------|----------|
| Figure 3 does not match caption/text | **Critical** | `figures/f3_retention_bars.pdf` |
| Figure 6 shows masked value instead of free-width value | **High** | `figures/f6_expansion_control.pdf` |
| Broken `\texttt` (tab instead of backslash) | **Medium** | Line 415 |
| 5 figures unreferenced in manuscript | **Low** | `figures/` directory |
| Single seed for all experiments | **Medium** | Throughout |
| OOD thresholds not held-out validated | **Medium** | Section 6.3 |
| Architecture vs. objective confound | **Medium** | Section 9 |

---

## 6. Recommendations

1. **Fix Figure 3** — this is the most important action. Either:
   - The figure is plotting the wrong data (e.g., joint values in both bars), in which case it should be regenerated; or
   - The text overstates the routed-serving quality, in which case the claims should be revised to match the data.

2. **Fix Figure 6** — add the real ladder's free-width perplexity (31.07) as a fourth bar, or change the y-axis/annotation to make clear that the "Real growth (B)" bar shows the masked value, not the joint damage.

3. **Fix the LaTeX error** on line 415.

4. **Reference or archive** the 5 unreferenced figures.

5. **Consider adding error bands** to figures where single-seed uncertainty is relevant (at minimum, state the seed floor in each caption).

---

*Review conducted by LongCat 2.5 Preview (Free), 2026-09-28.*
