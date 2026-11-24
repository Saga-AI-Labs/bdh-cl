# Host run launch record (2026-11-25)

**Status: RUNNING.** This note records the launch; it does not change the
frozen G0 record (`docs/notes/2026-11-24_host-g0-completion.md`, `f49d9b5`).

## 1. Launch

| field | value |
|---|---|
| started | 2026-11-25T00:39:36 CET (process start) |
| pid | 150892 (own session; survives the agent session) |
| git sha | `f49d9b5` (G0 frozen) |
| command | `scripts/quinn/launch_host.sh` |
| log | `out/host/host100m-e1.log` |
| output dir | `out/host/` |
| checkpoint stem | `bdh_files_host100m-e1` |
| shape | 100M, 4 layers, block 512, batch 8, compiled |
| steps | 488,281 (one pass, seed 1337) |
| data | train 1,999,999,882 B, sha256 `4692331783fb84d5...`; val `bf4600f0...`; test `43f67e13...` |
| projection | 799 ms/step x 488,281 = 4.52 d, plus ~40 min of evals and checkpoint writes; done around 2026-11-29 12:30 CET |

The launcher carries the full command in one detached process. No judge, lease,
scheduler or timer is involved; see G0 section 6.3 and plan section 14.

## 2. What it writes

- `last`: every 5,000 steps, overwritten (about 1.2 GB with Adam state);
- `best`: on val improvement, diagnostic only;
- `step050000` ... `step450000`: every 50,000 steps, kept (about 11 GB total);
- `bdh_files_host100m-e1_done.json` on completion, with step, best val, wall
  clock, data/code hashes and the final checkpoint sha256.

The verdict will be scored on `last`, not `best` (G0 5.4).

## 3. Check and resume

```
tail -f out/host/host100m-e1.log
grep -E "val_loss|done marker" out/host/host100m-e1.log | tail -5
```

If the process dies, rerun the same launcher. `--resume` restores model,
optimizer, step, best val, crop cursor and RNG state, and refuses if the data
hash or config fingerprint changed:

```
setsid nohup scripts/quinn/launch_host.sh > out/host/host100m-e1.log 2>&1 < /dev/null &
```

Only a crash is recoverable this way. Nothing external may stop a healthy run.

## 4. After `done`

1. Key 1: `scripts/quinn/key1_score.py --ckpt out/host/bdh_files_host100m-e1_last.pt
   --val data/host/fineweb_val.txt --ngram out/host/key1_ngram.json --out
   out/host/key1_host100m.json`. Gate: <= 1.087674 nats/byte and order-6
   resolution >= 80 %.
2. Key 2 only if key 1 passes: generate 133 x 256 B greedy, score both seats,
   run `key2_verdict.py`. The gate is the frozen v2 rule.
3. Report the branch (A/B/C) and, if key 1 fails, bring the C1 decision back to
   the operator before starting it.

## 5. Ceiling note on C1

At the measured 799 ms/step, C1 (4 GB, 100M, 4L) is 9.04 d, so host + C1 is
13.56 d against the 14 GPU-day ceiling, 0.44 d margin. The operator's signature
note (2026-11-25) records that the ceiling is not raised: if the host rate
holds, both arms fit; any extension of C1 or a slower measured rate needs a new
decision before C1 starts. C2 already exceeds the ceiling.

## 6. What this launch does not establish

- The host's key 1 or key 2 outcome.
- Any claim about the model before `done` and scoring.
- That the run will finish; the 4.52 d is a projection from 600 measured steps.
