# Host model training plan (2026-11-24)

**Status: PLAN, not a prereg. Nothing here authorizes a run.** The key-2 half of
G0 is frozen (`93ba5b5`, `docs/notes/2026-11-24_key2-g0-freeze.md`). The host
fields of G0 are not. The first run below starts only after the G0 completion
record in section 4 is signed.

- Objective served: a competent chat model on BDH-CL. This run is the base, not
  the chat model.
- Supersedes: the shape and data options in
  `docs/plans/2026-11-19_chat-host-planning-round.md` D2-D6, where this plan
  chooses among them. Those options remain the record.
- Does not supersede: the chat prereg (`2026-11-03_chat-model-prereg.md`), the
  graft-2 plan, or the frozen key-2 instrument.

## 1. Where this sits

```
key 2 frozen  ->  host pilot (this plan)  ->  graft phase
                          |
                    key 1 + key 2
```

What changed since the 2026-11-19 planning round:

| item | state |
|---|---|
| key 2 | frozen 2026-11-24; `F_d` 2/2/3, `M_d` 4.50/4.50/4.33; rubric v2 |
| 3.22B checkpoint | verdict recorded 2026-11-24: fails all three dimensions |
| 3.22B role | negative band and filter proof; **not** the host |
| FineWeb-Edu sample | already on disk: 3 shards, 1,637,101 rows, 4.85 GB parquet |
| purity evidence | 56.7 MB text probe, 200 crops, 0 anomalies; not yet the carve |
| key 1 | not built for this corpus; `0.8519` is the legal carve and does not transport |
| host train/val carve | not built |
| A/B/C thresholds | not numerically frozen |

Naming: the checkpoint holds 3.22B parameters; the repo's files for it use the
name `3.62b`. This plan says 3.22B and means the same checkpoint
(`out/routed_probe/bdh_textmix_p3_mixed_best.pt`).

The 3.22B verdict settled the instrument question on material that was already
abandoned. This plan is the run that can produce new information about a base
that is still in contention. That is the difference the operator asked for, and
it is the test any item below has to pass to be admitted.

## 2. What the run must answer

Two questions, one model, one pass:

| question | instrument | what counts |
|---|---|---|
| did the model absorb the corpus statistics a 6-gram extracts from the same bytes? | key 1: val NLL vs a train-carve 6-gram on identical positions | statistical adequacy |
| does it compose on 256 B free generations? | key 2: frozen v2 rubric, 133 prompts, two seats | coherence, relevance, language |

The key-2 measurement on this host is **non-circular**, unlike the 3.22B verdict:
its coherence and language bands are the 3.22B generations, a different model.
This is the first key-2 result that is not calibrated on the object it scores.

Not asked of this run: chat quality, instruction following, SFT, routing,
quantization, long-range coherence (256 B is local by registration), or a human
band. Each has a later owner in section 9 or 10.

## 3. Cost discipline

The steering rule for this leg: **a prerequisite is admitted only if it is
needed to score the run or to keep it comparable.** Everything else waits.

Admitted: the carve, the census, key 1, the loader, checkpoint resume, the
shape, the A/B/C numbers, the frozen scoring path.

Cut, with reasons:

| cut | reason |
|---|---|
| MinHash / near-duplicate removal | exact-duplicate share is measured; near-dup is a corpus-quality project, not a gate for this run |
| BPE | a tokenizer is an architecture decision, not a fix for a byte-level host; item 7 stays open |
| multi-epoch | repeats views; the starvation diagnosis is about unique bytes, and key 1 compares against a one-pass counter |
| 8 layers as the baseline | depth is D4, conditional on outcome B; 4 layers is the registered baseline |
| TP=2, QAT, TensorFold on the training path | section 9; each would make a failure unattributable |
| a fresh prompt set or a human key-2 band | key 2 is frozen; consuming either would start a new instrument |
| a second architecture arm in the same run | two variables, one verdict; not scoreable |

The side-track test: if an item cannot change which branch (A/B/C) the run
lands on, it is not in this leg.

## 4. The G0 completion record

One commit, before the run. Each row is a file or a number with a hash.

| # | field | artifact | cost |
|---|---|---|---|
| 1 | data manifest and carve rule | `data/host/carve_manifest.json` + three byte files | ~1 h |
| 2 | purity census on the carve | `data/host/census.json` | ~1 h |
| 3 | key-1 counter: 6-gram NLL, 4-gram, resolution shares | `out/host/key1_ngram.json` | ~1 h after the counter exists |
| 4 | key-1 margin | in the G0 note | free |
| 5 | key-1 model scorer | `scripts/quinn/key1_score.py` + a dry run on the 3.22B | ~half day |
| 6 | shape and sampling convention | in the G0 note | free |
| 7 | A/B/C numbers and budget cap | in the G0 note | free |
| 8 | resume and checkpoint policy | `pipeline/train.py` change + test | ~half day |
| 9 | item 8 schedule-or-defer | one line in the G0 note | free |

The G0 note is `docs/notes/2026-11-24_host-g0-completion.md`, separate from the
key-2 freeze so the key-2 record is not edited after signing.

Durability: `/data/*` and `/out/` are gitignored. The manifest, the census JSON,
the n-gram JSON, the builder and the G0 note are force-added in the G0 commit.
The 2 GB of carved bytes stay on disk and are identified by sha256; they are
rebuildable from the three parquet shards, whose hashes are in the manifest, by
the committed builder. That is the same rule as the key-2 freeze: commit the
record and the small artifacts, record the large bytes by hash.

## 5. Data

### 5.1 Corpus

FineWeb-Edu `sample-10BT`, already downloaded:

| shard | rows | parquet bytes | est. text bytes |
|---|---|---|---|
| `10BT/000_00000.parquet` | 726,000 | 2,152,819,114 | 3.56 GB |
| `10BT/001_00000.parquet` | 729,000 | 2,152,222,432 | 3.73 GB |
| `10BT/013_00000.parquet` | 182,101 | 540,632,672 | 0.85 GB |
| total | 1,637,101 | 4,845,674,218 | **8.14 GB** |

Text bytes are estimated from the first row group of each shard (4,910 B per
document average); the builder records the exact total. The 100BT and 350BT
shards in `out/fineweb_edu_probe/sample/` are comparison probes and are excluded
from the host corpus.

No extra quality filter. The sample is already the top-scored educational
subset; a `language_score` cut would be a new filter chosen without an
instrument. Record the score distribution instead.

### 5.2 Carve rule

Document-level, hash-based, built once:

- unit: one parquet row = one document; separator `\n\n`; no document split.
- `h = first 8 bytes of sha256(id)` as an integer.
- `h % 1000` in `[0, 5)` -> val; `[5, 10)` -> test; otherwise train.
- val cap 8 MB, test cap 8 MB, train cap 2,000 MB; the cap is applied at a
  document boundary, so the train file is at most 2,000 MB and may be a few
  bytes short.
- order: ascending `h`, so each split is a uniform sample of the corpus rather
  than the first shard prefix. The order and the first and last document ids are
  part of the manifest.

Why document-level and hashed: a tail split leaks the corpus register into the
val carve and flatters the 6-gram. The legal `0.8519` came from a 28/1/1 MB tail
split with 96 % order-6 resolution, which is the same-corpus caveat written into
section 18. A hashed document split does not remove register similarity, but it
removes the trivial leak of adjacent text.

Why 8 MB val: key 1 reads 128 fixed 512 B offsets (65,536 targets); 8 MB leaves
16,384 candidate blocks and room for the 50-byte memorisation check without
reusing the key-2 prompts.

### 5.3 Census

Run the existing census on each carved file, for example:

```
.venv/bin/python scripts/corpus_purity_census.py \
  data/host/fineweb_train.txt --scan --json data/host/census_train.json
```

Run it on the carve, not on the 56.7 MB probe. Required outputs:

| measure | gate |
|---|---|
| dominant script per crop (200 crops) | Latin on every crop |
| cross-script purity, p05 | >= 0.99 |
| anomalous crops | 0 |
| ASCII byte share | recorded; probe was 0.993 |
| language marker rates (en, de) | recorded; probe was 209.2 / 0.24 per 1k |
| exact-duplicate documents by id and by content hash | recorded; no gate |
| non-ASCII document share | recorded |
| license and attribution from the dataset card | recorded in the manifest |

A non-zero anomalous-crop count blocks the run until the cause is named. A
duplicate share above 5 % is recorded as a finding, not a block.

### 5.4 Loader

Add `--dataset files` with `--train-file`, `--val-file`, `--test-file`. Do not
reuse `textmix`: `_prepare_textmix` reads `mb * 1e6` bytes and then takes the
val and test from the tail of that read, which would overlap the train bytes we
just carved. The new path is a direct read of three files and nothing else.

Acceptance: the three files hash to the manifest; no document id appears in two
splits; `load_dataset` reports the exact byte counts.

## 6. Key 1: the statistical floor

### 6.1 Definition

Key 1 is the model's mean NLL on 128 evenly spaced 512 B offsets of the val
carve, compared with a 6-gram counted on the train carve and evaluated on the
same targets. Same positions, same bytes, one pass each. Lower is better.

This repeats the section 18 instrument so the numbers are comparable to the
3.22B result. The 4-gram is reported as a sensitivity check, not as the gate.

### 6.2 Counter

A full order-6 table over 2 GB is tens of GB and slow. Use a target-restricted
exact counter instead:

1. derive the 6-gram, 4-gram and unigram contexts that occur at the val targets;
2. one chunked pass over the train bytes, counting only pairs whose context is
   in that set;
3. NLL with seen-context backoff 6 -> 4 -> 0, as in section 18.

This is exact for the val positions and needs memory proportional to the val
target count, not the train size.

Acceptance before it is trusted: reproduce the legal `0.8519` (order 6, same
128 x 512 offsets, 28/1/1 MB carve) to within 1e-4. A counter that cannot
reproduce the registered number is not the same instrument.

### 6.3 Margin

`key1_pass` iff `model_nll <= ngram6_nll - 0.10` nats/byte and the resolution
precondition in 6.4 holds.

Rationale: the standard error on 65,536 targets is about 0.008 nats, so 0.10 is
roughly twelve standard errors; it is 38 % of the 3.22B model's +0.2635 deficit.
Both the raw counter NLL and the margin are frozen. Sensitivity at 0.05 and 0.20
is reported but cannot replace the frozen value.

The rule is a lower bound, not a target. A host that beats the counter by 0.4
satisfies it; the record reports the measured delta.

### 6.4 Resolution precondition

Report the share of val targets that resolve at order 6, order 4 and order 0
(the legal values were 96.0 / 2.6 / 1.5 %). If order-6 resolution is below 80 %,
the counter is declared weak: key 1 is recorded as `not established`, which is
not a pass and cannot contribute to outcome A. The resolved-subset comparison is
then reported alongside, with the same margin.

### 6.5 Model scorer

`scripts/quinn/key1_score.py --ckpt ... --train ... --val ... --ngram ...
--out ...` emits:

- mean NLL, head (0-63) / context (64-511) / tail (256-511) splits;
- word-start and word-interior NLL;
- the per-position curve on the same 128 offsets;
- delta against the counter, win share, bootstrap 95 % CI;
- checkpoint sha256, git sha, and the exact command.

A dry run on the 3.22B checkpoint must reproduce the registered `1.1155` at
mult 1024 on the legal carve (section 18.1) before the script is used on the
host. That is the second end-to-end check on the instrument.

### 6.6 What key 1 does not prove

Beating a 6-gram is statistical adequacy on one carve, not coherence. The 3.22B
counterexample is the registration: a model can be far below the counter and
still be salad, and a model can beat it and still fail key 2. Key 1 is necessary,
not sufficient, exactly as the prereg says.

## 7. Shape, sampling, schedule

### 7.1 Shape

| parameter | value | reason |
|---|---|---|
| parameters | 100,925,440 | registered baseline; measured in `bench_100m.log` |
| `n_embd` / `n_head` / `mult` | 512 / 8 / 128 | same |
| layers | 4 | cheapest baseline; depth is D4, not a default |
| block | 512 | registered; 256 B generation fits with margin |
| batch | 8 | measured b8/t512 |
| dtype / compile | bf16 autocast / on | measured 2.1x at 6 layers |

Measured throughput, all b8/t512, 100M:

| shape | ms/step | B/s | 2 GB wall clock |
|---|---|---|---|
| 6 layers, uncompiled | 2,182 | 1,877 | 12.3 d |
| 4 layers, uncompiled | 1,475 | 2,777 | 8.3 d |
| 6 layers, compiled | 1,031 | 3,973 | 5.8 d |
| 4 layers, compiled (est.) | ~696 | ~5,900 | **~3.9 d** |

The 4-layer compiled row is an extrapolation of the measured 6-layer compile
factor (2.12x). The smoke test in 7.8 replaces it with a measured number before
the long run starts.

### 7.2 Data volume

2,000 MB, one pass, 488,281 steps of 4,096 B. This is the registered 100M/2 GB
shape, at 20 bytes per parameter.

Why not 4 GB now: the first arm should be the cheapest that can land on a
branch. If key 1 fails, 4 GB is the pre-registered C1 arm (section 8.4). If it
passes, the extra 4 days bought nothing. Choosing 4 GB to avoid the possibility
of C is a legitimate G0 decision, but it must be taken before the run, not after
key 1 is seen.

### 7.3 Sampling

**Shuffled single pass**: a seeded permutation of the non-overlapping 512 B
crops, consumed once. The permutation and its seed are part of the run record,
so the exposure can be reconstructed exactly. One epoch, no repeats.

Why not the default random crops: at 488,281 steps the random path draws 2 GB of
views but covers about 63 % of the crop positions. Key 1 is evaluated on unique
val text, so a 63 % coverage handicap would be attributed to the model when it
is an artefact of sampling. The counter reads each train byte once; the model
should too. That is the fair comparison, and it makes the exposure auditable.

Fallback: if the smoke test exposes a problem in the ordering path, use random
crops and register the ~63 % unique coverage in the G0 note. That choice is made
at G0, not after the result.

### 7.4 Resume

A 4-day single run needs resume. Add `--resume` to `pipeline/train.py`:

- restore model, optimizer, step, best val, and the crop cursor;
- restore the RNG state used for the permutation;
- refuse to resume if the data hash or the config hash differs;
- on a fresh run, `--resume` with no checkpoint is a no-op.

Acceptance: stop at step 20,000, resume, and match the uninterrupted val loss to
within 1e-3 with no step gap. Bit-identical is not required across a process
restart; step continuity and loss continuity are.

### 7.5 Schedule and hyperparameters

| parameter | value |
|---|---|
| peak LR | 1e-3 |
| min LR | 1e-4 |
| warmup | 2,000 steps |
| decay | cosine to `max_iters` |
| weight decay | 0.1 |
| grad clip | 1.0 |
| seed | 1337 |

The LR values are the pipeline defaults used by the prior 100M runs; the warmup
and decay horizon are scaled to this run's length. No LR sweep: a sweep is a
side track, and the smoke test will catch a divergence.

### 7.6 Checkpoints and evaluation

- `last`: every 5,000 steps, overwritten (about 1.2 GB with Adam state).
- `best`: on val improvement, kept for diagnosis only.
- milestone: every 50,000 steps, kept (9 files, ~11 GB).
- eval: every 5,000 steps, 100 batches (410 KB), for the loss curve.
- key 1: at 25 %, 50 %, 75 % and end, on the fixed positions, for the curve.
- a manifest with sha256 for every kept checkpoint.

**The verdict is scored on `last`, not `best`.** The schedule is fixed, so the
final checkpoint is the registered object; using `best` would let the val carve
select the checkpoint and then score key 1 on the same carve. `best` is retained
to diagnose a run that diverges, and its val number is reported, but it is not
the scored model.

### 7.7 The run

```
.venv/bin/python -m pipeline.run train \
  --model bdh --dataset files \
  --train-file data/host/fineweb_train.txt \
  --val-file data/host/fineweb_val.txt \
  --test-file data/host/fineweb_test.txt \
  --n-embd 512 --n-head 8 --n-layer 4 --mlp-internal-dim-multiplier 128 \
  --block-size 512 --batch-size 8 \
  --max-iters 488281 --warmup-iters 2000 --lr-decay-iters 488281 \
  --eval-interval 5000 --eval-iters 100 --log-interval 200 \
  --data-order shuffled-onepass --data-seed 1337 --resume \
  --compile --device cuda --dtype auto \
  --out-dir out/host --run-name host100m-e1
```

### 7.8 Smoke test

2,000 steps on the real data and shape, about 25 minutes at 4L compiled. Checks:
loss falls, the byte rate matches the table, the checkpoint saves and resumes,
the crop cursor advances, no OOM, and the peak is recorded. It is not a result
and is not scored.

## 8. Gate arithmetic, outcomes, stop rules

### 8.1 Key 2

Frozen: per dimension, `mean_d >= M_d` and `min_d >= F_d` over the 100 gate
items; the 33 argue items are reported separately and not gated. Coherence has
one seat (registered deviation). The commands are the frozen ones:

```
.venv/bin/python scripts/quinn/key2_generate.py \
  --checkpoint out/host/bdh_files_host100m-e1_last.pt \
  --prompts data/evals/key2_prompts_v1.json \
  --out out/host/host100m_key2_gen.jsonl \
  --meta-out out/host/host100m_key2_gen.meta.json --hash-checkpoint

.venv/bin/python scripts/quinn/key2_judge.py \
  --base-url http://192.168.178.51:8888/v1 --model Qwen3.8-Flash-Next \
  --input out/host/host100m_key2_gen.jsonl \
  --out out/host/host100m_qwen.json --log out/host/host100m_qwen.log

.venv/bin/python scripts/quinn/key2_judge.py \
  --base-url http://192.168.178.200:1234/v1 --model gemma-4-31b-it \
  --input out/host/host100m_key2_gen.jsonl \
  --out out/host/host100m_gemma.json --log out/host/host100m_gemma.log

.venv/bin/python scripts/quinn/key2_verdict.py \
  --verdict out/host/host100m_qwen.json \
  --verdict out/host/host100m_gemma.json \
  --out out/host/host100m_verdict.json
```

No `--compare` argument: the comparison is against the calibration bands, and a
host pass is not a replication check. The ordering row `positive > host > 3.22B`
is recorded from this pass; it is currently "not run" in the key-2 freeze.

### 8.2 Key 1

As section 6: `model_nll <= ngram6_nll - 0.10` with order-6 resolution >= 80 %.

### 8.3 Outcomes

| key 1 | key 2 | record | next |
|---|---|---|---|
| pass | pass | pass | G4: graft phase on this host |
| pass | fail | fail (salad) | coverage diagnosis first; D4 only if the diagnosis names composition, not bytes |
| fail | pass | fail (gate) | off-anchor: diagnose prompt OOD and carve representativeness; no depth arm |
| fail | fail | fail | coverage/data route (C arms) |

D4, if it fires, is 8 layers at the same 100M parameters: about 7.8 d compiled
at 2 GB, versus 3.9 d for 4 layers. It is not run by default.

### 8.4 Outcome C arms, pre-registered

If key 1 fails, the next lever is unique bytes, not depth:

| arm | shape | views | est. wall clock | stop rule |
|---|---|---|---|---|
| C1 | 100M, 4L | 4 GB | ~7.9 d compiled | key 1 at 50 % and end |
| C2 | 50M, 4L | 4 GB | ~4 d est. | key 1 only |

Order fixed: C1 then C2. Key 2 is run on a C arm only if key 1 passes. C1 fits
the cap in 8.5. C2 does not, so it is not authorized here: it runs only after a
new decision, and then only if C1 shows the direction is right.

### 8.5 Budget and kill rules

- cap for this leg: 14 GPU-days, including the smoke, the host arm and one
  follow-up arm (D4 or C1), but not scoring. Host 3.9 + C1 7.9 = 11.8 fits;
  a second follow-up arm (C2) would exceed the cap and needs a new decision;
- key-2 scoring: about 3 h per pass for both seats;
- kill a run early if val loss is flat for 50,000 steps **and** the key-1 delta
  is still worse than +0.20 (the model more than 0.20 nats above the counter,
  with no trend);
- a run is only a run if the command, git sha, data hashes and checkpoint hashes
  are in its record. Otherwise it is a probe.

## 9. The three changes and their timing

| change | trigger | now | this plan |
|---|---|---|---|
| TensorFold | operator authorization; exactness contract | **authorized 2026-11-24** | serving-side; build during the run, gate after it |
| QAT | FP32 plateau: after graft #2, serving gate and the third-domain run (QAT v2 section 8) | not fired | the host checkpoint is the FP32 reference |
| TP=2 | a coherent host that does not fit one box (D8) | not fired | the first host stays on one device |

**TensorFold.** The operator authorized it on the exactness contract: an
accepted draft must equal the same engine's plain token. That is a serving
property. It does not touch weights or training, and it cannot change the key-2
scores, which are text judgments.

Scope as this plan reads the authorization: install, integrate the BDH family
operator, verify exactness, benchmark. No weight change and no training-loop
change. A wider scope is a new decision.

Timing: build the integration during the host run, in a separate environment,
with no GPU workload while training is active. The exactness gate needs the host
checkpoint, so it runs after the run and before G4: all 133 prompts must decode
bit-identically to the plain path, and the checkpoint bytes must be unchanged.
If the gate fails, serving stays on the plain path and the failure is recorded;
the host verdict is unaffected.

**QAT.** Not now. The host leg is the FP32 reference any later QAT delta is
measured against. Introducing quantization during the host run would make a
key-2 failure ambiguous between starvation and quantization, which is the one
attribution this run exists to make.

**TP=2.** Not now. The host fits one box at 23.1 GiB uncompiled or 16.6 GiB
compiled (both measured), and the first host must stay comparable to the
single-device series. TP=2 fires only if a coherent host does not fit, and then
the bridge study is the entry condition.

## 10. Item 8 (SFT ordering)

**Defer, with a named trigger.** The claim is that SFT presupposes fluency. It
is testable at 100M for about 1 h (~2k steps on 2-5k synthetic pairs), but only
after a host passes key 2. Before that, the test cannot separate "SFT does not
create fluency" from "this host has none". Trigger: the first host that clears
G3. Record the deferral in the G0 note so it is a decision, not an omission.

## 11. What this plan does not cover

- Chat or instruction behaviour, SFT, and the 4.4b composition metric.
- Routes, specialists, or the graft itself; those start at G4 and have their own
  prereg.
- BPE, near-duplicate removal, multi-epoch training, or a data-mixture sweep.
- Long-range coherence; key 2 is local by registration.
- A human key-2 band; the freeze records the GPT calibration read in its place.
- Any 3.22B-scale training; that route is excluded by arithmetic.

## 12. Decisions requested

1. **Data budget**: 2,000 MB train, 8 MB val, 8 MB test, document-hash carve.
   Recommended. The 4 GB alternative must be chosen now, not after key 1.
2. **Shape**: 100M, 4 layers, block 512, batch 8, compiled, 488,281 steps.
   Recommended.
3. **Sampling**: shuffled single pass. Recommended; random crops with a
   registered 63 % unique coverage is the fallback.
4. **Key-1 margin**: 0.10 nats/byte with the 80 % resolution precondition.
   Recommended.
5. **Budget cap**: 14 GPU-days, one follow-up arm, D4 only on a diagnosis.
   Recommended.
6. **Item 8**: defer to the first G3 pass. Recommended.
7. **TensorFold**: build the serving integration during the run, with no GPU
   workload while training is active; gate on bit-exact decoding and unchanged
   checkpoint bytes after the run. Recommended.

## 13. First actions, in order

1. Build the carve and the manifest (~1 h).
2. Census and exact-duplicate count on the carve (~1 h).
3. Add `--dataset files`, `--data-order shuffled-onepass` and `--resume`; run
   the 2,000-step smoke (~half day).
4. Build the target-restricted counter; reproduce legal `0.8519`; score the
   3.22B to reproduce `1.1155` (~half day).
5. Write and sign the G0 completion record with every hash (~1 h).
6. Run the host (~3.9 d, measured at smoke).
7. Score key 1, generate and score key 2, write the verdict record (~4 h).
8. Name the branch and request the next plan (graft or C arm).

Step 6 does not start until step 5 is signed. If the smoke test contradicts the
4-layer compiled estimate, the wall clock in this plan is replaced by the
measured one before step 6, and only the cost table changes.
