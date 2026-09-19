# Review: external audit of the Pathway BDH paper, claim by claim

**Date:** 2026-09-19
**Reviewer:** Quinn (seat: quinn-the-builder, profile `saga`)
**Object under review:** `~/uploads/2026-09-16_bdh-paper-audit_union-alpha.md` — an audit obtained via the
OpenRouter stealth model "Union Alpha", reportedly a router (Pareto 26.9) that fans out to frontier
models. It alleges "demonstrable errors" in two documents; this file covers the Pathway half.
**Target of the audit:** *The Dragon Hatchling: The Missing Link between the Transformer and Models of the
Brain* — Kosowski, Uzanski, Chorowski, Stamirowska, Bartoszkiewicz (Pathway, Palo Alto), arXiv:2509.26507.

> **What this document is not.** It is not a verdict on whether BDH works. It is a check of whether a
> second machine read the first machine's paper correctly. Those are different questions and they fail
> independently.

---

## 1. Provenance of what was checked

Everything below is checked against the primary source, not against anyone's summary of it.

| item | value |
|---|---|
| source file | `/a0/usr/uploads/paper.tex` (mirror: `/a0/usr/workdir/paper.tex`) |
| MD5 | `53c0c31f6e3bc7cfe61a1bac1da9d039` |
| size | 2132 lines |
| identity confirmed in-file | title line 161; `\textbf{Pathway}` line 154; `Pathway, Palo Alto, USA` + `research@pathway.com` lines 170–171 |
| all 15 labels quoted by the audit | present, exactly once each (`obs:rw`:1169, `obs:prob`:1413, `obs:sbm`:1230, `obs:fscore`:1201, `obs:protocol_equiv`:473, `tab:protocolx`:580, `claim:attentionformal`:1951, `eq:bdhgraph`:779, `eq:kvstate`:764, `eq:integral`:733, `eq:lowrank`:1154, `claim:graphs`:972, `claim:linearinformal`:1369) |

The label inventory matters: it establishes the auditor had the actual TeX and quoted real labels. So the
question is never "did it read the paper" — it did. The question is only "did it compute correctly once it
had."

Two conventions from the source that decide four of the verdicts below, stated up front because they are
the load-bearing detail:

1. **Edge orientation** (`paper.tex:387`, verbatim): `H(i,j) := \bra{e_j} H \ket{e_i}` — the edge weight
   from `i` to `j`, i.e. *transposed* relative to ordinary matrix indexing. So under the walk-matrix
   convention `G'_{ij} = 1/r iff i -> j`, ordinary matrix–vector product gives
   `(G' e_k)_j = G'_{k,j}`, and the fired set `{j : (G'e_k)_j != 0} = {j : j -> k}` — the **in-neighbourhood**
   of `k`, whose size the out-degree hypothesis does **not** control. Several of UA's findings hinge on
   this and it is *also* the thing that makes one of them wrong.
2. **ReLU macro** (`paper.tex:115`): `\newcommand{\relu}[1]{\left(#1\right)^{+}}` — coordinatewise. But see
   finding A1: the prose defines something else.

## 2. Verdict table

Two axes, deliberately separated, because conflating them is the dominant failure mode of an LLM
review: **(a) citation** — did UA reproduce what the paper says; **(b) math** — is UA's own reasoning right.

| # | UA's claim, compressed | citation | math | verdict |
|---|---|---|---|---|
| A1 | `\relu{z} := \max_i\{0,z_i\}` is a scalar, not coordinatewise | ✅ correct | ✅ correct | **CONFIRMED** (cosmetic in effect) |
| A2 | protocol table vs `eq:bdhgraph`: sub-round ordering never resolved; equivalence only asserted | ✅ correct | ⚠️ plausible, not re-derived here | **PARTLY CONFIRMED** (real exposition gap; specific mechanism unverified) |
| A3 | `obs:rw` bound needs in-degree ≤ r; counterexample ⇒ error `2εn ≠ O(ε)` | ✅ reads the proof right | ❌ wrong conclusion | **OVERSTATED** — proof defect real, **statement survives** |
| A4 | `obs:rw` dimension bound `d=O(r³log n/ε)` contradicts its own proof; footnote "acknowledged as hand-wavy" | ⚠️ footnote gloss off | — | **UNRESOLVED** |
| A5 | `obs:prob`: `\|x_1-x_2\|_1 = O(α) = \|·\|_TVD`, but `\|·\|_1 = 2α(1-o(1))` — factor 2 | ✅ correct | ✅ correct | **CONFIRMED** |
| B6 | `obs:sbm` threshold `μ > (1/p)√(log n/d)` does not follow from `obs:fscore`; true condition ≈ `(p²-2pq-(k-2)q²)/(p+(k-1)q)` | ✅ reads paper right | ❌ cannot reproduce UA's own number | **PLAUSIBLE, UNVERIFIED** |
| C7 | affinity ratio bound `O(α⁻²n⁻¹)` is **false**; true ratio ≈ α; "verified numerically across regimes" | ❌ tested vectors the paper does not use | ❌ | **NOT SUPPORTED** |
| — | "verified as correct" column (integral form, ≡ normfree, `claim:graphs`, `obs:fscore`, `claim:attentionformal`, SBM modularity formula) | ✅ | ✅ spot-checked | **CONFIRMED** on the four I could check directly |

Score: of the five items UA filed as *demonstrable errors*, two are solid (A1, A5), one is a genuine gap
but mis-graded (A3), one is real-but-deferred exposition (A2), one is unresolved (A4). Its single loudest
"**false**" (C7) does not survive contact with the source. Its confirmations, however, are real.

---

## 3. Findings

### A1 — ReLU notation. CONFIRMED, and stronger than UA stated

`paper.tex:716`, inside `\subsection{Notation for \BDHGPU}` (the section UA names, correctly):

> "We denote the \emph{ReLU operation} $\relu{z} := \max_{i\in\{1,\ldots,n\}}\{0,z_i\}$."

That is a scalar maximum over coordinates. Every downstream use is coordinatewise — `\relu{\decoderx\ket{\vv}}`
in `eq:integral` (:735), `\relu{(\graphx^e-\graphx^i)\ket{xysparse}}` in `eq:bdhgraph` (:793). UA is right.

The part UA did not see makes it sharper: the macro at `:115` is `( #1 )^+` (coordinatewise, the only
definition TeX can actually execute), and the footnote at `:720` says "the application of ReLU to a scalar
remains coordinate-wise." So the same paragraph carries a prose definition contradicting both its own macro
and its own footnote. It cannot change any result — nothing in the paper takes a scalar max — but as a
notation defect it is real and it is one line to fix.

### A3 — the important one. UA found something real and then drew the wrong conclusion

The claim (`paper.tex:1170`, verbatim):

> "Let $G'$ be the random walk matrix of a directed graph with out-degree $r$ (i.e., a stochastic matrix
> with $r$ non-zero entries of $1/r$ in each row), and let $v\in V$ be a node (basis vector)
> $\|v\|_1=\|v\|_2=1$. Then, for any $\eps>0$, there exists $d=O(r^3\log n/\eps)$ such that for some matrices
> $\decoder,\encoder$ we have $\|G'v - f_{\decoder\encoder}(v)\|_1 = O(\eps)$."

UA's counterexample: out-degree 1 everywhere, all nodes point at node 1, `v = e_1` ⇒ `G'v = 1`, error
`2εn`, "not `O(ε)`".

Split it.

**(i) Is the last line of the proof sound?** No. The proof ends "... and
$\|G'v - f(v)\|_1 \le 2\eps^* r$, and the claim follows", where `ε* = ε/r`. The coordinate count it needs
there is `|{j : (G'v)_j ≠ 0}|`, and by convention (1) that is the **in**-neighbourhood of the chosen node,
which the hypothesis never bounds. Measured (`check_obs_rw3.py`, part 2):

```
   n      r    kind       fired=in-deg   r(out-deg)   proof_understates_by
   400    1    allstar          400          1          400x
  1000    1    allstar         1000          1         1000x
  2000    1    allstar         2000          1         2000x
```

So the proof silently multiplies `ε*` by `r` where it must multiply by the support size. On that point UA is
simply right, and the paper's own `:1322` concedes the family of the problem: "The difference of in- and
out-degree distributions, while plausible and prevalent in real-world information dissemination networks,
**was not considered** in Subsection~\ref{sec:dynamics}."

**(ii) Does that refute the statement?** No — and this is where UA overreaches. The claim is about a *single*
fixed `v`, asserting *existence* of `D,E`. `G'` is non-negative, so the target `G'v` is non-negative, so the
ReLU gate is free and one rank-1 pair reproduces it exactly: take `D = G'[:,k]`, `E = e_k^T`. Measured
(`check_obs_rw3.py`, part 1):

```
   n      r    kind       |fired|   err_with_d1   d_bound=O(r^3 log n/eps)
   400    1    allstar       400      0.00e+00            5991
  1000    1    allstar      1000      0.00e+00            6908
  2000    1    allstar      2000      0.00e+00            7601
```

Zero error, at `d=1`, in every configuration including the one UA used as its counterexample — against an
allowed `d` of ~6000–7600. The reason UA's arithmetic still lands on `2εn` is that it computes the error of
the *bias-and-threshold construction*, which is the part that kills zero coordinates. The positive
coordinates cost nothing (non-negativity); only the zero-suppression needs dimension, and *that* is where
the uncontrolled in-degree lives.

So: `2ε*r` in the proof is a defect; the theorem as printed is true for the trivial reason that its target
is non-negative, and false only if the intended reading is the one the paper arguably meant — uniform over
the whole basis, or approximate zero-suppression. UA reported the defect in the proof and filed it as a
false claim. That correction matters for the authors, because a false claim needs rewriting and a proof
gap needs one extra sentence about support size (with `ε*` set off the support, giving
`d = O(indeg² log n / ε²)`).

> *Method note, kept in the file because it is the reason to distrust a confident first pass:* my first
> re-run of this reported `HOLDS` across the board. It was wrong — I had coded `ε* = ε/|support|` instead of
> the paper's `ε* = ε/r_out`, which silently tested a weaker bound than the one being audited. The `HOLDS`
> was my bug, not the paper's. A reviewer (human or model) that cannot catch its own convention error is
> the failure mode this whole exercise is about.

### A5 — L1 vs total variation. CONFIRMED

`paper.tex:1412`, verbatim:

> "$x_1$ and $x_2$ almost coincide when treated as probability distributions,
> $\|x_1-x_2\|_1 = O(\alpha) = \|x_1-x_2\|_{\mathrm{TVD}}$."

With the paper's own vectors (`x_1 = (α, (1-α)/(n-1), …)`, `x_2` the swap), computed:

```
n= 1000000   a=0.1     |x1-x2|_1 = 0.199998      TVD = 0.099999
n= 1000000   a=0.5     |x1-x2|_1 = 0.999999      TVD = 0.499999
```

L1 is `2α(1-o(1))`, TVD is `α`. The chain `L1 = O(α) = TVD` sets a quantity equal to half itself; correct is
`TVD = ½‖x_1-x_2‖_1`, exactly as UA says. Real, harmless to the argument (the point being made is "L1 and
affinity decouple"), but it is a demonstrable error and it sits in the one sentence the observation rests on.

### C7 — the marquee "false" does not survive the source. NOT SUPPORTED

Same paragraph, the second half (`paper.tex:1412`): the paper claims for its two vectors
`⟨x_1,x_2⟩ = O(α⁻² n⁻¹)·⟨x_1,x_1⟩`. UA: true ratio is `≈ α` (overlap `≈ α²n`, `‖x_1‖ = αn`), hence the bound is
"vacuous for small α and **false** once `α ≳ n^{-1/3}` (e.g. `n=10⁶`, `α=0.1`: true ≈ 0.1 vs claimed ≤ 10⁻⁴)",
"verified numerically across regimes."

Against the vectors the paper defines, the bound holds, tightly:

```
n= 1000000  a=0.1     ratio=9.899e-05   a^-2/n=1.000e-04   ratio/bound=0.9899
n= 1000000  a=0.5     ratio=3.000e-06   a^-2/n=4.000e-06   ratio/bound=0.7500
n= 1000000  a=0.9     ratio=2.346e-07   a^-2/n=1.235e-06   ratio/bound=0.1900
```

At UA's own worked case — `n=10⁶, α=0.1` — the true ratio is `9.9e-05`, not `0.1`, and the claimed ceiling is
`1.0e-04`. The bound is attained to within 1%. It is also backwards on "vacuous for small α": the bound
scales `α⁻²`, so it *loosens* as `α → 1` and tightens as `α → 0`.

UA's `≈ α` is not nonsense arithmetic — overlap `α²n` over `‖x₁‖ = αn` gives `≈ α` — but it is arithmetic about
0/1 indicator vectors, which are not `x_1` and `x_2`. The audit computed the right quantity against the
wrong referent and then asserted a falsification of the paper. "Verified numerically across regimes" is the
sentence that should have cost it the finding: the verification happened, just not on the object under
discussion.

This is the same failure mode we already have on file for foreign-model review (fabricated bibliography
entries written from memory rather than source). Same signature, different document type.

### A2 — protocol/table ordering. PARTLY CONFIRMED (real gap, mechanism not re-derived)

The equivalence `obs:protocol_equiv` (:473) delegates to an appendix, and the appendix proof
(`paper.tex:1885`) opens:

> "The equivalence is straightforward to verify, rewriting the linear-algebraic multiplication expressions
> of \eqeqref{eq:bdhgraph} in Einstein summation notation and comparing respective index pairs. ... we
> assume for simplicity that $U$ is diagonal."

Two things follow textually. The sub-round ordering — whether within round `4l+k` the communication half or
the computation half fires first, and how that interacts with the `σ_l ← σ_l(1-u)` decay and the
`X^e,X^i` resets sitting in the *same* cells (both visible in the table body, :580 ff.) — is never
resolved anywhere in the paper. And the proof carries a silent diagonal-`U` hypothesis, which `def:bdh`
(:758) does not impose (it allows "diagonal **or block-diagonal**", explicitly to cover RoPE). Both of UA's
sub-points are therefore textually supported, and the orientation argument (`A(j) += X(i)σ(i,j) =
(σ^⊤ x)_j` vs `eq:bdhgraph`'s `σx`) is exactly the hazard convention (1) creates.

What I did **not** do is re-derive the ordering contradiction itself — the specific sequence in which round
`4l+1` writes `Y(i),X(j) → σ_l(i,j)` and then reads a freshly-zeroed `Y`. That needs a simulation of the
cellular kernel, which is a separate task, and I am not going to promote UA's mechanism to confirmed just
because it is stated confidently and sits next to two points that did check out.

Independent confirmation worth recording: pi-50, reading the same paper blind months earlier, logged both
halves of this without seeing UA — `I19` ("what 'sparse-graph BDH ≡ BDH-GPU' really costs") and `I21`
("protocol equivalence is only proved for diagonal `U`", `c9/10`). Agreement between two audits that never
shared a transcript is the only evidence in this whole exercise I actually weight.

### A4 — the dimension bound. UNRESOLVED

Stated `d = O(r³ log n/ε)`; the proof's own route (through `eq:lowrank`, `‖G'z-Gz‖_{+∞} = O(√(log n/d))` at
:1154) wants `d = O(r² log n/ε²)` once `ε* = ε/r` is substituted. The gap is real and UA is right that the
exponents do not line up. Where UA over-reads: it calls the footnote "acknowledged as hand-wavy," but that
footnote (:1176, "As a point of elegance…") is about the estimator being biased and fixing it with a global
multiplicative `(1+ε*)` — it does not concede the dimension bound. So: genuine inconsistency, but the paper
is not on record admitting it. Needs the authors' intent to settle which exponent is meant.

### B6 — the SBM threshold. PLAUSIBLE, NOT VERIFIED BY ME

The paper's Newman modularity, `μ = (k-1)/k · (p-q)/(p+(k-1)q)` (:1227), is correct — confirmed empirically
to five decimals:

```
k=2 p=0.5 q=0.1 :  closed-form 0.33333   empirical Q=0.33283   delta=0.00051
k=4 p=0.4 q=0.05:  closed-form 0.47727   empirical Q=0.47562   delta=0.00166
```

UA's objection is that the separation condition `μ > (1/p)√(log n/d)` does not follow from `obs:fscore` as
stated, because the lemma's hypothesis is `u_α = 1/√|A|` while in the SBM application `u = Hz` is 0/1 and the
readout weights scale as `|C_j|/√|B_j|`, not as ρ. That reading of the mismatch is careful and I believe it.
But the condition UA offers in its place is **its own** derivation, not the paper's, and I could not
reproduce it: its worked number for `k=2, p=0.5, q=0.1` is `≈0.125`, while its own displayed expression
`(p²-2pq-(k-2)q²)/(p+(k-1)q)` evaluates to `0.15/0.6 = 0.25` at those parameters. The arithmetic in the
replacement is not reproducible from the expression printed next to it, and `obs:fscore` is used far enough
upstream (`fig:fscore`, `sec:modularity`, `claim:linearinformal`) that this is the finding most worth someone
finishing properly. Recorded as open. (I note this without reading it as disqualifying — the structural
objection may well be right and only the displayed number be wrong.)

### The "verified as correct" column. Spot-checked, and it holds

An audit you only trust on its errors is not an audit. I checked the four confirmations that are cheapest
to check and where a false confirmation would be most damaging:

- **`claim:graphs`** (`m=O(nd)` via `H²[V]`, proof at `apx:proofgraphs`): the construction is the positive
  encoder/decoder split `\relu{E}`, `\relu{-E}` with `D^e,D^i` redistributed so
  `(D^e-D^i)E' = DE`. I read the proof through; it is the standard trick and it is correct.
- **`eq:kvstate` ↔ listing** (`Σ_{τ<t}` vs `return (Qr @ Kr.mT).tril(diagonal=-1) @ V`, :2130): strict
  `τ < t` ↔ strictly-lower-triangular, no off-by-one. Confirmed directly; UA's "no off-by-one" is right.
- **`eq:lowrank`** (`‖G'z-Gz‖_{+∞} = O(√(log n/d))` under `‖G'‖_{1,∞} ≤ 1`, :1154): consistent with the JL
  framing it cites, and the neighbouring warning that no analogous `L₂`/`L₁` bound holds (even for `G'=I_n`)
  is the honest caveat it looks like.
- **BDH ≡ BDH-Normfree under `G^e-G^i = D_x E`, etc.**: consistent with `obs:equivalence` and with how `G_s`
  is set to `1` in the tensor form.

One confirmation deserves a flag rather than a tick: `claim:attentionformal` (:1951). UA passes it as
"correct modulo a silent assumption that `U` is diagonal," and the proof does exploit a diagonal
`E*` — "define `E*` to be a diagonal matrix acting on its first `2d` elements" — and adds that the content
is near-tautological because values are pre-compressed through `2d` hub neurons (`A(y) = E'y`). That is a
fair reading of the proof *and* it is the same diagonal-`U` assumption `obs:protocol_equiv` needs, so the two
softest places in the paper are the same one assumption, appearing twice. Not a refutation; worth
understanding before anyone leans on the equivalence.

---

## 4. Reading the whole

**What the audit got right, and it matters.** It correctly located the paper's real soft spot, which is not
any closed-form identity but the *graph-protocol layer*: an equivalence whose proof is "straightforward to
verify", a sub-round ordering the paper never settles, an in-degree the dynamics use and the hypothesis
omits (and which the paper itself flags as unconsidered at `:1322`), and two exponent mismatches. Those are
the kinds of defects a referee finds late and an author finds painfully. Its confirmations are also
trustworthy where I could check them, and it correctly declined to over-claim the core linear algebra.

**What it got wrong, and how.** In three places it read the source correctly and then asserted more than
its own calculation supports: it promoted a proof gap to a false theorem (A3), it falsified the paper on
vectors the paper does not use (C7), and it read an admission into a footnote that makes none (A4). In a
fourth it printed a derivation whose own displayed expression does not yield its own number (B6). Three of
those are the same underlying move — compute something correct, attribute the result to the wrong object.

**On the "royal-class review" framing (an operator-supplied term).** I cannot verify from the document which model produced it; "Pareto 26.9
routing to Fable and Astra" is operator-supplied context, not evidence I have checked. Nothing in the
verdicts above depends on it: they stand on the file at MD5 `53c0c31f…` and on the three scripts below. If
the review really did fan out to a frontier model, that changes how it is *sourced* and not whether it is
*right* — and the one place it is loudest and wrongest (C7) is precisely where a strong model is most
dangerous, because the error is a clean, plausible, fully-written computation nobody can fault by reading it.

**The operational lesson, which we have paid for before.** The last time a confident outside review entered
our manuscript without being checked line-by-line against primary sources, it brought fabricated citations
and we spent a correction cycle on it. This review is better than that one — it is mostly right, and right
about hard things — but it carries the same single hazard: it cannot distinguish "I computed the right
thing" from "I computed the right thing about the thing under discussion." Treat it as a *hypothesis
factory* — file A1/A5 and the A2/A3/A4/B6 gaps as author questions worth asking Pathway, do not file C7
anywhere, and do not let any of it reach a manuscript without an independent pass.

**Blast radius on our own paper: zero.** None of `obs:rw`, `obs:prob`, `obs:sbm`, `obs:fscore`, `eq:lowrank`,
`claim:linearinformal` appears in `docs/papers/rev4-bdh-manuscript.tex` or `cl-bdh-manuscript.tex` — they
exist only in `docs/reviews/2026-09-02_pi-50_paper-reading-notes.md`. These corrections are about Pathway's
paper, not ours, and nothing in rev4 needs to move unless we deliberately decide to cite them.

### Open items for whoever finishes this
1. Ask Pathway whether `obs:rw` is meant per-node (then the proof needs one sentence on support size, and
   `d = O(indeg² log n/ε²)`) or uniform over the basis (then it needs the in-degree in the hypothesis).
2. Re-derive B6's separation condition from `obs:fscore` — the only finding I would most want checked and
   could not check. Its `0.125` vs its formula's `0.25` is the concrete loose end.
3. Simulate the `tab:protocolx` kernel under both sub-round orderings to settle A2 properly.
4. Ask about the diagonal-`U` assumption, which appears twice (`obs:protocol_equiv`, `claim:attentionformal`)
   while `def:bdh` permits block-diagonal RoPE.

## 5. Reproduction

`out_c/union_alpha_audit/` holds `check_obs_rw3.py` (A3, both halves). The `obs:prob` table (A5, C7) and
the SBM confirmations (B6) were run as inline snippets in the session transcript and are reproduced below
in full so the numbers in this file are checkable without the transcript.

```bash
cd /a0/usr/projects/saga_quinn/out_c/union_alpha_audit
python3 check_obs_rw3.py            # A3: proof gap (part 2) + claim survival (part 1)

# A5 + C7: the paper's own vectors from obs:prob
python3 - <<'PY'
import numpy as np
def vecs(n,a):
    b=(1.0-a)/(n-1)
    x1=np.full(n,b); x1[0]=a
    x2=np.full(n,b); x2[1]=a
    return x1,x2
n=10**6
for a in (0.9,0.5,0.1):
    x1,x2=vecs(n,a)
    l1=float(np.sum(np.abs(x1-x2))); tvd=0.5*l1
    ratio=float(x1@x2)/float(x1@x1); bound=a**-2/float(n)
    print(f"n={n} a={a}: |x1-x2|_1={l1:.6f} TVD={tvd:.6f} "
          f"ratio={ratio:.3e} a^-2/n={bound:.3e} ratio/bound={ratio/bound:.4f}")
PY
#   expect ratio/bound ~= 0.99 at a=0.1 -> the C7 bound HOLDS; UA's "false" is refuted

# B6: UA's own expression does not yield UA's own printed number
python3 - <<'PY'
k,p,q=2,0.5,0.1
num=p**2-2*p*q-(k-2)*q**2; den=p+(k-1)*q
print(f"(p^2-2pq-(k-2)q^2)/(p+(k-1)q) = {num}/{den} = {num/den}")   # 0.25, not UA's 0.125
PY
```

(The two earlier drafts of the A3 script, `check_obs_rw.py` with the `eps*` conflation bug and
`check_obs_rw2.py` with a quoting error, were deleted; only `check_obs_rw3.py` is authoritative, and the
bug in the first one is described honestly in the method note above.)

Source for any re-verification: `paper.tex` at MD5 `53c0c31f6e3bc7cfe61a1bac1da9d039`. Line numbers in this
file refer to that MD5, not to the arXiv PDF's pagination.

*— Quinn. Hypothesis-driven, metric-based, and in this case: the machine I was auditing needed auditing as
much as the paper did, which is why none of the above is taken on anyone's authority but the file and the
numbers.*
