# Phase-1 HF release checklist

Date: 2026-09-15 · Owner: Quinn (A0 seat) · Status: pending (upload in flight)

Context: 40 RA2b checkpoints (best+last, 20 languages, 152 GiB) plus dataset card and
acquisition metadata are being uploaded to `Saga-AI-Labs/bdh-cl_phase-1` (public).
Uploader: gx10, `upload_phase1.py`, XET enabled. ETA ≈ 07:00 CEST.

## Open items (operator-approved, queued after upload completes)

1. **Remote verification** — after `done - all files uploaded`: confirm 43 remote files
   (40 checkpoints + card + 2 metadata files), compare per-file size and sha256 against
   the local `.metadata` staging markers (they hold sha256 of every staged file). Post
   the verification summary to the HAK bus (room `bdh-cl`) for pi-50.
2. **Local cleanup (gx10), pi-50 order** — only after remote verification:
   - Delete local `ladRA2b` copies in `out/` that are now remote-verified (+152 GiB).
   - Keep both Qwen model caches on gx10 (operator decision, 2026-09-15: "Die beiden
     Qwen-Modelle müssen bleiben") — do NOT reclaim the +99 GiB stock-twin lever.
   - Cross-box duplicates (~70 GiB, 25 files): hash-confirm against `.200`, then delete
     the gx10 side. Coordinated with pi-50 after uploads finish.
   - Single-copy `ladRA2` files (19 files, 97.4 GiB): build phase-1b upload list (or copy
     to `.200`) BEFORE any deletion — manuscript numbers rest on them.
3. **Paper + GitHub notes** — after remote verification: add notes in the manuscript and
   the GitHub README that phase-1 data is available in the HuggingFace dataset repo
   `Saga-AI-Labs/bdh-cl_phase-1`.
4. **GitHub README pointer** — update the bdh-cl README so it references the current
   paper version (rev 4.6, `docs/papers/rev4-bdh-manuscript.pdf`).
5. **Descriptions and tags** — both HuggingFace (dataset page) and GitHub (repo topics)
   need proper descriptions and keyword tagging for Saga-AI-Labs pages.
