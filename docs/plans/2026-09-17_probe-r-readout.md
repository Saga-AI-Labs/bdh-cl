# Probe R — Matched-Information Residual Readout Diagnosis

Status: READY FOR FREEZE, NOT SCIENTIFICALLY SCORED · 2026-09-17 · Quinn

Operator authorization: follow-up 1 of the three probes approved after the Sonde C report update. Runner: `scripts/quinn/probe_r_readout.py`. Remote workspace: `bdh-4090:/media/data/coding/bdh`. No commits or pushes are included in this execution step.

## 1. Question and scope

Does a shallow residual readout remain inferior to a byte baseline when both receive the same input prefix and the same training crops? Compare mean pooling with the last available state, and early layers with the final layer.

This is a new controlled comparison, not a causal decomposition of the old 93.1% versus 100% result: crop length, teacher window, sampling and splits also change. A closed gap would be consistent with an information-budget explanation, not isolate it. A remaining gap would establish a limitation of the tested readout protocol, not absence of information in BDH.

## 2. Model and inputs

Checkpoint: `/var/tmp/bdh_europarl_ladRA2b-lt_last.pt`. The runner records the full checkpoint SHA256 and configuration before scoring. Expected configuration from the preparatory inspection: four layers, embedding dimension 512, eight heads, block size 512, internal multiplier 736. Runtime assertions must confirm the depth and valid candidate widths; defaults are not evidence. Abort on a configuration mismatch rather than silently changing the experiment.

Twenty Europarl languages, in runner order: en, es, pl, fr, de, cs, da, pt, fi, hu, bg, it, et, el, sk, sv, ro, nl, sl, lt.

For each language, use the loader's last-1-MB test region. Draw one deterministic start with seed `5000 + language_index`, then take 96 adjacent, nonoverlapping 96-byte crops. Record offsets, source-region identity and crop bytes. Sharing the seed convention does not make these crops identical to P-R3's randomly drawn 512-byte crops.

Per-language contiguous fold allocation: 56 training, 16 validation, 24 test crops. Totals: 1120 / 320 / 480. All methods use the same folds. Byte intervals must not overlap between folds. Adjacent crops may share documents or repeated content: this is byte-interval separation, not verified document-level independence. Previously inspected corpus material is not a wholly untouched external test population.

The draft runner also prepares separate train-region byte crops. These are unused diagnostic artifacts, not inputs to any fitted comparator; their preparation does not authorize unequal training budgets.

## 3. Targets and feature access

All methods receive exactly the same 96-byte input crop. Byte inputs remain uint8; only model tensors are converted to integer token IDs.

A2 target: minimum next-byte NLL across 23 prefix-masked routes, widths 2048 through 47104 in steps of 2048. Average prediction positions 31 through 94, targeting bytes 32 through 95. Exclude the rolled final target, which would wrap to byte zero. Restore full-width weights before residual extraction.

Extract post-layer normalized states via the checked LayerNorm hook convention, index `3 * layer + 3`, for layers 0, 1 and 3. For each layer compare:

- mean over positions 32 through 95;
- state at position 95.

These are normalized readouts, not the complete internal state. The mean includes states with shorter causal prefixes, whereas the final state can access the complete 96-byte prefix.

## 4. Fitting and evaluation

Byte comparator: fixed add-one byte-4-gram model, trained per domain on the same 56 training crops per language used by the heads. Map predicted domain to its modal A2 route using training labels only, with deterministic tie-breaking. This comparator is domain-supervised, unlike the directly A2-supervised heads. Report the supervision difference; do not describe both as exclusively label-free.

Heads: layers {0, 1, 3} × pooling {mean, last} × architecture {linear, MLP-256}: twelve fixed variants. Training recipe: Adam, learning rate 0.03, 600 steps, weight decay 0.0001, seed 0. Fit feature standardization on training folds only. Select one variant by validation accuracy; break ties lexicographically by variant name. No test-driven recipe changes.

Score the selected head and fixed byte comparator once on the 480 test crops. Report overall and per-domain correct counts, descriptive Wilson intervals, and paired discordant counts. Validation scores for all twelve variants describe the layer/pooling comparison; they are not twelve independent confirmatory test results.

Report the training-modal route selected using the true test domain as a descriptive oracle-domain reference only, not a deployable competitor. Persist per-crop predictions and labels for audit. Conditional language-specific results with small denominators are descriptive.

## 5. Interpretation and stopping rules

Primary comparison: selected-head test accuracy minus byte-comparator test accuracy. Report the measured difference and paired counts whether positive, zero or negative. No continued head search after the final test.

A higher score does not establish semantic memory addressing, novelty detection, OOD rejection or correction of the A2 teacher's Legal-depth behavior. A lower score does not establish an architectural inability to represent addresses. Comparisons between layers and pooling are scoped to the fixed training recipe and validation selection.

## 6. Verification and execution

Before scientific scoring:

- synthetic CPU end-to-end test, including all twelve variants;
- training-mask versus index equivalence and invariance to changed held-out labels;
- fold counts 1120/320/480 and exclusive fold membership;
- byte serialization, finite scores/features and valid route bounds;
- freeze protocol and runner hashes in the run directory.

Synthetic remote tests passed on 2026-09-17; logs are under `out_c/probe_r_checks/`. Their toy accuracies are not scientific results. Further fixes remain pre-measurement amendments until the frozen launch manifest is written.

Run under the shared `out_c/followup_gpu.lock`, batch 1, with unbuffered logs, incremental artifacts and an explicit exit-status file. No concurrent large GPU model loading. Leave `out/` and the Hugging Face upload untouched. A queued process is not a running measurement; report actual lock and progress state. No runtime installations, checkpoint mutation or automatic retries after OOM.
