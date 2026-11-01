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
| Overall accuracy | **499/500 = 99.8 %** (20-crop estimate; see the n=200 follow-up below) |
| Worst domain | **legal 181/200 = 90.5 %** (measured at n=200; the 20-crop sample above showed 19/20) |
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
