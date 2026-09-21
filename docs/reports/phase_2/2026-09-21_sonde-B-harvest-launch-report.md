# Sonde B -- harvest launch: grow mechanism proven on the card at bs=512

Status: launch-stage smoke verified on the real card. The full (a)/(b)/(c) harvest
run is NOT yet executed; it is gated on a separate operator GO. Author: @quinn-the-builder
(saga). Date: 2026-09-21.

## 0. Provenance

- Run-site: host alias bdh-4090 (192.168.178.200), user a0-quinn, tree
  /media/data/coding/bdh, interpreter .venv/bin/python (torch 2.13.0+cu130).
- Instrument under test: pipeline train path with --init-from, --grow-mult,
  --route-aware, --route-alpha, --block-size, --out-dir.
- Driver on the run-site: out_c/sondeB/harvest/sondeB_harvest.sh,
  md5 796616efac928f77faed02319b75ea8a, 68 lines, 3755 bytes,
  byte-identity against the local file reported VERIFIED_BYTE_IDENTICAL.
- Coordination bus: room bdh-cl; launch intent seq 378
  (client_msg_id quinn-sondeB-harvest-run-1, state working_on); exclusive claim
  scope_id s_bdh-cl_000065_f3590e, kind exclusive, units 1, ttl 30 min.
- Every number in this report is quoted from a tool printout this session, not
  from recall. Recall-only values, if any, are labelled and treated as claims.

## 1. Why this report exists

Two reports already sit in docs/reports/phase_2: the Sonde D hybrid-crop readout
(2026-09-20, commit f39627b) and the Sonde B mechanism smoke (2026-09-21, commit
0a4edaf, amended by the section 7 ruling commit 957515e). Neither documents the
step this session reached: exercising my own grow invocation on the physical card,
from a byte-verified driver, with outputs routed away from the read-only out/.
This is that launch-stage record.

## 2. What was gated before the card was touched

The card was not the first thing I used. Before any claim I closed, in order:

1. Reachability and authority. The 4090 was reachable; an initial probe that
   printed an OK on a failed connect was a self-caught bug (the exit code was
   read from an intervening echo, not from ssh). Fixed by capturing rc on its own
   line.
2. The trained widths, read from checkpoints, not assumed: base 128, code 160,
   math 192, legal 224, ga 256, every one at block_size 512. This closed the last
   precondition that had been held in memory as 'commonly 512'.
3. The frozen section 7 decision (read from the committed file): retain the three
   twin-growable pairs prose__math (+64), prose__code (+32), math__ga (+64);
   retain ga__code as the (b)-only cell (no code__ga flip); add prose__legal
   (served ppl 4.94) as the (a)-anchor; keep ladder-scale, no 100M pass.
4. The out-dir mechanism, read from pipeline/config.py: the save path is
   os.path.join(cfg.out_dir, stem_tag.pt) and out_dir defaults to 'out', so a
   --out-dir override is the real control for keeping writes out of the read-only
   out/.
5. Wiring before syntax: the launch driver was checked so that every function is
   defined before use and every required call is present exactly once, before any
   bash -n. Only then was the syntax gate run (bash -n rc=0).

## 3. The launch-stage smoke (the new result)

A single smallest cell was grown to prove, on the real card, that my flags work
end to end: init from the base(128) checkpoint, grow to 160, five iterations, with
--out-dir set to the out_c working dir.

Printed facts (quoted):

- dataset textmix; train 28,000,000 B | val 1,000,000 B | test 1,000,000 B
- route-aware: prefix mask 8192..10240 | loss = 0.9*prefix + 0.09999999999999998*full
- growth: 128 -> 160 mult (+2048 neurons/head trainable) | old neurons + embed +
  lm_head frozen (bit-exact via step-end restore)
- model: bdh | params 126,091,264 | device cuda | dtype torch.bfloat16
- step 5 | val_loss 4.1534 | ppl 63.65 | bpw 5.992 | test_loss 4.6163 | test_ppl 101.12
- done -> .../out_c/sondeB/harvest/bdh_textmix_smoke-harv-prose__code_best.pt
- smoke rc = 0

Readback: the produced checkpoints appear under the out_c working dir
(bdh_textmix_smoke-harv-prose__code_{best,last}.pt, 1511046998 bytes each). The
card was idle before the run (util 1 percent, mem 287 MiB, no competing train
process), and the init checkpoint was confirmed present (1211147753 bytes).

## 4. The out/ invariant, stated exactly (not overclaimed)

The control that keeps out/ free of my outputs is --out-dir: with it set, the save
path resolves under the out_c working dir, which is exactly what the readback shows.

I must be precise about a check that does not prove what it looks like it proves.
A grep for 'harv|smoke' under out/ returned two files:

- bdh-linear_shakespeare_smoke_best.pt
- bdh-linear_shakespeare_smoke_last.pt

These are NOT from this run. They are pre-existing, unrelated artifacts (a linear
model on shakespeare) that predate this session. So the honest statement is: my
grow smoke added nothing to out/, and its only outputs landed under the out_c
working dir. It is NOT true that out/ holds no smoke file at all, because those two
unrelated files are in it. The valid evidence that I did not touch out/ is the
--out-dir routing plus my run-name files appearing only under the working dir; a
blanket 'no smoke anywhere in out/' test would be false and is not the proof.

## 5. What this smoke does and does not establish

Establishes, on the real card:

- My grow flag spelling loads a bs=512 checkpoint via --init-from and grows it
  (+32 to 160 here) with the route-aware prefix mask and the frozen-neuron/step-end
  restore path.
- --out-dir routes the produced checkpoints away from out/.
- The byte-verified driver parses (bash -n rc=0) and runs (rc=0).

Does NOT establish:

- The scientific result. The (a)/(b)/(c) decision needs the full set of grown
  cells (prose__math, prose__code, math__ga) and the eval passes (ga__code (b)
  cell, prose__legal (a)-anchor, and the (c) storage check on grown slices by an
  epsilon-relative tolerance, not bit-equal). That is the full run, under a separate
  GO.
- Any population-level conclusion; ppl here (63.65 val, five iterations) is a
  plumbing readout only, and the smoke ppl are appendix-level, not evidence of
  learning.

## 6. Honest failure ledger for this launch attempt

Every red that appeared was mine to catch, and each is named so a reader trusts
the parts that are not red:

- OK-print-on-failed-connect: an early reachability probe reported success because
  the exit code was read from the wrong command. Fixed by capturing rc on its own
  line.
- False MD5_MATCH=NO: a filter looked for the token 'md5' inside the hash line
  (the hash is a leading hex field), so it matched nothing and printed the empty
  branch. Fixed by extracting the first whitespace field; both sides then showed
  the same hash 796616efac928f77faed02319b75ea8a.
- Two verifier scripts, one with a naive UTC-clock read and a bad file open mode,
  reported a bogus expiry and wrote an empty lease file; both were repaired, and
  the live scopes list on the board -- not the claim echo -- is the source of truth
  for the hold.
- One driver authoring used an invalid patch prefix and was corrected; the wiring
  readback after the fix showed both functions defined before use, the required
  call present once, and exactly one final marker.

## 7. Standing state and the gate that remains

- Read-only surfaces respected: out/ and the seed2 checkpoints under out_a were
  not modified by this run.
- The card was claimed exclusively for the launch. The release meant to run at the
  reporting seam did not execute, because of two verifier bugs of mine (a token
  variable name read wrong under the nounset option, then a whoami sent to a
  room-scoped path instead of the top-level route). It completed later in a verified
  follow-up at 07:39Z, proven by a board readback (DELETE 204, live scopes list
  empty, zero gpu rows). The claim was therefore held idle for about eighteen minutes
  past the smoke, a protocol blemish I own rather than hide. Re-claim is the first
  action when the full run is authorized.
- seed-3 remains off.
- Open: authorize and run the full (a)/(b)/(c) harvest set under a fresh claim and
  a bus intent, then evaluate the grown cells.

## 8. Reproduction

From /media/data/coding/bdh on bdh-4090, after a fresh claim and a posted intent:

- full set: bash out_c/sondeB/harvest/sondeB_harvest.sh (writes only under
  out_c/sondeB/harvest via --out-dir)
- per cell, mirror the smoke invocation with the cell's --init-from, --grow-mult,
  --text-mix and --out-dir, and the shared --model bdh --dataset textmix --n-embd
  512 --n-head 8 --block-size 512 --no-freeze-attn --route-aware --route-alpha 0.9
- eval cells use scripts/eval_router.py with --routes and --oracle-routes, writing
  their routdiag text under the same out_c working dir.

-- Quinn, 2026-09-21
