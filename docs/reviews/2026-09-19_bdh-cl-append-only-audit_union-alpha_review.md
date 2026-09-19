# Audit of an audit: Union Alpha on *Append-Only Neural Memory* (rev 4.6)

**Subject under review:** `/a0/usr/uploads/2026-09-17_bdh-cl_append-only-neural-memory-audit_union-alpha.md`
MD5 `fb8ed65cbede7ca63ee9e26d6ad79c9b`, 15911 bytes, 65 lines, mtime 2026-09-19 04:38:06.
**Object it addresses:** our own manuscript, `docs/papers/rev4-bdh-manuscript.tex`, MD5 `dc2731b09bbb71c09b977c07a3e722db`, 1190 lines.
**Provenance of the reviewer:** operator-supplied context. A stealth OpenRouter model marketed as "frontier-level", reported as a router that may route to Fable and Astra. Neither the routing decision nor the model that actually worked is known. **Nothing below depends on that identity**, and no judgement here is weighted by it in either direction.

**Verification method.** Every claim is separated into the two things it actually is — *citation* (does the paper say what the audit says it says) and *computation* (is the audit's own arithmetic right) — and decided against primary sources:

- the TeX, read verbatim rather than filtered, for every quoted sentence;
- `docs/data/` and `docs/reports/`, for every measured number;
- `out_c/union_alpha_audit/check_manuscript_audit.py`, for every arithmetic claim — **recomputed, not accepted**. The manuscript is the object under attack, so no quoted number was ever checked against the manuscript's own prose.

This is the same procedure applied an hour earlier to the companion audit of the Pathway paper (`2026-09-19_bdh-paper-audit_union-alpha_review.md`), which produced the failure mode this document watches for: an auditor performing correct arithmetic against the wrong referent.

**Headline.** The audit is substantially right about our paper and wrong about its own arithmetic in one place we should not have accepted unchecked. Of seventeen claims: **ten hold**, **four hold only in part**, **two do not hold as stated**, and **one is right in substance while its stated number is wrong**. The single most consequential defect is the one the audit did find and rank first — an unproved `[PROVED]` on `cor:prefix`. (An earlier draft of this review named a second, deeper defect, that the forgetting numbers had no artifact; that was my error, and it is corrected in §C.7 rather than erased.)

---

## 0. Provenance of the audit itself

Established before any claim was read, because a companion upload had already arrived with the wrong contents.

- It is **not** the Pathway document: 0 occurrences of `obs:rw`, `tab:protocolx`, `Dragon Hatchling`, `eq:bdhgraph`; distinct MD5 from `2026-09-16_bdh-paper-audit_union-alpha.md`.
- All **15** referenced TeX labels exist, each exactly once, in our rev4: `prop:soft` 269, `sec:decay` 173, `thm:dissoc` 227, `thm:criterion` 233, `cor:prefix` 247, `lem:zf` 262, `prop:amp` 278, `rem:exp` 284, `fig:fcs` 303, `sec:fcs` 307, `sec:ra2b` 370, `sec:readout` 461, `sec:ood` 622, `sec:xscript` 674, `app:meas` 1157.
- Its attribution is correct: rev4:25 reads `\author{Agon Sandro Buchholz \\ \small Saga AI Labs}`. The audit's title line `(Buchholz, rev 4.6)` is not a signature artifact; the reviewer read the real file.

So the working question was never whether the audit had the text. It was whether it computed against it correctly.

---

## 1. A — demonstrable errors

### A.1 — `prop:soft` prints the wrong constant. **HOLDS. Confirmed against us, by computation.**

Our own sentence, verbatim (rev4:269):

> `$(1{+}g_1)^2+g_1g_2\varepsilon\delta=4$ for all input magnitudes $a>0$`

The audit derives `=1` from the paper's own one-step state `x_1 = (a(1+g_1), g_2\delta a)` and the two-step first-component condition `a(1+g_1) + g_1\sigma(a(1+g_1)) + g_1\varepsilon g_2\delta a = a` on the branch `1+g_1>0`.

I did not accept the derivation. I instantiated it numerically — no CAS: `sympy` is absent from both runtimes and a guessed import died twice, so the check was rewritten as a polynomial identity under random instantiation, which decides it at least as firmly. For each of six random `(a, g_1, \varepsilon, \delta)` points I solved the *displayed* equation for `g_2` at each candidate constant, then tested whether that pair satisfies the paper's **original, undivided** two-step condition:

```
R = 1  satisfies the paper's own condition in 6/6 probes
R = 4  satisfies the paper's own condition in 0/6
```

Two things follow, and they are different.

The printed `=4` does not satisfy the paper's own stated state. **The error is in our text and the audit found it.**

The proposition's *conclusion survives*, as the audit itself says. At `g_2=0` the requirement reduces to `(1+g_1)^2 = 1`, forcing `g_1=0` in an open range — which is exactly our own later reduction at rev4:1145, `g_2=0` the first component reduces to `g_1(1+\sigma(a(1+g_1)))=0`. So this is a wrong constant in a displayed equation, not a false theorem, and the fix is to print `1`.

The audit's second point — that the derivation silently lives on the positive-ReLU branch while quantifying "for all `a>0`" — also holds: the construction never visits `1+g_1<0`, and the universal quantifier is doing work the argument does not discharge.

### A.2 — the decay reconciliation, and "five decimal places". **RIGHT IN SUBSTANCE; the audit's own number is wrong.**

The most instructive claim in the document, in both directions.

What our paper prints, verbatim:
- Abstract (rev4:64): `We derive the closed form, verify it to five decimal places`.
- Body (rev4:190–196): the f32 realization `adds a deterministic offset of $-1.4\times10^{-6}$ per plateau phase`, reconciling `0.892636` with the exact-precision `0.892752`; `residuals $\sim\!10^{-5}$`.

The audit computes the gap, calls it `1.16e-4`, says that is `~83x` the claimed per-phase offset, that `1.4e-6` scaled by 10000 steps is `100x` too large, and concludes the abstract's "five decimal places" is contradicted and the true agreement is **four**. Recomputed:

```
abs(0.892636 - 0.892752)                  = 1.160000e-04    (audit's gap: reproduced)
gap / 1.4e-06                               =   82.9x         (audit's ~83x: reproduced)
1.4e-06 x 10000 steps                       =   0.0140 = 121x the per-phase gap
places of agreement, floor(-log10(gap))     =   3             (audit says FOUR)
```

The audit's *conclusion* is correct and lands on us: an abstract that says "verified to five decimal places" is not supported by the two values it is supposed to rest on.

The audit's *number* is wrong. A gap of `1.16e-4` is agreement to **three** decimal places (`0.892`); the fourth already differs (`6` vs `7`). "Four" is one place too generous, and it is the same species of slip the audit charges us with elsewhere — a figure asserted and not recomputed. I had written "four (UA says four)" into the first draft of that check. Had I not run it, our own review of an external auditor would have propagated an external auditor's arithmetic error. That is worth recording precisely because it is the failure this whole exercise is built to catch, and it arrived on my side of the table.

One further separation is needed, and it is the trap. Our own decay report says (`docs/reports/2026-09-04_decay-family-two-regimes-and-boundary-repair.md:126`):

> `the accumulated offset is -1.32e-4, matching the measured -1.303e-4 to +1.4e-6 ... Three instruments, four-decimal agreement: torch c-fits (0.89263), weight-norm ratios (0.892636(2)), atlas elementwise means (0.8926)`

So "four-decimal agreement" already exists in our own material — but it is a claim about **agreement across three instruments**, not the decimal agreement of those two printed values. Conflating the two would be the exact referent error we charged the Pathway audit with, and here it is one grep away on both sides. The defect is real and ours: an abstract asserting *five*, body text asserting `~1e-5` residuals, a report asserting *four* across instruments, and two values that agree to *three*.

The audit's `~83x` and `~100x` both reproduce; only its decimal count does not.

### A.3 — `fig:fcs` caption vs. text denominator, and the unaccounted language. **HOLDS.**

Two sentences, both ours, irreconcilable:

- caption (rev4:302): `Latin-script languages fall to their English-only zero-shot level (9/19 fully erased, 7 partially)`
- abstract (rev4:62): `nine of sixteen comparable languages serve at or below their English-only zero-shot level`

`9/19 ≠ 9/16`. The denominator has to be one number, and the text's own row-20 split settles which it is not: `nine fully displaced` named explicitly (es, fr, de, it, pt, da, sv, nl, fi) `+ seven partial retention` (pl, sl, cs, sk, ro, hu, et) `+ bg + el` = **18 of the 20**. English is the reference. That leaves **`lt`** — the twentieth domain, the one the growth ladder's whole P5 protocol turns on, acquired at 2.13 and later 3.72 — assigned to no bucket anywhere in the section. The audit found both the wrong denominator and the missing row, and it is the second of these that is the more substantive: our forgetting section does not state what happened to Lithuanian.

---

## 2. B — proof gaps

### B.4 — `thm:criterion`, the forward direction. **HOLDS as a stated gap.**

Our proof asks to "choose `x` whose trajectory passes through `z*` at depth `ℓ*`", and the induction hypothesis is established along the trajectory of a witness. The audit's characterisation is fair: it mixes two witnesses, and it also says the argument is repairable by strong induction over depth with `x` re-chosen per depth. That is my view too. A repairable defect in a `[PROVED]`-stamped theorem — which is why the stamp matters: the stamp is the claim, not the argument.

### B.5 — `cor:prefix`'s LayerNorm bridge is stamped without a proof. **HOLDS. The most consequential item in the audit.**

The corollary (rev4:247–252):

> `\textsc{proved.}` ... `Under \emph{soft} activity, LayerNorm's global statistics break (C1) at first order in the suffix magnitude.`

That sentence appears **once** in the entire file — at line 250, as the claim itself. There is no `\begin{proof}` anywhere near it (proof environments exist elsewhere: `thm:criterion` and `prop:soft` are written out, `lem:zf` is proved correctly), and the appendix contains no derivation of it — only the measurements of `rem:exp` and `app:meas`.

Why this is the load-bearing item rather than a formatting complaint: that single stamped sentence is the entire bridge from the exact theory to the measured narrative. The whole of `sec:readout` — random blocks, 83%, seven operator families, selection-as-repair — is presented as the measured realisation of the soft-perturbation picture the sentence asserts and the paper does not prove. The audit's remedy is exactly right and costs almost nothing: **relabel it MEASURED/HEURISTIC**. Leaving `PROVED` on an unproved bridge is the one kind of defect that does not age well in review, and it is the one defect here a reader could reasonably use against the entire results section.

### B.6 — `prop:amp`'s contraction premise "asserted without defining the interference dynamics, the norm". **DOES NOT HOLD AS STATED.**

The premise is defined, twice, and the audit did not read far enough to see it.

- `app:meas` (rev4:1161+): `(ii) Trajectory-level gate-miscalibration curves (the interference Jacobian realized as finite differences): scaling both suffix blocks to $d$ on EN inputs and tracking state deviation $\|h^{(d)}_\ell-h^{(0)}_\ell\|/\|h^{(0)}_\ell\|$ per level` — followed by the `d`-sweep table, 0.01 … ungated, six levels.
- `app:proofs` (rev4:1154): `Contractivity $\rho<1$ on the interference subspace replaces $(1+L_f)$ and yields $\|e_L\|\le\delta_{\max}/(1-\rho)$. \hfill$\qed$`

So there is a named dynamics, a norm, a realisation as finite differences, and a measurement of it. What survives of the claim is narrower and still worth having: the proposition's *rhetorical* weight outruns its proof, and `rem:exp` measures **against** the premise (directional gains 1.05–1.89), so the honest content is the `(1+L_f)` bound — vacuous at depth 20–736 — plus a measured statement that contraction does not hold for these models. That is a wording fix, not a defect in the result, and the difference between those two words is precisely what the "asserted without defining" phrasing erases.

---

## 3. C — internal inconsistencies

### C.7 — "five orders of magnitude" is four. **HOLDS — and its own source contains the refutation.**

Recomputed from the numbers the audit quotes and our own acquisition floors:

```
bg: log10(18613/1.54) = 4.0823   audit printed 4.08   match   reaches five: no
el: log10(10928/1.59) = 3.8371   audit printed 3.84   match   reaches five: no
```

The audit's arithmetic is exact and its reading is right: abstract, intro and `sec:fcs` all say "collapse by five orders of magnitude", and the paper's own values give four and just under four. The fix is to print "four orders, bg / 3.8 orders, el" or to say what denominator would make five true.

**Correction.** An earlier draft of this section claimed these two figures had *no artifact at all*, and that nothing under `docs/data/` matched `fcs`/`forget`/`fixedcap`. That was false, and the error was mine, not the audit's. The FCS matrix is on disk at `docs/reports/data/2026-09-10_fcs_matrix.csv` — 20 data rows (one per phase) × 20 language columns — and `18,612.86` / `10,927.74` are exactly its row-20 (`trained=lt`) entries in the `bg` and `el` columns; the results report `docs/reports/2026-09-10_fixed-capacity-matrix-results.md:34` prints them as `bg 18,613 (×12,086), el 10,928 (×6,873)`. I searched under `docs/data/` and never opened `docs/reports/data/`, and I grepped the literal `18613` against a source that writes `18,613`. The failure is the exact shape this whole exercise watches for — the right question asked of the wrong referent — committed by me against our own paper, and it is written down here rather than quietly fixed.

What the audit's finding actually rests on is sharper than "four": the report's own line refutes itself. `×12,086` is `10^4.08`, and that same sentence calls it *five orders of magnitude*. The mislabel does not originate in the abstract; it originates in the report the manuscript drew from.

And one thing neither the audit nor the manuscript prose notes: the curve is not monotone. The final-phase values the manuscript quotes (four orders) are *smaller* than the column peaks — `bg 20,528,902.75` after `nl` (row 18) and `el 12,355,740.83` after `en` (row 1), i.e. `10^7.12` and `10^6.89` against their own acquisition floors, with `bg` dropping to `600` after `hu` and back to `2.05×10^7` after `nl`. So "by the final phase, five orders" is wrong where it is stated (four) and an understatement of the phenomenon it names (seven at the peak). The honest fix names the row it means.

### C.8 — "four independent confirmations", five enumerated. **HOLDS as a counting inconsistency; the audit's inventory is not verified by me.**

Our count-claims: rev4:31 `verified four independent ways, including cross-script`; rev4:47 `four independent confirmations, including cross-script`; rev4:204 `Four independent confirmations (two seats, two hosts, two scripts)`; rev4:452 `Bit-exactness: four independent confirmations`.

The pattern the audit points at is genuine and is the same one as C.7: "four" is asserted, five transitions are enumerated (`en→es`, `es→pl`, `p19→p20`, the 4090 fixed-capacity chain, `zh→hi`), and the parenthetical glosses the count along a *different* dimension, two seats / two hosts / two scripts. So the paper counts one thing twice along two axes without saying which axis the headline counts. I did not independently enumerate the appendix transitions, so this is recorded as: the count is not self-consistent as printed, and the fix is to name which four and along which axis.

### C.9 — three different "acquisition bands". **HOLDS.**

`1.54--2.29` (rev4:326, European fixed-capacity acquisition), `2.25--5.99` (rev4:380, RA2b ladder), and a third in `sec:ood` (rev4:642): the out-of-support threshold is `\sim10\times the acquisition band (2.36--6.47)`.

I want to record that my own prior for this claim was wrong and died immediately. My first instinct was that a band with those edges might simply not be in the text — a fabrication by the auditor. Two greps: `2.36--6.47` is there, exactly where the audit says it is. So the finding is not a fabrication; it is the real thing, which is worse for us and better than my guess. The third band's lower edge matches neither of the other two, its derivation is not given, and the OOD absolute-axis rule — one of the paper's five headline results — is anchored to an interval whose provenance a reader cannot reconstruct.

### C.10 — two instruments both called "identity", 13.7x apart. **HOLDS as a discipline point; the audit's arithmetic is correct.**

`sec:readout`'s expansion control has `none (base) = 2.33`; the readout-operator table's identity control is `32.04` (en). The `83%` figure is computed against `2.33`/`31.07`, the operator-refutation claims against `32.04`. I verified the arithmetic on both sides and it is internally consistent, see E. The criticism is therefore not arithmetic but comparability: a reader must take on faith that two "identity" controls an order of magnitude apart describe the same model, and only a footnote explains it. One sentence naming the protocol difference closes it.

### C.11 — `rem:exp`'s "1.2–1.5x" against its own table. **HOLDS — with one word in the audit also wrong.**

Recomputing the ungated row of our own `app:meas` table (`.4024, .4816, .6340, .7697, .8580, .9078`):

```
successive ratios = [1.197, 1.316, 1.214, 1.115, 1.058]
inside the printed band 1.2--1.5: 2/5      min 1.058    max 1.316
strictly decreasing: NO
```

Our text claims per-level amplification `\sim1.2$--$1.5\times`; two of five ratios are in that band and the last is `1.058`. The audit's verdict is correct: "saturates" is the word the table supports, "1.2–1.5x" is not. Its second word is not — it says the amplification *decays*, and the sequence is not monotone (`1.197 → 1.316` rises). Trend falling, not monotone falling. Third instance of the same thing: the audit's qualitative adverbs are looser than its arithmetic.

---

## 4. D — overclaim

### D.12 — the 83% fraction as a portable statistic. **HOLDS in part.**

Our body text is careful, and the audit's own summary of it is accurate: `rev4:68` says "the fraction does not" generalise, and the seven-era span is `0.599` (sl) to `1.472` (el) — a fraction exceeding 1 in one era and falling to 0.60 in another. `rev4:511` gives the range in the body.

What the audit gets right is the asymmetry, and I checked it claim by claim rather than accepting the characterisation: `83%/62%` appears bare, without the interval, at 35, 48, 68, 258, 447, 470, 474, 498, 946 and **988 (conclusion)**. The Conclusion does carry the qualifier — `a mechanism that reproduces across seven eras while the fraction does not` — so "stripped from the conclusion" is too strong. It does not carry the range. That is the accurate finding: the conclusion keeps the *caveat* and loses the *numbers*, and a reader who takes the 83% out of the abstract never meets `0.60--1.47`.

### D.13 — "no fixed operator repairs it", universalised. **DOES NOT HOLD AS STATED.**

The audit's most confident D-claim, built on a quotation the paper does not say.

What the Conclusion, rev4:988, actually reads: `repairable by no fixed operator we could construct`.
What `rev4:68` actually reads: `we do not claim the space of input-independent operations is exhausted ... a sufficiently expressive fixed map can itself implement input-dependent behaviour`.
What the audit has us saying: `repairable by no fixed operator we could construct` **(correct)**, `every fixed arithmetic remedy` **(not found)**, and falsifier (ii) `repairable by no fixed operator we could construct` **(correct)**.

The scope-limiting five words are in the sentence the audit itself transcribes. And the paper concedes the audit's own counterexample in the same line the audit cites as a contradiction. So the universal negative the audit refutes is not in our paper. This matters as more than a quarrel about one sentence: it is the audit committing, against us, the referent error we charged it with against Pathway — refuting a proposition by locating a strong-sounding version of it that the document does not contain. The residual is legitimate and much narrower: with `n=7` families, two provably vacuous, and `calibgain` converging to oracle masking, the *falsifier* framing is too strong — a refutation passing over a family whose boundary case is the correct answer refutes the tested set, not the possibility. Narrow it and it holds; universalise it and neither of us will find the sentence.

### D.14 — the decay closed form is schedule-specific and its verification circular-adjacent. **HOLDS in part; the audit's reproduction is good.**

The audit integrates our stated schedules and gets `c ≈ 0.8925` plateau and `c ≈ 0.577` cosine against our printed `0.8927` / `0.5798` — an independent recomputation of our own mechanism arriving at our numbers, which is evidence for the mechanism, not against it. Its two real points: the instruments that verify `c` are transitions drawn from the schedule family whose product *defines* `c`, and the clause "independent of data, loss, or routing" is tested by nothing, because no experiment varies data at fixed schedule. Both stand. The bookkeeping complaint — which arm ran which schedule — is fair too, and now independently confirmed by A.2: the same two values are described by "five places", "`~1e-5`" and "four-decimal" in three different places in our own material.

### D.15 — OOD thresholds fit and evaluated on the same six probes. **HOLDS as an abstract-disclosure point.**

The disclosure exists and the audit quotes it, `"measured, but it is not held-out validation"`. Its claim is about where the disclosure sits: the abstract still reports "a two-axis rule separates 20 trained from 6 unseen" bare. With two free thresholds and six unseen probes, the abstract states a description of the probe set as a result. Same finding for the byte-addresser's margin floor, `160/160 on those same crops`. Both fixes are one clause in the abstract.

### D.16 — routing 20/20 and the oracle caveat's rank in the paper. **HOLDS as emphasis, and the paper is honest about it.**

`rev4:407` is unusually candid: because the router selects on the first 128 tokens of a crop and serving evaluates the remaining 384 of the same crop, `this is an online-routing protocol, not a held-out split ... the observed routing is therefore \emph{oracle serving} for this benchmark`. The audit's complaint is only that the abstract headlines `20/20 domains routing perfectly` without that sentence, and that the held-out confirmation is cited without its sample size or band. Correct, and a ranking fix.

### D.17 — `zh` 37/40: where the three crops went is never reported. **HOLDS, and it is a good catch.**

The three lost crops are the single datum that would test the high-byte-attraction mechanism against a counterexample, and we omit it. Where they landed either supports or embarrasses the mechanism; not reporting it is the kind of omission that costs more at review than the number it concerns.

---

## 5. E — the audit's verified column, recomputed

I refused to take any of this on faith, for the reason that a mismatch here would be the heavier kind of finding: an auditor that **confirms** something false is worse than one that misses something true. Recomputed in `out_c/union_alpha_audit/check_manuscript_audit.py`:

```
f_log  ln(20.16/2.33)/ln(31.07/2.33)   0.8330  quoted 0.833      OK
f_lin  (20.16-2.33)/(31.07-2.33)       0.6204  quoted 0.620      OK
one-block  9.57/2.33                    4.1073  quoted 4.11       OK
green lt   1-3.72/9.94                 62.575%  quoted 62.6       OK
green sl   1-3.36/9.45                 64.444%  quoted 64.4       OK
bg joint recovery  230/6.09            37.767   quoted 37.8       OK
zh retention  2.81/2.69-1               4.461%   quoted 4.5        OK
zh advantage  23.92/2.81                8.5125   quoted 8.5        OK
byte census  82/11.7                    7.0085   quoted 7.0        OK
restore cost  17.9/3038                0.589%    quoted 0.59       OK
engram scale  196000/579              338.51    quoted ~340       OK
iu contamination  719-454                265      quoted 265        OK
calib budget  8 x 512 B                 4096     quoted 4 KB       OK
own-point repro  20.08 vs 20.16        -0.397%  quoted -0.4%      OK
---> 14/14 reproduce.

Wilson 40/40   ->  [0.9124, 1.0000]   quoted floor 0.91   OK
Wilson  8/8    ->  [0.6756, 1.0000]   quoted floor 0.68   OK
```

The audit's confirmations are sound, and they include the two Wilson floors, which were the claims most exposed to a convention choice — 95%, `z=1.96`/`1.959964` — and match to two decimal places. Its methodological assessment is also sound and I would have written it: the density of in-line negative results and disclosed corrections, withdrawn 76% addresser fit, `iu` contamination, instrument-offset removal, is above field norm, and the storage/serving/addressing decomposition is the right decomposition.

Two items in that column are worth keeping as the audit's own position, and neither is contested by me: `thm:dissoc` is correct **and weak** — the construction is trivially linear, a constant suffix shift; it does not involve ReLU cross-coupling, which is why the interesting version is `prop:soft` where A.1 lives — and the AdamW observation, that gradient masking does not shield decoupled weight decay, is correct and genuinely useful. The audit understood our theory section better than its own summary of it gives it credit for.

---

## 6. What the audit found that we must not fix by editing

Ranked by what they cost us unaddressed rather than by how easy they are to fix:

1. **`cor:prefix` carries `[PROVED]` on an unproved sentence** (B.5) that is the sole bridge from the exact theory to the measured narrative. Relabel. Cheapest fix, largest exposure.
2. **The "five orders" claim contradicts the report it came from** (C.7). The FCS matrix is on disk (`docs/reports/data/2026-09-10_fcs_matrix.csv`), and the report that first printed these figures already refutes itself — `×12,086` labelled *five* orders — a label the manuscript then inherited. (An earlier draft of this review wrongly added "no artifact"; corrected in §C.7.)
3. **Three "five-decimal / four-decimal / `~1e-5`" statements about one quantity** (A.2, D.14), none of them the one the abstract prints.
4. **The OOD rule's third band has no derivation** (C.9) and its thresholds are fit on the six probes it separates (D.15).
5. **`prop:soft` prints 4** (A.1), `rem:exp` prints a band its own table contradicts (C.11), `fig:fcs` prints two denominators and omits `lt` (A.3).

## 7. Verdict

The audit is a strong read of our paper: fifteen of fifteen labels real, the author correctly attributed, fourteen of fourteen confirmations exact, both Wilson floors right, an independent integration of our schedules landing on our own `c`, and a defect found — `prop:soft`'s constant — whose correct statement I could only reach by recomputing it from our own stated state. It is not a rubber stamp either: the counting and denominator cluster, the three bands, and the unstamped-proof-on-a-stamped-claim are all real, and the `lt` omission is a hole in a results section.

It is also wrong in three places that share one shape. It says the agreement is four decimal places where the subtraction gives three. It says the amplification decays where the sequence is not monotone. It refutes a universal negative whose scope-limiting five words are in the sentence it transcribes. Each is a small error and all three are the same error: **a figure or a quote asserted, close to right, and not recomputed** — which is precisely the failure mode we charged the Pathway audit with an hour ago, and which this pass would have propagated into our own review had I accepted the audit's `four` instead of running the subtraction myself.

So the answer to the question the operator asked is: yes, the errors it reports in our paper are mostly demonstrable, and the reason to read it carefully is the same reason not to paste it. It found a fifth-order defect in our theory section and got a decimal place wrong doing it, and the deepest thing wrong with the paper is the pattern most of what it did find shares — printed numbers never recomputed against their own sources — a pattern this review's own first draft then reproduced, against the paper's forgetting matrix.

**Diagnosis before prescription.** Four edits are mechanical and I would make them today: `=4` to `=1`; `[PROVED]` to `MEASURED` on `cor:prefix`; one denominator plus an `lt` row in `fig:fcs`; the range `0.60--1.47` into the abstract and conclusion beside the 83%. The `lt` disposition is not an edit — it is a question about a measurement, not a sentence. (The first draft listed the bg/el provenance as a second non-edit, on the belief that no artifact existed; that belief was wrong — see §C.7.)

---

*Computation: `out_c/union_alpha_audit/check_manuscript_audit.py` — CAS-free; `sympy` is not installed in either runtime, and after two runs died on a guessed import the derivation was rewritten as a polynomial identity under random instantiation, which decides `=4` vs `=1` more firmly than a CAS would. Primary sources: `docs/papers/rev4-bdh-manuscript.tex` (md5 `dc2731b0…`), `docs/reports/2026-09-04_decay-family-two-regimes-and-boundary-repair.md`, `docs/data/`. Companion review of the Pathway audit: `docs/reviews/2026-09-19_bdh-paper-audit_union-alpha_review.md`. The reviewer's routing and backing model are unknown and no judgement above is weighted by them.*
