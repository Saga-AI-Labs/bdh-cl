# Scaling-readiness P3 report - mixed K=8 pilot ladder (P3-PASS)

- Date: 2026-09-23 (run window 01:48:09 - 05:28:17 host time, 3 h 40 min 08 s)
- Seat: A0-Quinn - Pre-registration:
  `docs/plans/2026-09-22_scaling-readiness-p3-prereg.md`
  (`1cf3dbf0c04d3596b83cec6df435d1e46ca241d6`), gates frozen before launch
- Operator GO for the training spend on the 4090. Pre-claim idle gate verified by each of
  nvidia-smi (0 %, 287 MiB) and ps (no competing pipeline.run/eval_router),
  before the claim. GPU claim `s_bdh-cl_000154_fa5ebb`
  (`gpu://rtx4090`, exclusive), renewed every ~9 min while the driver ran
  (renew HTTP 200, never lapsed), released HTTP 204 when the card was idle
  again (287 MiB / 0 %). Bus intent `m_bdh-cl_0000000447` before launch.
- Base: read-only reuse of `out_a/bdh_textmix_ladA-A1-K5-seed2-base_last.pt`
  (mult 128, width 8192); the 150k base steps were NOT re-run (declared in
  the intent before launch, per the pre-registration).
- Instrument: `out_c/scaling_readiness/p3_driver.sh`, md5
  `2791b2ec6f6e49c125125f3590451ee6`, identical local and guest (md5 gate
  passed). Writes only `out_c/scaling_readiness/p3/`; `out/` and `out_a/`
  untouched.
- Protocol (frozen, per the existing sonde-B form, not re-invented):
  `--model bdh --dataset textmix --text-mix-mb 30 --n-embd 512 --n-head 8
  --block-size 512 --max-iters 10000 --batch-size 1 --warmup-iters 1000
  --lr-decay-iters 10000 --grow-mult 32 --no-freeze-attn --route-aware
  --route-alpha 0.9`, fresh optimizer per phase, F-V9 step-end restore,
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

## 1. The ladder (7 grows, never grown together before)

| phase | domain | width | train_rc | wall s | ckpt bytes | ckpt md5 |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | de | 10240 | 0 | 1130 | 1511046577 | add1438f2dd673e3a0d8195e40acffcd |
| 3 | es | 12288 | 0 | 1375 | 1813044657 | d74921a9aa0049ae251bfbaffb9ecc41 |
| 4 | pl | 14336 | 0 | 1578 | 2115042737 | e9707f8f88bed8c4fd1bf059ee0d4067 |
| 5 | code | 16384 | 0 | 1497 | 2417040859 | 89e90ecd7a8bb0c70e22d93a6447efa9 |
| 6 | math | 18432 | 0 | 2067 | 2719038939 | 081f95ba148deae32eb2f1f7cb683c0f |
| 7 | legal | 20480 | 0 | 1963 | 3021037040 | fd9f802d831f9e88e21206d448d9f4ff |
| 8 | ga | 22528 | 0 | 2282 | 3323035057 | 8814ddc62d737e05c5c0b1fe221bd889 |

Size sanity: the pl checkpoint (width 14336) is 2115042737 B against the
sonde-B legal checkpoint of the same width at 2115042989 B - a 252 B
optimizer-state difference, the width is real; the ga checkpoint matches
2115042737 * 22528 / 14336 = 3.323e9 to the megabyte.

Corpus md5s as recorded by the driver: de `f77dd3ab69ea7cc7ef9248e4d96449e1`,
es `17d03c84750988fdf84705ef4935db7f`, pl `4f9b2d58efdff2b928005ccbf91b08ce`,
code `82fe4bf18725b550b23a4e1040b10a2d`, math `6a1a069e969e85b00532328550e10540`,
legal `0135960429085039dbe5385f649e75fe` (gate passed), ga
`e170553dacb07a78aabf34c0ecbbdb2b`.

## 2. P5 at every transition: 7/7 PASS

Read from the raw files `out_c/scaling_readiness/p3/p3_p5_<tag>.txt` (all
seven). Per transition, the masked parent block is bit-exact in encoder,
encoder_v, decoder, embed, lm_head and attn.freqs(shared); the optimizer
moments of the masked block are zero (`v(masked)==0`, `m(masked)==0` at
step 10000) and the grown segment is nonzero (`v(grown)!=0`, max|w| in
0.539-0.749). Every file ends in `P5-VERDICT: PASS`.

Instrumentation note: the driver's log line reads `    P5 rc=0 ->` with an
empty tail - my grep pattern for the verdict token did not match the script's
output format (`P5-VERDICT: PASS`). The exit code was real; the verdicts
above are read from the files, not from the log line.

## 3. First-phase retention (frozen gate: |Delta| <= 0.08)

prose@8192, window 128 tok, 200 crops/domain, own width:

| reading | prose ppl |
| --- | --- |
| base checkpoint (before any grow) | 2.48 |
| after the first grow (de, width 10240) | 2.48 |

Delta = 0.00, gate passed.

The joint line of those two evals reads 2.48 vs 12.98 - that is a different
evaluation scope (the base was measured over prose alone, the post-grow file
lists prose served inside the 8-domain ladder run) and is NOT a retention
reading of the same quantity; the gate is decided on the prose@8192 rows
alone.

## 4. Full 8x8 confusion at the last checkpoint (routing gate)

`bdh_textmix_p3-ga_last.pt`, routes = [8192, 10240, 12288, 14336, 16384,
18432, 20480, 22528], window 128 tok, 200 crops/domain (verbatim from
`p3_confusion_final.txt`, 1213 B, rc=0):

```
               8192    10240    12288    14336    16384    18432    20480    22528
    prose       200        0        0        0        0        0        0        0
       de         1      199        0        0        0        0        0        0
       es         0        0      200        0        0        0        0        0
       pl         0        0        0      198        2        0        0        0
     code         3        0        0        0      197        0        0        0
     math         0        0        0        0        0      200        0        0
    legal         5        0        0        0        0        0      195        0
       ga         0        0        0        0        0        0        0      200
```

Routing on the diagonal: 200+199+200+198+197+200+195+200 = **1589/1600 =
0.9931**, gate (>= 0.95) passed. Off-diagonal: 11 crops (de 1, code 3, legal
5 leaking to the un-grown base width 8192; pl 2 to 16384) = 0.69 % - well
under the 4.5 % leak of the sonde-B harvest, same direction (the router
occasionally prefers the narrower prose prefix).

Routed ppl of each domain at its own width: prose 2.48, de 2.64, es 2.59,
pl 3.10, code 6.30, math 1.75, legal 2.63, ga 2.44; joint full-width
reference 34.34 (served positions only, 8 domains). The per-domain own-width
rows are the measure; the cross-domain rows (e.g. code 183.94 at 10240) are
not comparable across widths and are not gate-bearing.

## 5. Frozen gates - verdict

| gate | requirement | measured | result |
| --- | --- | --- | --- |
| P5 | 7/7 | 7/7 PASS (raw files) | met |
| routing | >= 0.95 | 0.9931 | met |
| first-phase retention | \|Delta\| <= 0.08 | 0.00 | met |

**Verdict: P3-PASS -> GO A1-K20 unchanged** (the pre-registration's PASS
branch; no narrowed mix, no knee to record).

## 6. Cost, correction of the pre-registered estimate

The pre-registration carried "~8-12h" scaled from A1-K5 at 2.46 h/phase.
The run took **3 h 40 min 08 s** wall (01:48:09 -> 05:28:17): the seven
grows sum to 11892 s (3 h 11 min 52 s), the instruments (eight own-width
routdiags, seven P5 checks, two retention evals, the 8x8) to ~28 min.
Per phase 19-38 min. The estimate was too high - measured at batch_size 1,
block_size 512 on the 4090, a 10k-step phase costs ~20-38 min, not 2.46 h
(the P1b reference: 20 min 13 s for one 10k-step grow at width 12288).

## 7. Reproduction

```
ssh bdh-4090 'cd /media/data/coding/bdh && bash /tmp/p3_driver.sh'
# guest artifacts: out_c/scaling_readiness/p3/
#   p3_ladder_analysis.txt, p3_<tag>_train.log, p3_p5_<tag>.txt,
#   p3_routdiag_<tag>.txt, p3_retention_base.txt, p3_retention_after_grow1.txt,
#   p3_confusion_final.txt, bdh_textmix_p3-<tag>_{last,best}.pt
# driver log: /tmp/p3.log
```

## 8. Open, not measured

- single ladder, single seed, no reference ladder; no p-values (n = 200
  crops/domain, descriptive).
- the second-boundary directionality (math__ga) was not probed here beyond
  the confusion matrix rows; no dedicated measurement.
- acquisition, joint-vs-routed table and per-phase bytes beyond the ckpt
  sizes were recorded by the driver, not re-analysed in this report.
