# Sonde B - legal-leak position-decomposition report

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: **COMPLETE**
Result of the pre-registered run of record: `docs/plans/2026-09-22_sonde-B-legal-leak-position-prereg.md`
Instrument of record: `scripts/eval_router.py` @ `2f0dc9d1` (additive `--pos-dump`)
Thread narrative: `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-thread-report.md`
The results it interrogates: window probe `.../legal-leak-window-report.md`, content probe `.../legal-leak-content-report.md`
Operator GO this leg answers: the residual half of the flips.

---

## 0. The question, and the answer in one line

The window probe left 7 (seed-2) and 5 (reference) legal crops still routing DOWN to the narrower prefix
at scoring window 384, against 193 and 195 stayers, and the content probe found no crop feature that
separates them. What was never looked at is the internal structure of the routing score itself: the router
scores a prefix by the mean loss over the first 384 positions, and the decision between 12288 and 14336 is
the sign of

    M = sum over t of m(t),   where m(t) = loss_12288(t) - loss_14336(t).

Two pre-registered readings competed. **H-few**: a few positions carry the margin, so the flip is a
few-token event. **H-cancel**: the per-position contributions are individually far larger than their sum,
so the flip is the small residual of a near-cancellation.

**Answer: H-cancel, on both ladders, under the frozen rule.** Median consistency ratio `R = |M| / A` is
**0.0735** on seed-2 and **0.1139** on the reference, both under the frozen 0.15, while H-few fails on both
ladders and on both of its two conditions. The leakers are in fact **less** concentrated than the stayers.
On this reading the residual flip is not about particular tokens: it is an arithmetic outcome at the
decision boundary, and that is where the one-sidedness now lives.

## 1. What was fixed before measuring

The pre-registration (`107ecb0e`, written before any position-level measurement) froze:

- the statistics per crop: `M = sum_t m(t)`, `A = sum_t |m(t)|`, `R = |M|/A`, `k50` (how many of the largest
  `|m(t)|` are needed to reach 50 percent of `A`; 192 is the perfectly uniform case for 384 positions),
  `conc5`, `top1_pos`, `neg_share`;
- the two decisive thresholds, on **medians**, on **both** ladders: H-few if median `k50 <= 20` AND median
  `R >= 0.5`; H-cancel if median `R <= 0.15`; everything else reported as mixed with no promotion;
- the reproducibility gate: the same run must reproduce the window-384 confusion exactly (seed-2 7 at
  12288 / 193 at 14336; reference 5 at 12288 / 195 at 14336), or the probe is void and the discrepancy is the
  finding;
- and the statement that at n = 7 and n = 5 this is descriptive: **no test statistic, no p-value, no rate**.

## 2. Run and provenance

- Host `bdh-4090`, run window **2026-09-22 09:30:16 - 09:35:27** (guest local), two re-evals, one per ladder.
  **No training.**
- Exclusive GPU claim `s_bdh-cl_000123_df91ac` (HTTP 201), held under a detached renewer, released HTTP 204;
  card idle at 287 MiB / 0 percent afterwards, and `NO_GUEST_PROCS`.
- Ladders and corpus as pinned in the pre-reg: seed-2
  `out_c/sondeB/harvest/bdh_textmix_harv-prose__legal_last.pt` (md5 `d94686ad9f90d4750ba8d02b88ffd9ea`),
  reference `out_c/sondeB/harvest_ref/bdh_textmix_harv-prose__legal_last.pt` (md5
  `8d89b2cabe0c0dccd595fc76bd74c822`), corpus `data/textmix2/legal.txt` (md5
  `0135960429085039dbe5385f649e75fe`).
- Routes 8192,10240,12288,14336,16384; crops 200; batch 4; window **384**; `--route-grid --pos-dump legal:12288,14336`;
  domains spec and order identical to every earlier leg, so these are the same 200 byte ranges.
- Instrument: `scripts/eval_router.py` @ `2f0dc9d1`, working-tree md5 `ed9fd326a4c2d62f9d8428577730dbaf` - the
  md5 pinned in the run intent (`m_bdh-cl_0000000433`) and recorded matching on the guest in the run log.
  Driver md5 `f31a5534652d67293ec916272b2a50c3`.
- Raw dumps (fetched and row-counted locally): `out_c/sondeB/harvest/posdump_w384_seed2.txt`
  (`/tmp/leaks/posdump_w384_seed2.txt`, 93542 B, **200** summary rows, **27** `POS_ROW` arrays) and
  `out_c/sondeB/harvest_ref/posdump_w384_ref.txt` (`/tmp/leaks/posdump_w384_ref.txt`, 87840 B, **200** rows,
  **25** arrays). Every array holds exactly 384 values. Arrays cover the leakers plus the pre-registered
  fixed sample of the first 20 stayers by crop index (7+20, 5+20).
- Analyzer: `out_c/sondeB/position_analyze.py` -> `/tmp/leaks/position_analysis.txt` (deterministic re-run).

## 3. The gate passed, and what the verification does and does not cover

- **Reproducibility gate PASSED exactly** on both ladders: seed-2 7 leakers at 12288 / 193 at 14336; reference
  5 at 12288 / 195 at 14336. The analyzer derives the leaker set from `chosen` and **asserts** it equals the
  pre-registered set before it makes any comparison, so a silent drift would abort rather than mislead.
- **Independent sign/coherence check over all 400 rows**: every leaker has `M < 0` strictly (7/7 and 5/5) and
  every stayer has `M >= 0` (193/193 and 195/195, no exception either way), and the only two widths ever
  chosen across both
  dumps are 12288 (all 12 leakers) and 14336 (all 388 stayers). The argmin is behaving as exactly the sign of
  `M` at the boundary pair, with zero exceptions. That is a verified invariant over all 400 rows of this run, not an assumption.
- **Internal consistency of the arrays**: `M` and `A` were re-derived from the printed per-position arrays and
  compared to the instrument's own printed values - max absolute discrepancy `1.431e-03` (seed-2) and
  `1.353e-03` (reference) on `M`, `1.112e-03` and `1.603e-03` on `A`. Those are float32 summation scale over
  384 terms, so the arrays and the summary row are the same arithmetic.
- **Honest boundary on coverage**: only `M` and `A` were independently re-derived. `R`, `k50`, `conc5`,
  `top1_pos` and `neg_share` are taken from the instrument's own computation over those same arrays (each is a
  deterministic function of `m(t)`; `R` additionally divides the two quantities just re-derived). They were
  not re-derived by a second implementation.

## 4. The frozen readings, and the verdict

Medians over leakers and over the 20-crop stayer sample, per ladder:

| group | median R | median k50 | median conc5 | median neg_share |
| --- | --- | --- | --- | --- |
| seed-2 leakers    | **0.0735** | 40.0 | 0.1262 | 0.3464 |
| seed-2 stayers    | 0.4242     | 35.0 | 0.1426 | 0.2656 |
| reference leakers | **0.1139** | 38.0 | 0.1446 | 0.3854 |
| reference stayers | 0.3971     | 36.0 | 0.1365 | 0.2604 |

- **H-cancel: ACCEPTED.** Both leaker medians sit under the frozen 0.15, on both ladders.
- **H-few: REFUTED on both ladders and on both of its conditions.** Median `k50` is 40.0 and 38.0 against a
  threshold of 20, and median `R` is 0.0735 and 0.1139 against a threshold of 0.5.
- No promotion beyond the frozen reading is made, and none is needed to reach the conclusion.

Two individual leakers straddle the 0.15 line and are named rather than smoothed over: seed-2 crop 151 at
`R = 0.1541` and reference crop 166 at `R = 0.1844`. The frozen rule is on the median, and the median is
what the pre-registration fixed; two straddlers out of twelve do not change it, but a verdict that only survived by
averaging would not have been worth the run either, and these are the values a follow-up inherits.

## 5. Per-crop decomposition of every leaker

`lateD = lateA - lateB` is listed for completeness of the row (see section 8); no frozen reading uses it.

```
seed-2
  crop             M             A        R    k50    conc5 neg_share  top1_pos      lateD
    80     -3.175904    119.153595   0.0267     41   0.1273   0.3464        26  -0.010799
   122     -7.975825     73.815819   0.1080     41   0.1149   0.3359       287   0.056496
   135     -3.423312     76.244110   0.0449     34   0.1657   0.3411       324   0.096480
   148     -3.679210     81.436638   0.0452     34   0.1262   0.3385        15   0.020918
   149     -6.912043     94.002579   0.0735     31   0.1861   0.4010       149   0.091503
   151    -22.088131    143.291489   0.1541     49   0.1064   0.4323       320  -0.020607
   164     -9.135921    116.424484   0.0785     40   0.1235   0.3620       314   0.026305

reference
  crop             M             A        R    k50    conc5 neg_share  top1_pos      lateD
    41    -14.838729     99.233170   0.1495     40   0.1141   0.4974       372  -0.011645
    50    -10.089838     88.609535   0.1139     37   0.1518   0.3854       282   0.005076
   131     -6.774426     96.290482   0.0704     39   0.1216   0.4661       331   0.031959
   149     -0.212168     98.758286   0.0021     38   0.1497   0.3698       288   0.116613
   166    -16.939404     91.865494   0.1844     30   0.1446   0.3359        47   0.081292
```

## 6. The comparison that makes H-cancel mean something: what separates leakers from stayers

This is the substantive part of the result, and it is not the part the pre-registration hoped for.

- **Concentration does NOT separate them - it points the wrong way.** Leaker median `k50` is 40.0 (seed-2)
  and 38.0 (reference) against stayers at 35.0 and 36.0: the leakers are slightly **less** concentrated than
  the crops that route correctly, not more. `conc5` is comparable across the two groups on both ladders
  (0.1262 vs 0.1426; 0.1446 vs 0.1365). Every group sits well under the perfectly-uniform 192, so absolute mass
  is somewhat concentrated everywhere - but concentration is not the variable that distinguishes a flip from a
  stay. H-few did not merely fail its threshold; its predicted direction is absent.
- **What does separate them is the consistency ratio and the sign split.** `R` is 4-5x lower at the leakers on
  both ladders (0.0735 vs 0.4242; 0.1139 vs 0.3971). And `neg_share` - the share of positions on which the
  narrower prefix is locally better - is HIGHER at the leakers on both ladders (0.3464 vs 0.2656; 0.3854 vs
  0.2604), consistently in the same direction on both.
- **Read together, that is a specific picture.** At a leaker, roughly two thirds of the positions locally
  prefer the WIDER prefix and only about a third prefer the narrower one, and still the magnitude-weighted
  sum lands negative: the decision is not a count-majority phenomenon at all, it is a weighted residual whose
  two sign-groups nearly cancel. A correct routing (a stayer) is instead a coherent verdict - one direction
  genuinely dominates the sum. The leakers are the crops where the score has almost nothing left over after
  the cancellation, and the sign of that remainder picks the width.

## 7. The cancellation made concrete (descriptive supplement, not part of the frozen rule)

To keep the boundary clean: section 4 is the pre-registered verdict. The quantities below were computed by me
from the printed `POS_ROW` arrays after the fact, are not thresholded, and promote nothing.

| ladder | median over leakers: max&#124;m&#124; / A | max over leakers | crops where any single position exceeds 5 percent of A |
| --- | --- | --- | --- |
| seed-2    | 0.0340 | 0.0696 | 2 of 7 (crops 135 at 0.0557, 149 at 0.0696) |
| reference | 0.0394 | 0.0489 | 0 of 5 (maximum 0.0489, at crop 149) |

- **No single position can flip any of these decisions.** On the worst leaker on either ladder, the largest
  single per-position contribution carries **6.96 percent** of the total absolute mass `A`; median 3.4 percent
  (seed-2) and 3.9 percent (reference). This is the direct arithmetic form of the H-few refutation: whatever the
  router is deciding, it is not deciding it on one token.
- **Reference crop 149 is the exemplar of the whole thread's residual.** Its decision margin is `M = -0.2122`
  against a total absolute disagreement of `A = 98.7583` - the router resolves this crop by **0.21 percent** of
  the disagreement it saw, and **123 of its 384 individual positions** are each, on their own, larger in
  magnitude than the entire quantity that decided the case. Its `neg_share` is 0.3698 and `k50` 38: no
  concentration, just near-perfect cancellation.
- On seed-2 the same quantity is far smaller: the number of positions individually larger than |M| is 0, 1
  or 3 out of 384 (maximum 3, at crop 80), so the seed-2 leakers are near-cancellations that are not quite
  at knife's edge, while the reference contains one crop that genuinely is. Both readings of H-cancel are therefore not identical across ladders,
  and the difference is worth stating rather than pooling: n=7 versus n=5, and pooling them would invent a
  uniformity the data does not show.

## 8. Two disclosures

1. **`lateA`/`lateB` are printed but not frozen.** The instrument emits `lateA|lateB|lateD` columns in the
   summary row (`scripts/eval_router.py`, the `crop_idx|M|A|R|k50|conc5|top1_pos|neg_share|lateA|lateB|chosen`
   header at line 137). These were **not** declared in section 3 of the pre-registration, they were **not**
   used in the frozen readings, and they are **not** used anywhere in this report's conclusions. They are
   reproduced in the table above only so the printed row and the table reconcile one-for-one. Reading them
   would be a fresh, separately pre-registered question (early-window versus late-window split of `A`), not an
   extension of this one.
2. **The array sample is leakers plus a fixed 20 stayers.** The internal-consistency check of section 3
   therefore covers the 12 leakers and the pre-registered 40-crop stayer reference sample, not all 388 stayers;
   the 400-row sign/coherence check, by contrast, covers every row, because it reads the summary table. Stated
   because "verified on the arrays" and "verified on all 400 rows" are different claims and only the second is
   universal.

## 9. What this settles, and what it hands on

**Settled, at the strength the data supports (n=7 and n=5, descriptive):**

- The residual legal flip is **not a few-token event**. H-few is refuted on both ladders and in both of its
  conditions, and independently by the fact that no single position carries more than 7 percent of the
  per-crop absolute disagreement.
- It is a **near-cancellation outcome**: at the leakers the signed margin is a small fraction (7-11 percent
  at the median, 0.2 percent at the extreme) of the disagreement the router actually saw, whereas correct
  routings are coherent at around 40 percent (medians 0.3971 and 0.4242).
- Together with legs 4 and 6 (not capacity, not content or crop position), this closes the pre-registration's
  alternative readings and lands where the thread expected: the one-sidedness is a property of **how the loss
  sum scales with prefix width near the decision boundary**, not of the identity of the crops or their tokens.

**Handed on, not answered here** - the pre-registration said a clean H-cancel result would move the question
rather than close it, and that is what happened:

- The remaining question is the **scaling law itself**: what makes the wider prefix's positive contributions
  systematically just fail to outvote the narrower prefix's negative ones at these particular crops, and why
  the failure is one-directional (every one of the 12 leakers went DOWN to 12288; no crop ever left 14336 for a
  width above it). A width-scaling study of `A` and `M` against prefix length near the boundary is the
  indicated instrument. That is a **new** pre-registration, not an extension of this one.
- Reading the bytes of the decisive positions - the follow-up this probe was meant to select for if H-few had
  won - is **not** indicated by an H-cancel result, and is not taken up.
- **Untouched by this leg, as bound:** P1 stays falsified at 189 with the band {191..199}; the ablation result
  and the window probe's attenuation claim are not re-opened.

## 10. Limits, stated plainly

- n = 7 and n = 5. These are descriptive readings under thresholds fixed before the run, not tested claims;
  no p-value, no interval, no rate, and the two straddlers of section 4 show how much a single crop can move a
  median at this size.
- The stayer comparison is a fixed 20-crop sample per ladder, so all four medians carry different denominators
  (193, 195 stayers exist; 20 each were arrayed for the consistency check, while the stayer medians use the full
  193/195 summary rows).
- The probe decomposes **where the margin sits**, not **why the sum scales as it does**; it does not touch the
  weight-level or optimizer-level account of that scaling.
- One scoring window only (384, chosen so this leg analyses exactly the crops the window probe left), so the
  cancellation structure at shorter windows is untested here.
- One corpus, one boundary pair, one repetition per ladder; no md5 re-verification or forward pre-flight of the
  checkpoints beyond the pins of section 2 was run this session.

---

*One line for the paper, if it survives the operator's reading:* the surviving mis-routings are not driven by
any identifiable content or token; each is the thin residue of a near-cancellation between per-position
losses that disagree in opposite directions - the router decides on 0.2 to 18 percent of the disagreement
it is shown (all twelve leakers; ladder medians 7.4 and 11.4 percent).
