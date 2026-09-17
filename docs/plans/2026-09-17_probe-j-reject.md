# Probe J — Independently Calibrated Byte-Router Rejection

Status: PRE-MEASUREMENT AMENDMENT, READY FOR FREEZE · 2026-09-17 · Quinn

Operator GO covers this follow-up. The earlier draft was never scientifically executed. Its incorrect ratio calculation, calibration-as-test evaluation, ambiguous domain thresholds and unavailable Inuktitut test region were identified before scoring. Synthetic CPU checks only have run. This document replaces that unexecuted draft; freeze its SHA256 with the runner before measurement. No commits or pushes are authorized by this document.

## Question

Can a fixed, independently calibrated byte-score threshold reject new text regions from the previously examined OOD languages while retaining known languages?

P-C4′ demonstrated failure of its particular reject construction. It did not isolate a causal explanation. Its six languages are now development languages, not untouched language-level tests. This follow-up tests new source regions from five of them, with an explicit missing sixth cell.

## Fixed model and score

CPU only. Reuse the add-one ByteNGram implementation from c_arms.py, with n=4 and vocabulary 256. Fit twenty domain-class models and one pooled model on training crops only. Every scoring row is uint8.

Primary score: minimum class NLL divided by input byte count. Since the implementation scores length-minus-three transitions, record this denominator convention consistently rather than calling it transition-normalized NLL.

Primary acceptance: minimum class NLL per input byte <= tau. Set tau to the 99th percentile of ID calibration scores, NumPy method='higher'. Freeze tau before any ID-test or OOD scoring. No threshold adjustment after evaluation.

Pooled/best-class NLL ratio and unseen-four-gram fraction are descriptive only. The ratio is pooled_nll / best_nll, not pooled_nll / crop_length. Neither diagnostic participates in acceptance or model selection. This single-axis primary rule is an explicit pre-measurement replacement of the faulty unexecuted two-axis draft, motivated by the known P-C4′ failure.

## ID source separation

Use the twenty Europarl source files identified by pipeline.data._europarl_blocks. Let each source length be L. Select 96 nonoverlapping 512-byte crops per language per partition from these absolute byte intervals:

- training: [L-3000000, L-2000000);
- calibration: [L-2000000, L-1700000);
- independent ID test: [L-1300000, L-1000000).

All regions are mutually disjoint and separated where appropriate; the new ID test does not use the old NPZ last-1-MB crop population. Draw aligned 512-byte slots without replacement using NumPy default_rng, seed 12000 + 100*partition_index + language_index. Hash source files and all selected crops; record absolute offsets. Assert interval disjointness and reject exact duplicate crop hashes across fitting, calibration and ID test before scoring. If duplicate content prevents the fixed sample, report a preflight blocker rather than silently changing the sample after scoring.

These sources are previously studied corpora. Nonoverlapping byte intervals do not establish independent documents or absence of repeated paraphrases. State that limitation.

Domain classification accuracy and classification accuracy conditional on acceptance are available for ID test data. Route mapping, if reported, uses only the original NPZ's designated training-label fold; never use its held-out labels. No new A2 reference labels are computed here, so route correctness on new crops is not claimed. Domain classification is not A2 agreement.

## OOD test sources

Use lv, ga, zh, ja and hi source files from P-C4′. For source length L, draw 96 nonoverlapping 512-byte aligned slots without replacement from [0, L-2000000-1048576), seed 13000 + language_index. This excludes the entire previous development tail plus a 1-MiB guard. Record source and crop hashes and absolute offsets. Check duplicate crop hashes against ID partitions before scoring. These are new regions of known development languages, not genuinely new languages or necessarily independent documents.

The clean Inuktitut source xscript_iu_syl.txt has only 126144 bytes, all within the excluded development region. Its independent OOD cell is BLOCKED, not FAIL and not silently omitted. No contaminated replacement and no fresh-data claim for its old crops. The five available cells may run without waiting for this missing source.

## Frozen readout and decisions

- J-1: independent ID-test acceptance >=0.95 overall, with per-language counts, false-reject rates and descriptive Wilson intervals. Calibration coverage is reported separately and cannot establish J-1.
- J-2: for the five evaluable OOD languages, no language has its mean primary NLL accepted by the frozen crop-calibrated threshold. Report each crop-level false-accept rate and Wilson interval as well. This domain-mean rule is an explicitly descriptive aggregation using the same threshold, not a separately calibrated domain classifier.
- J-3: ID domain-classification accuracy before and after rejection; OOD predicted-domain distributions. No OOD correctness verdict because there is no correct trained domain for an unseen language.

If any available OOD domain passes the acceptance rule, J-2 is FAIL. If all five are rejected, report PASS ON FIVE AVAILABLE CELLS with the full six-cell suite INCOMPLETE because Inuktitut is blocked. Neither outcome validates production serving or language-novelty generalization. No post-hoc score search.

## Execution and audit

Save frozen runner/protocol hashes, source/crop provenance, calibration scores and tau before final scoring. Persist per-crop scores, predictions and decisions, independent ID results, OOD results, blocked cells and explicit exit status under out_c/probe_j/. Bound CPU threads to two. Do not load BDH, acquire GPU memory, alter out/, or interfere with the upload or Probe R. Synthetic tests must cover uint8 serialization, manual likelihood equivalence, ratio arithmetic, disjoint sampling, quantile calibration and JSON serialization before launch.
