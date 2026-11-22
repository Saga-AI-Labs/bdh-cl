# Session resume - after the .52 -> .53 move

**Purpose:** continue the BDH-CL work on the new host without relying on the old
chat context. Read this first, then verify the host before running anything.
**Snapshot:** 2026-11-23, commit `2b2bf3f`, working tree clean.
**Old host:** `spark-d1da`, repo at `/srv/coding/bdh-cl`, aarch64, one GPU.

---

## Resume prompt (paste this into a fresh session)

> You are resuming the BDH-CL project after a host move. The repo is at
> `/srv/coding/bdh-cl`. Read `docs/notes/2026-11-23_session-resume.md` first,
> then verify the host (hostname, GPU, `.venv`, `git status`, disk) and report a
> short status. The binding key-2 specification is section 8 of
> `docs/notes/2026-11-19_key2-coherence-rubric.md`; the prompt set and rubric
> were operator-approved on 2026-11-22 at the hashes in that note. Do not start
> training, delete data, or commit anything without operator confirmation. The
> 3.62B negative checkpoint is not local; it must be re-downloaded from
> Hugging Face `Saga-AI-Labs/bdh-routed-probe`.

## State

**Decided**
- Host is English-first. Europarl is excluded from host and specialist training;
  de/zh may return later as routed specialists.
- Key 1 is a corpus-specific rule: byte 6-gram, order 4/6, backoff, no
  discounting, host train carve -> host val carve, margin frozen before the run.
  The 0.8519 value is the legal-carve value, not transportable.
- Key 2 is sample-based and must be frozen before the first host run. Gate per
  dimension: `mean_d >= M_d` and `min_d >= F_d`; no mean across dimensions.
- Key 2 prompt set: 133 authored prompts = 100 gate (50 explain + 50 describe)
  + 33 argue diagnostic. Greedy, 256 B, prompt <= 128 B.
- Positive reference: human target 40 answers (minimum 20); not available at
  this freeze, so the certified English `good`@256 band is the fallback.
- Negative bands are per dimension: coherence = 3.62B salad; language =
  language-broken subset; relevance = clean off-topic control.
- Judges: exactly two local seats, Qwen primary + Gemma cross-check. No third
  seat; harness models (Deepseek, GLM) are not judges. NULL cap 5 %.
- TP=2 remains out of scope until the registered trigger fires. One Spark.
- Commits only after operator confirmation. `data/` needs `git add -f`;
  `out/` is gitignored. HF uploads are done by Quinn.

**Artifacts**
| path | what |
|---|---|
| `data/evals/key2_prompts_v1.json` | 133 prompts, hash `c1d9c62c...12e23c` |
| `data/evals/key2_rubric_v1.json` | anchors + judge system prompt, hash `8788ac78...33d65f` |
| `out/key2_calibration/reference_scale.jsonl` | 108 cert-scale rows |
| `out/key2_calibration/reference_positive.jsonl` | 18 `good`@256 positive rows |
| `out/key2_calibration/reference_manifest.json` | hashes, counts, band stats |
| `out/key2_calibration/prompts_review.md` | operator review sheet |
| `out/judge_calibration/` | historical 4.4b certification rows |
| `out/routed_probe/` | diagnostics, bench log, graft-2 logs |
| `out/fineweb_edu_probe/` | FineWeb-Edu sample + census, host-corpus candidate |

**Cleanup done 2026-11-23.** `out_c/` and `out_a/` are gone (~296 GB freed).
The mapping is in `archive/2026-11-out-c-retirement/README.md`. Historical
reports keep their old `out_c` paths on purpose. `hf_token` was removed; rotate
the token if it was live.

## Startup checklist on .53

```bash
cd /srv/coding/bdh-cl
git pull --ff-only
hostname -I
git status -sb
.venv/bin/python -V
.venv/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())"
df -h /srv/coding
```

If the repo path, `.venv` or CUDA changed, fix that before any run. The judge
endpoints are separate boxes; do not assume the old IPs
(`192.168.178.200:1234`, `192.168.178.51:8888`). They were down on 2026-11-23.

## Next moves, in order

1. **Re-download the 3.62B checkpoint** (only HF has it):
   ```bash
   hf download Saga-AI-Labs/bdh-routed-probe bdh_textmix_p3_mixed_best.pt \
     --local-dir out/routed_probe
   ```
   The upload log (`archive/2026-11-routed-probe/upload-summary.txt`) records
   `rc=0` for all 7 routed-probe files. Verify the local size (38.7 GB) before
   loading.

2. **Key-2 generation** (operator said "later"; ask before starting):
   ```bash
   .venv/bin/python scripts/quinn/key2_generate.py --limit 10 \
     --checkpoint out/routed_probe/bdh_textmix_p3_mixed_best.pt \
     --out out/key2_calibration/gen_3.62b.jsonl \
     --meta-out out/key2_calibration/gen_3.62b.meta.json \
     --log out/key2_calibration/gen_3.62b.log --hash-checkpoint
   ```
   Measure the first 10 prompts, then resume without `--limit` and with
   `--resume`. Smoke rate on the old Spark: 1.39 B/s, ~6.8 h for 133 x 256 B;
   replace that estimate with the observed rate.

3. **Judge calibration** once Qwen/Gemma are reachable: score the 108 scale
   rows, 18 positive rows and the negative bands with
   `scripts/quinn/key2_judge.py`; then run `scripts/quinn/key2_analyze.py` with
   the per-dimension negative flags. Set `F_d`/`M_d`, freeze at G0.

4. **Key 1**: `scripts/diag_context.py ngram` is still hardcoded to `LEGAL`.
   Add a corpus argument before building the host 6-gram. G0 needs the host
   train/val carve, the 6-gram, margin and order-resolution shares.

5. **Host corpus**: `out/fineweb_edu_probe/` has a 55 MB text sample and a
   census; on-disk English data is ~0.6 GB. About 1.4 GB are still missing for
   the 2 GB target, and the purity census is pending.

## Blockers

- Key-2 G0 freeze: needs judge scores, `M_d`/`F_d`, and the operator sign-off.
- Judge endpoints unreachable as of 2026-11-23.
- 3.62B generation not started (checkpoint must be downloaded first).
- Host corpus incomplete; contamination check against the host corpus pending.
- de/zh specialists are data-blocked: only Europarl is on disk and it is
  excluded.

## Guardrails

- No commit without operator confirmation; no destructive cleanup without a
  verified HF copy.
- The cert set `data/evals/judge_set_v1/` is read-only and is not a key-2
  prompt pool.
- Key 2 measures coherence, topical consistency and language, not facts or
  instruction following; do not import 4.4b correctness into it.
- A judge NULL/JSON failure is "not scoreable", never a silent drop.
