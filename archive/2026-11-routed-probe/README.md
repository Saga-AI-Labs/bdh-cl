# Archive: routed-grow probe uploads

**Date:** 2026-11-18/19
**Repo:** Hugging Face `Saga-AI-Labs/bdh-routed-probe`
**Result:** 7/7 files uploaded, all `rc=0`
**Summary:** `upload-summary.txt`

---

The seven checkpoints were uploaded in the 2026-11-18/19 window. The local
copies under `out_c/routed_probe/` were already gone at the 2026-11-23 cleanup;
HF is the only copy.

| file | result |
|---|---|
| `bdh_textmix_g2_code_best.pt` | rc=0, 1.45 h |
| `bdh_textmix_g2_code_last.pt` | rc=0, 1.56 h |
| `bdh_textmix_grow896to1024_last.pt` | rc=0, 0.96 h |
| `bdh_textmix_p1_legal_new_best.pt` | rc=0, 1.23 h |
| `bdh_textmix_p1_legal_new_last.pt` | rc=0, 1.26 h |
| `bdh_textmix_p3_mixed_best.pt` | rc=0, 1.24 h |
| `bdh_textmix_p3_mixed_last.pt` | rc=0, 1.17 h |

The key-2 negative band uses `bdh_textmix_p3_mixed_best.pt`; re-download it from
the repo before any generation run.
