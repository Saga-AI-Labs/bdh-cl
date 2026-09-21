# Sonde B -- mechanism smoke: the pipeline can grow a bs=512 checkpoint at the true twin width

Date: 2026-09-21 | Seat: A0-Quinn | Runtime host: .200 (/media/data/coding/bdh)
Predecessor: Sonde D hybrid-crop readout (`docs/reports/2026-09-20_sonde-D-hybrid-crop-addressing-report.md`, commit f39627b)
Pre-registration: `docs/plans/2026-09-20_sonde-B-train-damage-pairs-prereg.md`
Status: mechanism question answered at the artefact. Harvest run (the (a)/(b)/(c) decision) is NOT run; one cell is blocked on an operator ruling (section 6).

---

## 1. What this report covers

Sonde D answered the addressing question read-only and ended on a gap: the hybrid oracle column reads `nan` because a never-trained domain has no trained prefix expert (readout, section 6b gap). Sonde B exists to remove that ceiling: train the damage pairs so each gains a real width, then grade surface-versus-content against an oracle.

Before any harvest, B faced the gate the A pre-reg established: freeze, functional check, and a smoke that proves the mechanism, all at the artefact, no earlier than a freeze and a bus intent before any card claim. This report documents that gate coming down green, plus one structural finding the frozen strategy itself could not absorb (section 6).

All artefact paths under `out_c/` are gitignored (`.gitignore` line 20). Their load-bearing content is transcribed in this report with the md5/rc/seq lines that carry them; nothing here asks the reader to trust a file they cannot see.

## 2. Twin widths measured at the checkpoints (not assumed)

The trained-width strategy is twin-matched: each cell grows toward the width its real-domain twin already holds. That strategy is only usable if those widths are measured, and they were -- per checkpoint, from the run-site, with the repo's own interpreter (`.venv/bin/python`, torch 2.13.0+cu130, measured on the .200):

| phase checkpoint | `mlp_internal_dim_multiplier` | `block_size` | `n_embd` | `n_head` | `route_alpha` |
| --- | --- | --- | --- | --- | --- |
| ...-base_last.pt | 128 | 512 | 512 | 8 | 0.9 |
| ...-code_last.pt | 160 | 512 | 512 | 8 | 0.9 |
| ...-math_last.pt | 192 | 512 | 512 | 8 | 0.9 |
| ...-legal_last.pt | 224 | 512 | 512 | 8 | 0.9 |
| ...-ga_last.pt | 256 | 512 | 512 | 8 | 0.9 |

(`...` = `out_a/bdh_textmix_ladA-A1-K5-seed2`.) The widths ascend by exactly +32 per phase -- the A ladder's own protocol value, read, not imported. The steps and alpha match the frozen cfg of the same files (`grow_mult 32`, `route_aware True`, `init_from` chaining confirmed by the cfg dump).

This measurement mattered beyond enabling the strategy: the pre-reg had at one point mis-cited probe_s's block as inheritable. The check showed probe_s is bound to its own 128 window (`block_size=128` hardcoded at `probe_s_semantic.py:193`; its `512` is a fact-count at :121, not a block size) -- so the block was overridden to 512 for the A base and pinned, not inherited. The correction stands as a visible layer in the pre-reg (its section 5), not a silent edit.

## 3. Run-site identity, pinned to the four files the run loads

The .200 checkout was reconciled against the container's git reads, through the documented access path (`a0-quinn@.200` with the container key; host `ai`, SSH_RC=0):

| file | md5 (.200 = container) |
| --- | --- |
| pipeline/config.py | 904b69549d953d72017126549ed2a2e1 |
| pipeline/train.py | 3ad7848ded61f35ee292bc24d5c728e4 |
| pipeline/data.py | c45ea50de77b44c7816e9636e782461e |
| pipeline/transformer.py | b1d3e18e6cc33534593b7dd1ddb8cfde |

`git status` lists none of the four as modified; run-site HEAD measured `e6bf359`. Scope stated tight: byte-identical for the four imported files is NOT a claim that the whole checkout equals the container copy. The freeze pins these four by md5 -- the run's true code surface.

An earlier attempt at this reconciliation ran inside the container while claiming to test the run site and printed MISSINGS; it was withdrawn as an address error (the fifth instance this session of guessing where to read instead of reading). The instrument was then moved into a script file executed via `ssh ... bash -s`, which removes the nested-quoting failure mode structurally rather than carefully.

## 4. Functional check: rc=0, three sections (the freeze gate)

Script: `out_c/sondeB/sondeB_functional_check.sh`; log: `out_c/sondeB/fc_b_out.txt`. It pins, it does not assert: the widths above came from `torch.load(..., map_location=cpu)` on each checkpoint's cfg.

1. **Width pinned from checkpoints** -- five widths read back (128/160/192/224/256), ladder consistency judged against the MEASURED base (+32 per phase, not a hard-coded truth), bs 512 and alpha 0.9 on all. PASS.
2. **eval_router byte-parity** -- copy at `out_c/sondeB/eval_router.py` md5-equal to the pristine `scripts/eval_router.py`, both `73832ecd08f24eded93a98a74572be6e`. PASS.
3. **Hybrid cell dry-formed on real bytes** (numpy, no forward, no card) -- the code__math cell: `crop_len 512`, `front==X[:128] True`, `tail==Y-slice True`. PASS.

Two honesty notes carried into the record. First, `N_full 16384` is recorded DERIVED, not measured: it is the product of two measured scalars, `chunk_size 64 x mlp_internal_dim_multiplier 256`; it is not a cfg key and was not copied from the A artefact as a fact. Second, the session's own prior check (`out_c/sondeB/functional_check.py`, the DataAdapter probe) was disqualified before trust: `DataAdapter` is defined nowhere in the repo, so that check can never import successfully and its PASS would prove nothing. The B check replaces it on purpose-built grounds.

## 5. Mechanism smoke: the question the freeze left open, answered

The functional check measured existing checkpoints; it never produced a grown one. Whether the pipeline accepts a `bs=512` grown of the A base via `init_from + grow_mult + route_aware` was the open half of section 5. The smoke answered it.

Protocol: `out_c/sondeB/smoke_sondeB.sh`, base `out_a/bdh_textmix_ladA-A1-K5-seed2-legal_last.pt` (width 224), `--grow-mult 2` (deliberately small; 32 was probe_s's own value for its own territories and was NOT inherited), `--block-size 512` explicit, route-aware with alpha 0.9, `--no-freeze-attn`, `TORCHDYNAMO_DISABLE=1` set per the host's JIT hazard, 8 iterations, batch 1, writes only under `out_c/sondeB/smoke`, `out/` and `out_a/` untouched, instrument pristine. The invocation mirrors the validated launcher form; the flags were verified against the real argparse surface (`pipeline.run train --help`) -- 18/18 present -- before the card was touched. An earlier draft of this script imported a `make_dataset` symbol that does not exist (`data.py` exports `load_dataset`) and used a non-existent `os.path.getmtime`; both were caught by reading the entrypoints first and removed before any claim.

Result, read back from the PRODUCED checkpoint (not asserted):

```
SMOKE_ACHIEVED_WIDTH 226   (224 + grow 2, as intended)
SMOKE_BS 512               (the block override held through a real grow run)
SMOKE_GROW_MULT 2
SMOKE_RC=0
```

Corroboration from the run's own log: `growth: 224 -> 226`; `route-aware: prefix mask 14336..14464` (= 64x224 to 64x226); `old neurons + embed + lm_head frozen (bit-exact via step-end restore)`; device cuda. The produced pair sits at `out_c/sondeB/smoke/bdh_textmix_sondeB-smoke_{best,last}.pt` (2,133,917,764 bytes each).

What the smoke does NOT say: the 8-iteration ppl (2.37 val / 2.26 test) is a smoke number with zero scientific weight. It proves plumbing: a legal checkpoint can be grown to a twin width at bs 512 while the old-neuron freeze path engages.

## 6. Card protocol: claim with work behind it, released verified

Intent #365 (2026-09-21T01:02Z) opened the item; #366 carried the freeze (03:13Z); #367 was the claim intent (03:21Z); claim `s_bdh-cl_000062_336732` (exclusive, TTL 30 min) was verified by reading the live scope list, not by trusting the 201. The smoke ran under the lease; release returned 204 and the live list came back empty; done #368 (03:28Z) closed the loop. The card was never held idle.

## 7. Open: one frozen pair cannot be twin-grown (operator ruling needed)

The frozen pairs were prose__math, prose__code, math__ga, ga__code. Resolving grow-mults from the measured widths:

| cell | front width | back width | needed delta | status |
| --- | --- | --- | --- | --- |
| prose__math | 128 | 192 | +64 | machine-ready |
| prose__code | 128 | 160 | +32 | machine-ready |
| math__ga | 192 | 256 | +64 | machine-ready |
| ga__code | 256 | 160 | -96 | **structurally impossible** |

For ga__code the back territory is narrower than the front one: a grow-mult cannot be negative, so twin-matched growth is not definable for that pair. This is a defect in the frozen strategy at that cell, found by arithmetic against measured values -- and it surfaced before any claim, which is the whole value of freezing first.

Analyst position (not applied): ga__code can still serve the (b) addressing question without any growth, because (b) needs an oracle expert only for the back territory, and code already has one at 160; what it cannot reach is the (c) storage question, which requires a real growth boundary. The alternative -- flipping the cell to code__ga (160 to 256, +96) -- answers a different question than the frozen one and is therefore an operator decision, not a silent edit. The three healthy pairs plus the prose__legal 4.94 anchor remain ready to run on the next GO.

## 8. Provenance

- This report is the committed surface for a run whose artefacts live under gitignored `out_c/` (`.gitignore:20`); the md5, rc, width, and scope-id lines above are their transcribed evidence.
- Freeze (not committed, by gitignore): `out_c/sondeB/freeze.json`.
- Functional check and log: `out_c/sondeB/sondeB_functional_check.sh`, `out_c/sondeB/fc_b_out.txt`.
- Smoke script and produced checkpoints: `out_c/sondeB/smoke_sondeB.sh`, `out_c/sondeB/smoke/bdh_textmix_sondeB-smoke_*.pt`.
- Bus trail: bdh-cl #365, #366, #367, #368; scope `s_bdh-cl_000062_336732` claimed and released.
- Read-site identity: four pipeline md5s above, run-site HEAD `e6bf359`.
- Deliberate exclusions from this commit: `scripts/eval_router.py` (modified from earlier work, stays out), `docs/data/*` (untracked data notes).
- Integrity note for the day: the earlier recap message that followed the Sonde D commit contained a degenerate repetition artifact from this session's local model deployment (operator-noted, discarded, no measurement value); outputs in this phase were deliberately kept short after two such events.
