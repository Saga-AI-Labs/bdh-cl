# Audit: "The Dragon Hatchling" (BDH) — mathematical soundness

Scope: equations, claims, and observations as pasted (TeX source in conversation). Verified items listed for context; issues are separated into (A) demonstrable errors, (B) proof gaps, (C) unsupported conclusions.

## Verified as correct (context)
- BDH-GPU integral form (eq:integral / eq:bdh / eq:kvstate) — unrolled and checked consistent; Hebbian entries decay by exactly $t-\tau$ factors of $U$; code listing's `tril(diagonal=-1)` matches strict $\tau < t$. No off-by-one.
- BDH ≡ BDH-Normfree under $G_x^e-G_x^i = D_xE$, $G_y^e-G_y^i = D_yE$, $G_s = \mathbf 1$.
- Claim claim:graphs (excitatory/inhibitory split, $m = O(nd)$ via $H^2[V]$) — correct.
- Claim obs:fscore (selective activation via JL inner products + union bound) — essentially correct.
- Claim claim:attentionformal — proof correct modulo a silent assumption that $U$ is diagonal; content is near-tautological (values are pre-compressed through 2d hub neurons via $A(y) = E'y$).
- SBM modularity formula $\mu = \frac{k-1}{k}\,\frac{p-q}{p+(k-1)q}$ — correct.

## A. Demonstrable errors
1. **ReLU notation (Notation section).** $\relu{z} := \max_{i\in\{1..n\}}\{0, z_i\}$ returns a scalar max, not the coordinate-wise ReLU intended everywhere else.
2. **Protocol table (tab:protocolx) vs. eq:bdhgraph — sub-round ordering inconsistency.** Eq:bdhgraph (and §3.1's compute-then-communicate order) matches the table's σ-decay timing only under one uniform ordering; under either ordering the equivalence in Obs. obs:protocol_equiv ("straightforward to verify") breaks: round 4l+1 performs the Hebbian write $Y(i),X(j)\to\sigma_l(i,j)$ and then reads a freshly zeroed Y, and rounds 4l+1..3 require communicate-then-compute. Also an orientation/transposition mismatch: the protocol readout $A(j) += X(i)\sigma(i,j) = (\sigma^\top x)_j$ vs. eq:bdhgraph's $\sigma x$. Repairable, but the claimed proof ignores sub-round ordering entirely.
3. **Claim obs:rw (Markov propagation), in-degree.** The L1 error bound $2\eps^* r$ implicitly needs $\mathrm{in\text{-}degree}(i) \le r$, but the hypothesis only bounds out-degree. Counterexample: out-degree 1 everywhere, all nodes point at node 1, $v = e_1$ ⟹ $G'v = \mathbf 1$, error $2\eps n$, not $O(\eps)$.
4. **Claim obs:rw, dimension bound.** Stated $d = O(r^3 \log n / \eps)$ contradicts the proof's own requirement $d = O(r^2 \log n/\eps^2)$ (from $\eps^* = \eps/r$ and error $\sim\sqrt{\log n/d}$). The footnote's fix is acknowledged as hand-wavy.
5. **Obs. obs:prob, L1 = TVD "equality".** $\|x_1 - x_2\|_1 = 2\alpha(1-o(1))$, while TVD $= \alpha$. Factor-2 error (equality should be TVD $= \tfrac12\|x_1-x_2\|_1$).

## B. Proof gaps
6. **Obs. obs:sbm (in-cluster propagation).** The threshold $\mu > (1/p)\sqrt{\log n/d}$ does not follow from Claim obs:fscore: the lemma's setting ($u_\alpha = 1/\sqrt{|A|}$) doesn't match the application ($u = Hz$ is 0/1, readout scales with $\sqrt{|A|}$, and $w_j \propto |C_j|/\sqrt{|B_j|}$, not ρ). The actual separation condition is roughly
   $\dfrac{p^2 - 2pq - (k-2)q^2}{p + (k-1)q} \gtrsim \sqrt{\log n/d}$,
   which is *stricter* than stated (e.g. $k=2$, $p=0.5$, $q=0.1$: derived ≈ 0.125 vs. stated ≈ 0.167 at $c\sim1$).

## C. Unsupported / false conclusions
7. **Obs. obs:prob, affinity-ratio bound $O(\alpha^{-2}n^{-1})$.** The true ratio $\langle x_1,x_2\rangle/\langle x_1,x_1\rangle \approx \alpha$ (overlap ≈ $\alpha^2 n$, $|x_1| = \alpha n$) in the independent regime, and $\approx 1-\alpha$ in the noisy-copy regime. The claimed bound is vacuous for small α and **false** once $\alpha \gtrsim n^{-1/3}$ (e.g. $n=10^6$, $\alpha=0.1$: true ≈ 0.1 vs. claimed ≤ 10⁻⁴). Verified numerically across regimes.
8. Remaining unaudited: eq:lowrank's $\|\cdot\|_{+\infty}$ norm, scaling-law/hyperparameter claims (Tab. translation, Appendix B), σ state-capacity / Claim claim:linearinformal, model-merging and no-BPTT experimental claims.

## Summary
Core linear-algebra identities (equivalence of formulations, low-rank rewiring, attention form) are sound. The main defects cluster in the *graph-protocol* layer: an ordering inconsistency between the communication protocol and the equations, an in-degree assumption used but not stated, inconsistent dimension bounds, and the obs:prob estimates, which are wrong by a factor of 2 (TVD) and by orders of magnitude in the wrong direction (affinity bound).
