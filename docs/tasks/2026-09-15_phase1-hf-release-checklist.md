# Phase-1 HF release checklist

Date: 2026-09-15 · Owner: Quinn (A0 seat) · Status: partially done, cleanup executed, design-doc queued

Context: 40 RA2b checkpoints (best+last, 20 languages, 152 GiB) plus dataset card and
acquisition metadata are being uploaded to `Saga-AI-Labs/bdh-cl_phase-1` (public).
Uploader: gx10, `upload_phase1.py`, XET enabled.

## Done

- [x] **Upload completed** — `done - all files uploaded` 09:46:33 CEST, 163,125,418,204 B over 45 files.
- [x] **Remote verification** — 40/40 sha256 join: remote LFS OIDs vs local staging-marker digests;
      size_mismatch=0, oid_mismatch=0, missing_remote=0 → VERIFIED. Independently corroborated by
      pi-50 (#296: re-downloaded one checkpoint end-to-end, sha256 == recorded LFS oid; #299 recomputed
      both boxes' hashes on one shared name-list). Posted to bus (seq 294, 301).
- [x] **RA2b local cleanup (gx10)** — both hardlink paths (`out/` + `hf_phase1_upload/checkpoints/`)
      removed after verification; `hf_phase1_upload/` staging deleted; 185 MB upload log truncated.
      df: 31 G → 183 G free. Card + `.gitattributes` + 2 metadata files on remote kept.
- [x] **Stray test-file removed** — `.write-test-main` deleted from the dataset (45 → 44 remote files;
      commit `74757bda`). The `.gitattributes` is HF-generated LFS machinery and stays.
- [x] **Cross-box ladRA2 duplicates (gx10)** — hash-confirmed (sha256 on both boxes, not length),
      pi-50 acked the exact 25-file list (#299). 25 sha-identical files deleted from gx10 with the
      `.200` counterpart retained: before=42, removed=25, after=17. df: 183 G → **254 G free**.
- [x] **.gitignore hardened** (commit `9061644`) — `hf_phase1_upload/` and `.hf_token` excluded,
      closing the `git add -A` credential/152-GiB leak risk pi-50 named (#290 §2).

## The 17 single-copy ladRA2 files (gx10-only) — hash-confirmed

sha256 join (gx10 42 files vs .200 25 files): 25 identical pairs (deleted from gx10), **17 gx10-only**
files, 0 same-name mismatches. The 17 are the `bg/el/et/fi/hu/sk/sl` best+last pairs (7 languages × 2 =
**14**, not the "(12)" I mis-wrote in bus #298) plus `lt_best.pt`, `lt_repaired.pt`, and
`lt_repaired_repair.json` — **17 files, 88 GiB**. These are the only copies of anything, and they back
`ladRA2-` names cited in `bdh/docs`, so they are NOT deletable until replicated.

Note: pi-50's earlier length-based audit (#290) reported this set as "19 files / 97.4 GiB"; the hash join
superseded it to 17 / 88 GiB. Use 17 / 88 going forward.

## Open items (queued)

1. **Phase-1b destination (operator ruling pending)** — replicate the 17 single-copy ladRA2 (88 GiB) to
   either a second public dataset repo `Saga-AI-Labs/bdh-cl_phase-1b` (XET, ~1-2 h) or a copy to `.200`
   (6.1 T free). Do NOT delete these from gx10 until that destination is confirmed and verified.
2. **RA2b second copy (risk, operator ruling pending)** — RA2b (152 GiB) is now single-copy on HF after
   the local delete. pi-50 (#296) recommends a re-download to `.200` (~6 h at ~7 MB/s) to remove the
   single-point-of-failure. Queued behind the operator's replication decision.
3. **`.200` replication audit (pi-50, #290 §5)** — 380 unique files / 733 GiB live only on `.200`.
   Replication (not cleanup) to be scoped; untouched by me.
4. **Paper + GitHub notes** — after the above settles: add notes in the manuscript and the GitHub README
   that phase-1 data is available in the HuggingFace dataset repo `Saga-AI-Labs/bdh-cl_phase-1`.
5. **GitHub README pointer** — update the bdh-cl README to reference the current paper version
   (rev 4.6, `docs/papers/rev4-bdh-manuscript.pdf`).
6. **Descriptions and tags** — HuggingFace (dataset page) and GitHub (repo topics) need proper
   descriptions and keyword tagging for Saga-AI-Labs pages.

## Related (separate project)

- **Skald** (working name, operator-liked) — consolidated eval-haus: suite adapters (BDH-CL, pi-50
  abliteration/refusal, saga benchmarks, Jacobian-Lens module), unified result-store, dual API+UI
  (weight-atlas / HAK pattern), no cloud-LLM in the analysis chain. Design-doc next, after upload
  housekeeping. Identity link to weight-atlas via checkpoint-hash.
- **DMT/43-sites mystery** — pi-50's paired transitions found 43 REFUSED→OFF_TARGET sites (all on former
  refusal sites, ~1% of conversions); my own abliterated-Qwen DMT interlude (Transformer-DMT answer to a
  chemistry question, context-dependent) is the anecdotal case. Reproduction design in the Skald doc.