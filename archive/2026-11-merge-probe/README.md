# Archive: merge/prune probe (`merge_probe`)

**Date:** 2026-11
**Origin:** `out_c/merge_probe/` (BDH-CL training host)
**Size:** 22 GB, 3 checkpoints
**Status:** experiment complete, **negative result** - pruning a pooled model does not recover it

---

## What it was

After the pooled merge was shown to fail (expert-merge archive), the question
was whether the merged model could be **repaired by pruning**: remove the
neurons that carry the interference and keep the useful ones.

Three artifacts were produced:

| checkpoint | what | size |
|---|---|---|
| `merged_pruned896.pt` | merged model, pruned to 896 mult | 11.28 GB |
| `zh_pruned448.pt` | `zh_last` pruned to 448 mult | 5.64 GB |
| `zh_pruned448_fixed.pt` | same, with the 4D-frequency fix | 5.64 GB |

## Result: negative

Three prune attempts degraded the model massively (5.64 -> 21.78 -> 57.48 ppl).
The August script **zeroed weights without changing the width**, so it did not
physically slice - it removed capacity without freeing it. A later fix paired
the pruned neurons and still did not recover the parent.

**Pruning is not the repair path.** The working route is routing (masked
forward), not post-hoc surgery on a pooled model.

## Where the data lives

```
Hugging Face:  Saga-AI-Labs/bdh-expert-merge  merge_probe/
               sha256 (LFS): merged_pruned896 06492347d7c5...
                              zh_pruned448    bf5651d70a73...
                              zh_pruned448_fixed 1786baea2670...
```

## What it is good for now

Nothing active. It is the evidence that the prune repair fails, and it is the
baseline for any future attempt to recover a pooled model.

## How it ended up here

`out_c/merge_probe/` was retired 2026-11-22 as a "phantom structure". The
checkpoints were uploaded to HF; the local copies are Hardlinks to the staging
directory, so their verification is a self-comparison rather than an independent
one - the first verification (15/15 OK) covers them.
