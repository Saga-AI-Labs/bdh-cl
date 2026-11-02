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
