# Scaling-readiness P1b pre-registration - one grow, reduced legal cell

- Date: 2026-09-22 (UTC) - Seat: A0-Quinn - Status: FROZEN before launch
- Parent: `2026-09-22_scaling-readiness-gaps-and-probes-prereg.md` (76dd597), P1b
- Operator GO: 2026-09-22, P1b and P3 approved for the 4090 (idle), GPU via
  `gpu://rtx4090` exclusive claim; renewed while running, released when done.

## 1. What is trained (the only training spend of P1b: one cell, bounded)

One grow on the seed-2 base only (no reference-ladder run, no new base):

- init von: `out_a/bdh_textmix_ladA-A1-K5-seed2-base_last.pt` (mult 128,
  N = 8192), read-only
- grow-mult 64: 128 -> 192, so N neu = 192 * 512 // 8 = 12288
- corpus: `prose__legal:data/textmix2/legal.txt`, md5
  `0135960429085039dbe5385f649e75fe` (pinned; abort if it differs)
- protocol repeated from the existing sonde-B/B form (not re-invented):
  `--model bdh --dataset textmix --text-mix-mb 30 --n-embd 512 --n-head 8
  --block-size 512 --max-iters 10000 --batch-size 1 --warmup-iters 1000
  --lr-decay-iters 10000 --no-freeze-attn --route-aware --route-alpha 0.9`
  (F-V9 step-end restore, fresh optimizer per run)
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, batch-size 1 (OOM guard
  for width 192; taken from the wide-checkpoint lesson)
- written to `out_c/scaling_readiness/p1b/` only; `out/` and `out_a/` are not
  touched; guest HEAD stays at `e6bf359`

## 2. What is measured (no further training, eval only)

- `eval_router.py` on the new ckpt, `--routes 12288 --window 128 --crops 200
  --mb 30 --batch 4`, five domains as in the harvest (pinned corpus md5s)
- comparison value (Vergleichszahl): the gm96 legal cell at its own width =
  2.20 ppl. Source stated: P1a table, `prose__legal` seed-2 `_last` served at
  14336 = 2.20 (P1b is seed-2 only, so the 2.20 of the P0 record refers to
  the same family; both readings are stated, no silent mixing)
- secondary: the same eval at 8192 (the un-grown width) as the no-growth floor

## 3. Frozen reading (set before the run; no re-reading afterwards)

- `|gm64 - gm96| <= 0.10` ppl -> adopt the stopping rule: stop growing a
  domain when the forced-width final increment < 1.15x (from `--route-grid`);
  flag legal gm96 as over-grown in the manuscript
- `gap > 0.25` ppl -> keep gm96 sizing; the saturation reading is withdrawn
- `0.10 < gap <= 0.25` -> INCONCLUSIVE; sizing unchanged, reported as it is
  (the pre-registration leaves this band unclassified; it is declared here
  rather than silently decided after the run)

## 4. Gates and abort conditions

- abort (do not start) if: the corpus md5 differs; the GPU claim is not held;
  any process runs on the card that is not mine
- the run is bounded at one cell and at ~60 min; if it exceeds 90 min it is
  stopped and reported, not awaited
- outputs: ckpt + `p1b_gm64.routdiag.txt` (md5-pinned in the report)
- bus: intent before, done after (`bdh-cl`)
