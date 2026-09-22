# Scaling-readiness P3 pre-registration - mixed K=8 pilot ladder

- Date: 2026-09-22 (UTC) - Seat: A0-Quinn - Status: FROZEN before launch
- Parent: `2026-09-22_scaling-readiness-gaps-and-probes-prereg.md` (76dd597), P3
- Operator GO: 2026-09-22, P1b and P3 approved for the 4090 (idle), GPU via
  `gpu://rtx4090` exclusive claim; renewed while running, released when done.
- This is the only mid-cost item of the plan; every number and gate below is
  taken from the parent pre-registration, corrections are stated as corrections.

## 1. What is trained

One ladder, 7 grows, this mix (Europarl + code/legal crossing script/register)
has never been grown together:

1. base: `prose` (wikitext-103-raw, 540568191 B on the guest)
2. de  (`europarl-v7.de-en.de.txt`, 328463491 B) - PRESENT on the guest
3. es  (`europarl-v7.es-en.es.txt`, 324915736 B) - PRESENT on the guest
4. pl  (`europarl-v7.pl-en.pl.txt`, 101121586 B) - PRESENT, the P-R3 hard cell
5. code (`data/textmix2/code.txt`, 40529764 B)
6. math (`data/textmix2/latex.txt`, 40006401 B)
7. legal (`data/textmix2/legal.txt`, 40347823 B, md5 `0135960429085039dbe5385f649e75fe`)
8. ga   (`data/europarl/DGT.en-ga.ga.txt`, 55409138 B)

Protocol congruent with B/C0 and the sonde-B form, not re-invented:
`--model bdh --n-embd 512 --n-head 8 --block-size 512 --max-iters 10000
--warmup-iters 1000 --lr-decay-iters 10000 --grow-mult 32 --no-freeze-attn
--route-aware --route-alpha 0.9` (F-V9 step-end restore, fresh optimizer per
phase). textmix phases via `--dataset textmix --text-mix ... --text-mix-mb 30`,
europarl phases via `--dataset europarl --europarl-langs <L> --europarl-lang-mb 30`.
`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, `--batch-size 1` as in the
wide-checkpoint OOM guard.

Base: read-only reuse of the existing prose base checkpoint is permitted
(the sonde-B resume did NOT re-run the 150k base steps); if the base is reused
the base cost drops away, otherwise the base (150k steps) is trained first and
its cost is added. Which of the two applies is stated in the intent envelope
before the launch, not decided after.

Writes: `out_c/scaling_readiness/p3/` only; `out/` and `out_a/` are not
touched; guest HEAD stays at `e6bf359`.

## 2. Instruments per phase (Sonde-A suite, reduced)

- acquisition; P5 (`scripts/p5_inchain_check.py <parent> <child>`) at every
  transition; full 8x8 confusion at 200 crops, window 128, mb 30, batch 4;
  retention deltas; joint-vs-routed; wall-clock and bytes/phase.

## 3. Frozen gates (from the parent pre-registration, verbatim)

- P3-PASS if P5 7/7 AND routing >= 0.95 AND first-phase retention
  `|Delta| <= 0.08` -> GO A1-K20 unchanged
- P3-PARTIAL if storage holds but routing 0.85-0.95 or cost slope > 2x first
  phase -> GO A1-K20 with narrowed mix (drop hardest Europarl cell) + record
  knee
- P3-FAIL if P5 fails any transition -> HALT, pivot to F-V9 audit (Gate A-FAIL)

## 4. Cost, correction

- Scaling from A1-K5: 12.3h / 5 phases = 2.46 h per 10k-step phase. The 7 grows
  are therefore ~17.2 h; plus the base cost if the base is not reused.
  Correction: the parent text says "~8-12h"; that figure does not agree with
  the stated per-phase scaling (7 x 2.46 = 17.2) and is superseded here.
- abort (do not start) if: a corpus md5 differs from the pin; the GPU claim is
  not held; a foreign process runs on the card
- a phase exceeding 1.5x the 2.46h estimate is stopped and reported, not awaited
- outputs: per-phase ckpts + routdiags + `p3_ladder_analysis.txt` (md5-pinned
  in the report); bus: intent before, done after (`bdh-cl`)
