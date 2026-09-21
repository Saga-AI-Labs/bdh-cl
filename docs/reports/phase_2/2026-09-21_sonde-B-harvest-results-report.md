# Sonde B harvest results: grown cells, addressing readout, storage integrity

Date: 2026-09-21 (UTC 15:30-16:57). Seat: A0-Quinn. GO: operator full (a)/(b)/(c) harvest go;
pair selection, twin-matched widths and scale per pre-reg section 7 (operator: pick something reasonable).
Run-site: bdh-cl, /media/data/coding/bdh (four pipeline files md5-identical to tracked HEAD e6bf359).
Card: gpu://rtx4090 claimed exclusive (scope s_bdh-cl_000067_8ee931), detached renewer kept it live,
released at 16:56:47Z (DELETE 204, live-scope readback empty). out/ and out_a/ untouched;
every artifact under out_c/sondeB/harvest.

## 0 Design as applied (frozen pre-reg)

- Grown cells: prose__math, prose__code, math__ga, prose__legal ((a)-anchor). Eval-only: ga__code
  per operator ruling -- retained (b)-only, no flip; oracle = code at per-head width 10240.
- Widths twin-matched to the measured A-ladder set 128/160/192/224/256 (n_embd 512, n_head 8
  gives per-head 8192/10240/12288/14336/16384); grow_mult = twin - 128; block-size 512 mandatory.
- Training: 10000 iters, route-aware alpha 0.9, init from the A-ladder base_last.

## 1 Addressing readout (routed own-width plane; window 128, crops 200, batch 4,
five-domain SPEC verbatim from the committed reference invocation; 200 crops/domain)

Format: domain | claim distribution | served ppl.

prose__math (expert trained: math) | joint 25.33
  prose  200/200 at 8192                     | 2.48
  math   200/200 at 12288 (its expert)        | 1.41
  code   65 at 8192, 86 at 10240, 49 at 12288| 72.67
  ga     197 at 8192, 3 at 10240              | 27.72
  legal  188 at 8192, 12 at 10240             | 4.97

prose__code (expert trained: code) | joint 7.67
  prose  200/200 at 8192                     | 2.48
  code   200/200 at 10240 (its expert)        | 4.92
  math   200/200 at 10240 (served by code)   | 15.06
  ga     200/200 at 10240 (served by code)    | 19.94
  legal  53 at 8192, 147 at 10240             | 4.25

math__ga (expert trained: ga) | joint 26.95
  prose  200/200 at 8192                     | 2.48
  code   200/200 at 10240                    | 4.95
  math   200/200 at 12288                    | 1.46
  ga     200/200 at 16384 (its expert)        | 2.36
  legal  50 at 8192, 150 at 10240            | 4.27

prose__legal -- the (a)-anchor (expert trained: legal) | joint 16.32
  prose  200/200 at 8192                     | 2.48
  legal  191 at 14336, 8 at 12288, 1 at 10240| 2.21
  code   6/31/120/43 across 8192..14336       | 85.89
  math   6/84/59/51 across 8192..14336        | 39.37
  ga     56 at 8192, 115 at 10240, 29 at 12288| 25.52

ga__code (b), eval-only, oracle code at 10240 | joint 22.92
  prose  200/200 at 8192                     | 2.48   oracle nan
  code   200/200 at 10240                    | 4.95   oracle 4.95
  math   200/200 at 12288                    | 1.46   oracle nan
  legal  199 at 14336, 1 at 8192             | 2.29   oracle nan
  ga     200/200 at 16384                    | 2.34   oracle nan

Readings, separated from interpretation:

1. Trained expert present gives a tight diagonal and oracle-grade serving. ga claims its own
   16384 column 200/200 at ppl 2.36. legal claims its trained 14336 column at 2.21, within 0.08
   of the 2.29 its A-expert serves in the (b) cell.
2. No expert present: the domain scatters across neighbouring columns and serves 4-5x worse.
   code homeless 72.67/85.89 vs 4.92/4.95 with its expert; ga homeless 27.72/25.52 vs 2.34/2.36.
   Addressing failure and ppl failure arrive together, which is the dissociation this instrument is for.
3. The (b) equality leg: code served 4.95 equals oracle 4.95, delta 0.00 on the routed plane. This
   is the 4b reference plane (routed own-width), not the cold unrouted table -- the referent that
   decides whether the stop-rule is checked or falsely breached.
4. Measured, not smoothed: the anchor legal row leaks 9/200 crops below its trained column
   (8 at 12288, 1 at 10240). Small boundary leakage, same family as seed-2 known legal-crop leak;
   it does not move the ppl. Reported as landed, not rounded to the 200/200 the design predicted.

## 2 Storage integrity (c) -- all three grown cells

encoder_frozen, encoder_v_frozen, decoder_frozen, embed_weight_frozen, lm_head_frozen all
BIT_EXACT_OK against their init checkpoint; new columns present at grown width. failed_regions 0
in every case (prose__math verified during the run; the other two in the recovery, CPU-only,
CUDA hidden). Growth stores without corrupting what it must not touch.

## 3 Training readouts -- plumbing, no learning claim

math__ga: final val ppl 2.28, best val ppl 2.22. prose__legal: final val ppl 2.16, test ppl 2.19.
The final step lines for prose__math and prose__code were not captured in this session prints
and are not asserted; the checkpoints and the evals above stand on their own.

## 4 Honest ledger -- what went wrong before it went right (all mine)

1. The driver eval step silently failed: required --domains was never passed and rc was unchecked,
   so the (b) table was never produced and a 295-byte argparse usage stub sat under a
   .routdiag.txt name. Caught only by reading file contents instead of trusting filenames. The
   stub is kept for provenance (hash below), not deleted.
2. The driver announced prose__legal as the (a)-anchor but issued no grow command for it, and my
   first recovery runner inherited that omission -- the gap survived one repair cycle by my hand.
   The anchor was trained and measured separately (sondeB_anchor.sh).
3. The intended oracle code:160 is a multiplier, not a route; eval_router rejects widths absent
   from --routes, so the per-head 10240 was required. It would have errored even with domains set.
4. The card sat idle under an exclusive lease roughly 17-18 minutes while authoring tooling failed
   (two heredoc wedges, a brace closed with done, a bad token variable name).
5. The first two writes of this report by the document editor returned a render but landed outside the repo under the framework root, where the repo tooling would not have staged it; the report exists because shell wrote it at an absolute path, so
   a tool render is not evidence of an artifact.

## 5 Limits and next

Single seed per cell, 200 crops, ladder scale (100M deliberately out of scope). ga__code stays
eval-only: (c) cannot be closed on that pair because its back twin is narrower than its front, so
no growth boundary exists -- documented and ruled, not fixed away. The clean separation shown here
(where experts are trained, routing is exact and serving is oracle-equal; where absent, both
degrade together) points at one countermeasure worth pre-registering: a reject/abstain layer over
homeless domains. Not proposed as settled here.

Provenance hashes (md5, card host):
- eval_prose__math.routdiag.txt  158143b8b7a17cc8aafca8f2d21ce2c1
- eval_prose__code.routdiag.txt  925bf6b6f21643e15d80582f153de4a3
- eval_math__ga.routdiag.txt     aa0393e10f49bb3f512a9ca68144442f
- eval_ga__code_b_fixed.routdiag.txt a0b22e56bb72714146be51e188eff1dd
- eval_prose__legal.routdiag.txt b65ea90140526cf95105c2222cbc337b
- harv-ga__code_b.routdiag.txt (broken stub, kept) c0b35874c78d057aa65f224e29139399
- storage checker /tmp/sondeB_c_check.py be8db0cd1ca7c16f931d79c7a56a914b

Model transparency: A0-Quinn, saga profile, locally hosted Qwen3.8-Flash-Next. Two degenerate
repetition outputs occurred on this session chat surface; both were disclosed and discarded as
non-measurement, and outputs were kept short as a control on that failure mode.
