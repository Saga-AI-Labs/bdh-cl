# Probe S — factual addressing under shared language templates

Status: PREMEASUREMENT AMENDMENT A2, 2026-09-17. Operator-authorized implementation
and launch only; no commits, pushes, installations, HAK messages, or R/J reruns.

## Correction record

The committed draft at 3108ea7 was NOT execution-ready. This amendment replaces it
and the malformed, unexecuted local A1 addition. No scientific S scoring preceded
this amendment. The old draft remains recoverable from Git; no old claims survive
by implication. Corrections: the primary byte router is content-aware, never a
ceiling; routing is query-only; a byte is not a word; oracle A is old-only;
arbitrary unseen bindings and underspecified Q-comp are removed; factual keys
uniquely determine territory; budgets and evaluation are fixed below. Q-comp is
explicitly deferred to a separate protocol establishing answerability.

## Question and interpretation

Can query likelihood select the territory containing an acquired fact when both
territories share language, templates, and balanced component vocabularies?
This is a closed-world recall/withheld-paraphrase test, not semantic-only evidence.
Surface conjunction association can solve it. No guarantee excludes that solution.
Two primary routes, equally many A/B queries: chance routing accuracy = 0.5.

## Deterministic facts and splits

All text is lowercase ASCII. Corpus seed 17092026; base model seed 17092027;
growth seed 17092028. Sampling uses independent torch generators with model seed
+10 (train) and +20 (validation). Manifest order is deterministic.

Entity vocabulary is the 32 words `m` + two letters, from `maa` through `mbf`;
relation vocabulary is the 16 words `r` + two letters, `raa` through `rap`;
answer vocabulary is the 64 words `v` + two letters, `vaa` through `vcl`.
Cartesian entity/relation pairs define 512 distinct factual keys. Seeded random
permutations of entity and relation indices assign A when the sum of permuted
indices is even, B otherwise. Each entity and each relation occurs equally often
in A/B. There are 256 facts per territory. Each of the 64 answers occurs four
times per territory, independently shuffled with the corpus RNG. Bindings have
no compositional derivation. A fact has one answer globally and no territory token.

Every fact is trained in both templates (512 distinct rows per territory):

- T1: `the {relation} of {entity} is {answer}.`
- T2: `for {entity}, {relation} has value {answer}.`

Each row begins with a newline (context start) and ends at the period. Padding
uses byte zero as input and target -100 (ignored loss); it never adds another fact.
Batches sample rows uniformly with replacement. Every row and every model call
has fresh state; no context is carried across facts.

Calibration/validation: first 32 facts of each territory, template
`{entity} has {relation} equal to {answer}.` (64 rows total). These are known
bindings under a withheld template, NOT unseen facts. They are monitoring only;
no thresholds, parameters, checkpoints or budgets are selected from them.
Pipeline validation uses 4 batches every 500 steps and at phase end, always
full-width, including during growth. This is descriptive, not the B oracle.
No test data is exposed to the pipeline loader (`test=None`).

Test: all trained facts, each under two withheld templates (1024 queries total,
512 per territory):

- P1: `for {entity}, the value of {relation} is `
- P2: `the value for {relation} of {entity} is `

Seen-template acquisition controls: T1/T2 prefixes for every fact (1024 queries).
Calibration and test query strings are disjoint from each other and training
prefixes. Test answers must exactly match manifest training bindings. No separate
unseen-binding split is scored. Manifests persist full texts, prefixes, bindings,
territories, template IDs and split labels before training.

## Frozen training recipe

Directly call `pipeline.train.train(Config(...))` twice. Only its imported
`load_dataset` is replaced in-process by a one-fact-per-row adapter; model creation
and checkpoint saving are wrapped for assertions, without altering updates.
No copied growth implementation and no core edits. The byte-stream/MB loaders
cannot enforce these row boundaries. This adapter deviation is explicit; it is
not a claim of parity with the ordinary stream dataset or its learning curves.

BDH: 2 layers, embedding 256, 4 heads, vocabulary 256, base multiplier 128;
grow increment +32, final multiplier 160. Per-head routes: A indices [0,8192),
B [8192,10240). Block budget 128; batch 8, dynamically right-padded within batch
(no sequence exceeds the block budget). Dropout 0, k_sparse_ratio 0, ALiBi 0,
no_bptt false, carry_state false, sequential_batches false, TBPTT horizon 1.
CUDA bfloat16 autocast, float32 parameter storage; compile false; TF32 disabled.
AdamW learning rate 0.001, cosine to 0.0001, warmup 100 steps, betas (0.9,0.95),
weight decay 0.1, gradient clip 1.0. Cosine horizon equals phase budget.
Base = exactly 4000 steps on A; grown = exactly 2000 steps on B. No early stop,
no retry after scientific scoring, no tuning from real test or smoke acquisition.
Use fixed `last` checkpoints only; pipeline `best` files are unused artifacts.
Growth freezes embed/head and attention, preserves the old frequency lattice,
uses gradient masks plus step-end restore. Route-aware alpha=1.0: B-only loss.
The pipeline still computes a full-width loss multiplied by zero; this extra
forward is retained for actual code-path reuse and must remain finite.

## Routing and full-answer scoring

Both routers receive IDENTICAL complete answer-free query bytes, including initial
newline and trailing space. Neither receives the answer, label or territory.
A2 minimizes mean next-byte NLL of query bytes 1..end conditioned on their preceding
query bytes, over A and B only. Byte router: separate order-5 byte models (4-byte
context, reset at each row), add-0.1 smoothing over all 256 bytes, trained on full
training rows, scored on the same query positions; ties select A. All conversion
into the byte router is explicitly numpy uint8. No content-blinded primary arm.

After selecting routes, use the grown BDH under oracle, A2-selected and byte-selected
masks to generate the full answer greedily. Full width is descriptive only. These
are routing comparisons with a SHARED reader, not different language-model readers.
Stop at the first `.` or after 16 generated bytes including delimiter; exact success
requires the generated bytes to equal `answer + '.'`, with no stripping or case
normalization. Missing delimiter, extra bytes or one correct initial byte is failure.
No state leaks across queries; autoregressive generation may only use its own query
and generated prefix. Conditional full-answer NLL (including period) is descriptive,
computed AFTER routing and never used for route selection. Persist both candidate
predictions/NLLs so wrong-route controls are available, plus full-width outputs.

## Gates and failure labels

- Acquisition: seen-template oracle exact accuracy >=0.80 in EACH territory.
  If base seen-template control fails, label base acquisition failure. If A passed
  before growth but fails after growth, label retention failure. Failed B acquisition
  cannot establish a routing failure.
- P-S1 transfer/availability: oracle paraphrase exact accuracy >=0.80 per territory.
  If acquisition passes but P-S1 fails, label paraphrase transfer failure, NOT storage
  failure. Routing scores may still be reported descriptively, not interpreted as
  an addressing failure despite available recall.
- P-S2: A2 routing accuracy >=0.85 pooled, with per-territory values reported.
  <=0.60 is a prespecified routing falsifier ONLY if acquisition and P-S1 pass.
- P-S3: report byte routing and shared-reader exact accuracy alongside A2. If byte
  routing >= A2 routing, or byte-routed exact accuracy >= A2-routed exact accuracy,
  no advantage over this surface baseline is established (surface-resolvable caveat).
- P-S4 retention: post-growth A seen-template oracle accuracy >=0.75. Also report
  pre/post A seen-template and paraphrase accuracy, with full-width descriptive.
- S-PASS requires acquisition, P-S1 and P-S2. It does not establish semantic-only,
  scalable or chat-grade addressing. All failures remain results, not retry triggers.

## Mechanics gates and bounded smoke

Smoke uses ONLY separate toy vocabularies (`taa` entities, `uaa` relations, `waa`
answers and following words), seed 717, 8 facts total. Two checks: tiny model
(embedding 16, heads 2, base mult 4, growth +2) at 2 base +2 growth steps; then
production shape/batch/dtype at 2+2 steps. Wall-clock cap for entire smoke =900 s.
It checks mechanics, not accuracy or tuning. If production shape is infeasible,
stop and report; do not silently downsize the scientific run.

Required checks: full-answer exact scoring against a deterministic synthetic
predictor (multi-byte wrong-answer and missing-delimiter negatives); full-answer NLL
alignment; changed withheld answers cannot change either router; uint8 roundtrip
and rejection of int64; exact mask coverage/disjointness; no train/test query
intersection; every test answer justified by a training fact; finite losses;
fresh-state calls; actual AdamW old-gradient masking, observable decay before
restore, bit-exact old tensors after restore, changed new tensors; exact unchanged
embed/head/frequencies. Assertions run on the actual pipeline path, including
checking frozen tensors at subsequent batches/checkpoints. Old-route functional
comparison is SEPARATE from tensor equality: float32 logits on fixed control
prefixes before versus after growth, atol=0.0001, rtol=0.0001, with maximum absolute
difference logged. Masks must not be assumed to yield bit-identical floating-point
reductions. No exact pipeline parity claim beyond the directly tested code path.

## Launch and artifacts

Inspect remote GPU and processes; refuse duplicate S. Acquire nonblocking exclusive
`out_c/followup_gpu.lock` before any model loading and retain it through training,
evaluation and final artifacts. Smoke also holds this lock. Run with remote
`bdh-4090:/media/data/coding/bdh/.venv/bin/python`.

Before training freeze source/protocol hashes, Configs, corpus/query JSON manifests,
uint8 corpus binaries, dependency inventory/hash, host/runtime details and original
Git revision/dirty status under timestamped `out_c/probe_s/`. Verify successful
smoke attestation binds the same source/protocol hashes before real launch.
Store per-query JSONL incrementally, checkpoints, structured phase events, logs,
checks JSON, PID, running status and final exit_status.txt. Exit 0 means execution
completed, not scientific S-PASS. On failure persist traceback and nonzero exit.
Verify a real worker PID AND increasing training steps after detached launch.
Leave `out/`, HF uploads and R/J untouched. No commits, pushes or installations.
