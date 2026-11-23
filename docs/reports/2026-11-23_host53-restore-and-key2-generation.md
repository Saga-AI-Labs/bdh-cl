# Host .53 restore and key-2 generation: one missing venv, one wrong wheel, one missing argument

**Date:** 2026-11-23
**Question:** after the `.52` -> `.53` host move, is the project back to a state
where the key-2 measurement can run, and what did the first host-side key-2
artifact look like?
**Answer:** yes to the environment, no to the gate. The host, the frozen
artifacts, the checkpoint and the key-2 reference set are all restored and
hash-verified, and the 133-prompt 3.62B generation is complete (133 rows, 8.27 h,
1.06 B/s). But no judge has scored a single sample, so `M_d`/`F_d` are not set
and key 2 has no verdict yet. Three defects were found and fixed on the way: a
`.venv` that did not move, a torch wheel that cost 1.63x throughput on this
hardware, and a `collect_state` call that OOM-killed the box.

---

## 1. Host verification

| check | result |
|---|---|
| hostname / IP | `spark-da5a` / `192.168.178.53` - the expected `.53` box |
| arch / GPU | aarch64 / NVIDIA GB10, compute capability 12.1 (`sm_121`) |
| driver | 580.178.04 |
| disk | `/dev/nvme0n1p2` 3.7 T, 3.5 T free after restore |
| repo | `main`, clean, in sync with `origin/main` at resume time (`83ea88c`) |

Tracked content moved cleanly. The four frozen gate inputs verified against the
hashes registered on 2026-11-22:

| artifact | sha256 |
|---|---|
| `data/evals/key2_prompts_v1.json` | `c1d9c62c...12e23c` |
| `data/evals/key2_rubric_v1.json` | `8788ac78...33d65f` |
| `data/evals/judge_set_v1/cert_items_merged.json` | `8570d8cd...c6ce50` |
| `data/textmix2/code.txt` | `d4da44b4...39252` |

## 2. What the move actually lost

Both losses are gitignored, so git carried neither.

| path | state after the move | recovery |
|---|---|---|
| `.venv` | absent; no torch, numpy or HF CLI anywhere on the box | rebuilt |
| `out/` | absent entirely | partly regenerated, partly copied back |
| `data/textmix2/` | absent (`legal.txt`, `code.txt`, `latex.txt`) | copied back; `code.txt` sha256 and `legal.txt` md5 + byte size both re-checked against the pinned values |
| `.jspace/` ledger | absent (gitignored) | not recovered; history is in the reports |

`out/` was the expensive one. `out/key2_calibration/` was regenerable from the
frozen cert set; `out/judge_calibration/` and `out/routed_probe/` were not, and
were copied back from the old host the same day. The 3.62B checkpoint was never
local - HF is its only copy.

Note for the record: the 2026-11-23 cleanup (which reclaimed ~296 GB by
retiring `out_c/` and `out_a/`) had already documented the routed-probe
checkpoints as "local copies already gone". The move then removed the rest of
`out/`. That ordering is why a checkpoint was deleted shortly before it was
needed.

## 3. Environment rebuild, and the wheel that mattered

Installed: Python 3.12.3, torch 2.14.1+cu130 (CUDA 13.0), triton 3.8.0,
numpy 2.5.5, pyarrow 26.0.1, requests 2.34.2, huggingface_hub 2.4.0. `.venv`
is 7.6 G.

The first attempt used torch 2.10.0+cu128 with the assumption that cu128 covered
`sm_121`. It does not; neither build lists `sm_121` (cu128 tops out at
`sm_120`, cu130 at `sm_120`), but only the cu130 build runs at the expected
rate. Measured with `scripts/bench_100m.py --layers 6 --steps 30`, b8/t512:

| build | 100M step | bytes/s | bf16 8192^3 matmul |
|---|---|---|---|
| Spark reference (2026-11-12 report) | 2,192 ms | 1,868 | - |
| Spark rerun (2026-11-18 `bench_100m.log`) | 2,182 ms | 1,877 | - |
| torch 2.10.0+cu128 (first install) | 3,565 ms | 1,149 | 10.3 TFLOPS |
| **torch 2.14.1+cu130 (final)** | **2,273 ms** | **1,802** | **85.5 TFLOPS** |

The archived `bench_100m.log` shows the same device string (`NVIDIA GB10`), so
the reference is the same hardware class: 2,273 ms is a 4 % delta, the cu128
build is a 63 % regression. `requirements.txt` still says `torch>=2.3`, so a
plain `pip install -r` on this box reproduces the slow build silently. Pinning
the cu130 index is recommended and not yet done.

## 4. Key-2 reference set restored

`scripts/quinn/key2_reference.py` reads only the frozen cert set, so the
calibration rows are deterministic:

| check | result |
|---|---|
| `reference_scale.jsonl` | 108 rows (18 en items x 6 variants) |
| `reference_positive.jsonl` | 18 rows |
| positive band bytes | 242-255 (min/median/max) |
| full `good` bytes | 288-886, median 588.5, none <= 256 |
| format-constrained items | `cert_en05`, `cert_en09`, `cert_en10`, `cert_en16` |

Every value agrees with section 8.3 of the key-2 rubric, so this is the same
reference the freeze was approved on, not a new one.

## 5. Checkpoint recovery

The repo is a HF **dataset**, not a model. The resume note's command omitted
`--repo-type dataset`; without it the API returns 404, which reads like a
missing or private repo. Corrected command:

```bash
hf download Saga-AI-Labs/bdh-routed-probe bdh_textmix_p3_mixed_best.pt \
  --repo-type dataset --local-dir out/routed_probe
```

| check | coverage | result |
|---|---|---|
| size | `stat` byte count of the local file | 38,657,073,228 B (36.00 GiB), equal to the upload log entry |
| sha256 | re-hashed all 38,657,073,228 local bytes | `ce24e0fd...0e1874`, equal to the HF LFS oid stored at upload |
| load | full `state_dict` load via `load_model_mmap`, 25.8 s | succeeded; mmap keeps the Adam state off-heap |
| config | read back from the loaded checkpoint | n_layer 4, n_embd 1024, n_head 16, mult 1024, block 512 |

**The artifact is 3,221,749,760 params (3.22 B), not 3.62 B.** The size math
confirms it independently: 12 bytes/param (fp32 weights + Adam m + Adam v) times
3.2217 B = 36 GiB, exactly the file. "3.62B" is a label carried by the notes and
the rubric. It does not change the negative-band procedure, but the frozen G0
record should not name the wrong model. Renaming is an operator decision and has
not been done.

## 6. Generation: the run, and the OOM that preceded it

First attempt died with rc=137 about 20 s in. The kernel log shows a global OOM,
not a Python error: `total-vm:194020616kB, anon-rss:0kB`, and it killed
`systemd` as collateral. That signature matches the 2026-11-07 diagnosis note
(on GB10 the CUDA pool is invisible in process RSS and lives in NVRAM-managed
pages).

Root cause: `key2_generate.py`'s `greedy_bytes` called `model(idx_cond)` with the
default `collect_state=True`, building a 4-layer KV state in fp32 (the
checkpoint loads as float32) and discarding it on every one of 256 steps. On the
119 GiB unified pool that was enough. Every other eval script in the repo
already passes `collect_state=False`; this was the last call site. Logits were
verified bit-identical on this checkpoint (`max abs diff 0.0`), matching the
2026-11-07 note's finding.

Result after the fix (`expandable_segments:True`, greedy, 256 B, block 512,
float32):

| metric | value |
|---|---|
| rows | 133 (100 gate / 33 diagnostic) |
| families | 50 explain / 50 describe / 33 argue |
| rate | 1.06 B/s (10-prompt smoke: 1.07 B/s) |
| wall | 29,779.5 s = 8.27 h |
| length | all 133 exactly 256 B, none empty |
| prompt bytes | max 66 (cap 128) |
| language-broken subset | 71 rows with non-ASCII bytes |
| diversity | 43 distinct 40-byte prefixes |

Content is the registered salad, and it is uniform across families: legal
boilerplate loops (`the provisions of the provisions of ...`, with "the
provision(s) of" about 30 % of all words), with Irish fragments (a leading
token `D` + U+00E9 + `anfar`, and `Ba`) producing the non-ASCII rows. The
71-row language-broken subset matters
for section 8.3: the language floor `F_language` can be negatively calibrated
because that subset exists.

Provenance: `out/key2_calibration/gen_3.62b.jsonl` and `.meta.json` carry
`checkpoint_sha256 ce24e0fd...`, `prompts_sha256 c1d9c62c...`,
`git_head 4b7c036`, torch 2.14.1+cu130, hostname `spark-da5a`. The 10-prompt
smoke is preserved as `gen_3.62b.smoke.{log,meta.json}`.

## 7. What is measured, and what is not

Measured: the host, the throughput, the reference rows, the checkpoint identity,
the 133 generations, their length, their language mix and their repetition.

Not measured: any judge score. Both judge endpoints
(`192.168.178.200:1234`, `192.168.178.51:8888`) refused connections all session.
Therefore:

- no `mean_d` or `min_d` exists for any dimension;
- `M_d` and `F_d` are not set, so the G0 freeze has not happened;
- key 2 has **no** verdict on this host model. The generation is the input to
  the measurement, not the measurement.

`scripts/quinn/key2_judge.py` still defaults to the old `.51:8888` address, so
the current addresses must be passed explicitly (or the defaults updated) when
the judge boxes return.

## 8. Open items

1. **Judges.** Boot and reach them; then score the 108 scale rows, the 18
   positive rows and the three negative bands; then set `M_d`/`F_d` at G0.
2. **Naming.** Correct `3.62B` -> `3.22B` in the rubric before G0 freezes.
3. **Key 1.** `scripts/diag_context.py` is still hardcoded to
   `LEGAL = "legal:data/textmix2/legal.txt"`; the corpus is back and
   `legal.txt` re-matches its pinned md5, so the path works again, but the host
   carve needs a corpus argument.
4. **Host corpus.** FineWeb-Edu 10BT shard (2,152.2 MB) and a clean purity
   census are in place (purity p05 = p50 = 1.0, 0/200 anomalous crops, English
   markers 209/1k vs German 0.24/1k). The train/val carve itself is not built.
5. **Pinning.** Pin the cu130 wheel in `requirements.txt`.

## 9. Provenance

Commits on `main`, local only at the time of writing (not pushed):

| commit | content |
|---|---|
| `21eed6b` | env rebuild and post-move inventory note |
| `2b8d739` | dataset repo-type fix; verified restore |
| `4b7c036` | `collect_state=False` OOM fix in `key2_generate.py` |

Working notes: `docs/notes/2026-11-23_env-rebuild-53.md`,
`docs/notes/2026-11-23_session-resume.md` (download command corrected).

Tooling: J-Space Cognition Suite SV1 installed to
`~/.config/opencode/skills/j-space/` (upstream `b2023124`,
`verify_suite` clean, 90/90 unit tests pass).
