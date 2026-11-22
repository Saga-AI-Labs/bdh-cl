# Archive: Stage A probe scripts and logs (`out_a/`)

**Date:** 2026-11
**Origin:** `out_a/` (BDH-CL training host)
**Status:** retired 2026-11-23
**Size:** 4.3 MB, 72 files (scripts and logs only)

---

## What it was

`out_a/` held the Stage A probe drivers and their logs: the domain sweep, the
K25/W1024 chain and status scripts, the code/legal position dumps, and the
per-language score logs for the 2026-10/11 probe campaign.

The large checkpoints the old reports name (`out_a/bdh_textmix_k25w1024-zh_last.pt`
and the ladder checkpoints) were already gone before this cleanup. No
checkpoint remains in `out_a/`; this archive is scripts and logs.

## Contents

`out_a-20261123.tar.gz` (967 KB) is the full tree:

```
out_a/
  code_dumps.sh, code_posdump.sh, domain_sweep.sh
  k25w1024_chain.sh, k25w1024_chain_v2.sh, k25w1024_status.sh
  legal_posdump.sh
  logs/   (per-language score logs, chain logs, position dumps)
```

List the archive without unpacking:

```
tar -tzf archive/2026-11-stage-a/out_a-20261123.tar.gz
```

## Why it is kept

The reports of the 2026-10/11 probes cite `out_a/` paths and their log names.
The tarball keeps the provenance without leaving a phantom top-level directory.
The registered numbers stay in the reports; this archive is the raw driver and
log record, not a second result surface.
