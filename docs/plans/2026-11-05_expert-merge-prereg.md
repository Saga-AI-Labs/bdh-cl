# Expert-merge preregistration v0.3 (FROZEN)

**Status:** FROZEN v0.3 · drafted 2026-11-05 (v0.1), frozen same day after review
incorporation · asb drafted, Quinn reviewed; both seats signed off (the review table
of 2026-11-05 is incorporated in full). No run has been authorised yet — freezing makes
the predictions below binding; run authorisation is separate. Fills the divergent-branch
open item of `docs/reports/2026-11-04_merge-experiments.md` (§6.3) and operationalises
the frame in `docs/notes/2026-11-04_bdh-paper-merge-claim-verified-with-caveats.md`.

v0.3 closes the optimiser-schedule gap that v0.2 left open (its miss, not a later
discovery): §2.3a now names the schedule, its selection rule and the measured probe
that chose it, and fixes the training seed. Predictions P1-P5 are unchanged.

**Changelog v0.1 → v0.2 (per Quinn's review):** branch corpus 640 MB → 15–30 MB, target
20 MB (measured step times at mult 896 make 640 MB a 20–36-day run, not 1–1.5 days);
`embed`/`lm_head` frozen in the branch so P5 bit-exactness survives the merge (documented
deviation from the paper, which averages embeddings); prune fix switched from pair-gather
to contiguous blocks (attempt 2 had correctly gathered freqs and still failed —
contiguity, not pairing, is the decisive property); P3 sharpened from ≤ 1.6966 to
≤ 1.2479 (the ancestor-descendant merge already undercut the old threshold).

**Changelog v0.2 -> v0.3:** optimiser schedule named and justified by a measured
probe (§2.3a) instead of left to the pipeline default; `min_lr` documented as the
parameter that silently reshaped arm A; training seed fixed at 1234 for B1/B2
(matched data order, so P4 isolates the fake-quant forward); probe numbers reported
for all three arms, not only the chosen one.

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
- **Q-D (instrument):** does the repaired contiguous-block prune pass its no-replay
  control?

## 2. Design

### 2.1 Parents and topology

- **Parent A (untouched):** `out_a/bdh_textmix_k25w1024-zh_last.pt` (mult 896, 2.82B).
  It participates in the merge as-is. No further training on it.
- **Branch B:** a *clone* of zh_last, fine-tuned on the expert corpus with **all
  neuron-carrying tensors trainable** (`decoder`, `encoder`, `encoder_v`, `attn.freqs`)
  and **`embed`/`lm_head` frozen**. The freeze is a deliberate, documented deviation
  from the paper protocol (which averages embeddings at merge time): a full fine-tune
  necessarily moves `embed.weight` and `lm_head`, the merge-time embedding-hash
  assertion would fail, and `merge.py` falls back to averaging — giving up P5
  bit-exactness, our strongest invariant, for a marginal gain at a 15–30 MB branch
  corpus. Freezing only the two D×V tensors does NOT recreate the frozen-grow trap:
  that trap is degenerate because the branch's *neurons* are frozen (the branch already
  is the union, merge-experiments report §5); here every neuron trains.
- **Merge:** `pipeline/merge.py` parent-A ∥ branch-B. Embedding hash equality is
  asserted at merge time; with embeddings frozen on both sides it must hold (it held
  across the whole ladder under frozen-trunk growth), the average fallback stays a
  no-op, and P5 carries over to the sibling merge.
- **Excluded by lineage rule:** `legal_last` (ancestor of zh_last), any checkpoint
  downstream of zh_last (none exists).

### 2.2 Corpus gate (before any GPU time)

- Candidate: **PG-19 / Gutenberg long prose**, **15–30 MB train split, target 20 MB**
  (~19.5k steps at 2,048 tokens/step, 2 epochs). Rationale: largest capability gap to
  the europarl-translationese trunk (narrative, long-range coherence), cleanest purity
  profile, clean licensing.
- **Why not the paper-faithful 640 MB:** measured step times at mult 896 are
  2.8–5.4 s/step (Phase 24: 5,404 ms/step route-aware). The v0.1 size collides with
  the branch budget by a factor of 15–25:

  | branch corpus | steps (2 ep) | @ 2.8 s/step | @ 5.4 s/step |
  |---|---|---|---|
  | 640 MB (v0.1) | 625,000 | 20 d | 36 d |
  | 100 MB | 97,700 | 3.2 d | 6.1 d |
  | **20 MB (target)** | **19,500** | **15 h** | **29 h** |
  | 15 MB (August replay size) | 14,650 | 11 h | 22 h |

  The smaller corpus trades capability payload for mechanism-test validity — Q-A/Q-B
  are mechanism tests, not quality claims.
- **Census gate:** `corpus_purity_census.py --scan` on the prepared split must show
  dominant-script purity p5 ≥ 0.99, anomaly Wilson upper bound < 2 %, marker rates
  recorded. Fail → re-filter, not proceed.
- **Held-out:** a fixed **2 MB tail (10 %, ≈ 4k blocks of 512)** split off *before*
  training; eval never touches train bytes.
- Note: the corpus choice optimises the *mechanism test* (max gap, min dirt), not the
  chat product. Product corpora belong to the chat prereg §6, same gate.

### 2.3 QAT A/B (branch level)

- **B1:** FP32 fine-tune (reference).
- **B2:** identical schedule and identical frozen set (embed/lm_head per 2.1),
  fake-quant forward with STE, per-level scales (QAT proposal hard rule 4).
- **Prerequisite:** the Q1 probe (0.3M, ≤ 0.1 nat gate) must be green before B2 runs —
  the proposal's ordering is binding. If Q1 fails, B2 is dropped and the merge
  proceeds FP32-only; QAT stays closed at every level.
- B1 and B2 can run in parallel on the two Sparks (15–29 h each per the table in
  2.2); otherwise B2 follows B1.

### 2.3a Optimiser schedule and training seed

v0.2 said only "identical schedule" and left the value to `pipeline/config.py`, whose
default is a from-scratch schedule (`learning_rate 1e-3`, `warmup_iters 30`,
`lr_decay_iters 300`). Applied to a converged 2.82B checkpoint that default would not
fine-tune, it would overwrite. The value is therefore named here, and it was chosen by
measurement rather than by analogy to the ladder.

**The probe.** Three arms, 100 steps each, from `zh_last` on the 20 MB Gutenberg
corpus, `--freeze-embed --weight-decay 0 --seed 1234`, batch 1, block 512. A fourth
variable was found in the process: `min_lr` defaults to `1e-4`, so any arm whose peak
is `1e-4` runs a flat cosine -- constant rate, not a slow one.

| arm | peak | warmup | decay iters | R2 (mean, steps 81-100) | min |
|---|---|---|---|---|---|
| A | 1e-4 | 20 | 100 | **1.7893** | 1.7712 |
| B | 3e-4 | 20 | 100 | 1.7550 | 1.7408 |
| C | 1e-3 | 10 | 100 | 1.7848 | 1.7714 |

**Selection rule, fixed before the arms were read** (R1-R5, adopted from the RBC-1
cycle's review): R1 disqualify any arm with NaN/inf or an end loss above its own
step-10 level; R2 metric is the trailing mean over steps 81-100; R3 among survivors
pick the **lowest peak rate whose R2 is within +5 % of the best**; R4 a tie within
0.5 % goes to the lower rate; R5 if no arm survives, the schedule stays open and B1/B2
wait rather than proceeding on a broken schedule.

**Outcome.** All three arms survive R1 (each ends well below its step-10 loss: A
2.4220 -> 1.7712, B 2.3625 -> 1.7408, C 2.2942 -> 1.7714). All three sit inside the
+5 % band (A +1.95 %, B 0.00 %, C +1.70 %). R3 therefore selects **arm A: peak
`1e-4`, warmup 20, decay 100** -- the lowest rate in the band, not the lowest loss.

**Honest limits of this probe.** (i) The A-B gap is 1.95 % on ten tail points; that is
not a resolution at which one rate can be called better, which is precisely why R3
prefers the gentler schedule instead of ranking. (ii) The lengths are calibrated to the
probe, not the branch: with `--lr-decay-iters 100` every arm reaches `min_lr = 1e-4` at
step 100, so the arms differ in the path they take, not in the regime they hold. The
branch runs ~19.5k steps and will need `lr_decay_iters` on that order. (iii) The probe
can disqualify a destructive rate; it cannot optimise one.

**Schedule for the branch.** Peak `1e-4`, warmup proportional to run length
(~500 steps for a 19.5k-step branch), cosine decay to `min_lr`, with `min_lr` set
**below the peak** (1e-5) so the decay is real rather than nominal -- the parameter that
silently flattened arm A.

**Training seed: 1234 for both B1 and B2.** The seed fixes batch order (`torch.randint`
in `get_batch`) and the dropout masks, so the two branches see the same data sequence and
the P4 comparison isolates the fake-quant forward as the only difference. This is
matched pairs, not bit-exactness: CUDA reduction order remains free to vary, so the
same seed yields reproducibly *ordered* runs, not identical ones. The eval seed being
numerically equal (1234, §2.5) is harmless -- different generators.

### 2.4 Repaired prune as instrument check (not on the critical path)

`merge_prune.py` is fixed first per `2026-11-04_merge-prune-diagnosis.md` and its
2026-11-05 addendum: prune in **contiguous blocks** (`--block`, the mechanism
`scripts/prune_eval.py` has carried since August), and **gather** the original
frequencies (`new_freqs = old[keep_idx]`), never `get_freqs(N_dst)`. Contiguity —
not pairing alone — is the decisive property: attempt 2 gathered the correct
frequencies and still failed (5.64 → 21.78 ppl) because scattered survivors present
an irregular phase sequence the model never saw. Whole contiguous blocks preserve
both the pair structure and the local phase ladder. Block size fixed at **8** before
the control runs (even ⇒ pairs never straddle a block boundary; small ⇒ selection
granularity). A pair-wise sorted gather remains theoretically equivalent but untested
and is not part of this prereg.

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
- **P3 (capacity direction survives, sharpened per review):** merged on legal ≤
  **1.2479** — the merged-legal nll of the *ancestor-descendant* merge. The v0.1
  threshold (zh_last's own 1.6966) was already undercut by that flawed merge
  (1.2479), so clearing it would establish nothing beyond the broken merge; the
  sibling merge must match or beat the confounded merge on legal territory. If
  violated, the width gradient was a ladder-lineage artifact, not width — that would
  also revise RBC-1 v0.2's reading.
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

~half a day CPU (corpus + census), 15–29 h GPU per branch at the measured step-time
band (parallel on two Sparks), <1 h merge+eval, <1 h prune control. Whole experiment
≈ **2 days on two Sparks** — a fraction of the two-branch §6.3 design, with a
capability payload instead of a synthetic split.

## 7. Reproduce

```
# corpus gate
.venv/bin/python scripts/corpus_purity_census.py data/expert/pg19_train.txt --scan
# branches (embed/lm_head frozen per 2.1; corpus 20 MB, held-out tail split off first)
python -m pipeline.run finetune --ckpt out_a/...-zh_last.pt --data data/expert/pg19_train.txt ...
# merge + eval
python -m pipeline.merge --ckpt-a out_a/...-zh_last.pt --ckpt-b out_c/expert_b1.pt ...
python scripts/quinn/merge_probe_eval.py --models ...-zh_last.pt ...expert_b1.pt ...merged.pt \
  --domains expert:data/expert/pg19_heldout.txt zh:data/europarl/xscript_zh.txt \
  legal:data/textmix2/legal.txt code:data/textmix2/code.txt \
  --mb 30 --crops 200 --block 512 --batch 2 --out out_c/expert_merge/eval.json
# prune control (fixed script: contiguous blocks, gathered freqs)
python scripts/quinn/merge_prune.py --ckpt out_a/...-zh_last.pt --target-mult 448 \
  --domains legal:... zh:... --order importance --block 8 \
  --out out_c/expert_merge/zh_pruned448_blocks8.pt
```
