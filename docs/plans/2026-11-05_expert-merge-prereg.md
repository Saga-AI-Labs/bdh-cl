# Expert-merge preregistration v0.1 (DRAFT)

**Status:** DRAFT v0.1 · drafted 2026-11-05 · asb (assistant-drafted; freezes only after
both seats sign off). No run has been authorised. Fills the divergent-branch open item
of `docs/reports/2026-11-04_merge-experiments.md` (§6.3) and operationalises the frame
in `docs/notes/2026-11-04_bdh-paper-merge-claim-verified-with-caveats.md`.

## 0. The story in one paragraph

The merge probe showed that fusion is cheap and P5-exact but that merging an ancestor
with its descendant dilutes (legal +0.19, zh +0.47 nats) through trunk duplication and
cross-talk. The paper's protocol — siblings diverging from a shared base — is untested
at our scale. This prereg runs the cheapest faithful version: keep `zh_last` as an
untouched parent, fine-tune a *clone* of it on long prose, merge the two, evaluate
against both parents. It doubles as the first at-scale QAT evidence (FP32 branch vs
fake-quant branch) and validates the repaired prune instrument. One experiment, three
purposes: topology test, QAT preview, tooling gate.

## 1. Questions

- **Q-A (topology):** does a sibling merge beat the measured ancestor-descendant merge
  at matched eval? (Ancestor-descendant reference: merged zh nll 2.1969, legal 1.2479.)
- **Q-B (capability):** does the merged model gain the expert capability at bounded
  home-territory cost?
- **Q-C (QAT):** does fake-quant branch training hold ≤ 0.1 nats against its FP32
  twin at 2.82B scale? (Q2-flavoured evidence; the QAT proposal's Q1 gate remains a
  prerequisite — see 2.3.)
- **Q-D (instrument):** does the repaired pair-gather prune pass its no-replay control?

## 2. Design

### 2.1 Parents and topology

- **Parent A (untouched):** `out_a/bdh_textmix_k25w1024-zh_last.pt` (mult 896, 2.82B).
  It participates in the merge as-is. No further training on it.
- **Branch B:** a *clone* of zh_last, **full fine-tune (all neurons trainable**,
  paper protocol) on the expert corpus. Freezing is explicitly out: a frozen-grow
  branch already *is* the union, and the merge degenerates (ancestor-descendant trap,
  merge-experiments report §5).
- **Merge:** `pipeline/merge.py` parent-A ∥ branch-B. Embedding hash equality is
  asserted again at merge time (it held across the whole ladder).
- **Excluded by lineage rule:** `legal_last` (ancestor of zh_last), any checkpoint
  downstream of zh_last (none exists).

### 2.2 Corpus gate (before any GPU time)

- Candidate: **PG-19 / Gutenberg long prose**, ~640 MB train split (~paper-faithful
  branch size; ~1.2B tokens ≈ 2 epochs). Rationale: largest capability gap to the
  europarl-translationese trunk (narrative, long-range coherence), cleanest purity
  profile, clean licensing.
- **Census gate:** `corpus_purity_census.py --scan` on the prepared split must show
  dominant-script purity p5 ≥ 0.99, anomaly Wilson upper bound < 2 %, marker rates
  recorded. Fail → re-filter, not proceed.
- **Held-out:** a fixed 10 MB tail split off *before* training; eval never touches
  train bytes.
- Note: the corpus choice optimises the *mechanism test* (max gap, min dirt), not the
  chat product. Product corpora belong to the chat prereg §6, same gate.

### 2.3 QAT A/B (branch level)

- **B1:** FP32 fine-tune (reference).
- **B2:** identical schedule, fake-quant forward with STE, per-level scales (QAT
  proposal hard rule 4).
- **Prerequisite:** the Q1 probe (0.3M, ≤ 0.1 nat gate) must be green before B2 runs —
  the proposal's ordering is binding. If Q1 fails, B2 is dropped and the merge
  proceeds FP32-only; QAT stays closed at every level.
- B1 and B2 can run in parallel on the two Sparks (~1 day each); otherwise B2 follows
  B1.

### 2.4 Repaired prune as instrument check (not on the critical path)

`merge_prune.py` is fixed first per `2026-11-04_merge-prune-diagnosis.md`: keep
neuron **pairs** (both members, adjacent, even/odd roles intact), gather the original
frequencies (`new_freqs = old[keep_idx]`), never `get_freqs(N_dst)`.

- **Control (no replay):** unmerged `zh_last` 896→448 must land ≤ 7.0 ppl on both
  legal and zh (mild term-removal band). Fail → the instrument is still broken; the
  merge eval proceeds anyway, and prune-based remedies stay closed.

### 2.5 Evaluation protocol

`merge_probe_eval.py`: protocol crops (seed 1234, block 512, 200 crops, mb 30),
full-block NLL without routing; models = parent-A, branch-B1, branch-B2 (if run),
merged; domains = expert held-out, zh (`xscript_zh.txt`), legal (`textmix2/legal.txt`,
prose proxy), code (`textmix2/code.txt`, out-of-scope guard). Protocol-mode census rows
are joined per crop as covariates (RBC-1 v0.3 practice).

## 3. Predictions (falsifiable)

- **P1 (sibling beats ancestor-descendant, strict):** merged zh nll **< 2.1969**.
  Mechanism: no bit-exact trunk duplication; zh neurons pristine in parent-A.
- **P1b (home band, soft):** merged zh nll ≤ 1.7306 + 0.30 = **≤ 2.03**. The paper's
  comprehension band (+0.04–0.07) does not directly map to LM-on-home-language; its
  production-side analogue degraded +0.46 — hence the band, and why P1 is the strict
  claim.
- **P2 (capability lands):** merged on expert held-out ≤ branch-B1 + **0.15 nats**
  (zh neurons rarely crack the pooled top-k on English prose).
- **P3 (capacity direction survives):** merged on legal ≤ zh_last on legal
  (nll ≤ 1.6966). If violated, the width gradient was a ladder-lineage artifact, not
  width — that would also revise RBC-1 v0.2's reading.
- **P4 (QAT gate):** B2 vs B1 ≤ **0.1 nats** on the same protocol (QAT proposal gate,
  now at bridge scale).
- **P5 (instrument):** repaired-prune control ≤ **7.0 ppl** both domains, no replay.

## 4. Decision table

| outcome | consequence |
|---|---|
| P1, P2 hold | sibling merge is the validated scaling move; chat prereg §4.3 gains the measured pooled-k dilution figure; product plan may branch-and-merge |
| P1 holds, P2 fails | cross-talk dominates even for siblings → §4.3 resolves toward **routed routes** (isolation beats pooled budget); merge stays a research instrument |
| P1 fails | sibling assumption wrong at our scale; the 7-day two-branch design (report §6.3) is the next escalation, not the product |
| P4 holds | QAT at branch level suffices; no from-scratch QAT base needed (chat base may stay FP32-trained, quant finished in replay) |
| P4 fails | from-scratch QAT base becomes justified — *then* the new-base question from 2026-11-05 discussion is answered by measurement |

## 5. What this does not establish

- No dialogue/chat-quality claim (§4.4 metric undefined; no dialogue corpus here).
- No claim about merged models under routing (pooled-k vs routed-k measured here only
  as dilution, not as a router comparison).
- No scaling-law claim from one sibling pair.
- No Q3 claim (end-to-end quant of merged *and pruned* artifacts stays open until the
  prune control passes).

## 6. Cost

~half a day CPU (corpus + census), ~1–1.5 days GPU per branch (parallel: 1.5 days
total), <1 h merge+eval. Whole experiment ≈ **2–3 days on two Sparks** — roughly a
third of the two-branch §6.3 design, with a capability payload instead of a synthetic
split.

## 7. Reproduce

```
# corpus gate
.venv/bin/python scripts/corpus_purity_census.py data/expert/pg19_train.txt --scan
# branches
python -m pipeline.run finetune --ckpt out_a/...-zh_last.pt --data data/expert/pg19_train.txt ...
# merge + eval
python -m pipeline.merge --ckpt-a out_a/...-zh_last.pt --ckpt-b out_c/expert_b1.pt ...
python scripts/quinn/merge_probe_eval.py --models ...-zh_last.pt ...expert_b1.pt ...merged.pt \
  --domains expert:data/expert/pg19_heldout.txt zh:data/europarl/xscript_zh.txt \
  legal:data/textmix2/legal.txt code:data/textmix2/code.txt \
  --mb 30 --crops 200 --block 512 --batch 2 --out out_c/expert_merge/eval.json
# prune control (fixed script)
python scripts/quinn/merge_prune.py --ckpt out_a/...-zh_last.pt --target-mult 448 \
  --domains legal:... zh:... --order importance --out out_c/expert_merge/zh_pruned448_fixed2.pt
```
