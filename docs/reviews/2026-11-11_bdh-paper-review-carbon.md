# In-Depth Peer Review — *Append-Only Neural Memory: Storage, Addressing, and Growth* (Revision 5.0)

**Manuscript reviewed:** `docs/papers/rev5/rev5-bdh-manuscript.tex` (1,303 lines) and compiled `rev5-bdh-manuscript.pdf` (29 pages), at git HEAD `529338e` (manuscript last modified in `297cf92`)  
**Figures audited:** All 10 included PDFs in `docs/papers/rev5/figures/` (rasterized and visually inspected against captions, text, data CSVs, and `scripts/quinn/rev5_paper_figures.py`)  
**Supporting code & data cross-checked:** `bdh.py`, `pipeline/train.py`, `scripts/eval_router.py`, `docs/papers/rev5/data/*`, `docs/papers/rev5/figure_manifest.json`, `docs/reports/*`, `docs/reviews/*`  
**Reviewer:** Gemini 4 Carbon (`respan/google_gemini_ai/gemini-4-carbon:free`)  
**Date:** 2026-11-11  

---

## Executive Summary & arXiv Readiness Verdict

### Verdict: **NOT READY as-is — Ready for arXiv after targeted fixes (primarily 1 critical figure bug, 2 mathematical proof/statement repairs, and several LaTeX/figure/packaging cleanups)**

Scientifically, this is an **unusually strong, transparent, and original measurement paper**. Its core conceptual contribution—decomposing continual learning in a shared-readout depth-recurrent language model into **storage** (bit-exact parameter/path preservation), **serving** (joint summation readout interference vs. prefix-masked readout), **addressing** (label-free NLL selection vs. cheap byte-geometry prefiltering), and **support** (two-axis OOD rejection)—is genuine, crisp, and empirically well-demonstrated. The scientific hygiene is exemplary: pre-registered predictions with preserved `FAIL`, `NEGATIVE`, `REFUTED`, and `NOT STARTED` outcomes; multi-instrument triangulation of the AdamW weight-decay confound (`c = 0.8927` / `0.5798`); explicit self-retraction of a confounded 76% addresser result; and open disclosure of Inuktitut corpus contamination. Every headline arithmetic claim in the text (`+4.3%` median routed cost, `+8.0%` max at `hu`, `83.3%` log-scale / `62%` linear random-expansion damage, `4.1×` single-block cost, Wilson intervals `[0.91, 1.0]` and `[0.68, 1.0]`, decay constants, and f32 rounding accumulation) **recomputes cleanly** from the committed artifacts.

However, my visual inspection of the rendered PDFs and line-by-line mathematical audit uncovered **critical issues that prior review rounds missed (or introduced during revision)** and that **must be repaired before uploading to arXiv**:

1. **CRITICAL — Figure 8 (`figures/f4_ood_scatter.pdf`) plots completely corrupted data for the 20 trained languages, directly contradicting its own caption, Section 7.3, and `ood_probe.csv`.** In the figure, the 20 blue dots ("trained languages") sit at y = **20–230 PPL** (joint PPL!) instead of 2.36–6.47 PPL (best-route PPL), and at x = **0.16–1.80×** (`36.70 / joint_ppl`!) instead of ≥ 5.7× (`joint_ppl / routed_ppl`). Nineteen of the twenty trained languages lie on the **wrong side** of both threshold lines in the plot, and `lv`/`ga` visually sit *inside* the blue trained cluster!
2. **HIGH — Two mathematical errors in Section 3 / Appendix B:**
   - **Proposition 1 (`prop:soft`)** has an algebraic mismatch between the main text and the proof: line 348 states $(1+g_1)^2 + g_1 g_2 \varepsilon\delta = 1$, which simplifies to $g_1(2 + g_1 + g_2\varepsilon\delta) = 0$ and **does** have a continuous open-range family of non-zero solutions $g_1 = -(2 + g_2\varepsilon\delta)$ (e.g., $g_1 \approx -2$), falsifying the stated equation's claim! Furthermore, the appendix proof (lines 1254–1259) uses an inconsistent gating convention between step 1 ($x_1 = a(1+g_1)$, omitting $\sigma$) and step 2, and subtly assumes $1+g_1 > 0$ without stating $g_i \in [0, 1]$.
   - **Theorem 1 (`thm:dissoc`)** fails to account for the **terminal LayerNorm** in `bdh.py`: line 288 of `bdh.py` ends every level with `x = self.ln(x + y)` before projecting `logits = x @ self.lm_head` (line 290). In actual BDH, any additive constant $c\mathbf{1}$ added inside the residual stream is annihilated *at the end of the same level* (`LN(h + c1) = LN(h)`), and even if added *after* `LN` (`F'(h) = F_A(h) + c1`), it shifts logits only along $c(\mathbf{1}^\top W_{\text{head}})$ rather than arising from neuron growth in $(E, E_v, D_c)$ (whose output passes through two `LN`s). Moreover, `\mathbb{1}` on line 284 renders as a garbled **`⋊`/`\Bbbk`-style symbol (`c⋊`)** in the PDF (page 8) because `amssymb` does not define blackboard-bold digits!
3. **MEDIUM — Figure & Typography defects visible in the compiled PDF:**
   - **9 of 10 figures are never cited in the prose** (`\ref{fig:...}` is only ever called for `fig:architecture`; Figures 2–10 float onto arbitrary pages—often *before* the section that introduces their topic—without a single text reference).
   - **`f_architecture.pdf` (Figure 1)** has overlapping arrows/text (`append + zero-init weights` arrow cuts straight through the text `old prefix`; stray diagonal arrow from outside the box; omits `\operatorname{relu}` and intermediate `LN`; Equation on line 132 has typo $\nu = \operatorname{relu}(x@E)$ instead of $u = \operatorname{relu}(x@E)$).
   - **arXiv-incompatible repository self-references** in prose (raw Markdown backticks rendering as `` `docs/reports/...' ``, dangling reference to local draft `rev5-ai-disclosure-draft.md` "pending operator re-review", internal HAK-bus jargon like "two seats" and "the operator asked for it").

None of these flaws undermine the **empirical findings** of the project. All of them are straightforward to fix in 1–2 days of focused editing and plotting. Below is the complete, itemized audit across (1) Scientific Soundness & Methodology, (2) Mathematics & Theory, (3) Figure-by-Figure Visual Audit, and (4) LaTeX / Editorial / arXiv Packaging.

---

## 1. Scientific Soundness & Methodological Audit

### 1.1 What Makes This Paper Scientifically Worth Publishing on arXiv

1. **Clean Conceptual Decomposition:** Separating *parameter/path storage*, *joint vs. routed readout serving*, *label-free vs. input-side addressing*, and *out-of-support rejection* resolves a persistent confusion in continual learning (where parameter freezing, capacity allocation, and task-ID routing are routinely conflated).
2. **The AdamW Decoupled Weight-Decay Confound (Section 2.3):** Identifying that `grad = 0` (via multiplicative gradient masking) still triggers decoupled weight decay $p_{\text{exit}} = p_{\text{entry}} \prod_{t=1}^T (1 - \mathrm{lr}_t \cdot \mathrm{wd})$ in PyTorch's `AdamW`, deriving the exact schedule product ($c = 0.892752$ in f64, $0.892637$ in f32 vs. measured $0.892636$; $c = 0.579775$ under cosine), and repairing it via step-end snapshot restoration ($0.59\%$ step-time overhead) is a high-value, practical systems-and-methodology contribution with immediate relevance beyond BDH (e.g., sparse/MoE expert training).
3. **The Random-Expansion & Readout-Operator Suite (Section 6):** Showing that appending *untrained Gaussian blocks* to a frozen English checkpoint reproduces $83.3\%$ of the log-PPL degradation ($62\%$ linear) while zero-initialized inert blocks cost $0.0\%$, and that `calibgain` gradient-fitted on English spontaneously silences appended territories ($\le 0.12$ vs. $\approx 2.4$ on base)—rediscovering oracle masking—is a crisp mechanistic demonstration of why shared unnormalized summation readouts fail under growth.
4. **Non-Unimodality of Cumulative-Prefix NLL & Two-Instrument Divergence (Section 7):** Showing that bisection over prefix widths fails ($14\text{--}16/20$ land in wrong local minima) while hashed byte $1\text{--}4$-gram logistic regression matches the likelihood router $20/20$ in-support, and explaining *why* they diverge on Hindi/Inuktitut (surface $n$-gram centroid proximity vs. realized multi-byte weight fit in `bg`/`el`), is novel and genuinely insightful.
5. **Exemplary Epistemic Honesty:** Table 1 (pre-registration register), explicit Wilson score intervals accounting for domain clustering (`n=20` clusters rather than `n=800` or `n=160` pseudo-replicates), and transparent reporting of negative/refuted hypotheses set a rare standard of candor.

### 1.2 Independent Verification of Headline Numbers

I independently recomputed the mathematical and statistical quantities from `docs/papers/rev5/data/*`, `docs/reports/data/2026-09-10_fcs_matrix.csv`, and Python schedule simulations:

| Quantity in Manuscript | Source / Formula Checked | Recomputed Value | Status |
|---|---|---|---|
| Default schedule decay $c$ (f64 / f32) | $\prod_{t=0}^{9999}(1 - \mathrm{lr}_t \cdot 0.1)$, warmup 30, decay 300 | `0.892752` (f64) / `0.892637` (f32) | **Exact match** |
| Per-step f32 rounding at plateau | $(1 - 10^{-5})_{\text{f64}} - (1 - 10^{-5})_{\text{f32}}$ | `1.358e-8` ($\times 9700 \approx 1.32\times 10^{-4}$) | **Exact match** |
| Cosine schedule decay $c$ | Warmup 1000, decay 10000, $\min\mathrm{lr}=10^{-4}$ | `0.579775` vs. `0.5798` | **Exact match** |
| Routed serving vs. acquisition exit | `a4_routed_cost.csv` (`routed_p20 / acquisition_exit`) | Median `+4.295%`, min `-0.82%` (`fr`), max `+7.99%` (`hu`) | **Exact match** |
| p19 $\to$ p20 routed drift | `ladRA2b_routdiag_p19.txt` vs. `p20.txt` | 19/19 non-`lt` domains identical to 2 decimal places | **Exact match** |
| Joint serving ratio at `lt` ckpt | `ra2b_matrix.csv` (`checkpoint == 'lt'`) / `acq_exit` | Median `11.43×`, min `1.00×` (`lt`), max `37.80×` (`bg`) | **Exact match** |
| Expansion control (en base) | $\ln(20.16/2.33)/\ln(31.07/2.33)$ & linear | `0.8329` (`83%`), linear `0.6204` (`62%`), 1-block `4.107×` | **Exact match** |
| Wilson 95% lower bounds | $40/40$ and $8/8$ ($z = 1.96$) | `0.9124` $\to$ `[0.91, 1.0]`; `0.6756` $\to$ `[0.68, 1.0]` | **Exact match** |
| FCS row-20 collapse & `en` oscillation | `2026-09-10_fcs_matrix.csv` | `bg`: $1.54 \to 18612.86$ (`×12,086`); `el`: $1.59 \to 10927.74$ (`×6,873`); `en` bands `10.45–13.56` & `22.13–29.14` | **Exact match** |
| Manifest SHA-256 integrity | `figure_manifest.json` (8 files) | All 8 hashes match committed files | **Exact match** |

### 1.3 Methodological & Substantive Caveats to Tighten for arXiv Reviewers

1. **Architecture vs. Objective Confound (Section 12, item iv — needs earlier signposting):**
   The fixed-capacity baseline (Section 4) trains with plain next-token NLL ($\alpha = 0$) at `batch_size = 4`, whereas the growth ladder (Section 5) trains with route-aware loss ($0.9 \cdot \text{prefix-NLL} + 0.1 \cdot \text{full-NLL}$) and drops to `batch_size = 1` for phases 5–20. Section 4.1 and Section 12(iv) disclose both facts honestly, but **the Abstract and Introduction still frame the contrast without mentioning the $\alpha=0.9$ auxiliary objective**. Mentioning "route-aware masked growth ($\alpha=0.9$)" in the Abstract prevents a skeptical ML reviewer from feeling ambushed in Section 12.
   *(Note: Also clarify in Section 2.1/2.2 what "prefix" means during training vs. serving! In `pipeline/train.py:303–325`, `keep[n_old:] = 1.0` and `route_neuron_mask = keep.clone()` when `side == "new"`, meaning the training auxiliary loss masks **only the newly grown slice $[n_{\text{old}}, n_{\text{new}})$**, whereas `eval_router.py:65` sets `m[:k] = 1.0`, evaluating **cumulative prefixes $[0, k)$**! If RA2b trained with `keep[n_old:] = 1.0`—or if an earlier commit used cumulative `[:n_new]`—that distinction is crucial. Lines 152 and 333 of `train.py` call `n_old..n_new` "prefix", which is actually a **slice/tile**, while cumulative `[0, k)` at serving is a **prefix**. Verify against the exact RA2b training commit and state explicitly whether the $\alpha=0.9$ loss masks `[0, n_new)` or `[n_old, n_new)`!)*
2. **Genealogical Mislabelling of `fi` and `ro` in FCS Oscillation (Section 4.2, lines 418–428):**
   Line 418 groups `fi` (Finnish — a **Uralic** language, not Romance/Germanic) into *"es, fr, de, it, pt, da, sv, nl, fi; the Romance/Germanic group"*, and line 427 states that `en` oscillates *"between 10.5–13.6 ppl after Romance/Germanic phases and 22.1–29.1 after Slavic/Uralic phases"*—whereas in `2026-09-10_fcs_matrix.csv`, row 9 (`fi`, Uralic) gives `en = 11.31` (in the low band) and row 17 (`ro`, Romance) gives `en = 22.48` (in the high band, likely due to Romanian orthographic/diacritic statistics). Fix in one sentence: note that `fi` clusters behaviorally with the Western-Latin/Romance-Germanic byte group while `ro` clusters with the Slavic/Eastern-Latin group—which actually *strengthens* the paper's thesis that **byte statistics, rather than linguistic genealogy**, drive transfer and interference!
3. **"Attention unfrozen" in Protocol Table (line 212) Contradicts Section 2.1 (line 139):**
   Line 139 correctly notes: *"The attention block carries no trainable parameters (its only state is the RoPE frequency buffer)"* (and `pipeline/train.py:351` prints `"parameter-free (bdh; freeze flags inert)"`). Yet the protocol table on line 212 says `"attention unfrozen"`, which confuses Transformer readers into thinking $W_Q, W_K, W_V$ are being updated across phases (which would violate bit-exact storage!). Change line 212 to `"attention parameter-free (RoPE buffer prefix-preserved)"`.
4. **RoPE Right-Associative Exponent Detail (`train.py:264` vs `bdh.py:78`):**
   In `bdh.py:78`, `theta ** (q / n)` with `theta = 2**16` computes $(2^{16})^{q/n} = 65536^{q/n}$. In `pipeline/train.py:264`, `2 ** 16 ** ((idx // 2 * 2) / n_new)` is **right-associative** in Python, computing $2^{(16^{q/n_{\text{new}}})} \neq (2^{16})^{q/n_{\text{new}}}$! As noted in `docs/notes/2026-08-30_pi_q02-exactness-derivation.md` (§5), this does not affect old-path bit-exactness (because `old_f` is copied verbatim), nor does it invalidate growth acquisition, **but** new neurons enter on a $2^{(16^r)}$ frequency curve rather than $65536^r$. One sentence in Section 2.1 or a code fix/note ensures complete implementation fidelity if anyone inspects the repo alongside the paper.
5. **"Bit-identical" Wording in Section 6.2 Table (`block-average` and `log-norm`):**
   The table on lines 622–623 and prose on line 638 state that `block-average` and `log-norm` returned *"bit-identical to identity"* values. However, the shipped `docs/papers/rev5/data/readout_operators.csv` records `identity (P-R1)` as `en=31.14, de=35.21, cs=60.86, bg=226.99, el=65.24`, while `block-average` is `31.14, 35.22, 60.85, 227.07, 65.29` and `log-norm` is `31.14, 35.22, 60.86, 226.92, 65.27`—differing by up to `0.04%` because `nn.LayerNorm` has `eps=1e-5` in the denominator ($\operatorname{LN}(c \cdot y) = c y / \sqrt{c^2 \sigma^2 + \epsilon} \neq y / \sqrt{\sigma^2 + \epsilon}$ in bf16/fp32!). Calling them *"invariant up to LayerNorm $\epsilon$ ($\le 0.04\%$ PPL difference)"* instead of *"bit-identical"* is both mathematically exact and consistent with `readout_operators.csv` (and avoids misusing the paper's own strict definition of *bit-identical*).
6. **Optional High-Value Addition — Post-Sep-28 Repo Results (`K20` Dual-Seed & `K25/W1024`):**
   While rev5 freezes the project state at September 28, 2026, the repository now contains completed multi-seed and non-parallel-register replications (`docs/reports/2026-09-29_k20-gx10-results.md`: Seeds 1 & 2 across 25 domains including `prose, code, math, legal, ga, zh`, 99.18% routing, plus `2026-10-31_k25w1024-routing-matrix-results.md` at 2.82B params and `2026-11-07_masked-serving-results.md`). You do not *have* to delay arXiv v1 to merge a second experimental arc, **but** even a brief addendum or updated v2 will immediately neutralize the two biggest reviewer objections ("single seed" and "Europarl parallel register only").

---

## 2. Mathematical & Theoretical Audit

I checked every equation, theorem, lemma, proposition, corollary, and proof in Section 2, Section 3, and Appendix B against both mathematical validity and `bdh.py`.

### 2.1 Notation Typo in Section 2.1 (Equation on Line 132)
Line 132 writes:
$$\nu = \operatorname{relu}(x@E), \qquad v = \operatorname{relu}\bigl(\operatorname{LN}(a(u))@E_v\bigr), \qquad x \leftarrow \operatorname{LN}\Bigl(x + \operatorname{LN}\bigl((u \odot v)@D_c\bigr)\Bigr).$$
The first symbol is **`\nu`** ($\nu$, Greek nu), whereas the second and third equations—and Figure 1—use **`u`** ($u$, Latin u)!
- **Fix:** Change `\nu=` to `u=` on line 132. Also consider noting tensor axes briefly (in `bdh.py`, $x$ has shape `(B, 1, T, D)`, $E$ has `(nh, D, N)`, so $u = \operatorname{relu}(x@E)$ has shape `(B, nh, T, N)`, $a(u) = \operatorname{scores}(u) @ x$ actually returns `(B, nh, T, D)`—a residual-width vector per head, not a neuron-width vector!—which is then normalized over $D$ via `LN(a(u))` and projected back to `(B, nh, T, N)` by `@ E_v`). Making clear that $a(u, x)$ uses RoPE-rotated $u$ for causal linear attention scores `(QR @ QR_k.mT).tril(-1)` multiplying values $x$ (`bdh.py:140–143`, *not* softmax!) will delight careful readers: BDH uses **unnormalized causal linear attention** (`tril(diagonal=-1)`), which is why zeroed neurons contribute literally zero to attention scores without even a softmax denominator change!

### 2.2 CRITICAL MATH ISSUE 1 — Proposition 1 (`prop:soft`, Lines 344–351 & Proof B.5, Lines 1250–1261)

There are **three mathematical defects** in Proposition 1 and its proof sketch:

1. **False algebraic claim in the Proposition statement (line 348):**
   Line 348 states:
   > *"a two-dimensional ReLU system makes the requirement $(1+g_1)^2 + g_1 g_2 \varepsilon\delta = 1$ for all input magnitudes $a > 0$, unsolvable by any input-independent pair."*

   Expand $(1+g_1)^2 + g_1 g_2 \varepsilon\delta = 1$:
   $$1 + 2g_1 + g_1^2 + g_1 g_2 \varepsilon\delta = 1 \iff g_1\bigl(2 + g_1 + g_2\varepsilon\delta\bigr) = 0.$$
   For **any** $g_2 \neq 0$, setting $g_1 = -(2 + g_2\varepsilon\delta)$ solves this equation identically for all $a > 0$! That is an entire 1-D open curve of input-independent solutions!
   *(Why did this happen? In `archive/cl-bdh-manuscript.tex:265`, the RHS was `= 4` because the ungated specialist step $x \mapsto x + \sigma(x)$ maps $a \mapsto 2a \mapsto 4a$, whereas rev5 changed `4` to `1` on line 348 and `4a` to `a` on line 1255 without checking how the specialist map behaves!)*

2. **Inconsistent gating dynamics between Step 1, Step 2, and the Specialist in Proof B.5 (lines 1251–1259):**
   Look at the appendix proof (lines 1251–1259):
   - It defines $f'_1(x) = \sigma(x_1) + \varepsilon x_2$ and $f'_2(x) = \delta\sigma(x_1) + \gamma x_2$, with $I_A = \{1\}, I_B = \{2\}$.
   - Note first that in Lemma 1 (`lem:zf`), **the specialist coordinate $I_A = \{1\}$ is ungated** ($g_A \equiv 1$, only suffix $I_B = \{2\}$ has gate $g_2$)! If $I_A$ is ungated ($g_1$ is not a free suffix gate, or $g_1$ scales a *suffix* contribution into coordinate 1), the setup in B.5 is gating the specialist's own update $f'_1$ by $g_1$!
   - Even taking $x_{\ell+1} = x_\ell + g \odot f'(x_\ell)$ literally from $x_0 = (a, 0)$ with $a > 0$:
     - After 1 step: $x_1 = (a + g_1 \sigma(a),\; g_2 \delta \sigma(a)) = (a(1+g_1),\; g_2\delta a)$. For the **specialist** ($g_1 = 1, g_2 = 0$, or ungated specialist $x_{\ell+1} = x_\ell + f_A(x_\ell)$ where $f_{A,1}(x_1) = \sigma(x_1)$), step 1 gives $x_1^A = 2a$ and step 2 gives $x_2^A = 2a + \sigma(2a) = 4a$ (**not** $a$, unless $f_{A,1} = 0$!).
     - Conversely, if the specialist is the identity ($f_A \equiv 0$, so $f'_1, f'_2$ are *both* suffix blocks gated by $g_1, g_2$ and target is $x_2 = a$), then after 2 steps:
       $$x_{2,1} = a(1+g_1) + g_1\bigl[\sigma(a(1+g_1)) + \varepsilon g_2 \delta a\bigr] = a.$$
       **Only if $1 + g_1 \ge 0$** does $\sigma(a(1+g_1)) = a(1+g_1)$, giving $a[(1+g_1)^2 + g_1 g_2 \varepsilon\delta] = a$, which has the negative-gate solution $g_1 = -(2 + g_2\varepsilon\delta) < -1$—except at $1 + g_1 < 0$, $\sigma(a(1+g_1)) = 0$! Let us check $1 + g_1 \le 0$ when $\sigma(a(1+g_1)) = 0$: then $x_{2,1} = a(1 + g_1 + g_1 g_2 \varepsilon\delta) = a \iff g_1(1 + g_2\varepsilon\delta) = 0$! And in the second coordinate:
       $$x_{2,2} = g_2\delta a + g_2\bigl[\delta \sigma(a(1+g_1)) + \gamma g_2 \delta a\bigr] = g_2 \delta a \bigl(1 + \mathbf{1}_{1+g_1 > 0}(1+g_1) + \gamma g_2\bigr) = 0.$$
       Look at the bracket $(1 + \gamma g_2)$ (or $(2 + g_1 + \gamma g_2)$): **if $\gamma < 0$**, setting $g_2 = -1/\gamma > 0$ makes the bracket **zero** without $g_2 = 0$! Line 1257 claims *"the bracket is positive for $a > 0$"*—which is **false** unless $g_1, g_2 \ge 0$ and $\gamma \ge 0$ (or $g_2$ is small enough that $1 + g_2\gamma > 0$)! Also notice line 1257 has a typo inside $\sigma$: it writes `a + \sigma(a(1+g_1)) + g_2\gamma a` instead of `a + \sigma(a(1+g_1)) / a ...` (mixing $a$-factored and unfactored terms: $a + \sigma(a(1+g_1))$ is linear in $a$, fine, so $g_2\delta(a + \sigma(a(1+g_1)) + g_2\gamma a) = 0$ is algebraically homogeneous, provided $g_1, g_2 \in [0, 1]$ and $\gamma \ge 0$).
   - Finally, line 1260 claims *"Nonlinearity (the kink in $\sigma$) is exactly what forces hardness."* **This is false in the proof as written!** On the cone $x_0 = (a, 0)$ with $a > 0$ and $g_1 \ge 0$, $\sigma(a) = a$ and $\sigma(a(1+g_1)) = a(1+g_1)$ never cross the kink at $0$—the system is purely linear on $\mathbb{R}_{>0}$! To genuinely invoke the ReLU kink, you must evaluate at **both** $x_0 = (+a, 0)$ (where $\sigma(x_1) = a$) **and** $x_0 = (-a, 0)$ (where $\sigma(x_1) = 0$).

- **Clean, Bulletproof Repair for Proposition 1 (`prop:soft`):**
  Specify the gate domain explicitly ($g_1, g_2 \in (0, 1]$, standard soft-attenuation gates, with $\gamma \ge 0$, $\varepsilon, \delta > 0$, and identity specialist $F_A(x) = x$, or test both $x_0 = (a, 0)$ and $x_0 = (-a, 0)$). Even simpler and genuinely using the ReLU kink for **any** $(g_1, g_2) \in (\mathbb{R}\setminus\{0\})^2$:
  - Let $F_A(x_1, x_2) = (x_1, 0)$ on $\mathcal{X}_A = \mathbb{R} \times \{0\}$, and add gated perturbations $g_1(\sigma(x_1) + \varepsilon x_2)$ to coord 1 and $g_2 \delta \sigma(x_1 + 1)$ to coord 2. Evaluating at $x_1 = 0$ (where $\sigma(x_1)=0$ but $\sigma(x_1+1)=1$) immediately gives $x_{1,2} = g_2\delta$, and step 2 leaks $g_1 \varepsilon g_2 \delta$ into coord 1, forcing $g_1 g_2 \varepsilon \delta = 0$!
  - Or keep your exact equations $f'_1(x) = \sigma(x_1) + \varepsilon x_2$, $f'_2(x) = \delta\sigma(x_1) + \gamma x_2$ with **gates $g_1, g_2 \in [0, 1]$ and $\gamma \ge 0$** (on identity specialist $F_A = \mathrm{id}$): then $1+g_1 \ge 1 > 0$ and $2 + g_1 + g_2\gamma > 0$ are **strictly positive**, so $x_{2,2} = g_2\delta a (2 + g_1 + g_2\gamma) = 0 \implies g_2 = 0$, and then $x_{2,1} - a = a g_1(2 + g_1) = 0 \implies g_1 = 0$! (And remove the false sentence *"Nonlinearity (the kink in $\sigma$) is exactly what forces hardness"* if only $a > 0$ is used, OR evaluate at $a > 0$ and $a < 0$ so the kink actually does work.)

### 2.3 HIGH MATH / IMPLEMENTATION ISSUE 2 — Theorem 1 (`thm:dissoc`, Lines 283–294 & Proof B.2, Lines 1202–1219)

1. **Garbled symbol in PDF:** Line 284 writes `F'(h)=F_A(h)+c\,\mathbb{1}`, while lines 287–289 and 1204–1215 write `c\,\mathbf{1}`. In standard LaTeX with `amssymb`, `\mathbb{1}` is **undefined** for digits—it reads font slot `'1'` from the `msbm` blackboard table, rendering as a bizarre **`c⋊` / `\Bbbk`** glyph on page 8 of the PDF! Change `\mathbb{1}` on line 284 to `\mathbf{1}`.
2. **Mismatch with `bdh.py`'s actual LayerNorm placement and "parameter set contains $\theta_A$ unchanged":**
   - Theorem 1 states: *"Any such $F'$ whose parameter set contains $\theta_A$ unchanged still has old-task trajectories that differ from the specialist's at every depth."*
   - Wait: **how** is $F'(h) = F_A(h) + c\mathbf{1}$ realized by appending neurons to BDH's parameter set $(E, E_v, D_c)$? In `bdh.py:284–288`:
     ```python
     yMLP = xy_sparse.transpose(1, 2).reshape(B, 1, T, N * nh) @ self.decoder
     y = self.ln(yMLP)
     x = self.ln(x + y)
     ```
     Every BDH level **ends** with `x = self.ln(x + y)` (a zero-mean LayerNorm over $D$)! Therefore:
     1. The output of any BDH level $F_{\text{BDH}}(h)$ satisfies $\mathbf{1}^\top F_{\text{BDH}}(h) = 0$ identically. **No choice of suffix neuron weights in $(E, E_v, D_c)$ can ever produce $F'(h) = F_A(h) + c\mathbf{1}$ ($c \neq 0$)**, because `self.ln` projects out $\mathbf{1}$ at the end of every level!
     2. Even if an external module adds $+c\mathbf{1}$ *after* `self.ln(x + y)` at each level, at the next level `x @ self.encoder` is NOT preceded by `self.ln(x)` inside the loop (`self.ln(x)` is only called *before* the loop at `bdh.py:241`, and at the *end* of the loop at `bdh.py:288`!). Wait: look at `bdh.py:257`:
        `x_latent = x @ self.encoder` — there is **no** LayerNorm at the *start* of a level in `bdh.py`! The LayerNorm is at the *end* of the previous level (`bdh.py:288`, `x = self.ln(x + y)`). So if you define $F_A(h) = \operatorname{LN}(h + \operatorname{LN}(\text{MLP}_A(h)))$, then $F_A(h + c\mathbf{1})$ has $(h + c\mathbf{1}) @ E_A = h @ E_A + c(\mathbf{1}^\top E_A) \neq h @ E_A$! Thus $F_A$ as coded in `bdh.py` is **NOT shift-invariant** (`F_A(h + c1) != F_A(h)`), contrary to line 286 (*"Because the BDH level map is shift-invariant... every level begins and ends with LayerNorm"*)!
   - **Let's double-check `bdh.py:240–289`:**
     - Before loop (line 241): `x = self.ln(x)`
     - Inside loop (lines 257–288):
       - `x_latent = x @ self.encoder` (NOT shift-invariant in `x` unless $\mathbf{1}^\top E = 0$!)
       - `yKV, _ = self.attn(x_sparse, x, ...)` (`scores @ x` shifts by $(\text{scores}\mathbf{1}) c$, which `yKV = self.ln(yKV)` at line 272 cancels—**only** if `x_sparse` didn't change, which it **did** because `x @ self.encoder` is not preceded by `LN`!)
       - `y = self.ln(yMLP)` (line 287)
       - `x = self.ln(x + y)` (line 288 — zero-means the *output*, not the *input*!)
   - **What a great catch!** Both halves of the new Theorem 1 narrative in commit `6078d2c` misread `bdh.py`:
     1. A BDH level **ends** with `LN`, it does **not** begin with `LN` (line 241 is outside the `for level in range(C.n_layer):` loop!). So $\operatorname{LN}$ makes the output of `bdh.py` zero-mean, *not* shift-invariant to an external $+c\mathbf{1}$ injected after line 288!
     2. Meanwhile, inside actual neuron growth (appending columns to $E, E_v$ and rows to $D_c$), why does $F'(h) \neq F_A(h)$ when $\Delta\theta_A = 0$? It is much simpler and **100% faithful to `bdh.py`**: choose any non-zero vector $w \in \mathbb{R}^d$ not parallel to $\mathbf{1}$ (with $\operatorname{LN}(w) \neq 0$), set one suffix neuron's encoder column $e_{\text{new}}$ so that $h_{\text{old}}^\top e_{\text{new}} > 0$ at some $h_0 \in \mathcal{X}_A$ (or for a cleaner all-depth construction, take an abstract level map, **or** for literal BDH at depth $\ell=1..L$, construct two suffix neurons with opposite-sign input columns $+u, -u$ so $\max(0, x^\top u) + \max(0, -x^\top u) = |x^\top u| > 0$ for almost all $x$, writing along a fixed decoder row $w$!). Even more cleanly: if Theorem 1 is stated for an **abstract depth-recurrent map** (not claiming `bdh.py` itself has $F'(h) = F_A(h) + c\mathbf{1}$), say explicitly: *"In the abstract class of depth-recurrent maps whose level update takes the form $F_A(h) = \Phi(\operatorname{LN}(h); \theta_A)$..."* — and separate that cleanly from how BDH's summation readout $y_{\text{MLP}} = \sum_{i \le N} (u_i \odot v_i) d_i$ creates non-zero additive perturbations inside $\operatorname{LN}(x + \operatorname{LN}(y_{\text{MLP}}))$.
   - Fixing this makes Theorem 1 rock-solid against any code-checking referee.

### 2.4 Minor Formal Cleanups in Theorem 2 (`thm:criterion`), Lemma 1 (`lem:zf`), and Proposition 2 (`prop:amp`)

1. **Theorem 2 (`thm:criterion`, lines 296–308 & Proof B.3, lines 1221–1240):**
   - In the statement (line 297), $\mathcal{T}_A = \bigcup_{\ell \le L} \{F_A^\ell(x) : x \in \mathcal{X}_A\}$. Note that $F'(z)$ must agree with $F_A(z)$ for $\ell < L$ (i.e., $0 \le \ell \le L-1$): at terminal depth $\ell = L$, $F'(F_A^L(x))$ is depth $L+1$, which is never evaluated in an $L$-level network! Look at Proof B.3 line 1229: *"Choose $x \in \mathcal{X}_A$ whose trajectory passes through $z^*$ at depth $\ell^* < L$ (such $x$ exists by definition of $\mathcal{T}_A$)"* — if $\mathcal{T}_A$ unions up to $\ell \le L$ (instead of $0 \le \ell < L$), a state $z^*$ visited **only** at $\ell^* = L$ violates $\ell^* < L$ unless "for all $L$" means unbounded depth $L \in \mathbb{N}$ (yet line 299 fixes $L$ and quantifies $0 \le \ell \le L$)!
   - **One-character fix:** Define $\mathcal{T}_A = \bigcup_{0 \le \ell < L} \{F_A^\ell(x) : x \in \mathcal{X}_A\}$ on line 297! Then $\ell^* < L$ holds by definition of $\mathcal{T}_A$, $\ell^* + 1 \le L$ is within the hypothesis $0 \le \ell \le L$, and both directions of the `iff` become 100% airtight for fixed finite depth $L$!
   - Also in Proof B.3 line 1222: `h_0 = E(x)` overloads $E$ (which Table 2 defines as the latent neuron encoder matrix $E \in \mathbb{R}^{n_h \times d \times N}$, whereas here $E(\cdot)$ means the token embedding!). Write $\mathrm{emb}(x)$ instead of $E(x)$ on lines 1222 and 1238.
   - And in Theorem 2 line 305 vs. line 1236: clarify whether $P_A$ is a linear projection on the residual space $\mathbb{R}^d$ or on an augmented neuron/channel space; if $H_A = \operatorname{im} P_A$ and $P_A^2 = P_A$, then on $H_A$ (where $P_A z = z$ and by C1 $F'(z) \in H_A \implies P_A F'(z) = F'(z)$), C2 ($P_A F' P_A = P_A F_A P_A$) gives $F'(z) = P_A F_A(z)$, which equals $F_A(z)$ **assuming $F_A(H_A) \subseteq H_A$** (specialist invariance). State $F_A(H_A) \subseteq H_A$ explicitly.

2. **Lemma 1 Proof Typo (line 1243):**
   Line 1243 writes: `With suffix gating $f_b\mapsto g_b(x)\odot f_b(b)$-terms only` — `f_b(b)` is a typo for `f_b(h)` (or just `f_b`). Moreover, if multiple suffix blocks $b \in \{1, \dots, B\}$ sum into the residual (`\sum_b g_b(x) \odot f_b(h_\ell)`), two non-zero suffix blocks could in principle cancel each other ($g_1 f_1 + g_2 f_2 = 0$) unless gated/grown **sequentially one phase at a time** (requiring preservation after each phase $b = 1$, then $b = 2$, etc.) or having disjoint coordinate supports. Adding *"under sequential per-phase preservation"* makes Lemma 1 exact even for multi-block sums in $\mathbb{R}^d$.

3. **Proposition 2 Proof (`prop:amp`, line 1268):**
   Unrolling $\|e_{\ell+1}\| \le \rho \|e_\ell\| + \delta_\ell$ from $e_0 = 0$ gives $\|e_L\| \le \sum_{j=0}^{L-1} \rho^{L-1-j} \delta_j \le \delta_{\max} \frac{1 - \rho^L}{1 - \rho} \le \frac{\delta_{\max}}{1 - \rho}$ (using $1 + L_f$ when Lipschitz constant is of the residual increment $f'$, i.e., $h_{\ell+1} = h_\ell + f'(h_\ell)$). Note that in BDH, the full level map is $h_{\ell+1} = \operatorname{LN}(h_\ell + \operatorname{LN}(\dots))$, not $h_\ell + f'(h_\ell)$, so $1 + L_f$ in Proposition 2 is the Lipschitz constant $L_{F'}$ of the composed level map (and indeed Remark 3 measures whole-map JVP gains $1.05\text{--}1.89$, not $1 + L_f \ge 1$). Aligning the notation ($L_{F'}$ vs. $1 + L_f$) avoids any confusion between $L_{F'} \approx 0.9$ (contractive directions) and $1 + L_f \ge 1$.

---

## 3. Figure-by-Figure Visual Audit

I rasterized all 10 PDF figures in `docs/papers/rev5/figures/` at 200 DPI and inspected every axis, bar, point, legend, annotation, and caption, as well as their placement in `rev5-bdh-manuscript.pdf`.

*(Note on numbering: Because rev5 inserted three new figures—`f_architecture.pdf` as Fig. 1, `decay_regimes.pdf` as Fig. 2, and `leakage.pdf` as Fig. 3—the historical `f1`..`f6` files are numbered Figures 4–9 in the compiled PDF.)*

### Summary Table of All 10 Figures

| PDF Fig # | Filename | Referenced in `\ref`? | Matches Data & Text? | Verdict |
|---:|---|---|---|---|
| **Fig. 1** | `f_architecture.pdf` | Yes (`fig:architecture`) | Mostly (schematic, minor visual bugs) | **Needs visual polish** |
| **Fig. 2** | `decay_regimes.pdf` | **No** (`fig:decayregimes` uncited) | Yes (minor rounding/label nits) | **Good; fix 2 label nits + cite** |
| **Fig. 3** | `leakage.pdf` | **No** (`fig:leakage` uncited) | Partially (orphan title `budget j <= 0.15` unexplained in text) | **Clarify caption/text + cite** |
| **Fig. 4** | `f2_fcs_heatmap.pdf` | **No** (`fig:fcs` uncited; floats *before* Sec. 4!) | Yes (`20×20` rows 1..20; caption says 20-domain) | **Good; fix row-count note + cite** |
| **Fig. 5** | `f1_ladder_curves.pdf` | **No** (`fig:ladder` uncited) | Yes (minor y-label / phase-order caveat) | **Good; clarify x-axis for RA2 + cite** |
| **Fig. 6** | `f3_retention_bars.pdf` | **No** (`fig:retention` uncited) | **Yes — rev4 bug is FIXED** | **Accurate & clear; cite in text** |
| **Fig. 7** | `f6_expansion_control.pdf`| **No** (`fig:expansion` uncited; floats into Sec. 5.4!) | **Yes — rev4 bug is FIXED** | **Accurate & clear; fix placement + cite** |
| **Fig. 8** | `f4_ood_scatter.pdf` | **No** (`fig:ood` uncited) | **NO — CRITICAL DATA BUG** | **BROKEN — MUST REGENERATE** |
| **Fig. 9** | `f5_cross_script.pdf` | **No** (`fig:xscript` uncited) | Mostly (`iu-clean` split visually shown as 20/20 while arrow says "split not reported") | **Fix `iu-clean` bar color + cite** |
| **Fig. 10**| `pareto_legacy_rev5.pdf` | **No** (`fig:paretolegacy` uncited; floats *above* App. A heading!) | Yes (text overlaps bars at bottom-left) | **Move footnote + `\FloatBarrier` + cite** |

---

### Detailed Figure Findings

#### 1. CRITICAL BUG — PDF Figure 8 (`figures/f4_ood_scatter.pdf`, TeX lines 700–704)
- **What the text and caption claim:**
  - Caption (line 703): *"Blue: 20 trained languages (ratio $\ge 5\times$, absolute ppl $\le 6.5$). Diamonds: 6 unseen — byte-adjacent (lv, ga) collapse on the ratio axis; cross-script (zh, ja, hi, iu) sit orders above on the absolute axis. hi breaches the trained ratio floor ($5.74\times$): the one-axis rule fails informatively; both axes together separate all 26."*
  - Section 7.3 (lines 718, 730): Trained languages have routing advantage $5.7\text{--}15.6\times$ and best-route PPL $2.36\text{--}6.47$.
- **What `figures/f4_ood_scatter.pdf` ACTUALLY shows (verified visually & algebraically):**
  - **Y-axis ("Best-route ppl (absolute)"):** The 20 blue dots are NOT at $2.36\text{--}6.47$! Instead:
    - `bg` is plotted at $y \approx \mathbf{230}$ (`230.22` = `bg`'s **joint** PPL!).
    - `hu` is at $y \approx \mathbf{74}$ (`73.88` = `hu`'s **joint** PPL!), **above** the horizontal dotted threshold line ($\approx 65$)!
    - `el`, `pl`, `cs` are around $y \approx 62\text{--}64$; `fi` at $51$; `sk` at $45$; `sl` at $20.4$; and a single unlabeled blue dot at the bottom right (`lt`) is at $y = 3.83$!
  - **X-axis ("Routing advantage (joint / best-route ppl)"):** Nineteen of the twenty blue dots lie at $x \in [\mathbf{0.16}, \mathbf{1.80}]$—far to the **left** of the vertical dashed `trained floor (5x)` line! Specifically:
    - `bg` is at $x = 36.70 / 230.22 = \mathbf{0.159}$!
    - `hu` is at $x = 36.70 / 73.88 = \mathbf{0.497}$!
    - `sl` is at $x = 36.70 / 20.39 = \mathbf{1.80}$!
    - Only `lt` sits to the right of $5\times$, at $x = 36.70 / 3.83 = \mathbf{9.58}$!
  - **Green diamonds (`lv` at $x=0.98, y=37.6$; `ga` at $x=1.39, y=50.5$):** Sit **right in the middle of the blue trained-language curve**, visually indistinguishable in region from `sk`, `en`, `de`, `fr`, `sv`!
- **Root cause of the bug:** Whoever originally generated `f4_ood_scatter.pdf` in rev4 (`ae791ed`) accidentally read `ra2b_matrix.csv` (`lt` checkpoint row = **joint** full-width PPL, `20.39..230.22`) into the variable meant for `routed_ppl` (`2.36..6.47`), and then computed `x = 36.70 / y`! And unlike `f3` and `f6`, `f4_ood_scatter.pdf` was **not** added to `scripts/quinn/rev5_paper_figures.py` during the rev5 rebuild, so the corrupted rev4 PDF was copied verbatim into `docs/papers/rev5/figures/`!
- **Required fix:** Add `make_ood_scatter_figure()` to `scripts/quinn/rev5_paper_figures.py` using `a4_routed_cost.csv` (`routed_p20` in `2.36..6.47`) and either per-domain `joint / routed` (`ra2b_matrix.csv` `lt` row / `routed_p20` — note that for `lt`, the final phase, full width *is* its own prefix so per-domain `joint/routed` is $3.83/4.04 = 0.95\times$, whereas the `36.70 / routed` aggregate-joint convention from `2026-09-11_a3-closed-set-probe.md` gives `5.67×–15.55×` for all 20 domains!).
  - **Important methodological check while fixing Fig. 8:** Notice how `5.7–15.6×` in Section 7.3 was originally computed in `a3-closed-set-probe.md` (line 44): `36.76 / routed_ppl` (dividing the *20-domain pooled joint reference* `36.70` by each domain's routed PPL!), whereas for `ga`, `zh`, `ja`, `hi`, `iu-clean`, Section 7.3 divides each domain's *own-corpus joint PPL* by its best-route PPL! If you instead use each trained domain's *own* joint PPL (`ra2b_matrix.csv` `lt` row) divided by its `routed_p20`, then 19 trained domains span **`5.50×` (`sl`) to `36.89×` (`bg`)**, while **`lt` (the 20th domain, whose territory IS the full width!) has ratio $\approx 1.0\times$** (`3.83 / 4.04 = 0.95×`) because full-width = routed-width for the final territory! Be 100% transparent about this in Section 7.3 and Fig. 8's caption: for the most recently appended territory $K$, full-width serving *is* its prefix, so its joint/routed ratio is trivially $\approx 1\times$ (which is known by construction, since route $K$ was selected!). Plotting all 20 blue points at $y \in [2.36, 6.47]$ will finally show the massive 1–2 order-of-magnitude vertical separation from `lv/ga` ($37.6, 50.5$) and `iu/zh/ja/hi` ($304\text{--}732$) that the paper describes!

#### 2. PDF Figure 1 (`figures/f_architecture.pdf`, generated by `rev5_paper_figures.py:155–208`)
- **Visual defects found on inspection:**
  1. In the right box ("append-only growth"), the vertical downward arrow from `"append + zero-init weights"` (`xy=(0.83, 0.49), xytext=(0.835, 0.68)`) **draws a black line straight across the middle of the `"old prefix"` box and collides directly with its text label**!
  2. In the left box ("one shared level"), line 190 of `rev5_paper_figures.py` has a stray annotation `ax.annotate("", xy=(0.17, 0.305), xytext=(0.28, 0.20), ...)` that draws an unexplained diagonal line from the bottom border of the rectangle into `"x + LN"`, clipping the `"a"` of `"all levels reuse..."`.
  3. In the right box, the arrow at the bottom (`xy=(0.75, 0.30), xytext=(0.83, 0.24)`) cuts diagonally across the bottom-left corner of the `"route mask"` box from the `"old path frozen"` label.
  4. Architectural completeness: the diagram shows $x \to E \to a(u) \to E_v \to D_c$ and $u \odot v \to D_c$, missing the `ReLU` nonlinearities, the fact that $u = \operatorname{relu}(x@E)$ feeds *both* $a(u)$ and $u \odot v$ (currently no arrow connects $E$ to $u \odot v$!), and the readout `LN` before `x +` (and outer `LN(x + LN(...))`).
- **Fix:** Adjust coordinates in `make_architecture_figure()` (5 minutes in Python): add an arrow from `$E$` down to `$u \odot v$`, remove the stray line 190 arrow, label `ReLU` and `LN(x + LN(·))`, and route the right-panel arrows cleanly between boxes instead of through text.

#### 3. PDF Figure 2 (`figures/decay_regimes.pdf`, TeX lines 252–256)
- **Visual check:** Clean two-panel semi-log plot showing $c^k$ across $k=0..20$ phases for G-family ($c=0.8927$) and RA2 ($c=0.5798$), and agreement with measured segment amplitudes at $k=1, 4, 9, 18, 19$.
- **Two minor label bugs in the right-panel legend:**
  1. Legend reads `G schedule product c=0.8928` while Section 2.3 (line 238) states `c=0.8927` (`0.892752` rounds to `0.8928` at 4 decimals, creating a 1-ulp text-vs-legend discrepancy).
  2. Red square legend reads `Measured (es -> , sd 2.2e-7)` — the target after `->` is **missing** (source report B.1 says `es -> en_best`).

#### 4. PDF Figure 3 (`figures/leakage.pdf`, TeX lines 322–327)
- **Visual check:** Dual-axis plot of `relative logit drift (%)` (left, red circles, $0.2\% \to 19.3\%$) and `top-1 agreement` (right, blue squares, $0.997 \to 0.43$) vs. `suffix-block activity scale j` ($0.05 \to 1.0$).
- **Context gap:** In rev3 (`archive/cl-bdh-manuscript.tex:319–327`), there was a subsection explaining the protocol (*16 EN windows, scaling ES suffix block by $j$, operating budget $j \le 0.15$ keeps $\ge 99\%$ top-1 agreement*). In rev5, that paragraph was cut, leaving the figure's title **`Soft-regime leakage: budget j <= 0.15`** and symbol $j$ completely undefined in the main text and caption! Add one sentence to the caption defining $j \in [0, 1]$ (uniform multiplier on an appended ES suffix block evaluated on 16 EN windows) and explaining the title's $j \le 0.15$ ($\ge 99\%$ top-1 agreement) reference point.

#### 5. PDF Figure 4 (`figures/f2_fcs_heatmap.pdf`, TeX lines 374–379)
- **Visual check:** Heatmap matches `2026-09-10_fcs_matrix.csv` accurately: diagonal blue boxes all pale yellow ($\log_{10}\text{ppl} \approx 0.2\text{--}0.36$), dark crimson columns at `bg` and `el` ($\log_{10}\text{ppl}$ up to $\sim 7.3$ at row 18 `nl`, where `bg = 20,528,903`), and visible alternating light/medium horizontal bands in the Latin columns matching the family-oscillation claim.
- **Minor text-vs-plot discrepancy:** Line 397 says *"yielding a $21 \times 20$ perplexity matrix"*, whereas `2026-09-10_fcs_matrix.csv` and `f2_fcs_heatmap.pdf` both have **20 rows** (`1: en` through `20: lt`), i.e. **$20 \times 20$**! Change `$21\times 20$` on line 397 to `$20\times 20$`. Also place Figure 4 *inside* Section 4 (currently TeX lines 374–379 sit at the end of Section 3, so it floats above Section 4's heading or onto page 10 awkwardly).

#### 6. PDF Figure 5 (`figures/f1_ladder_curves.pdf`, TeX lines 459–464)
- **Visual check:** Clearly shows RA2b (blue solid, 20 phases, flat in `2.25–3.72` for Latin + spikes at `bg 5.86` and `el 5.99`) vs. RA2 leaky (red dashed, climbing to `15.51` and `15.24`), with green arrows at phase 19 (`sl: -64%`) and phase 20 (`lt: -63%`).
- **Important precision caveat on x-axis alignment:** Look carefully at phases 6–18 of the red dashed curve (`RA2 leaky regime`). In RA2 (`2026-09-03_ra2-ladder-final-report.md`, Appendix A), the language ordering for phases 6–17 was **different** from RA2b! For example, at phase 15 (`sk` on the x-axis), the red square is plotted at **`15.51`**—which was RA2's **`bg` (phase 15 in RA2)**, not `sk`! And at phase 17 (`ro` on the x-axis), the red square is **`15.24`**—which was RA2's **`el` (phase 17 in RA2)**, not `ro`! Meanwhile phases 1, 2, 19 (`sl`), and 20 (`lt`) *do* match by language (`en`, `es`, `sl`, `lt`), which is why the caption's green arrows only claim *"same-position same-host cells lt ... sl"*. However, plotting RA2's phase-15 `bg` (`15.51`) directly above x-tick `15 sk` and RA2's phase-17 `el` (`15.24`) above `17 ro` without noting in the caption that **RA2 had a different mid-ladder permutation (so x-axis is phase index, and only phases 1–5, 19, 20 share the bottom language labels)** will mislead a reader into thinking Slovak (`sk`) and Romanian (`ro`) had 15.5 PPL in RA2! Add one clarifying clause in Figure 5's caption (and fix the minor text overlap of `lt -> lt: -63%` across the right border spine).

#### 7. PDF Figure 6 (`figures/f3_retention_bars.pdf`, TeX lines 495–500)
- **Visual check:** **Completely fixed from rev4.** Blue bars (routed serving, ~2.4–6.5 PPL) sit right on top of the black horizontal acquisition-exit ticks across all 20 languages, while orange bars (joint serving) tower at 20–230 PPL (except `lt`, the final territory, where joint = 3.83 and routed = 4.04). Matches `a4_routed_cost.csv`, `ra2b_matrix.csv`, and caption 100%.

#### 8. PDF Figure 7 (`figures/f6_expansion_control.pdf`, TeX lines 549–554)
- **Visual check:** **Completely fixed from rev4.** Two side-by-side log-scale panels (`Free-width joint PPL` in red: `2.33, 9.57, 20.16, 2.33, 31.07`; `Masked@8192 PPL` in green: `2.33, 2.33, 2.33, 2.33, 2.31`). Crystal clear and visually compelling.
- **Placement nit:** Because `figure` is placed at line 549 right after `\section{Readout mechanics}` with `[t]`, LaTeX floats it **backwards onto page 14 above Section 5.4**! Move it after line 563 or use `[!htbp]` / `\FloatBarrier` so it appears in Section 6.1.

#### 9. PDF Figure 9 (`figures/f5_cross_script.pdf`, TeX lines 770–775)
- **Visual check:** Stacked bar chart for `zh` (31 orange `el` + 6 purple `bg` + 3 gray `other`), `ja` (27 `el` + 13 `bg`), `hi` (10 `el` + 30 `bg`), and `iu-clean`.
- **Visual dishonesty nit on `iu-clean`:** For `iu-clean`, the bar is drawn as **exact 20 orange (`to el`) + 20 purple (`to bg`)**, with a small arrow at the top right saying `40/40 bg+el (split not reported)` (which also extends outside the right axis spine). Drawing a fake 50/50 orange/purple split when the `bg`-vs-`el` split wasn't recorded visually implies a 20/20 split! Either:
  1. Look up the actual `bg`/`el` split from `r3f_hull_geometry.py` / report `2026-09-11_pi-50_expansion-control-and-readout-operators.md` line 392, which **does** state `iu syllabic` likelihood router = **`el ×28 / bg ×12`**! (Verify against `ra2b_routdiag_iu_clean.txt` if accessible), OR
  2. Hatch/shade the `iu-clean` bar in a single combined color (`bg + el combined (split unlogged)`).

#### 10. PDF Figure 10 (`figures/pareto_legacy_rev5.pdf`, TeX lines 1186–1191)
- **Visual check:** Matches `rev5_paper_figures.py:130–153` (`EN, DE, ES` across 5 consolidation stages).
- **Two layout defects:**
  1. The footnote text `"Source: 2026-08-25 three-phase consolidation report; single-seed except replay row."` (`ax.text(0.01, 0.02, ...)`) is printed **directly on top of the bottom of the `Sequential endpoint` blue/orange/green bars**, reducing legibility. Move that note into the LaTeX figure caption instead of inside the plot area.
  2. On page 27 of the PDF, Figure 10 floats **above** the heading `A Legacy consolidation comparison`! Add `[!ht]` or `\usepackage{placeins}` / `\FloatBarrier`.

---

## 4. LaTeX, Typography, Citations & arXiv Packaging Audit

1. **Missing Figure & Table Cross-References in Text:**
   9 out of 10 figures (`fig:decayregimes`, `fig:leakage`, `fig:fcs`, `fig:ladder`, `fig:retention`, `fig:expansion`, `fig:ood`, `fig:xscript`, `fig:paretolegacy`) and Table 1 (`tab:predictions`) have `\label{...}` commands that are **never referenced via `\ref{...}` anywhere in the manuscript**! Every figure and table in an archival paper must be referenced in the prose (e.g., *"see Figure~\ref{fig:retention}"*, *"Table~\ref{tab:predictions} summarizes..."*).
2. **Garbled `\mathbb{1}` Glyph on Page 8 (Line 284):**
   Replace `\mathbb{1}` with `\mathbf{1}` (matches lines 287–289 and Appendix B.2).
3. **Doubled Word Typo (Lines 665–666):**
   `"Routed\nrouted serving remains within..."` $\to$ renders as `"Routed routed serving"` on page 16 of the PDF. Delete the duplicate `"routed"`.
4. **Raw Markdown Backticks & Straight Quotes in `.tex`:**
   - Line 85: `` `docs/reports/2026-09-11\_cross-script-rejection-suite.md` `` $\to$ renders in the PDF with mismatching curly single quotes `‘docs/reports/...’` instead of `\texttt{...}` (or better yet, remove internal repo file paths from an arXiv preprint or group them in a Reproducibility / Artifact Appendix!).
   - Line 723: `` `docs/reports/2026-09-11\_cross-script-rejection-suite.md` `` $\to$ same raw Markdown backticks.
   - Line 789: `"substantial"` uses ASCII straight double-quotes `"` instead of `` ``substantial'' `` (renders as two closing quotes `”substantial”` in T1 fontenc on page 19!).
   - Line 395: `\texttt{--init-from}` renders as an en-dash `-init-from` in T1 fontenc unless written `\texttt{-\/-init-from}`.
5. **Internal Repo / HAK-Bus Jargon & Unresolved Draft Pointers:**
   - **Title:** Drop `(Revision 5.0)` from `\title{...}` for arXiv (arXiv versions its own submissions `v1, v2, ...`; internal revision numbers in titles look like uncleaned working drafts). Also check `\date{September 28, 2026}` vs. actual submission date.
   - **AI Participation section (lines 1095–1098):** Currently points readers to *"drafted in `rev5-ai-disclosure-draft.md` in this revision's directory (pending operator re-review; the revision-4 draft is archived at `docs/papers/archive/rev4-ai-disclosure-draft.md`)"*. On arXiv, readers only download the PDF (or `.tex` tarball)—there is no `docs/papers/archive/` directory, and *"pending operator re-review"* signals an unfinished draft! Either fold a concise, finalized summary of the disclosure into an Appendix of the `.tex` file itself, or point to a stable public URL in `https://github.com/Saga-AI-Labs/bdh-cl` after finalizing operator review.
   - **"Two seats" & "the operator":**
     - Abstract (line 36), Section 1 (line 49), Section 2.3 (line 260), Section 5.5 (line 537), Section 7.3 (line 760): *"across two seats, two hosts, and two scripts"*. To an external arXiv reader unfamiliar with HAK bus terminology, *"two seats"* is opaque jargon (and *"two scripts"* sounds like Python scripts when you actually mean *writing systems*—Latin vs. Han/Devanagari—or vice versa!). Replace *"two seats"* with *"two independent agent instances/environments"* (or explain the term once), and disambiguate *"evaluation codebases"* vs. *"writing systems"*.
     - Lines 387, 984, 999: *"until the operator asked for it explicitly"*, *"The operator's framing"*, *"the operator's $20 \to 20{,}000$ question"*. Since the "operator" *is* the sole named author (Agon Sandro Buchholz), referring to the author in the third person as "the operator" reads strangely in an academic paper where the AI agents are not co-authors! Use standard authorial first person (*"until we tested it explicitly"*, *"Our framing"*, *"scaling from $20$ to $20{,}000$ territories"*).
6. **Repository URL Consistency:**
   Line 195 cites `\url{https://github.com/Saga-AI-Labs/bdh-cl}` (and `README.md` line 9 matches), while the local git remote is currently `asb-42/bdh.git`. Before posting to arXiv, ensure `https://github.com/Saga-AI-Labs/bdh-cl` is public and pushed to the exact commit cited so reviewers clicking the link don't hit a 404 or stale tree.
7. **Bibliography Check (`\thebibliography`, lines 1100–1178):**
   All 25 `\bibitem` keys are cited and all `\cite` keys resolve (0 missing, 0 uncited). Author lists, titles, venues, and arXiv IDs for `[1]`–`[25]` (`bdh`, `pgn`, `packnet`, `piggyback`, `supsup`, `expertgate`, `ewc`, `si`, `mas`, `gem`, `agem`, `shazeer`, `switch`, `gshard`, `chow`, `conformal`, `adamw`, `layernorm`, `rope`, `multilingual-cl`, `l2p`, `marin`, `engram`, `europarl`, `multiun`) were spot-checked and are accurate (note: the earlier rev4 `mas` author corruption is properly fixed to *Aljundi, Babiloni, Elhoseiny, Rohrbach, Tuytelaars*).

---

## 5. Prioritized Action Checklist for arXiv Submission

### Priority 1 — Blockers (Must Fix Before Uploading)
- [ ] **Regenerate `figures/f4_ood_scatter.pdf` (PDF Fig. 8)** from `a4_routed_cost.csv` + `ood_probe.csv` via `scripts/quinn/rev5_paper_figures.py` so the 20 trained languages plot at their actual best-route PPL (`2.36–6.47`) and routing advantage (`>= 5.5x`, with an explicit note on the final territory `lt` where full width = own prefix).
- [ ] **Fix Proposition 1 (`prop:soft`, line 348 & Proof B.5, lines 1250–1261):** State the gate domain $g_1, g_2 \in [0, 1]$ (with $\gamma \ge 0$, identity specialist $F_A = \mathrm{id}$), fix $(1+g_1)^2 + g_1 g_2 \varepsilon\delta = 1 \implies g_1(2 + g_1 + g_2\varepsilon\delta)=0$ (which only forces $g_1 = 0$ because $g_1, g_2 \ge 0$ and $\varepsilon\delta > 0$, or restore the specialist $x \mapsto x + \sigma(x)$ target $4a$ and evaluate at $\pm a$), and align the ReLU-kink explanation with the proof.
- [ ] **Fix Theorem 1 (`thm:dissoc`, lines 283–294 & Proof B.2, lines 1202–1219):** Replace `\mathbb{1}` with `\mathbf{1}` (fixing the garbled `c⋊` glyph on page 8), and correct the claim that `bdh.py` *"begins and ends with LayerNorm"* (`bdh.py` ends each level with `LN`, making level outputs zero-mean rather than input-shift-invariant; frame the $+c\mathbf{1}$ shift for abstract input-normalized depth-recurrent maps, or give the 2-neuron $|x^\top u| w$ non-zero suffix construction for literal `bdh.py`).
- [ ] **Fix Theorem 2 (`thm:criterion`, line 297):** Change $\bigcup_{\ell \le L}$ to $\bigcup_{0 \le \ell < L}$ so $\ell^* < L$ in the $(\Rightarrow)$ proof holds without edge-case failure at $\ell^* = L$, and write $\mathrm{emb}(x)$ instead of $E(x)$ in B.3.

### Priority 2 — Important Presentation & Precision Fixes (Strongly Recommended)
- [ ] **Fix Equation typo on line 132:** `\nu=\operatorname{relu}(x@E)` $\to$ `u=\operatorname{relu}(x@E)`.
- [ ] **Clean up `f_architecture.pdf` (Fig. 1):** Fix arrow colliding with `"old prefix"` text, remove stray bottom line, and connect `$E$` to `$u \odot v$`.
- [ ] **Clean up minor figure glitches:**
  - `f1_ladder_curves.pdf` (Fig. 5): Note in caption that RA2 used a different mid-ladder language permutation (so x-axis is phase number for red points, matching by language at phases 1–5, 19, 20); nudge green text left of right border.
  - `f5_cross_script.pdf` (Fig. 9): Either plot the true `iu-clean` split (`28 el / 12 bg` if verified) or use a single combined bar color instead of a synthetic 20/20 split.
  - `pareto_legacy_rev5.pdf` (Fig. 10): Move the bottom-left `"Source: ..."` text out of the bars into the caption.
  - `decay_regimes.pdf` (Fig. 2): Fix `"Measured (es -> , sd 2.2e-7)"` missing target and `0.8928` vs `0.8927` rounding note.
  - `leakage.pdf` (Fig. 3): Define $j$ and the $j \le 0.15$ budget in the caption.
- [ ] **Add `\ref{...}` citations in the text** for all 10 figures and Table 1, and tighten float placement (`\FloatBarrier` before Sections 4, 6, and Appendix A/B).
- [ ] **Verify and clarify `route_neuron_mask` slice vs. prefix in Section 2.1/2.2** (`keep[n_old:]` new-tile mask vs. `[:n_new]` cumulative-prefix mask during training, and signpost the $\alpha=0.9$ loss in the Abstract).
- [ ] **Small factual/precision cleanups:**
  - Line 212: `"attention unfrozen"` $\to$ `"attention parameter-free (RoPE prefix preserved)"`.
  - Line 397: `$21\times 20$` $\to$ `$20\times 20$`.
  - Lines 418–428: Note `fi` (Uralic) and `ro` (Romance) sort by byte-statistical cluster rather than linguistic family.
  - Lines 622–623, 638: Replace `"bit-identical"` for `block-average`/`log-norm` with `"invariant up to LayerNorm $\epsilon$ ($\le 0.04\%$)"` to match `readout_operators.csv`.
  - Line 665: `"Routed routed"` $\to$ `"Routed"`.
  - Lines 85, 723, 789, 395: Fix raw Markdown backticks, straight `"substantial"` quotes, and `--init-from` ligature.
  - Title & AI Disclosure: Remove `(Revision 5.0)` from title, replace `"pending operator re-review"` draft pointer with self-contained appendix or live public URL, and neutralize internal HAK-bus phrasing (`"two seats"`, `"the operator"`).
