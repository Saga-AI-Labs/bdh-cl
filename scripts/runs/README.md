# Run scripts - provenance

The scripts that produced the registered numbers of the routed-grow and
graft-2 campaigns, committed verbatim as they ran (paths included: they
reference `/tmp/opencode` scratch dirs for logs and `out_c/routed_probe`
for checkpoints). Logs and the tiny-scale checkpoints live in
`out_c/routed_probe/graft2/` and `out_c/routed_probe/scratch_p0_p3/`
(gitignored out-structure; mirrored to the project's HF runs dataset).
A repo checkout plus these scripts reproduces every registered gate.

| script | campaign | produced | log |
|---|---|---|---|
| `g0_dryrun.sh` | P1 era | the G0 dry-run pattern graft-2 plan section 2 reuses | `scratch_p0_p3/p3_dryrun/g0_dryrun.log` |
| `smoke_fullcov.py` | P1 era | the fullcov instrument smoke cited in probe report line ~303 | `scratch_p0_p3/` (this dir) |
| `p3_smoke_run.sh` | P3 era | P3 tiny smoke (G3 machinery) | `scratch_p0_p3/p3_smoke/smoke.log` |
| `ga1_run.sh` | graft-2 | G-A1: backup auto->off/on tiny gates, bit-exact 5.5378/5.5381 | `graft2/ga1/ga1.log`, `runc2.log` |
| `ga2_run.sh` | graft-2 | G-A2: 4-step dry run 1024->1152 + identity eval 1.7470/1.6858 | `graft2/ga2_dryrun/ga2.log` |
| `ga3_anchor.sh` | graft-2 | pre-run anchors: code@0 3.5787/3.5327 + the strict-prefix guard lesson | `graft2/ga3_anchor/anchor.log` |
| `ga3_run.sh` | graft-2 | G-A3: the real graft run (36.2 h, peak 91.99/96.40 GiB) | `graft2/ga3_run/ga3.log` |
| `ga3_matrix.sh` | graft-2 | the 7-cell post-matrix (all S1 bit-exact) + serving check | `graft2/ga3_matrix/matrix.log` |

Serving-check logs (`graft2/serve/`): `gen_serve_check.log` (round 1),
`gen_serve_check5.log` (the 5-sample replication standard),
`mixed_serve_check.log` (mixed-content cells, both checkpoints).
Prune sweep: `graft2/prune/prune_sweep_p3.log`.
Registered third-domain corpus: `graft2/code.txt`
(33,000,559 B, sha256 `d4da44b4...39252`; live copy `data/textmix2/code.txt`,
prep via `scripts/prep_code_corpus.py`).

Not committed: the G-A2 dry-run checkpoints (82 GB in /tmp - reproducible
by rerunning `ga2_run.sh` in ~10 min; the identity numbers live in the
log) and the raw CodeSearchNet parquet (522 MB - public, one `hf download`
command; lineage registered in the graft-2 plan section 8).

Post-campaign diagnostics (2026-11-18, report section 18):
`scripts/diag_context.py ngram` -> 6-gram 0.8519 nats/byte; `positions`
-> 1.1155/@1024, 1.7116/@896; `compare` joins them. Full curves:
`out_c/routed_probe/diag_ngram.npz`, `diag_positions_{896,1024}.npz`;
log `out_c/routed_probe/diag_positions.log`. `scripts/bench_100m.py` ->
100M throughput on the Spark: 2,192 ms/step (6 layers, 1,868 B/s),
1,482 ms/step (4 layers, 2,764 B/s), 23.1 GiB peak; compiled 1,025
ms/step (6 layers). `--two-pass` measures the route-aware compute shape
(two forwards at 0.9/0.1, one backward): 4,429 ms/step uncompiled,
2,091 compiled = 2.0x one-pass, 48.5/33.2 GiB peak.
