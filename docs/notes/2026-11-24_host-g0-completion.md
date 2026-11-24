# Host G0 completion record (2026-11-24)

**Status: READY FOR SIGNATURE - no host training run has started.**

This record freezes the host fields of G0 from
`docs/plans/2026-11-24_host-training-plan.md` section 4. The key-2 half of G0 is
already frozen (`93ba5b5`, `docs/notes/2026-11-24_key2-g0-freeze.md`); this note
is separate so that record is not edited after signing.

Object: a 100M BDH trained from scratch on English FineWeb-Edu, one Spark, one
pass over 2 GB of views. It is the base the graft phase grows, not the chat
model. The run is the first non-circular key-2 measurement, because its
coherence and language bands are 3.22B generations, not its own.

## 1. Frozen fields

| # | field | value | evidence |
|---|---|---|---|
| 1 | corpus | FineWeb-Edu sample-10BT, 3 shards, 1,637,101 docs | 2.1 |
| 2 | exact duplicates | 9,890 docs / 44,790,135 B (0.573 % of bytes) | 2.2 |
| 3 | carve | document hash, decimal-MB caps, global dedupe first | 2.3 |
| 4 | splits | train 417,864 docs / 1,999,999,882 B; val 1,544 / 7,999,959 B; test 1,653 / 7,999,852 B | 2.4 |
| 5 | purity | Latin 100 %, 0 anomalous crops, ASCII 0.994 | 2.5 |
| 6 | key-1 counter | 1.187674 nats/byte, SE 0.005462, order-6 resolution 98.26 % | 3.3 |
| 7 | key-1 threshold | `model_nll <= 1.087674` (1.5692 bpw) | 3.4 |
| 8 | shape | 100M (512/8/128), 4 layers, block 512, batch 8, compiled | 5.1 |
| 9 | exposure | 488,281 steps, one pass, 2.0e9 B decimal, seed 1337 | 5.2 |
| 10 | measured rate | 799 ms/step, 5,126 B/s, 13.31 GiB peak | 5.3 |
| 11 | wall clock | 488,281 x 0.799 s = 390,137 s = **4.52 d** | 5.3 |
| 12 | branch rule | A/B/C table and 14 GPU-day ceiling | 6 |

## 2. Data

### 2.1 Source

| shard | rows | bytes | sha256 |
|---|---|---|---|
| `out/fineweb_edu_probe/sample/10BT/000_00000.parquet` | 726,000 | 2,152,819,114 | `b1ba7b2ce4cb5ea6` |
| `out/fineweb_edu_probe/sample/10BT/001_00000.parquet` | 729,000 | 2,152,222,432 | `3fcf2dc69cd52503` |
| `out/fineweb_edu_probe/sample/10BT/013_00000.parquet` | 182,101 | 540,632,672 | `b393f51fefab26cd` |

Full hashes are in `data/host/carve_manifest.json`. Total scanned: 1,637,101
documents, 7,816,161,610 text bytes (no separators). The 100BT and 350BT shards
in the same directory are comparison probes and are excluded.

### 2.2 Exact duplicates, before the carve

| measure | value |
|---|---|
| documents total / distinct | 1,637,101 / 1,627,211 |
| bytes total / distinct | 7,816,161,610 / 7,771,371,475 |
| duplicate documents | 9,890 (0.6041 %) |
| duplicate bytes | 44,790,135 (0.5730 %) |
| largest duplicate group | 3 |
| distinct bytes | 7.771 GB |

Method: sha256 of the UTF-8 text; the first occurrence in ascending document
hash wins; later occurrences are dropped globally before the split. This also
removes the class of leak where the same text would land in two splits under
different ids. The 7.771 GB distinct is above both the 2 GB host budget and the
4 GB C1 budget, so neither is a silent shrink.

### 2.3 Carve rule

- one distinct document, UTF-8 bytes, joined with `\n\n`; no document split;
- `h = big-endian integer of sha256(id)[:8]`;
- `h % 1000` in `[0,5)` -> val, `[5,10)` -> test, else train;
- caps are decimal MB: train 2,000,000,000 B, val 8,000,000 B, test 8,000,000 B.
  A MiB reading would give 512,000 steps and 5 % more wall clock;
- cap applied at a document boundary, after the separator is counted;
- order: ascending `h`, so each split is a uniform sample rather than the first
  shard prefix.

### 2.4 Splits

| split | documents | bytes | sha256 | first h | last h |
|---|---|---|---|---|---|
| train | 417,864 | 1,999,999,882 | `4692331783fb84d5` | 1,342,108,514,259 | 4,765,927,711,537,306,943 |
| val | 1,544 | 7,999,959 | `bf4600f0ab4c6b9c` | 350,842,643,331,003 | 3,431,892,823,386,003,002 |
| test | 1,653 | 7,999,852 | `43f67e138abc50ea` | 82,621,667,357,009 | 3,693,520,647,914,702,008 |

Full hashes in the manifest. One pass = floor(3,906,249 crops / 8) =
**488,281 steps** of 4,096 B.

### 2.5 Purity census

`scripts/corpus_purity_census.py --mb 2000 --full --scan --crops 200` on the
train carve, and the same on val:

| split | dominant script | purity p05/p50 | anomalous | ASCII | EN/1k | DE/1k |
|---|---|---|---|---|---|---|
| train | Latin | 1.000 / 1.000 | 0 | 0.994 | 201.01 | 0.24 |
| val | Latin | 1.000 / 1.000 | 0 | 0.990 | 197.73 | 0.00 |

No extra quality filter: the sample is already the top-scored educational
subset, and a `language_score` cut would be a new filter without an instrument.

### 2.6 Durability

`/data/*` and `/out/` are gitignored. The byte files stay on disk and are
identified by sha256. The manifest, census, duplicate report, key-1 JSONs,
builder and this note are force-added in the G0 commit. Rebuild:

```
.venv/bin/python scripts/quinn/build_host_corpus.py --stage all
```

from the three parquet shards, whose hashes are in the manifest. The rebuild
reproduces the split hashes above (verified twice, including after the
separator-cap fix).

## 3. Key 1

### 3.1 Instrument

128 evenly spaced 512 B offsets on the val carve, 65,536 targets. A byte 6-gram
is counted on the train carve with seen-context backoff 6 -> 4 -> 0 (uniform
1/256), evaluated on the same positions. The model is scored on the same
positions with `collect_state=False`, fp32 weights, no mask. Lower is better.
This is the report section 18 instrument, restricted to the contexts the val
targets need (a full 2 GB order-6 table is tens of GB).

### 3.2 Counter acceptance on the registered legal carve

| quantity | registered (2026-11-18) | measured |
|---|---|---|
| mean NLL | 0.8519 | **0.851943** |
| head 0-63 | 0.8722 | 0.8723 |
| context 64-511 | 0.8490 | 0.8490 |
| tail 256-511 | 0.8392 | 0.8392 |
| resolution 6/4/0 | 96.0 / 2.6 / 1.5 % | 96.0 / 2.6 / 1.45 % |

The target-restricted counter reproduces the legal number to 4 decimals, so the
integer-counting path is the registered instrument.

### 3.3 Host counter

| quantity | value |
|---|---|
| mean NLL | **1.187674** nats/byte (1.7136 bpw) |
| bootstrap SE (512 positions) | 0.005462 |
| order-6 resolution | 98.2573 % |
| order-4 resolution | 1.5397 % |
| order-0 fallback | 0.2030 % |
| val targets | 65,531 |

The 80 % resolution precondition passes with margin. The 0.10 nats/byte margin
is ~18 standard errors on this carve, so the test is not noise-limited.

### 3.4 Threshold and margin

`key1_pass` iff `model_nll <= 1.187674 - 0.10 = 1.087674` nats/byte (1.5692 bpw)
and order-6 resolution >= 80 %.

The margin is fixed at 0.10 (operator decision 2026-11-24). Its origin is the
3.22B effect size (38 % of its +0.2635 deficit), not a transfer from the legal
carve. Sensitivity at 0.05 and 0.20 is reported but cannot substitute.

### 3.5 3.22B cross-check: named stack-drift finding

The plan asked the model scorer to reproduce the registered `1.1155` at mult
1024 on the legal carve. It does not, and the reason is the stack, not the
scorer:

| path | mean NLL | head | context | tail |
|---|---|---|---|---|
| registered 2026-11-18 | 1.1155 | 1.2750 | 1.0927 | 1.0932 |
| `diag_context.py positions` today | **1.1286** | 1.2912 | 1.1054 | 1.1057 |
| `key1_score.py` today | **1.1286** | 1.2912 | 1.1054 | 1.1057 |

The two independent scripts agree to four decimals, and the checkpoint identity
is confirmed by its own metadata (step 7600, best_val 1.0333116, matching the
report). The delta is +0.0131 nats/byte (1.2 %), a constant offset across head,
context and tail. The venv was rebuilt on 2026-11-23 (torch 2.14.1+cu130,
`docs/notes/2026-11-23_env-rebuild-53.md`), after the report was written; the
2026-11-18 number came from the previous stack. TF32 is off in the current run
(`allow_tf32=False`, matmul precision `highest`); the old stack's setting is not
recorded. The record therefore attributes the delta to a stack-level difference,
not to a scorer bug: two independent scripts agree today, and the object is the
same checkpoint.

Word-class check: the corrected per-target path returns 2.574908 / 0.839607 /
0.890344 (start / interior / other), matching the reference's 2.5749 / 0.8396 /
0.8903. The first dry-run JSON used a tiled per-position approximation in those
three fields only; the mean and profile were unchanged. The clean JSON is
`out/host/key1_322b_legal.json`.

Disposition: no bit-identical reproduction across stacks is claimed. The
scorer is checked against the reference path on the legal carve: both return
1.1286 with the same head, context and tail (3.5). The key-1 gate does not use
1.1155: its threshold comes from integer counting (3.2 reproduces exactly), and
the host is scored on the current stack with the same scorer that returns
1.1286.

### 3.6 What key 1 does not prove

Beating a 6-gram is statistical adequacy on one carve, not coherence. The 3.22B
model is the counterexample: it is above the counter and fails key 2. Key 1 is
necessary, not sufficient.

## 4. Prompt contamination (rubric 8.7)

Rule: the last eight words of each frozen prompt (the whole prompt if shorter),
as an exact byte phrase, searched in the 2 GB train carve.

**One hit of 133:** `k2_explain_49`, "Explain why we see lightning before we
hear thunder." (gate item). The phrase occurs at offset 1,825,488,065, inside an
article sentence: "This is why we see lightning before we hear thunder."

Disposition: the prompt set is frozen and is not edited. The verdict record will
report the gate with and without `k2_explain_49` as a sensitivity, never as a
substitution for the frozen 100. The item's own score is reported. Output
memorisation (50-byte verbatim overlap) is checked after the run.

## 5. Shape, sampling, schedule

### 5.1 Shape

| parameter | value |
|---|---|
| parameters | 100,925,440 |
| `n_embd` / `n_head` / `mult` | 512 / 8 / 128 |
| layers | 4 |
| block / batch | 512 / 8 |
| dtype / compile | bf16 autocast / on |

### 5.2 Sampling and exposure

Seeded permutation of 3,906,249 non-overlapping 512 B crops, consumed once
(`--data-order shuffled-onepass --data-seed 1337`). 488,281 steps, 2.0e9 B, one
pass. Random crops were rejected: at this step count they cover ~63 % of unique
positions, which would handicap key 1 for a sampling reason. The permutation
and cursor are in every checkpoint.

### 5.3 Measured throughput

Smoke A: 600 steps at the real shape, compiled. Steady state 799 ms/step
(steps 200-500: 799, 799, 799, 799), 5,126 B/s, peak allocated 13.31 GiB.
488,281 x 0.799 s = 390,137 s = **4.52 d**. The earlier 3.9 d figure was an
extrapolation from a different stack; this is the measured number.

At step 600 the smoke's val NLL was 1.4993 (bpw 2.163), above the 1.087674
threshold. The smoke is 0.12 % of the run and is not a forecast; it measures the
rate, the memory envelope and the resume path, not the endpoint.

Compile required Python development headers, which this box lacks and cannot
install system-wide (no sudo). They are extracted from
`libpython3.12-dev 3.12.3-1ubuntu0.17` (sha256
`945ad3f651f683c11e72d19d804b1cff097308dcffa01057635cba038f875164`) into
`~/.local/share/bdh/py312-headers`, and `scripts/quinn/launch_host.sh` puts them
on `CPATH`. The model, data and numerics are untouched.

### 5.4 Resume

`--resume` restores model, optimizer, step, best val, crop cursor, CPU/CUDA RNG
state and refuses on a data-hash or config-fingerprint mismatch. `last` is
written every 5,000 steps, `best` is diagnostic only, milestones every 50,000.
The verdict is scored on `last`, not `best`.

Test: smoke B ran 600 steps, was sent SIGTERM after the step-500 checkpoint
(exit 143), and was resumed with the same command. It restored step 500, crop
cursor 4,000 and the RNG state, then ran 500 -> 600. Final val 1.4994 against
smoke A's uninterrupted 1.4993: a difference of 0.0001, below the 1e-3
acceptance. The two runs already differed by 0.0011 at step 500 (bf16
cross-process nondeterminism), so the resume added no measurable divergence.

The test exposed one defect, now fixed: `last` was written before the
`best_val` update, so a resume saw `best_val=inf` and would have re-promoted
the next evaluation to `best`. The order is now best_val update -> `last` ->
`best`/milestone. It does not change the training trajectory.

### 5.5 Run command

```
setsid nohup scripts/quinn/launch_host.sh > out/host/host100m-e1.log 2>&1 &
```

The launcher carries the full command in one process; no judge, lease or timer
is involved (plan sections 8.5 and 14).

## 6. Gates, outcomes, budget

### 6.1 Key 2

Frozen v2 rule: per dimension, `mean_d >= M_d` and `min_d >= F_d` over the 100
gate items; 33 argue items reported separately. Coherence has one seat
(registered deviation). The host generation is the frozen 133-prompt set at
256 B greedy; the two seats are Qwen and Gemma. Scoring runs after the run
reports `done`, never inside training.

### 6.2 Outcomes

| key 1 | key 2 | record | next |
|---|---|---|---|
| pass | pass | pass | G4: graft phase |
| pass | fail | fail (salad) | coverage diagnosis; D4 only if it names composition |
| fail | pass | fail (gate) | off-anchor diagnosis; no depth arm |
| fail | fail | fail | C1 (4 GB, 100M), then C2 (50M) only after a new decision |

### 6.3 Ceiling and stop rule

The 14 GPU-days are an authorisation ceiling, not a kill rule. Host 4.52 d plus
C1 9.04 d = 13.56 d fits; C2 would exceed it and needs a new decision. A running
arm is never terminated on the clock alone.

Stop rule: a run stops early only if, over a trailing 50,000 steps, best val NLL
improved by less than 0.005 nats **and** the key-1 delta is still worse than
+0.20 nats/byte with no downward trend across the last three measurements.

### 6.4 Scoring

Key 1: `scripts/quinn/key1_score.py` on `last` and the milestone checkpoints.
Key 2: `key2_generate.py --checkpoint <last>`, then the two judge seats, then
`key2_verdict.py`. The ordering row `positive > host > 3.22B` becomes reportable
from this pass.

## 7. TensorFold (authorized, serving-side)

Authorized 2026-11-24 on the exactness contract. Scope: install, BDH family
operator, exactness verification, benchmark; no weight or training-loop change.
Build during the run in a separate environment, no GPU workload while training
is active. The gate runs after the run, on the host checkpoint: fp32 plain path,
CUDA, batch 1, greedy, 256 new bytes, block 512, the frozen 133 prompts,
133/133 byte-identical. The checkpoint sha256 is recorded at `done`, before any
downstream consumer, and re-hashed after the gate. bf16 is a separate gate and
cannot substitute. If the gate fails, serving stays on the plain path.

This is not part of the training sign-off; no host checkpoint exists yet.

## 8. Not covered

- The key-2 result itself (measured after the run).
- Output memorisation (50-byte overlap), checked after the run.
- SFT ordering (item 8), deferred to the first host that passes key 2.
- Human key-2 band; the GPT calibration read stands in its place per the freeze.
- Any 3.22B-scale training.

## 9. G0 artifacts

| artifact | sha256 |
|---|---|
| `data/host/duplicates.json` | `36d68e860b6bea74` |
| `data/host/carve_manifest.json` | `a93a41cd2ee9ea40` |
| `data/host/census_train.json` | `bce9756dda1d268d` |
| `data/host/census_val.json` | `a5e26c91b35ec52b` |
| `out/host/key1_ngram.json` | `74426d2f2f52467e` |
| `out/host/key1_legal.json` | `7f545dcfbc6f73d0` |
| `out/host/key1_322b_legal.json` | `99392dbf63bcd435` |
| `out/host/prompt_contamination.json` | `eacb2ec4c7b707da` |
| `scripts/quinn/build_host_corpus.py` | `3126b3aa9db98114` |
| `scripts/quinn/key1_ngram.py` | `b46b29a2891d9e89` |
| `scripts/quinn/key1_score.py` | `35e5a36dec4fbdb1` |
| `scripts/quinn/key2_prompt_contamination.py` | `dc78e40ba68a1231` |
| `scripts/quinn/launch_host.sh` | `1077144828919ea4` |
| `pipeline/train.py` | `76a1c9d827d5e728` |
| `pipeline/data.py` | `dad8613c9f556be2` |
| `pipeline/config.py` | `00e0e69cb488f7ad` |
| `out/host/resume_test.json` | `50f26e34e60dedd3` |
| `out/routed_probe/diag_positions_1024.npz` | `54cdd1161efdf848` |

Full hashes are written by the G0 commit. The carve byte files are not
committed; their hashes are in the manifest.

## 10. Sign-off

| item | disposition |
|---|---|
| data: duplicates, carve, splits, census | proposed |
| key-1 threshold 1.087674 and 80 % precondition | proposed |
| 3.22B stack-drift finding (3.5) | proposed, named not silent |
| prompt contamination (4) | proposed, sensitivity not substitution |
| shape, sampling, measured 4.52 d | proposed |
| resume test (5.4) | passed: 1.4994 vs 1.4993, delta 0.0001 |
| A/B/C, 14-day ceiling, stop rule | proposed |
| item 8 deferral | proposed |
| TensorFold gate | already authorized; timing restated |

Operator approval: pending.

Signed: ______________________  Date: ____________
