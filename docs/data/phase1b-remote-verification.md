# phase-1b remote verification (three-way sha256)

Generated 2026-09-16 by Quinn (A0 seat), operator-ordered formal verification ahead of any
deletion. Re-runnable via `bdh/scripts/quinn/verify_phase1b.py`. Identical instrument to the
phase-1 40/40 join.

For each object the bytes are pinned at three independent points:

- **(a) committed** pre-upload sha256 in `phase1b-ladra2-crossbox-join.md` (17:30 cross-box audit),
- **(b) gx10 fresh** `sha256sum` re-read of the live staging bytes tonight,
- **(c) HF remote** — the LFS `oid` for the 16 `.pt`, and a `resolve` download + local sha256 for
  the 2 REGULAR blobs (`README.md`, the repair `.json`), which carry no LFS oid.

a==b proves the on-disk bytes are unchanged since the audit; b==c proves transfer fidelity;
a==c is the non-circular committed<->remote link. All three equal is the claim.

| file | committed (17:30) | gx10 fresh (now) | HF remote | link | match |
|---|---|---|---|---|---|
| `bdh_europarl_ladRA2-bg_best.pt` | `c9b63d48f2e7ee8e…` | `c9b63d48f2e7ee8e…` | `c9b63d48f2e7ee8e…` | LFS | OK |
| `bdh_europarl_ladRA2-bg_last.pt` | `02f95b844791c91d…` | `02f95b844791c91d…` | `02f95b844791c91d…` | LFS | OK |
| `bdh_europarl_ladRA2-el_best.pt` | `80ff448b49e78ebf…` | `80ff448b49e78ebf…` | `80ff448b49e78ebf…` | LFS | OK |
| `bdh_europarl_ladRA2-el_last.pt` | `b8d79f498aba1b7f…` | `b8d79f498aba1b7f…` | `b8d79f498aba1b7f…` | LFS | OK |
| `bdh_europarl_ladRA2-et_best.pt` | `ffc14678af96a8a5…` | `ffc14678af96a8a5…` | `ffc14678af96a8a5…` | LFS | OK |
| `bdh_europarl_ladRA2-et_last.pt` | `8dac03b3d0703c43…` | `8dac03b3d0703c43…` | `8dac03b3d0703c43…` | LFS | OK |
| `bdh_europarl_ladRA2-fi_best.pt` | `ba243b863e7315ae…` | `ba243b863e7315ae…` | `ba243b863e7315ae…` | LFS | OK |
| `bdh_europarl_ladRA2-fi_last.pt` | `b9713d2503ca7e11…` | `b9713d2503ca7e11…` | `b9713d2503ca7e11…` | LFS | OK |
| `bdh_europarl_ladRA2-hu_best.pt` | `2bbf7e913e35c899…` | `2bbf7e913e35c899…` | `2bbf7e913e35c899…` | LFS | OK |
| `bdh_europarl_ladRA2-hu_last.pt` | `b41816f0f4e6689f…` | `b41816f0f4e6689f…` | `b41816f0f4e6689f…` | LFS | OK |
| `bdh_europarl_ladRA2-lt_best.pt` | `2d57e315e49afc8b…` | `2d57e315e49afc8b…` | `2d57e315e49afc8b…` | LFS | OK |
| `bdh_europarl_ladRA2-lt_repaired.pt` | `a7575f995fbb11c2…` | `a7575f995fbb11c2…` | `a7575f995fbb11c2…` | LFS | OK |
| `bdh_europarl_ladRA2-lt_repaired_repair.json` | `aacd4963c8e76ab8…` | `aacd4963c8e76ab8…` | `aacd4963c8e76ab8…` | DL | OK |
| `bdh_europarl_ladRA2-sk_best.pt` | `c30ccf8317ebe360…` | `c30ccf8317ebe360…` | `c30ccf8317ebe360…` | LFS | OK |
| `bdh_europarl_ladRA2-sk_last.pt` | `5ce3d91e406b5f98…` | `5ce3d91e406b5f98…` | `5ce3d91e406b5f98…` | LFS | OK |
| `bdh_europarl_ladRA2-sl_best.pt` | `1073614bc51efb17…` | `1073614bc51efb17…` | `1073614bc51efb17…` | LFS | OK |
| `bdh_europarl_ladRA2-sl_last.pt` | `735a7d756babdb14…` | `735a7d756babdb14…` | `735a7d756babdb14…` | LFS | OK |
| `README.md` | `f5128066712ffe8c…` | `f5128066712ffe8c…` | `f5128066712ffe8c…` | DL | OK |

**Result: PASS: 18/18 byte-identical across committed / gx10-fresh / HF-remote** — 17 payload objects + dataset card (`README.md`); 16 via LFS oid,
2 via download-hash. `.gitattributes` is HF-generated LFS machinery, not a payload object,
excluded here and kept on the remote (as in phase-1).

The 17 files remain on gx10 until pi-50 runs the retrieval spot-check (#303 convention) and
acks; deletion then requires an intent envelope naming the exact 17. Nothing was deleted in
this pass.

Remote total: 94240313535 B across 19 files (repo `Saga-AI-Labs/bdh-cl_phase-1b`).
