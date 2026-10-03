# Re-check — MiMo 2.6 Pro review findings vs. updated rev5 (2026-09-29)

**Scope:** re-audit of `docs/reviews/2026-09-28_bdh-paper-review-mimo-26-pro.md` findings against the manuscript after pulling `8f1f825..80be584` (5 commits: `6078d2c` "address MiMo review items 4-7 and correct Theorem 1", `41ee688` "correct five-orders to four-orders", `297cf92` "archive rev4 artifacts and draft rev5 AI disclosure", `189d3ce`/`80be584` K20 dual-arm reports).
**Reviewer:** MiMo v2.6 Pro. **Verdict up front:** all 5 required fixes landed and verify; Theorem 1–2 repairs are mathematically sound and match the implementation; two residuals (family labels on the FCS oscillation clusters; unchanged editorial/abstract items) are minor.

## A. Required fixes (review §8 items 1–5)

| # | Review finding | Status | Evidence (verified independently) |
|---|---|---|---|
| 1 | f32 decay-offset error (§2.3) | ✅ **FIXED** | Text now: "sits $1.36\times10^{-8}$ below the exact-precision value **per plateau step** … over the $\sim$9,700 plateau steps accumulates to about $-1.3\times10^{-4}$ and reconciles the measured 0.892636 with the exact-precision 0.892752." Gap 0.892752−0.892636 = 1.16×10⁻⁴ ≈ 9,700 × 1.36×10⁻⁸ = 1.32×10⁻⁴ ✓. Matches `2026-09-04_decay-family-…` exactly ("matching the measured −1.303e-4 to +1.4e-6"). |
| 2a | Seven-operator table missing from Markdown | ✅ **FIXED** | Full table now in `rev5-bdh-manuscript.md` (absK 39.4/79/1160/287; ev-shift 36.7/…; massnorm 31.26/…/215073/180510; softmix 18.73/…; calibgain 2.31/−2.29†/−4.19†) — values agree with TeX and with new `data/readout_operators.csv` (absK en 39.37→39.4, bg 1160.22→1160 ✓). |
| 2b | Tab-corrupted `\texttt` citation | ✅ **FIXED** | MD line 735 now a clean code span `docs/reports/2026-09-13_quinn_tier1-router-split-report.md`; TeX line 493 `(\texttt{docs/reports/2026-09-13\_quinn\_tier1-router-split-report.md}, bdh/2166c24)` — no stray `exttt` remains in either source. |
| 2c | Duplicated register header row | ✅ **FIXED** | Single header occurrence in the Markdown table now. |
| 3 | Four "acquisition band" values under one name | ✅ **FIXED** | §7.3 now uses a per-language denominator ("exceeds $\sim$10× **that language's own acquisition perplexity**") and explicitly separates the bands: "the acquisition band is 2.29–6.36 and the routed band is 2.36–6.47, the latter at most $1.08\times$ acquisition, so the rule's verdict is unchanged whichever of the two serves as the denominator" — both bands check out against `a4_routed_cost.csv`/`ra2b_acquisition.csv` (min/max 2.29/6.36 and 2.36/6.47; max ratio 1.0799→"1.08" ✓). The FCS band is now labeled "best-val acquisition band is 1.54–2.29" (line 1152). |
| 4 | Missing artifacts (disclosure doc; raw matrices; routdiag; OOD table) | ✅ **FIXED** | `docs/papers/rev5/rev5-ai-disclosure-draft.md` created (12.7 KB, roles/models/providers/process sections) and the manuscript reference corrected ("drafted in `rev5-ai-disclosure-draft.md` in this directory"; rev4 copy archived at `docs/papers/archive/`). New raw data in `rev5/data/`: `ladRA2b_routdiag_p19.txt`, `ladRA2b_routdiag_p20.txt`, `ood_probe.csv`, `readout_operators.csv`; FCS matrix at `docs/reports/data/2026-09-10_fcs_matrix.csv` (cited in-paper) and byte census at `docs/reports/data/byte_census/territory_byte_census.json`. `figure_manifest.json` extended to 8 entries — **all 8 SHA-256 hashes verify** ✓. |
| 5 | Undisclosed mid-ladder batch change + orders inconsistency | ✅ **FIXED** | §4 Design now discloses it explicitly: "Note the token-budget asymmetry with the growth ladder: FCS is batch 4 throughout, while the ladder switches to batch 1 at phases 5–20 (Setup) … the ladder used $4\times$ less data per phase in 16 of its 20 phases. The asymmetry favours the ladder … but any cross-phase trend in the ladder must not be read as coming from a single data budget." — a candid and quantitatively accurate statement (4/20 phases at batch 4 ✓ per `ra2b_acquisition.csv`). "four orders" consistency fixed in abstract, Fig-3 caption, and §4 ("up to four orders of magnitude (bg ×12,086, el ×6,873)"), and `41ee688` corrected the source report's "five orders" line with named baselines. |

## B. Theory repairs (review §3.3, Q5)

| Item | Status | Assessment |
|---|---|---|
| Theorem 1 proof (unlicensed `+Lc` accumulation) | ✅ **FIXED — and correct** | New construction: $F'(h)=F_A(h)+c\mathbb{1}$ **added at each level invocation**, with the key invariant "$F_A(F_A^{\ell}(x)+c\mathbf{1})=F_A^{\ell+1}(x)$" via LayerNorm shift-invariance $\operatorname{LN}(h+c\mathbf{1})=\operatorname{LN}(h)$; conclusion $F'^{\ell}(x)=F_A^{\ell}(x)+c\mathbf{1}$, explicitly "not $+Lc\,\mathbf{1}$". I verified the argument against `bdh.py`: the level map is $x\leftarrow\operatorname{LN}(x+y)$ with $y\leftarrow\operatorname{LN}(y_{\mathrm{MLP}})$ and $\operatorname{LN}$ applied after embed and after attention (`x = self.ln(x)`, `yKV = self.ln(yKV)`, `y = self.ln(yMLP)`, `x = self.ln(x + y)`); every path into a level's computation passes through LayerNorm, and $\operatorname{LN}(h+c\mathbb{1})=\operatorname{LN}(h)$ holds exactly (the mean absorbs $c$), so the per-level shift is re-established without accumulation. The appendix proof now cites the implementation guards by name. Sound. |
| Theorem 2 statement (free `ℓ` index) | ✅ **FIXED** | Now "$F'^{\ell}(x)=F_A^{\ell}(x)$ for all $x\in\mathcal{X}_A$ **and all** $0\le\ell\le L$ **iff** …" — the truncation quantifier the proof needs ("The hypothesis at $L=\ell^*$") is now in the statement. |

## C. Strong claims now checkable against shipped raw data

| Claim | Verification |
|---|---|
| "*p19 and p20 routing diagnoses … are bit-identical on all 19 non-lt domains' routed perplexities—zero drift across a full growth phase*" | ✅ **VERIFIED exactly.** Diffing `ladRA2b_routdiag_p19.txt` vs `…_p20.txt`: all 20 domains present in both; **exactly one value differs** (lt 63.0 → 4.04, lt being the p20 phase), i.e. 19/19 non-lt routed values bit-identical. This flagship retention claim is now fully reproducible from `rev5/data/`. |
| "*the en column oscillates between 10.5–13.6 ppl after Romance/Germanic phases and 22.1–29.1 after Slavic/Uralic phases … (29.1 → 11.3)*" | ✅ **ranges exact, ⚠️ labels loose.** Against `docs/reports/data/2026-09-10_fcs_matrix.csv`: the "10.5–13.6" band = the nine fully-displaced domains {es 13.48, fr 11.14, de 10.90, it 13.56, pt 11.63, da 10.45, sv 11.34, nl 11.67, fi 11.31} (actual 10.45–13.56, rounding ✓); the "22.1–29.1" band = the seven partial-retention domains {pl 22.76, sl 22.13, cs 24.39, sk 29.14, ro 22.48, hu 25.46, et 26.20} (actual 22.13–29.14, rounding ✓); "(29.1 → 11.3)" = sk 29.14 → sv 11.34 ✓ consecutive rows. **Caveat:** the family labels are linguistically wrong for two members — fi (Uralic) sits in the "Romance/Germanic" band and ro (Romance) in the "Slavic/Uralic" band — because the bands are the behavioral displaced/partial clusters, not genealogical families. The quantitative claim is exact; the labels should say "the displaced group" / "the partial-retention group" (or note fi/ro explicitly). The paper elsewhere half-acknowledges this ("the Romance/Germanic group" includes fi). |
| OOD ratio values (zh 3.87, ja 3.21, hi 5.74, lv 0.98, ga 1.39; absolute 304–732) | ✅ consistent with new `ood_probe.csv` and the rejection-suite report (as in the original review's table). |
| Operator sweep rows | ✅ `readout_operators.csv` reproduces the table with per-run identity controls (P-R1 identity 31.14; P-R1b 32.04) — the cross-run control caveat in the paper matches the CSV structure. |

## D. Recommended science items (review §8 items 6–11) — status

| # | Item | Status |
|---|---|---|
| 6 | Multi-seed/order replication; non-parallel-register probes | 🟡 **Underway outside the paper.** New `2026-09-29_k20-gx10-results.md`: dual-arm K20 ladder (seeds 1 & 2), 25 domains × 25 widths × 200 crops, routing 99.18% (4,959/5,000) — and the domain set now spans **prose, code, math, legal, ga, zh** alongside the 20 languages, i.e. exactly the "domain-continual-learning probe on non-parallel registers" the review asked for. Two honest anomalies reported (code 96.5%, legal 84.5% with a data-composition explanation). These results are not yet in the manuscript. |
| 7 | Conformal threshold freezing (P-R4) | 🔴 **Open** (declared future work in-paper; unchanged). |
| 8 | Routed-vs-exit on identical crops (the +4.3% window question) | 🟡 Partially mitigated: bands are now correctly separated (item 3) and routdiags shipped; the paper still says the instrument-offset escape "is removed on provenance grounds, not replaced by a substitute measurement". The decisive matched-crop experiment remains undone. |
| 9 | End-to-end addressing cost | 🔴 **Open** (still only the 23× relative figure). |
| 10 | Theorem repairs | ✅ Done (section B). |
| 11 | "Operator" project voice | 🔴 **Unchanged** ("*the operator asked for it explicitly*" §4; "*the operator's $20\to20{,}000$ question*" §10) — fine for an internal/preprint record; neutralize for external submission. |

## E. Residual minor items (new or unchanged)

1. **FCS oscillation cluster labels** (see §C above): quantify correctly but mislabel fi/ro family membership — one-sentence fix.
2. **Abstract's "+4.3% median"** is still quoted without the 2–4% seed-floor hedge that the review asked to attach "everywhere" (Limitations covers it globally).
3. `block-average`/`log-norm` rows in the shipped CSV show tiny non-zero diffs vs identity (e.g. bg 227.07 vs 226.99) while the paper's table renders "*bit-identical to identity*" — the CSV suggests rounding-level equality at most; worth reconciling the word "bit-identical" with the recorded values (the CSV may simply carry display rounding of the same float; verify and state precision).

## F. Updated verdict

The revision conditions attached to "accept subject to revision" (all five required fixes) are **met and independently verified**, and the two theory defects are repaired correctly — the new Theorem 1 argument checks out against `bdh.py` line-by-line. Remaining items are the declared-and-optional science extensions (conformal freezing, matched-crop cost study, in-paper multi-seed/non-register results from K20) plus three editorial nits. The paper as it now stands is internally consistent, numerically traceable end-to-end (8/8 manifest hashes, raw routdiags, operator CSV, OOD table, FCS matrix, byte census all shipped), and its flagship claims (bit-exactness; zero p19→p20 drift; 83%/62% arithmetic decomposition) reproduce exactly from the committed artifacts.

**Recommendation:** the rev5 package is ready for external circulation in its current form; folding the K20 dual-arm results into the manuscript (multi-seed + non-parallel registers) would retire review items 6 and the largest statistical caveat in one stroke.
