# Scaling-readiness P1b report - one grow, reduced legal cell

- Date: 2026-09-23 (UTC window; run 2026-09-22 23:09-23:30 UTC) - Seat: A0-Quinn
- Pre-registration: `docs/plans/2026-09-22_scaling-readiness-p1b-prereg.md`
  (`1cf3dbf0c04d3596b83cec6df435d1e46ca241d6`), gates frozen before launch
- Operator GO for the training spend on the 4090; GPU claim
  `s_bdh-cl_000154_fa5ebb` (`gpu://rtx4090`, exclusive), renewed every ~9 min,
  released when done. No other process on the card during the run.
- Instrument: `out_c/scaling_readiness/p1b_driver.sh`, md5
  `8dc8af3fbca10a076b16ffd7ef855057`, identical local and guest (md5 gate).

## 1. What was trained

One grow, seed-2 base only (no reference ladder, no new base):

| item | value |
| --- | --- |
| init | `out_a/bdh_textmix_ladA-A1-K5-seed2-base_last.pt` (mult 128, width 8192), read-only |
| grow-mult | 64: 128 -> 192, N = 192 * 512 // 8 = **12288** |
| corpus | `data/textmix2/legal.txt`, md5 `0135960429085039dbe5385f649e75fe` (gate passed) |
| protocol | bs 512, alpha 0.9, 10000 iters, fresh optimizer, F-V9, batch 1, mb 30 cap |
| writes | `out_c/scaling_readiness/p1b/` only; `out/` and `out_a/` untouched |

`grow_rc=0`, wall 01:09:18 -> 01:29:31 = **20 min 13 s** (~83-125 ms/step).
Checkpoint `bdh_textmix_p1b-gm64_last.pt` 1813044720 B, md5
`70c626d5a42bf437bb7fac6466f9560e`; `_best.pt` same size. Size sanity:
2115042989 * 12288 / 14336 = 1.813e9, matches the produced file to 0.005 %
- the width is real.

Train log: final `loss 1.9332`, `test_ppl 2.10`, best `val_loss 0.6721
(ppl 1.96)`.

## 2. Measurement (no further training)

`eval_router.py <ckpt> --routes 12288 --window 128 --crops 200 --mb 30
--batch 4`, five domains, pinned corpora; `eval_rc=0`, output 485 B (no stub).

Routed ppl, rows = true domain (200 crops each, all 200 routed at 12288):

| domain | routed @12288 |
| --- | --- |
| code | 71.64 |
| math | 38.66 |
| **legal** | **2.07** |
| ga | 28.76 |
| prose | 4.11 |
| joint full-width reference | 14.66 |

Trained-domain caveat as pre-registered: code/math/ga/prose are served by a
single-domain-trained model and are not comparable to the harvest cells; the
legal row at the model's own width is the measure.

## 3. Frozen reading

| quantity | value |
| --- | --- |
| gm64 legal served @12288 (this run) | 2.07 |
| gm96 legal served @14336 (comparison value, P1a table, seed-2 `_last`) | 2.20 |
| gap | abs(2.07 - 2.20) = **0.13** |
| band (pre-registered) | <=0.10 adopt stopping rule / >0.25 withdraw saturation / else INCONCLUSIVE |

**Verdict: INCONCLUSIVE.** 0.10 < 0.13 <= 0.25 is the declared middle band.

- the stopping rule (forced-width final increment < 1.15x) is **not adopted**;
- the saturation reading is **not withdrawn**;
- `legal` keeps its gm96 sizing; the over-grown flag on gm96 is **not raised**.

Direction noted, without changing the verdict: the half-size grow reaches a
slightly *lower* ppl at its own width (2.07 at 12288 vs 2.20 at 14336) - the
smaller model is not worse at its own width, which is what motivated the
saturation reading in the first place. One cell and one gap do not decide it;
the band does not.

## 4. Not measured

- the pre-registered secondary no-growth floor (@8192, the un-grown width) was
  **not measured**: the driver served only the trained width. It is secondary
  and not gate-bearing for the band; it can be measured post-P3 under the same
  claim if wanted.

## 5. Reproduction

```
ssh bdh-4090 'cd /media/data/coding/bdh && bash /tmp/p1b_driver.sh'
# guest artifacts: out_c/scaling_readiness/p1b/{p1b_train.log,
#                  p1b_gm64.routdiag.txt, bdh_textmix_p1b-gm64_{last,best}.pt}
# log: /tmp/p1b.log
```
