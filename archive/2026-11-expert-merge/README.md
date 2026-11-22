# Archive: expert-merge probe (`expert-b1`, `zh_b1_merged`)

**Date:** 2026-11
**Origin:** `out_c/expert_merge/` (BDH-CL training host)
**Size:** 88 GB, 3 checkpoints
**Status:** experiment complete, **falsified** - the merge route is closed

---

## What it was

The expert-merge probe tested whether two BDH checkpoints can be combined by
pooling the neuron dimension. It grew a fresh branch (B1) from `zh_last` on a
Gutenberg corpus with `embed`/`lm_head` frozen, then merged it with the parent.

| checkpoint | what | size |
|---|---|---|
| `bdh_textmix_expert-b1_best.pt` | branch B1, best val_loss 1.1225 (ppl 3.07) | 33.83 GB |
| `bdh_textmix_expert-b1_last.pt` | B1 last | 33.83 GB |
| `zh_b1_merged.pt` | ancestor merge, `zh_last` + B1 | 22.55 GB |

## Result: falsified

Four of four preregistered predictions failed. On all four domains the merged
model was **worse than the best parent**:

- zh nll 3.1975 vs the parent's < 2.1969 (prediction: beat it)
- expert nll +1.0 nat vs the parent
- legal 2.4406 vs the parent's 1.6966

The pooled forward pass **loses the weaker parent entirely** - it does not
average, it keeps the stronger. The working alternative is **routing**: masked
forward passes reproduce each parent **bit-exactly** (serving eval, 6 of 6
cells at +0.0000; training-time isolation, bit-exact over a 36 h run).

**Consequence: merging is not a scaling route. Routing is.**

## Where the data lives

```
Hugging Face:  Saga-AI-Labs/bdh-expert-merge  checkpoints/
               sha256 (LFS): expert-b1_best d130f291e5b7...
                              expert-b1_last 414d8abc9b01...
                              zh_b1_merged   9035ee14ffed...
```

## What it is good for now

Nothing active. It is the **evidence** that the pooled operator fails, and it is
the source of the negative numbers in the report. If a future merge attempt is
made, these are the baselines it must beat.

## How it ended up here

`out_c/expert_merge/` was retired 2026-11-22 as a "phantom structure". The
checkpoints were uploaded to HF and SHA-verified (3/3 OK, 2026-11-22), then
deleted locally.
