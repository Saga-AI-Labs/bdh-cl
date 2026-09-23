# Scaling-readiness K20 pre-registration - 19 Europarl + 4 B/C + 1 CJK anchor, two ladders

- Date: 2026-09-23. Seat: A0-Quinn. Operator GO (verbatim): "Dann nehmen wir die 19
  Europarl mit einem CJK-Anker. Go."
- Scope: TRAINING. Two ladders of 24 grows each on the two already-trained A1-K5 bases.
  No base pretrain is re-run. Writes only out_c/scaling_readiness/k20/. out/ and out_a/
  are read-only; the phase-2 upload set in out/ is never touched.
- Why K20 now: P3 (7 grows) measured acquisition and load-bearing on every phase; A1-K20
  is the arm the Sonde-A plan needs to read the cost and accuracy knee at scale, and
  P3c closed the capability gap Pi-50 named in #455 before this spend.

## 0. Why this exact mix (decided, not guessed)

The ladder tool `scripts/quinn/ladder_sondeA.sh` refuses `A1-K20` with exit 6: the
territory mix was an explicit operator decision and no mix was encoded. That decision is
made here and written out in full:

**24 grows: 19 Europarl language sides, 4 B/C classes, 1 CJK anchor.**

| # | tag | corpus (guest path) | corpus md5 | width |
| --- | --- | --- | --- | --- |
| 1 | es | data/europarl/europarl-v7.es-en.es.txt | 17d03c84750988fdf84705ef4935db7f | 10240 |
| 2 | pl | data/europarl/europarl-v7.pl-en.pl.txt | 4f9b2d58efdff2b928005ccbf91b08ce | 12288 |
| 3 | fr | data/europarl/europarl-v7.fr-en.fr.txt | fb585c23a9b38555b8a3f1141d73c5f2 | 14336 |
| 4 | de | data/europarl/europarl-v7.de-en.de.txt | f77dd3ab69ea7cc7ef9248e4d96449e1 | 16384 |
| 5 | cs | data/europarl/europarl-v7.cs-en.cs.txt | b4ea563c1b08f6f01689d3cb9948be54 | 18432 |
| 6 | da | data/europarl/europarl-v7.da-en.da.txt | 5c9f3b40a956851706245df46ee22722 | 20480 |
| 7 | pt | data/europarl/europarl-v7.pt-en.pt.txt | 48e3a3fec884fcec04c9b72f002bb18b | 22528 |
| 8 | fi | data/europarl/europarl-v7.fi-en.fi.txt | 7b0764323bea50104d72543752c6ccd5 | 24576 |
| 9 | hu | data/europarl/europarl-v7.hu-en.hu.txt | 8807c3192794e93c1a297d4beb773a57 | 26624 |
| 10 | bg | data/europarl/europarl-v7.bg-en.bg.txt | 4d2c67dc505caead148da9549b20f0a6 | 28672 |
| 11 | it | data/europarl/europarl-v7.it-en.it.txt | dbe546232b31a90b1f845ec6fbf4dd12 | 30720 |
| 12 | et | data/europarl/europarl-v7.et-en.et.txt | 7a37eccafc03906d60501fd7538a78b9 | 32768 |
| 13 | el | data/europarl/europarl-v7.el-en.el.txt | c930e71887e795ac2648e11e8e13b152 | 34816 |
| 14 | sk | data/europarl/europarl-v7.sk-en.sk.txt | 1d9b5bb09bcc6a646b6dff22699a5aad | 36864 |
| 15 | sv | data/europarl/europarl-v7.sv-en.sv.txt | 1306f4bade3fd9c78605f2b6116056d3 | 38912 |
| 16 | ro | data/europarl/europarl-v7.ro-en.ro.txt | bfe10371e91f624a93f2ed1f6ae50dbf | 40960 |
| 17 | nl | data/europarl/europarl-v7.nl-en.nl.txt | bbf95e1a05d5bdd5201d183184c8f246 | 43008 |
| 18 | sl | data/europarl/europarl-v7.sl-en.sl.txt | 319065a4fc0075cfe52c802bd0912c64 | 45056 |
| 19 | lt | data/europarl/europarl-v7.lt-en.lt.txt | f092553025e85d04a393f3111b03ea69 | 47104 |
| 20 | code | data/textmix2/code.txt | 82fe4bf18725b550b23a4e1040b10a2d | 49152 |
| 21 | math | data/textmix2/latex.txt | 6a1a069e969e85b00532328550e10540 | 51200 |
| 22 | legal | data/textmix2/legal.txt | 0135960429085039dbe5385f649e75fe | 53248 |
| 23 | ga | data/europarl/DGT.en-ga.ga.txt | e170553dacb07a78aabf34c0ecbbdb2b | 55296 |
| 24 | zh | data/europarl/xscript_zh.txt | dc2203307a9dc80ddd897e3109dbf3f6 | 57344 |

Domain tag `math` maps to `data/textmix2/latex.txt`, as in P3 (the tag is the label, the file
is the corpus). Prose is the pre-trained base, not a grow. Phase i has width 8192 + 2048*i.

**Order rationale (stated so it can be falsified, not discovered later):** the first 19
grows are RA2b's own order minus its `en` base (`es pl fr de cs da pt fi hu bg it et el sk sv
ro nl sl lt`), so each of the 19 languages sits at exactly the width it has in RA2b's
20-phase ladder (width depends on phase index, not on corpus). The 4 B/C classes come next,
as the annex the Sonde-A plan requires; `zh` closes the ladder as the cross-script anchor
(CJK, byte-distinct from every other corpus in the ladder, 1.29 GB, UTF-8 checked by `od`).

**Not comparable and not claimed:** `_europarl_blocks` reads the tail of a corpus file
(`raw[-need:]`), `_prepare_textmix` reads the head (`f.read(mb*1_000_000)`). The two loaders
therefore train on disjoint byte windows of the same file. No per-language number from this
ladder can be compared to an RA2b number; what is comparable is the protocol and the width
schedule. This limit is stated here so it cannot be mistaken for a result later.

## 1. Objects (md5 pinned before the run; a mismatch aborts, no training step taken)

Bases (reused read-only, never written):

| ladder | base checkpoint | md5 | seed |
| --- | --- | --- | --- |
| A | out_a/bdh_textmix_ladA-A1-K5-base_last.pt | 4346dec144c1d44cc8155a67eb9623ce | 1337 (config default, unlabeled) |
| B | out_a/bdh_textmix_ladA-A1-K5-seed2-base_last.pt | 8680bd26ed55ddd2883bd077ad49e665 | 2 |

Instruments and code, guest HEAD e6bf35919d1ef453f94b017c0e51d2e6a49a7463:

| file | md5 |
| --- | --- |
| scripts/eval_router.py | 73832ecd08f24eded93a98a74572be6e |
| scripts/p5_inchain_check.py | 4456a8ecfbd503e02a306cc3475b494e |
| pipeline/data.py | c45ea50de77b44c7816e9636e782461e |
| pipeline/train.py | 3ad7848ded61f35ee292bc24d5c728e4 |
| pipeline/config.py | 904b69549d953d72017126549ed2a2e1 |
| data/textmix/wikitext-103-raw/wiki.train.raw (prose) | 8a2d5ab8735b1246d49cf767b70d4dd0 |

All 24 grow corpora exist on the guest and are byte-distinct (24 distinct md5s, table above).
`lv` stays in reserve; `tinyshakespeare` (1.1 MB) is excluded as too small for 200 crops.
The `en` side of `de-en` is the RA2b base language and is not a grow.

## 2. Protocol (frozen, identical to P3 line for line)

`--model bdh --dataset textmix --text-mix "<tag>:<corpus>" --text-mix-mb 30
--n-embd 512 --n-head 8 --block-size 512 --max-iters 10000 --batch-size 1
--warmup-iters 1000 --lr-decay-iters 10000 --grow-mult 32 --init-from <prev>
--no-freeze-attn --route-aware --route-alpha 0.9`, fresh optimizer per phase, F-V9
step-end restore, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

Ladder A initialises from base A; ladder B from base B. Both run the same 24-phase order
INV-1: the two ladders differ only by initialisation seed.

## 3. Instruments per phase (as in P3, reduced)

- `p5_inchain_check.py <parent> <child>` at EVERY transition: storage must hold at every
  scale step, not spot-checked. A FAIL stops the ladder.
- `eval_router.py` own-width routdiag per phase (all domains accumulated, window 128,
  200 crops, mb 30, batch 4).
- Per-phase checkpoint bytes, md5, wall clock.
- Final phase: full confusion matrix over all 25 territory widths.

## 4. Frozen verdicts (set BEFORE the first training step)

- **K1 cost linearity:** per-ladder wall clock must stay within 1.5x the model in section 5.
  A phase exceeding 1.5x its predicted wall is stopped, logged, and reported, not awaited.
- **K2 storage:** P5 PASS on 24 of 24 transitions per ladder. Any FAIL stops the ladder and
  is reported with the parent/child pair.
- **K3 routing at final width:** final-phase routing accuracy >= 0.95 over the accumulated
  domains. Below 0.95 is K20-PARTIAL and is reported as such.
- **K4 first-phase retention:** prose ppl at 8192 before the first grow vs after it,
  `|delta| <= 0.08` (the P3 gate, unchanged).
- **K5 ladder agreement:** the two ladders report the same sign on K3 and K4. A disagreement
  is reported as such and is not averaged away.
- No p-values: two ladders, descriptive.

## 5. Cost (measured P3 calibration + arithmetic, plus two memory measurements)

- P3 calibration (measured, this repo): grows at widths 10240..22528 took
  1130,1375,1578,1497,2067,1963,2282 s = 11892 s; linear fit 0.094 s per width unit
  (residuals -10%..+10%).
- K20, 24 grows, widths 10240..57344, 10000 steps/phase, batch 1:
  `sum_i 0.094*(8192+2048*i), i=1..24 = 0.094 * 811,008 = 76,235 s = 21.2 h` per ladder
  (`811,008 = 24*8192 + 2048*24*25/2`, stated so the arithmetic is checkable).
  Two ladders: **42.4 h**, plus instruments and P5: planned wall **44-47 h**.
- **VRAM, measured through the real CLI on this guest** (5 steps, batch 1, bf16, textmix):

  | mult | width | params | peak VRAM | headroom |
  | --- | --- | --- | --- | --- |
  | 736 | 47104 | 579,076,096 | 18,174 MiB | 6.4 GB |
  | 896 | 57344 | 704,905,216 | 21,934 MiB | 2.6 GB |

  24.564 MiB total. The ladder's last phase (mult 896) is the measured worst case and it
  fits with 2.6 GB headroom. Both probes wrote no checkpoint into the repo and were deleted
  after reading; both ran under an exclusive `gpu://rtx4090` claim that was released after.

## 6. Stop rules (bound before the run, not improvised during it)

- checkpoint md5 mismatch, P5 FAIL, or a phase over 1.5x its predicted wall stops that
  ladder; the other ladder continues and the stop is reported.
- free space on /media/data below 600 GB stops the run (24 phases x ~14 GB x 2 ladders
  = ~672 GB worst case).
- GPU claim must be held and renewed for the whole window, or the run stops. No training
  without a live claim.

## 7. Ship

- Reports ASCII, end with newline; the j-space ship gate must report the outgoing register
  holds.
- Bus: intent before launch (with both base md5s and the full mix), done after, three-way
  SHA for each commit.
- Outputs: out_c/scaling_readiness/k20/, per-phase logs plus k20_ladder_A_analysis.txt and
  k20_ladder_B_analysis.txt, all md5-pinned in the report.
