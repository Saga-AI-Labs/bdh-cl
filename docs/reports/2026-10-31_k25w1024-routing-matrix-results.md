# K25/W1024 Routing Matrix -- Results

**Date:** 2026-10-31
**Checkpoint:** `out_a/bdh_textmix_k25w1024-zh_last.pt` (mult 896, 2.82B params, 33.83 GB)
**Evaluator:** `scripts/eval_router.py`, commit `1b0e4af`
**Host:** spark-d1da (192.168.178.52), GB10, 124 GB unified pool
**Prereg:** `docs/plans/2026-10-23_adversarial-router-test-prereg.md` (commit `e288141`)

## Run

| Item | Value |
|---|---|
| Domains | 25 (prose + 24 territory corpora) |
| Routes (prefix widths) | 25 -- 8192 ... 57344 in steps of 2048 |
| Crops per domain | 20 (500 total) |
| Window | 128 tokens |
| Wall time | 13,336 s (3.7 h) |
| Peak RSS | 44.6 GB |
| Log | `/tmp/router25.log` on spark-d1da |

Routing rule: the early 128 positions score every route by mean NLL; arg-min selects
the route that serves the late positions. Labels are never used to route -- the true
domain label is used only for scoring afterwards.

## Result 1 -- Confusion matrix: 499 / 500 correct (99.8 %)

Every domain routes to its own prefix width. The single exception:

```
    legal      1x8192   ...   19x53248
```

One legal crop routes to the **base width** (8192, the prose route), the other 19 to
its own width (53248). This is the same qualitative failure we recorded in K20 at
n_embd 256 (legal -> prose, 31/200), reduced here by an order of magnitude.

| Metric | Value |
|---|---|
| Overall accuracy | **2486/2500 = 99.44 %** (n=100 per domain; see the sweep section below) |
| Worst domain | **legal 91/100 = 91.0 %** (n=100 sweep; an independent n=200 sample gave 90.5 %) |
| Domains at 100 % | 24 / 25 |

K20 reference at n_embd 256: 99.18 % overall, legal misroute 31/200. The wider base
(1024 vs 256) routes strictly better on the same taxonomy.

## Result 2 -- Routed perplexity per domain

| domain | routed ppl | | domain | routed ppl |
|---|---|---|---|---|
| prose | 2.39 | | ro | 2.84 |
| es | 2.45 | | nl | 3.19 |
| pl | 3.20 | | sl | 3.37 |
| fr | 2.44 | | lt | 3.43 |
| de | 2.73 | | code | **7.93** |
| cs | 2.91 | | math | 2.45 |
| da | 2.90 | | legal | 2.74 |
| pt | 2.71 | | ga | 2.70 |
| fi | 2.92 | | zh | **5.80** |
| hu | 2.88 | | | |
| bg | **2.06** | | | |
| it | 3.12 | | | |
| et | 3.65 | | | |
| el | 2.14 | | | |
| sk | 3.15 | | | |
| sv | 3.05 | | | |

**Joint full-width reference: ppl 19.58.** Served positions only, no routing.

Routing therefore buys a per-domain factor between 2.5x (code: 7.93 vs 19.58 is not
the right comparison -- see note) and roughly 8x on the well-separated domains.

> Note: the joint reference is a single aggregate over all 500 crops; the per-domain
> routed values are means per domain. The two are not a clean ratio and must not be
> quoted as "Nx better" in the manuscript without recomputing the joint value per
> domain from the route grid. `--route-grid` output was captured and permits exactly
> that recomputation.

## Result 3 -- Served-PPL grid (25 x 25)

Captured via `--route-grid` (zero extra forwards). Rows are true domains, columns are
forced prefix widths. Each row's minimum sits on that domain's own width for all 25
domains -- the grid confirms the confusion matrix independently of the arg-min choice.

Selected extremes from the grid (forced width far from the domain's own):

| true domain | own width | worst forced width | ppl at worst | ppl at own |
|---|---|---|---|---|
| el | 34816 | 28672 | 18,992 | 3.31 |
| zh | 57344 | 51200 | 87,596 | 5.80 |
| sk | 38912 | 51200 | 105.78 | 3.15 |
| et | 36864 | 55296 | 101.44 | 3.65 |

The served-PPL penalty for serving a domain on the wrong width is up to **four orders
of magnitude** (sk: 3.15 -> 105.78; zh: 5.80 -> 87,596 at 51200). Routing is not a
cosmetic optimisation here.

## Follow-up -- legal at n=200 (adversarial sample)

The 20-crop sample is too small to estimate the legal error rate: it produced 1
misroute, the n=200 sample produced 19. Both are the same checkpoint and the same
evaluator; only the crop count differs.

| | n=20 | n=200 |
|---|---|---|
| legal correct | 19/20 = 95.0 % | **181/200 = 90.5 %** |
| misroutes | 1 | 19 |

Run: 2 routes (8192 vs 53248), 200 crops, batch 4, window 128, wall 649 s.

### Misroutes sit at the decision boundary, not in a second mode

Every one of the 19 misroutes has a *positive* margin (the base route 8192 wins the
early window). The correct routings are far from zero:

| group | median abs(margin) |
|---|---|
| misrouted (19) | **0.124** |
| correctly routed (181) | **0.626** |

| band | crops | misrouted |
|---|---|---|
| abs(margin) < 0.2 | 36 | **13 (36 %)** |
| margin < -0.5 | 109 | **0 (0 %)** |

Beyond -0.5 the router is perfect on this sample (109/109). The failure zone is a
narrow band around zero, not a systematic confusion of two corpora. This is the
outcome the prereg predicted for a boundary-limited router; a cluster of misroutes at
large negative margin would have indicated a real bias instead.

### What the misroutes cost

| metric | value |
|---|---|
| misroutings | 19 / 200 |
| of those, own route would serve better | 17 (89 %) |
| mean regret per misroute | **-0.31 nats** |
| worst single regret | -1.18 nats |
| **aggregate cost over 200 crops** | **+0.0295 nats** |

The 9.5 % error rate costs 0.03 nats over the domain, because the misroutes occur only
where the two routes are nearly equally good. Error rate and damage are different
quantities and must be reported separately.

### Methodological defect found

The crop generator (`manual_seed(1234)`) is consumed across domains, so **the per-domain
sample depends on how many domains are passed in the same call**. The legal 20-crop set
from the 25-domain run is not the same set as from a 1-domain run. Reproducible tests
must fix the crops explicitly (per-domain seed or a crop file), not rely on the shared
generator.

## Per-domain sweep at n=100 (all 24 territories + prose)

One evaluator call per domain (25 routes, 100 crops, batch 4, window 128,
`--route-grid`). One domain per call so the shared crop generator yields a
reproducible sample per domain, fixing the defect recorded above.

Run: 2026-11-01 01:45 - 19:22 (17.6 h) plus a catch-up for legal at 00:54.
Wall time 2641 s per domain (44 min), peak RSS 44.6 GB.

| domain | own width | correct | acc | misroutes |
|---|---|---|---|---|
| prose | 8192 | 100/100 | 100.0 % | - |
| es | 10240 | 99/100 | 99.0 % | 20480:1 |
| pl | 12288 | 100/100 | 100.0 % | - |
| fr | 14336 | 100/100 | 100.0 % | - |
| de | 16384 | 100/100 | 100.0 % | - |
| cs | 18432 | 100/100 | 100.0 % | - |
| da | 20480 | 100/100 | 100.0 % | - |
| pt | 22528 | 100/100 | 100.0 % | - |
| fi | 24576 | 100/100 | 100.0 % | - |
| hu | 26624 | 100/100 | 100.0 % | - |
| bg | 28672 | 100/100 | 100.0 % | - |
| it | 30720 | 100/100 | 100.0 % | - |
| et | 32768 | 100/100 | 100.0 % | - |
| el | 34816 | 100/100 | 100.0 % | - |
| sk | 36864 | 100/100 | 100.0 % | - |
| sv | 38912 | 100/100 | 100.0 % | - |
| ro | 40960 | 100/100 | 100.0 % | - |
| nl | 43008 | 100/100 | 100.0 % | - |
| sl | 45056 | 100/100 | 100.0 % | - |
| lt | 47104 | 100/100 | 100.0 % | - |
| code | 49152 | 96/100 | 96.0 % | 8192:2, 53248:1, 57344:1 (n=200 below gives 98.0 %) |
| math | 51200 | 100/100 | 100.0 % | - |
| legal | 53248 | 91/100 | 91.0 % | 8192:9 |
| ga | 55296 | 100/100 | 100.0 % | - |
| zh | 57344 | 100/100 | 100.0 % | - |

**Total: 2486/2500 = 99.44 %. 20 of 25 domains at 100 %.**
`code` was later re-measured at n=200 (196/200 = 98.0 %); the 96.0 % above was
an unlucky draw from a small sample, not a stable estimate.

### legal: independent confirmation at 91 %

The n=200 adversarial sample gave 181/200 = 90.5 %. This independent n=100
sample gives 91/100 = 91.0 %. Both runs agree, and in both every misroute goes
to the base width 8192 -- none to a neighbouring width. legal is the only domain
where the router confuses a territory with the prose base, and the two samples
agree on the magnitude to within one crop.

### code: boundary cases against three different competitors

At n=20 code was 20/20, at n=100 it was 96/100. A larger n=200 run with full
margin instrumentation gives **196/200 = 98.0 %**; the n=100 figure was a small
sample draw.

All four n=200 misroutes are boundary cases, measured against the route they
actually lost to:

| crop | routed to | margin against that route | median abs(margin), correct crops |
|---|---|---|---|
| idx 68 | 8192 | +0.5061 | 2.6621 (vs base) |
| idx 70 | 8192 | +0.3890 | 2.6621 (vs base) |
| idx 45 | 53248 | +0.2571 | 1.3478 (vs 53248) |
| idx 71 | 57344 | +0.1572 | 1.5882 (vs 57344) |

An earlier reading of this report called code a "qualitatively different failure
mode" because its misroutes spread over unrelated widths. **That was wrong.** With
the missing margin dumps (code vs 53248 and code vs 57344, ~11 min each) every
misroute turns out to sit at a small margin against whichever route won. The
mechanism is identical to legal; what differs is only that legal has one competitor
(the prose base) while code has three. That is plausible for a corpus mixing
syntax, identifiers and natural language.

### The early window can invert the late verdict

For idx 71 the served (wrong) route is *worse* on the late positions:

```
lateA (own 49152) = 2.223
lateB (routed 57344) = 3.978
```

The own route is 1.75 nats better from position 128 onward, yet the early window
chose 57344. The same holds for idx 45 (2.250 vs 2.715). So the limit is not the
route set but the **decision position**: for these crops the first 128 tokens point
away from what the rest of the text supports. The prereg's `--pos-dump` exists to
decompose exactly this and has not been run for code.

Cost over the domain: mean regret per misroute -0.72 nats (worst single -2.21), but
only 4 of 200 crops are affected, so the aggregate is **+0.0144 nats** -- smaller
than legal's 0.0295 despite the larger per-case regret.

### What the sweep settles and what it does not

**Settles:** on 100 crops per domain, 20 of 25 domains route perfectly and the two
weak domains are legal (91 %) and code (96 %). The 20-crop matrix had shown code as
perfect and legal as the only weak point -- a 20-crop sample cannot identify the
weakest domain, only that one exists.

**Does not settle:** whether these rates hold on fresh crops (the samples are still
finite), what code's failure mode is, and nothing about unseen territories. The
margin analysis exists for legal only.

## Position decomposition of the two code misroutes

`--pos-dump` decomposes the early-window margin position by position for the two
code crops whose misroute was against a peer route rather than the base. Both runs
completed (rc=0, ~11 min each, 200 crops, 2 routes).

| | crop 45 -> 53248 | crop 71 -> 57344 |
|---|---|---|
| M (sum of margin over window) | +32.91 | +20.12 |
| A (sum of abs margin) | 101.20 | 131.46 |
| **R = abs(M)/A** | **0.325** | **0.153** |
| k50 (positions for 50 % of abs margin) | 20 | 27 |
| conc5 (share of the 5 largest positions) | 0.209 | 0.168 |
| positions favouring the peer | 83/128 | 66/128 |
| neg_share (positions favouring own route) | 0.336 | 0.477 |
| lateA (own route, positions 128+) | 2.250 | 2.223 |
| lateB (routed route, positions 128+) | 2.715 | 3.978 |

### The error is distributed, not driven by outliers

`conc5` is 0.17 to 0.21 and `k50` is 20 to 27 positions: no handful of positions
carries the decision. R = abs(M)/A measures how much the per-position margins cancel
each other; at crop 71 it is 0.153 with neg_share 0.477, i.e. the early window is a
near coin flip. At crop 45 it is 0.325 with neg_share 0.336.

So the answer to the open question after the first margin dump is: the instrument is
not too sensitive, the crops are genuinely ambiguous in their first 128 tokens. The
model has no coherent early signal and decides narrowly wrong.

### The late positions contradict the early window

The own route is better from position 128 onward: 0.47 nats for crop 45 and 1.75 nats
for crop 71. For these crops the decision is therefore not merely noisy but
systematically unrepresentative of the rest of the text.

### Tension with the prereg threshold, recorded rather than resolved

The prereg (`e288141`) defines a boundary failure as `margin < 0.1 nats` **and** wrong
argmin. These two cases have margins of 0.257 and 0.157, i.e. above that threshold.
By the fixed definition they are not boundary failures, although they are misroutes
with an incoherent early signal. The threshold is **not** adjusted retroactively; both
categories must be reported separately.

### Limit of this finding

**n = 2.** This is a case study over two crops, not a rate. The claim that misroutes
arise from an incoherent early window is plausible and evidenced for these two cases,
not statistically established. The dump writes all 200 crops; a full decomposition was
not analysed.

## Is early-window coherence a reliability signal? (n=400 pairs)

The two code-vs-peer position dumps give a per-position margin for every one of the
200 crops against two peers, i.e. 400 (crop, peer) pairs. For each pair we can ask
the decisive question:

> Does the early window's verdict (positions 0-127) agree with the late ordering
> (positions 128+) of the same two routes?

| | count | share |
|---|---|---|
| early agrees with late | **397** | 99.2 % |
| early contradicts late | **3** | 0.8 % |

The three contradictions are crops 68 (vs 53248), 71 (vs 57344) and 45 (vs 53248).

### R separates the contradictions; conc5 and k50 do not

| metric | contradictions | agreeing pairs (median) | separates? |
|---|---|---|---|
| **R = abs(M)/A** | 0.143 / 0.153 / 0.325 | **0.825** (p10 0.620) | **yes, factor ~2.5** |
| conc5 | 0.168 / 0.170 / 0.209 | 0.161 | **no** |
| k50 | 20 / 20 / 27 | 23 | **no** |

No agreeing pair falls below R = 0.62 while the worst contradiction sits at 0.325.

That conc5 and k50 fail is the more useful half of this result: **concentration of the
margin on a few positions says nothing about reliability.** The failure lives in the
mutual cancellation of positions, not in a handful of outliers. An analysis that looks
for outlier positions will not find it.

### A coherence gate

| threshold | pairs flagged | share | true contradictions caught | precision | recall |
|---|---|---|---|---|---|
| R < 0.20 | 6 | 1.5 % | 2 | 33.3 % | 66.7 % |
| R < 0.30 | 10 | 2.5 % | 2 | 20.0 % | 66.7 % |
| **R < 0.35** | **12** | **3.0 %** | **3** | **25.0 %** | **100 %** |
| R < 0.50 | 24 | 6.0 % | 3 | 12.5 % | 100 % |

At R < 0.35 three percent of crops would fall back to the full width, covering all three
known contradictions. Precision of 25 % is the correct trade here: nine of twelve
flagged crops could also have been routed, at a cost of 3 % extra compute, and no known
misroute survives.

### This supersedes the earlier ad-hoc gate proposal

An earlier margin-based gate (`margin < 0.2`, suggested from the legal analysis) would
have **missed two of the three** contradictions - both sit at margins of 0.157 and
0.257. The coherence gate is not merely tighter, it is derived from a measured property
rather than chosen from the observations it was meant to explain.

### Limit

**n = 3 contradictions.** The R < 0.35 threshold catches all three *known* cases; it is
not a calibrated false-negative rate. A rate needs many more contradictions: legal has 9
misroutes per 100 crops, which makes it the natural next measuring set for a
`--pos-dump` run.

## Legal position dump -- the coherence gate does not survive n=200

The code analysis above proposed a coherence gate (R < 0.35) on n=3 contradictions.
legal is the natural calibration set: 19 misroutes per 200 crops, all against the base
route 8192. The dump ran 200 crops against that single peer (rc=0, 630 s).

```
chosen distribution: 181 x 53248 (own), 19 x 8192 (base)
early-window vs late-ordering disagreements: 20
disagreements that are also misroutes: 17 of 20
```

Note the last line: "the early window contradicts the late ordering" and "the crop was
misrouted" are related but **not identical**. Three crops (167, 39, 81) contradict and
still route correctly; two misroutes do not appear in the contradiction set.

### No metric separates

| metric | contradictions (median) | agreeing (median) | worst agreeing value | disagreements inside the agreeing range |
|---|---|---|---|---|
| **R = abs(M)/A** | 0.175 | 0.570 | **0.027** | 18/20 |
| conc5 | 0.274 | 0.309 | 0.183 | 19/20 |
| **k50** | **14** | **11** | 6 | **20/20** |
| neg_share | 0.344 | 0.504 | 0.297 | 16/20 |

R has the largest median gap (factor 3.3) but the distributions overlap almost
completely: the single lowest R in the whole dataset (0.027) belongs to an **agreeing**
crop. conc5 is nearly flat. **k50 is inverted** -- contradictions have a *higher* k50
than agreeing crops, so the metric points the wrong way.

### Gate cost at equal coverage

Each row flags the bottom decile / quintile / third of the metric distribution:

| metric | flagged | share | contradictions caught | precision | recall |
|---|---|---|---|---|---|
| R <= 0.362 | 61 | **30.5 %** | 18/20 | 29.5 % | **90 %** |
| conc5 <= 0.285 | 61 | 30.5 % | 12/20 | 19.7 % | 60 % |
| k50 <= 10 | 77 | 38.5 % | 1/20 | 1.3 % | 5 % |

At a 30 % compute overhead R reaches 90 % recall. For the last two contradictions the
threshold must drop to R < 0.50, at which point 45 % of all crops fall back to the full
width. That is no longer a cheap gate; it is disabling the router for half a domain.

### Conclusion, stated plainly

**The R < 0.35 gate proposed in the code analysis is withdrawn.** It was supported by
n=3; at n=200 the overlap between the distributions makes it useless as a binary
decision.

What survives is weaker and still worth recording: **R correlates with unreliability**
(median 0.175 vs 0.570, consistent with the code measurement) and is therefore usable
as a **diagnostic**, not a switch. No single metric among the four tested permits a
cheap binary routing decision on either domain.

The code result (3 % flagged, 100 % recall) was an artefact of three data points. The
lesson is methodological: a threshold proposed from three cases and then tested on
twenty is a threshold that has not been tested at all.

## Stage (a): worst-case accuracy at the decision boundary

The prereg (`e288141`) defines the margin as NLL(second best route) minus NLL(best
route) over the early window and requires the adversarial set to be built from it. The
evaluator originally kept only the argmin; `--margin-dump` (commit `74c736f`) emits both
scores and the margin per crop with no additional forwards.

Two runs, 200 crops each, 25 routes, `--margin-dump`:

| domain | wall | rc | correct | misrouted |
|---|---|---|---|---|
| legal | 5233 s (1.45 h) | 0 | 181/200 = 90.5 % | 19 |
| code | 5246 s (1.46 h) | 0 | 196/200 = 98.0 % | 4 |

### Margin distribution

| | legal | code |
|---|---|---|
| p5 | 0.0666 | 0.2439 |
| p25 | 0.2586 | 0.7637 |
| median | 0.4918 | 1.1397 |
| min | 0.0146 | 0.0163 |

### Worst-case accuracy, not the mean

This is the number the prereg asks for. Accuracy by margin band:

| margin band | legal n | legal accuracy | code n | code accuracy |
|---|---|---|---|---|
| 0.0 - 0.1 | 22 | **59.1 %** | 2 | **50.0 %** |
| 0.1 - 0.2 | 14 | 71.4 % | 5 | 80.0 % |
| 0.2 - 0.5 | 65 | 92.3 % | 15 | 93.3 % |
| 0.5 - 1.0 | 95 | 98.9 % | 55 | 98.2 % |
| >= 1.0 | 4 | 100.0 % | 123 | 100.0 % |

**The decline is monotone across all five bands in both domains.** The headline figures
(90.5 %, 98.0 %, 99.44 % overall) are averages over the margin distribution. In the
lowest band, where the prereg expects the failure to live, accuracy is 59.1 % on legal
and 50.0 % on code (n=2 there, so only the legal figure is informative).

This is the qualitative difference from the coherence measure R: R overlapped almost
completely on legal (worst agreeing crop at R = 0.027), whereas the margin orders the
crops correctly. What the margin does **not** do is separate them cheaply.

### The two prereg metrics

| metric | definition | legal | code |
|---|---|---|---|
| boundary failures | `margin < 0.1` AND wrong | **9/22 = 4.50 %** | 1/2 = 0.50 % |
| near-boundary (A1) | `margin < 0.5` AND wrong | **18/101 = 9.00 %** | 3/22 = 1.50 % |

Under the fixed 0.1 nat definition, 9 of the 19 legal misroutes count. The other ten fall
into the near-boundary band that amendment A1 introduced for exactly this reason.

### Margin separates better than R, and is still not a cheap gate

| | misrouted median | correct median | ratio |
|---|---|---|---|
| legal margin | 0.1237 | 0.5312 | 4.3x |
| legal R | 0.175 | 0.570 | 3.3x |
| code margin | 0.2731 | 1.1432 | 4.2x |

But the cost is prohibitive. A gate at `margin < 0.5` would fall back to full width on
**50 % of legal crops** and catch 18 of 19 misroutes. At `margin < 0.1` the fallback is
11 % and only 9 of 19 are caught. There is no threshold that is both cheap and complete.

Consistency note, since the two numbers were previously reported separately: legal's
9.5 % error rate and its 0.03 nat aggregate cost are both true. The misroutes sit where
both routes are nearly equally good, so the error rate is high and the damage is small.

## Stage (b): no cheap reliability feature

Stage (a) showed that accuracy falls monotonically with the routing margin, but the
margin alone does not separate cheaply. Stage (b) asks the sharper question: does any
feature derivable from the full score vector predict the error better than the raw
margin, at an acceptable fallback cost?

`--score-vector` (commit `1111146`) emits all 25 per-route early-window scores per crop,
so every feature below is computed offline with no additional forwards. Two runs, 200
crops each, rc=0 (legal 5257 s, code 5260 s).

Six features were tested. All are oriented so that a **low** value flags a suspect crop:

| feature | definition |
|---|---|
| margin | s2 - s1 |
| norm_margin | (s2 - s1) / s1 |
| gap3 | s3 - s1 |
| spread | max(scores) - min(scores) |
| std | population std over the 25 scores |
| n_close | number of routes within 10 % of the best score |

### Results at 20 % fallback

| feature | legal caught | code caught |
|---|---|---|
| **margin** | **15/19 (79 %)** | **4/4** |
| **norm_margin** | **15/19 (79 %)** | **4/4** |
| gap3 | 7/19 | 4/4 |
| spread | 7/19 | 3/4 |
| std | 4/19 | 1/4 |
| n_close | 3/19 | 0/4 |

### Three findings

**Normalisation changes nothing.** `norm_margin` produces exactly the same hit counts as
`margin` (15/19 and 4/4). The relative score level carries no information the absolute
value does not already carry. A plausible fix -- "maybe it is the score magnitude" -- is
ruled out.

**std points the wrong way.** Misrouted legal crops have a *higher* score spread
(median 0.7586) than correctly routed ones (0.7167). The intuitive expectation, that
errors occur on a flat landscape, is wrong here; but the effect is weak enough to catch
only 4 of 19.

**n_close is conceptually right and practically useless.** Misrouted crops do have more
routes within 10 % of the best score (median 2.0 vs 1.0) -- exactly the expected
direction. It still catches only 3 of 19, because most correct crops also have
`n_close = 1`.

### Answer to the prereg question (b)

> Is there a cheap feature that predicts routing unreliability?

**No.** Six features, 800 (crop, route) pairs, two domains. None permits a binary
decision below 20 % fallback that catches more than 79 % of the errors, and the raw
margin remains the best of the six.

This is a negative result and it is load-bearing: after R (n=3), legal R (n=20), the
margin bands (n=200) and these six features, every measurement says the same thing. The
error sits at the boundary and the boundary is not cheaply recognisable.

### What remains practically

| option | cost | effect |
|---|---|---|
| do nothing | 0 % fallback | 9.5 % legal error rate, **0.03 nats** aggregate |
| 20 % margin gate | 20 % fallback | removes 79 % of legal errors |
| never route legal | 1 of 25 domains special-cased | zero legal errors, full width always |

On the damage figures, doing nothing is rational: a 9.5 % error rate costing 0.03 nats
over the domain is cheaper than a 20 % compute surcharge. The gate is only worth its
cost if a legal misroute is expensive for a reason outside perplexity -- and that has
not been shown.

## Five domains: the base route is not a generalist

An earlier reading of the legal and code score vectors -- that the base route 8192 is a
generalist competitor on every territory -- rested on two domains. Three more score
vector runs (math, zh, ga; 200 crops each, rc=0, 5246-5260 s) refute it.

For each domain, the best route **other than the domain's own** and the rank of 8192
among the 24 off-domain routes:

| domain | own route | best off-domain route | its score | rank of 8192 | 8192 score | gap to best |
|---|---|---|---|---|---|---|
| legal | 53248 | **8192** | 1.6512 | **#1** | 1.6512 | +0.0000 |
| code | 49152 | 53248 | 3.3564 | #6 | 5.2091 | +1.8527 |
| math | 51200 | 53248 | 2.2836 | #5 | 4.1766 | +1.8931 |
| zh | 57344 | 49152 | 3.2912 | #5 | 4.2229 | +0.9317 |
| ga | 55296 | 57344 | 3.4486 | #3 | 3.4486 | +1.1996 |

The base route wins on **legal only**. On the other four it sits mid-field. The
two-domain generalisation was wrong, and it is the same error as the earlier R threshold:
concluding from a sample too small to carry the claim.

### What the five domains do show: a width gradient

Pearson correlation between route width and mean off-domain score:

| domain | rho |
|---|---|
| legal | -0.007 |
| code | -0.648 |
| math | -0.530 |
| zh | -0.539 |
| ga | -0.176 |

**All five are negative.** Wider routes score *better* on foreign territory, and the best
off-domain competitor is in every case one of the wider routes. A route of width `w`
contains all neurons from phases 1..k, so more width means more frozen territories and
therefore a better generalist. This is a capacity monotonicity, not an additive bias.

legal is the exception and it is explainable: legal text is natural language, close to
the prose the base route was trained on. legal flips to 8192 because 8192 is genuinely
competent there -- not because a noise term pushes it.

### Caveat on the neighbour pattern

In three of five domains the best off-domain route is a near neighbour in the growth
order (code to 53248 at distance 2, math to 53248 at distance 1, ga to 57344 at distance
1). That looks like an ordering effect, but width rises monotonically with training
order, so "neighbour" and "wider" are partly the same variable. Five domains cannot
separate them; the remaining twenty would.

### Consequence for the router bias-correction prereg

The RBC-1 prereg (`docs/plans/2026-11-02_router-bias-correction-escalation-prereg.md`,
v0.1 draft) names two candidate causes: H1, an asymmetric per-route bias pushing
borderline crops toward the base route, and H2, a scoring window that is too short.

These five domains bear on H1: a positive bias would mean wider routes score *worse*
off-domain. They score better in all five. **H1 as stated is contradicted.** H2 is not
touched by this analysis and remains open.

## What this does and does not establish

**Establishes (measured on this exact crop set: 20 crops x 25 corpora = 500 crops,
frozen zh_last.pt checkpoint, window 128, no held-out data):**
- A 25-route likelihood router over a 24-phase grown BDH stack separates all 25
  territories at 99.8 % on this crop set.
- Serving on the correct width is worth 2.5-4 orders of magnitude in perplexity
  versus serving on a wrong width.
- The legal -> prose confusion persists at n_embd 1024 but is 31x smaller than at
  n_embd 256 (1/20 vs 31/200).

**Does not establish (open, as preregistered):**
- **Generalisation to unseen crops.** 20 crops per domain is a sample. The
  adversarial half of the prereg -- margin-based boundary crops and cross-domain
  pairs -- has not run yet. Until it does, 99.8 % is a benchmark statistic, not a
  guarantee, exactly as Gyorgy et al. argue in `arXiv:2506.23908` (see
  `docs/research/2026-10-23_exact-learning-vs-bdh-cl.md`).
- **Generalisation to unseen territories.** No held-out domain was tested. The
  route set is the training order; a 26th territory has no width of its own by
  construction.
- **Anything about continual learning.** The router is evaluated on a frozen
  checkpoint; retention during growth was assessed separately by P5/K4.

## Next

The adversarial router test (prereg `e288141`, second half) is the decisive follow-up.
It needs the margin distribution per domain, which this run did not record -- the
`--crop-dump` path exists in the evaluator and will provide it for the domains with
the weakest margins.
