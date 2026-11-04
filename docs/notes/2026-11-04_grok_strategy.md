# Grok strategy note on BDH merging (external opinion)

**Date received:** 2026-11-04
**Author:** Grok (external model, not a project agent)
**Status:** filed for reference. Not an amendment, not a measurement.
**Editorial note (Quinn, 2026-11-04):** the analysis is sound on the central points and
agrees with our own measurements. Two corrections: the paper's merging experiment is
Section 6 (not 7.1), and the merged model there is 38M parameters -- our own merge of
two K25/W1024 checkpoints produced 5.44B, and the measured interference is larger than
the paper reports (+3.36 nats on the later phase rather than the paper's +0.23 to
+0.30). See `docs/reports/2026-11-04_merge-experiments.md` for our numbers.

---

**Yes, the BDH architecture's design makes domain-specific training + merging a plausible path toward larger, more capable models under local hardware constraints--but with important limitations and caveats from the paper.** It is not yet a fully demonstrated "scale-for-free" method at large sizes, and post-merge behavior needs careful handling.

### What the paper actually shows about merging
In Section 7.1 ("Model merging: concatenating two models"), the authors demonstrate a simple concatenation procedure on small (~19 M parameter) BDH-GPU translation models:

- Train a base model on one language pair (En-Es, \(n = 24576\) neurons).
- Continue-train clones on other pairs (En-Fr and En-Pt).
- Merge by **concatenating** all tensors that have an \(n\)-dimension (the large neuron dimension: \(E\), \(D_x\), \(D_y\), RoPE buffers, etc.) and **averaging** the remaining parameters (embeddings, output heads).
- Result: a model with doubled \(n\) (38 M parameters) that retains knowledge from both parent models *without any further training*.

Key observations:
- The merged model can still translate *into* English reasonably well and preserves some meaning.
- It shows "human-like degradation": when generating the non-English languages it mixes words/grammar across Spanish/French/Portuguese.
- A small amount of continued training on the combined data quickly restores proficiency.
- Because BDH-GPU scales primarily by increasing the single large dimension \(n\) (while keeping the bottleneck \(d\) and other hyperparameters fixed), concatenation is architecturally natural and produces another valid BDH-GPU model.

The authors highlight that the high-dimensional, sparse, positive, and relatively monosemantic neuron space makes concept composition via concatenation more feasible than in standard dense Transformer weight spaces. This is presented as an exploratory result on translation, not a large-scale multi-domain continual-learning demonstration.

### Implications for your 32 G / multi-domain setup
Your forked bdh-cl model already mixes Europarl + math + coding + legal. Training additional specialized models on different corpora and merging them is exactly the direction the architecture encourages. In principle:

- You can keep individual models small enough to fit comfortably on local GPUs.
- Concatenation along \(n\) produces a larger effective model whose parameter count (and theoretical capacity) grows roughly linearly with the number of components.
- The sparse positive activations and emergent modularity may help keep domain-specific knowledge relatively disentangled, reducing catastrophic interference compared with dense residual streams.

**Realistic expectations**:
- Zero-shot merge will almost certainly show some interference / mixing (analogous to the language-mixing observed in the paper).
- You will almost always need a modest amount of post-merge fine-tuning or continued pre-training on a balanced mix (or a carefully designed routing / gating stage) to recover peak performance and clean specialization.
- Scaling behavior beyond the ~40 M parameter regime shown in the paper is not yet empirically validated. Whether the same simple concatenation continues to work cleanly at hundreds of millions or billions of parameters, or whether interference grows, remains an open question.
- Memory and compute at inference time still grow with total \(n\), so a heavily merged model may eventually exceed local hardware even if the individual specialists do not.
- Your continual-learning fork (bdh-cl) is a useful foundation; merging is complementary rather than a replacement for good sequential training techniques.

### Suggested practical roadmap
1. **Reproduce and stress-test the paper's merge procedure** on your current codebase with small models first (different language pairs or simple domain splits). Confirm that concatenation + averaging works as described and quantify the degradation.

2. **Design clean specialist experiments**:
   - Keep a shared base (or a small common "core") if possible.
   - Train pure specialists (e.g., pure math, pure code, pure legal, pure additional languages) with the same \(d\), number of layers/heads, etc., so they are merge-compatible.
   - Use identical tokenizer / embedding initialization where feasible.

3. **Merge strategies to try**:
   - Naive concatenation + average of non-\(n\) tensors (paper baseline).
   - Weighted or selective concatenation (e.g., only merge certain layers or heads).
   - Add a lightweight routing / gating mechanism after merge (inspired by MoE ideas) so the model can preferentially activate domain-relevant neuron subsets.
   - Immediate short continued training on a carefully balanced mixture after every merge.

4. **Evaluation protocol**:
   - Domain-specific held-out sets + cross-domain transfer / interference tests.
   - Measure both zero-shot merge quality and quality after a fixed post-merge compute budget.
   - Track sparsity, monosemanticity of synapses, and activation patterns before/after merge--these are BDH's interpretability strengths.

5. **Hardware-aware scaling**:
   - Merge only as many specialists as your inference memory allows.
   - Explore progressive merging + distillation or pruning of low-utility neuron blocks if the combined \(n\) becomes too large.
   - Consider whether your continual-learning mechanisms can be applied *after* merging to further adapt the combined model.

6. **Longer-term ideas**:
   - Investigate whether the Hebbian synaptic state itself can be partially transferred or aligned across specialists.
   - Test whether training without (or with truncated) BPTT (also explored in the paper) interacts favorably with modular specialists.
   - Publish intermediate results; the BDH community is still small and empirical data at even moderate scale would be valuable.

**Bottom line**: The architecture gives you a more principled and structurally natural way to compose domain specialists than classic Transformer weight averaging or franken-merging. It is a promising route to exceed the capacity of any single model you can train on local hardware, provided you treat the post-merge recovery phase as essential and stay empirical about interference. Start small, measure carefully, and iterate on the merge + light fine-tune loop--that is the highest-leverage next step.
