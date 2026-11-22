# Archive: `out_c/` retirement

**Date:** 2026-11-23
**Replacement:** future working output goes to `out/<stage>/`; curated provenance
goes to `archive/`; checkpoints go to Hugging Face.
**Result:** `out_c/` removed, ~296 GB reclaimed.

---

## Why

`out_c/` had become a phantom structure: it mixed live calibration rows,
historical judge runs, routed-probe logs and several hundred GB of checkpoints
whose uploads were already verified. The key-2 scripts were moved to `out/` on
2026-11-22 (`26790d9`). This cleanup finishes the retirement.

## Mapping

| old path | now |
|---|---|
| `out_c/key2_calibration/` | `out/key2_calibration/` (live; manifest regenerated with `out/` paths) |
| `out_c/judge_calibration/` | `out/judge_calibration/` (historical 4.4b certification rows) |
| `out_c/routed_probe/` diagnostics | `out/routed_probe/` (npz, bench log, graft-2 logs, scripts) |
| `out_c/routed_probe/*.pt` | Hugging Face `Saga-AI-Labs/bdh-routed-probe` (7/7 uploaded) |
| `out_c/expert_merge/` checkpoints | HF `Saga-AI-Labs/bdh-expert-merge` (15/15 verified) + `archive/2026-11-expert-merge/` |
| `out_c/expert_merge/lr_probe/` | HF `bdh-expert-merge` `lr_probe/` (6/6) + `archive/2026-11-k25w1024-lr-probe/` |
| `out_c/merge_probe/` | HF `bdh-expert-merge` `merge_probe/` (3/3) + `archive/2026-11-merge-probe/` |
| `out_c/hf_expert_merge_stage/` | deleted after the 15/15 verification; upload/verify logs in `archive/2026-11-expert-merge/upload-verify/` |
| `out_c/expert_merge/freeze_tiny/` | `out/legacy/expert_merge_freeze_tiny/` (49 MB of tiny test checkpoints, not uploaded) |
| `out_c/hf_venv/` | deleted (disposable upload venv) |
| `out_c/hf_token` | deleted; rotate the token if it was still live |

## Checkpoint provenance

- Routed probe: 7 files uploaded 2026-11-18/19, all `rc=0`, including
  `bdh_textmix_p3_mixed_best.pt` and `bdh_textmix_p1_legal_new_best.pt`.
  The local copies were already gone at cleanup time; HF is the only copy.
- Expert merge: `verify_expert.log` reports 15/15 OK against repo commit
  `f1b5e0fb...`; `verify_expert2.log` reports the 315.7 GB repo view.
  `archive/2026-11-expert-merge/upload-verify/` keeps both logs and the
  upload summary.
- Merge probe: the three checkpoints were Hardlinks to the expert-merge stage
  and are covered by the same 15/15 verification.

## Historical reports

Reports keep the `out_c/...` paths they used at run time. They are the record of
where the artifact lived then; this table is the current location. Do not
rewrite old reports to the new paths.

## Legacy scripts

These scripts still contain historical `out_c/...` paths and are kept as the run
record, not as live entry points: `scripts/quinn/serving_eval.py`,
`mini_mask_a.py`, `merge_probe_eval.py`, `probe_j_reject.py`,
`probe_r_readout.py`, `probe_s_semantic.py`, `pc4_ood.py`, `merge_prune.py`.

Live tooling was repointed: `scripts/diag_context.py` -> `out/routed_probe/`,
`scripts/quinn/judge_calibration.py`, `scripts/judge_cert_report.py` and
`scripts/quinn/prune_rescore_rows.py` -> `out/judge_calibration/`, and the four
`key2_*` scripts -> `out/key2_calibration/`.
