# Merge experiments on BDH-CL: what worked, what did not

**Date:** 2026-11-04
**Question:** can two BDH-CL models be fused by neuron-dimension concatenation, and
is that a route to models larger than one machine can train?
**Short answer:** the merge itself works and is cheap. The follow-up step that the
August report relies on (prune back to a smaller width) did **not** work in this
session, and the reason is a difference between zeroing and slicing that I got wrong
three times before spotting it.

## 1. What the paper reports

`arXiv:2509.26507`, Section 6, plus Appendix `sec:bdh_merge_details`. Two branches are
trained from a **shared base** on disjoint language pairs, then fused:

```
        BaseEnEs  (n=24576, 19M params)
       /        \
   En-Fr        En-Pt            (clones, disjoint data)
       \        /
      MergedEnEsFrPt  (n=49152, 38M params)
```

Procedure: concatenate all tensors carrying the neuron dimension `n` (decoder,
encoder, encoder_v, RoPE frequency buffers); average everything without it (token
embeddings, lm_head). No finetuning for the reported numbers.

Their result: translation **into** English works for all three source languages;
translation **out of** English mixes the three. Their verdict is "human-like
degradation", repaired by "a small amount of training on all language pairs".

## 2. Our merge: works, cheap, P5 intact

`pipeline/merge.py` (since `22f7276`) implements exactly that procedure. Merging the
K25/W1024 phase checkpoints `legal_last` (mult 832) and `zh_last` (mult 896):

| step | time |
|---|---|
| load both via mmap | 0.0 s |
| `merge_checkpoints` | 1.9 s |
| build target model, save | 32 s |
| **total** | **34.2 s** |

Result: mult 1728, neurons 851,968 + 917,504 = 1,769,472, **5,436,342,272 parameters**,
21.75 GB in fp32.

Two facts make this cleaner than the paper's case:

**The embeddings are bit-identical across phases.** `embed.weight`
(`18b20147a9d10916`) and `lm_head` (`ea82b898ae9956d5`) hash the same in `legal_last`
and `zh_last`. The averaging step is therefore a no-op, and **P5 is not touched** -- a
concern I raised before measuring and which turned out to be unfounded for
cloned-from-one-base models.

**The merge is structurally exact.** Every shape checked: encoder/encoder_v
(16, 1024, 53248) + (16, 1024, 57344) -> (16, 1024, 110592); decoder
(851968, 1024) + (917504, 1024) -> (1769472, 1024). N per head for mult 1728 is
1024 * 1728 / 16 = 110,592. It closes.

## 3. Our merge: what it does to quality

Evaluated with the protocol crop sampling from `eval_router.py` (seed 1234, block 512,
200 crops per domain, full-block NLL **without routing**), 1617 s on one GB10:

| model | mult | params | legal ppl | zh ppl |
|---|---|---|---|---|
| `legal_last` | 832 | 2.62B | **2.88** | 40.74 |
| `zh_last` | 896 | 2.82B | 5.46 | **5.64** |
| `merged` | 1728 | 5.44B | 3.48 | 9.00 |

**The merge is neither a union nor a duplicate.** I had predicted it would duplicate
(zh_last already contains phases 1-24, legal_last 1-22, so the shared 22 phases would
appear twice) and therefore match `zh_last`. That prediction was wrong on both sides:

- On legal it **recovers capacity**: 5.46 -> 3.48. The legal half of the neurons is not
dead weight; it carries.
- On zh it **loses more than the paper reports**: 5.64 -> 9.00, +3.36 nats against the
  paper's +0.23 to +0.30 for the last-trained language.

The mechanism is cross-talk, not embedding noise: in the forward pass
`x @ self.encoder` runs over **all** 110,592 neurons, so the legal columns activate on
zh text and their decoder rows add to the output. With identical embeddings there is no
averaging penalty, and the interference arrives through encoder/decoder instead.

## 4. Prune + replay: three attempts, three failures

The August report (`2026-08-25_cl-h1-report.md`, Addenda 5, 8, 9) reports that
merge -> prune to a budget -> tiny replay finetune reaches near-joint quality at
original width: five languages at 2.55-2.87 ppl, from a merge that had degraded to
10.20 / 13.92 / 4.61 unrecovered.

I tried to reproduce that step and failed three times in one evening. The failures are
worth recording because each one was a different mistake.

### Attempt 1: slice encoder/encoder_v/decoder AND attn.freqs (crash)

`attn.freqs` is a single buffer of shape (1, 1, 1, N) shared across heads, so a
per-head index set cannot be represented in it. The script crashed on a 5-D/4-D
mismatch before writing anything.

### Attempt 2: shared index set, freqs sliced (bug)

Fixed the shape by keeping the same positions in every head. Wrote
`merged_pruned896.pt` (mult 896, 2,819,096,576 params -- exactly `zh_last`'s shape) and
evaluated:

| model | legal | zh |
|---|---|---|
| `zh_last` (reference) | 5.46 | **5.64** |
| `pruned896` | 11.54 | 41.31 |

Slicing `attn.freqs` removes rotation phases: every surviving neuron keeps its index
but the phase it multiplies against shifts. The **control test that exposed it**: the
same slicing applied to the UNMERGED `zh_last` (896 -> 448) gave legal 14.43 / zh
21.78. A model that was never merged lost two thirds of its quality. The bug was mine,
not the merge's.

### Attempt 3: freqs recomputed instead of sliced

Recomputed the buffer for the target width via `get_freqs(N_dst)`:

```
attn.freqs recomputed for N=28672 (was N=57344);
first 4 phases: [0.159155, 0.159155, 0.158725, 0.158725]
             -> [0.159155, 0.159155, 0.159032, 0.159032]
```

The control test got **worse**: `zh_pruned448_fixed` gave legal 18.36 / zh 57.48
against 14.43 / 21.78 for the sliced version. So freqs was one of at least two errors.

### The mistake underneath all three

The August pruning used `scripts/prune_eval.py`, which **zeroes** rather than slices:

```python
model.encoder.data.copy_(enc_b * flat.view(nh, 1, N))   # multiply by 0/1 mask
model.decoder.data.copy_(dec_b * flat.unsqueeze(1))
```

The config stays at the original mult. The model still computes over 57,344 neurons;
some are silent. RoPE phases are untouched because the width does not change. **The
August recovery numbers were never measured on a physically narrower model.**

My slicing produces a different architecture. Whether a sliced-and-replayed model can
reach the August figures is unknown and untested; what is now clear is that my three
attempts measured my own bugs, not a property of pruning.

## 5. What this means for the 10T question

The 10T target is not reachable by counting checkpoints, and the arithmetic is simple.

Each merge adds widths linearly, so seeding from 2.82B models:

| merges | mult | params | bf16 |
|---|---|---|---|
| 2 | 1,792 | 5.64B | 0.01 TB |
| 16 | 14,336 | 45.1B | 0.09 TB |
| 64 | 57,344 | 180.4B | 0.36 TB |
| 354 | 317,891 | 1.0T | 2.0 TB |
| 3,546 | 3,178,914 | 10.0T | **20.0 TB** |

Disk at 10T in bf16: 20 TB (`.52` has 3.7 TB, 2.4 TB free). Training time at ~2 days
per 2.82B model: **19 years** serially, ~9.5 years on two Sparks. Disk is not the
binding constraint; training time is.

A realistic four-week campaign on two Sparks reaches roughly **180B parameters** (64
merges, 0.36 TB). That is larger than GPT-3 and still nowhere near 1T.

**The structural requirement is more important than the arithmetic.** A useful merge
fuses **branches that diverge from a shared base on disjoint data**. Merging two linear
phases of one ladder duplicates what they already share; my measurement confirms it
does not add clean capacity, only cross-talk. The paper's En-Fr and En-Pt branches are
siblings; our legal_last and zh_last are ancestor and descendant.

## 6. Open items

1. **Prune + replay is unvalidated at this scale.** The August figures came from
   zeroing at original width. Whether slicing to a smaller width can be repaired by
   replay is an open measurement, not a known result.
2. **Cross-talk has no measured remedy yet.** Pruning is the candidate (remove the
   interfering neurons); it is untested because the tooling failed.
3. **A divergent-branch experiment would cost ~7 days on two Sparks** (two branches of
   8 phases each from the phase-22 checkpoint) and is the only way to test whether
   merging buys capacity rather than interference.
4. **The one clean positive:** merge is 34 s, P5-exact, and needs no finetuning to
   produce a working model. Whatever the branch design turns out to be, the fusion
   primitive itself is cheap and correct.

## 7. Reproduce

```
# merge
python -m pipeline.merge  # or the snippet in section 2

# evaluate parents and merged
python scripts/quinn/merge_probe_eval.py \\
  --models out_a/...-legal_last.pt out_a/...-zh_last.pt out_a/...-legalzh-merged.pt \\
  --labels legal_last zh_last merged \\
  --domains legal:data/textmix2/legal.txt zh:data/europarl/xscript_zh.txt \\
  --mb 30 --crops 200 --block 512 --batch 2 --out out_c/merge_probe/eval.json

# prune (CURRENTLY BUGGY - see section 4)
python scripts/quinn/merge_prune.py --ckpt <merged.pt> --target-mult 896 \\
  --domains ... --order random --out <pruned.pt>
```

The prune script carries the bug history in its docstring so the next reader does not
repeat it.
