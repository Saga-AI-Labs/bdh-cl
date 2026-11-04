# BDH paper merge claim: verified at 38M, with four caveats; interpretation frame for the in-house merge probe

**Date:** 2026-11-04
**Addressed to:** the author of `docs/plans/2026-11-03_chat-model-prereg.md`; same seat runs the merge-probe eval.
**Evidence:** arXiv 2509.26507 ("Dragon Hatchling", BDH), TeX source `https://arxiv.org/src/2509.26507` — Section "Model merging: concatenating two models" and Appendix "BDH Merging Experiment Details". All numbers below are quoted from that source.
**Status:** note. Documents a literature check prompted by an interview statement (co-author A. Kosowski: one can "just concatenate" separately trained English and French models, and "because of the sparse activation, it just works"). Reports no experiment of ours.

## What the paper actually reports

Protocol (Section + Appendix table, quoted):

1. **BaseEnEs**: 19M parameters (n=24576 neurons, d=256, 8 layers, 4 heads), trained
   from scratch on En-Es Europarl, 1.2B tokens (~2 passes over 612 MB).
2. **Clone** the base; continue training one clone on En-Fr (640 MB), one on En-Pt (616 MB).
3. **Merge**: concatenate every parameter tensor that has an `n` dimension (`W_y`,
   `W_x`, encoder, RoPE frequency buffers) along `n`; **average all other parameters**
   (token embeddings, token prediction weights). Result: n=49152, 38M parameters.
4. Evaluate **without any post-merge training or finetuning**.

Results (validation NLL, Table `model_merging_esfrpt`):

| model | Es→En | Fr→En | Pt→En | En→Es | En→Fr | En→Pt |
|---|---|---|---|---|---|---|
| specialists | 0.36 | 0.36 | 0.34 | 0.35 | 0.31 | 0.33 |
| **merged (Fr ∥ Pt)** | 0.43 | 0.40 | 0.39 | **1.45** | **0.77** | **0.86** |

- **Comprehension (X→En) merges free**: functional on all three pairs, mild dilution
  (+0.04–0.07 NLL vs the specialist).
- **Production (En→X) does not**: 2.3–4× worse loss, qualitative language mixing. The
  paper states a *small amount of joint training on all pairs* restores proficiency.

The architectural identity behind this is explicit: "a composition of models, obtained
by concatenation, is also a model in the same architecture, with a larger value of n" —
BDH scales uniformly in one dimension (d, layers, heads stay fixed; the paper trains
25M–800M all at d=256, varying only n).

## Four caveats against the interview reading

1. **"Separately trained" is not what was tested.** Both merged models are fine-tunes
   of the *same base* (shared init, shared En-Es history). Merging two from-scratch,
   independently trained models is never attempted in the paper.
2. **"It just works" holds only for the comprehension direction.** For an en-de-zh chat
   model, production (en→de, de→…) is the direction users exercise — and that is the
   direction that breaks without a brief joint pass.
3. **Scale: 38M, toy.** No merge experiment near LLM scale anywhere in the paper. The
   paper's largest *trained* model is 800M (n=1048576, d=256); scaling laws (10M–1B)
   are validated on translation, not chat.
4. **The mechanism is not isolated.** "Because of the sparse activation" is plausible
   (ρ≈5% ReLU activation, emergent Newman modularity, monosemantic synapses), but no
   ablation separates sparsity from the shared-base effect. The hoped-for "more is
   different than a sum of its parts" remains a hope: the data show additivity with
   dilution, not synergy.

## Connection to this repo

- The K25 grow-and-freeze ladder is the **sequential sibling** of this merge (growth
  along the same n dimension, shared training continuum, frozen phases) — and better
  instrumented than the paper's experiment: the five-domain capacity monotonicity
  (RBC-1 v0.2; all ρ negative, wider = better off-domain) is the same property the
  paper demonstrates for 2 shards at 38M.
- Merge does **not** lift the per-run training memory limit (merging two 400M models
  requires training two 400M models). It buys wall-clock parallelism and post-hoc
  language/domain addition. Candidate phase-2 option for the chat prereg: clone the
  chat base, specialize on purity-audited corpora, concatenate, then a short joint
  pass for the production direction.
- Irony worth recording: the paper merges on **Europarl** — the corpus family whose
  label lies we documented today (RBC-1 v0.3, crop 91; confirmed in
  `rbc1-v03-zh-numbers-confirmed.md`). At 19M parameters a crop-91 is invisible; at
  700M it is not. Corpus purity is a precondition for merge experiments too, not only
  for routing interpretation.

## Interpretation frame for the in-flight merge probe (written before results)

`out_a/bdh_textmix_k25w1024-legalzh-merged.pt` (built 2026-11-04 from `legal_last` and
`zh_last`; evals against both parents on legal and zh in flight). Three preregistered
expectations if the paper's claim transfers to this stack:

1. **Home territory:** merged NLL within ~0.1 nats of each parent on its own corpus
   (paper dilution at 38M: +0.04–0.07).
2. **Off-domain:** the merged stack is the widest configuration yet; capacity
   monotonicity predicts it scores **better than both parents on foreign territory**.
3. **Failure mode to watch — lineage:** in the K25 chain, `legal_last` is an
   *ancestor* of `zh_last` (zh grew after legal; frozen phases are bit-exact, P5). A
   naive concat therefore duplicates the shared frozen prefix [0..53248] — the paper
   never merged an ancestor with its descendant. If the probe shows home-territory
   dilution well beyond 0.1 nats or asymmetric legal/zh behaviour, check whether the
   merge deduplicated the shared prefix (bit-compare block [0..53248] against
   [57344..110592]) before interpreting the result as a merge failure. What the probe
   actually tests — the paper's protocol (shared-base fine-tunes) or the untested
   variant (ancestor ∥ descendant) — depends on this.

If the probe holds points 1–2, the chat prereg gains a validated option: languages can
be *added* to a grown stack by clone-tune-concatenate plus a short joint pass, and the
per-run hardware limit stops being the stack-size limit.
