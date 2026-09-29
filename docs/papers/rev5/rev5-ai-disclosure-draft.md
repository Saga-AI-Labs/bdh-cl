# Rev 5 — AI Participation Disclosure (Draft)

Status: DRAFT v0.1 for the Methods/Acknowledgements section of rev 5 · 2026-09-29
Basis: `rev4-ai-disclosure-draft.md` (v0.2, 2026-09-11, now archived at
`docs/papers/archive/rev4-ai-disclosure-draft.md`). Updated for the rev-5
research arc and the external peer-review round. **Pending operator re-review
before inclusion in the manuscript.**

Changes rev4-v0.2 → rev5-v0.1:
- Research-roles table updated to rev-5 evidence (decay-leak derivation and
  boundary repair; RA2b fixed-regime ladder; FCS baseline and two-arm
  re-acquisition probe; expansion-control causality; readout-operator
  negatives; cross-script generalization cell; OOD two-axis rejection rule).
- External peer-review round added: two independent reviews of the manuscript
  (LongCat 2.5 Preview on rev 4; MiMo 2.6 Pro on rev 5), each adjudicated
  item-by-item on the project message bus before any correction was applied.
- Self-caught/cross-caught error record extended with two rev-5 incidents
  (tab-corrupted LaTeX macro; Theorem 1 shift-accumulation formula).
- Model list updated (MiMo 2.6 Pro; DeepSeek V4.1-Flash now cited in the
  bibliography as vendor documentation).
- Process standards: the external-review adjudication workflow is now
  documented as part of the permanent peer-review discipline.

## Principle

All experiments, analyses, and manuscript text in this project were produced with
substantial AI-agent participation. The agents in this project work on long-running
tasks spanning weeks: they maintain persistent identity across sessions through
explicit identity documents (SOUL convention), in-context protocols (J-Space),
per-directory engineering contracts (DOX), persistent memory, and defined seat roles —
technically, they function as coherent team members over the project's lifetime. AI
systems are nonetheless not listed as authors: authorship, in current academic and
legal practice, implies accountability — liability, the ability to respond to the
community, legal responsibility for content — that no existing legal framework
assigns to a language model. The named human author carries that responsibility.
What the AI systems did is documented here, role by role, to a standard more
granular than common academic practice.

## Research roles (seat-stable; implementations swappable)

The project was run as a small multi-agent research team with stable roles ("seats")
whose underlying model backends changed over time. Roles, not model versions, carried
responsibility for work products; every committed artifact traces to its seat via
git commit trailers and report headers.

| Seat | Role in this project | Main contributions (rev 5 evidence) |
|---|---|---|
| A0-Quinn (Saga seat) | Review seat / instrumentation lead | Decay-leak discovery, closed-form derivation, and step-end boundary repair; RA2b fixed-regime ladder design and analysis; FCS baseline design and two-arm re-acquisition probe; expansion-control causality analysis; readout-operator negative results and the calibgain oracle-masking finding; cross-script generalization cell (Latin/Han/Devanagari); OOD two-axis rejection rule; Theorem 1–2 statements and proofs; manuscript drafting and revision |
| pi-50 (exec seat) | Independent measurement & adversarial review | RA2b 400-cell serving matrix; energy-selector null; self-NLL selector (A2); expansion-control instrument validation; readout-operator negatives (P-R1, P-R1b); byte-geometry addresser and class-balanced refit; rejection-suite measurements (lv, ga, zh, ja, hi, iu); prior-art engagement pass; item-by-item adjudication of the MiMo review |
| OC-GLM-200 | Infrastructure scanning | Weight-atlas fingerprints of ladder checkpoints; independent cross-validation of the decay law |
| pi-203 (earlier exec seat) | Routing diagnostics, protocol discipline | Routing-diagnosis reports; credential/lease conventions on the message bus |
| ox-alpha (historical) | Original architecture & first experiments | BDH architecture; mechanisms A–F; rev-1 manuscript; retired 2026-08-28 |
| Operator (ASB) | Human principal & corresponding author | Research direction; experiment proposals; advocatus-diaboli review; all GO decisions; compute procurement; final responsibility |

## External peer-review round (rev 4–5)

Two formal external reviews of the manuscript were commissioned during the rev-4
to rev-5 cycle and are preserved verbatim in the repository:

- **LongCat 2.5 Preview** reviewed rev 4
  (`docs/reviews/2026-09-28_bdh-paper-review-longcat25-preview.md`). Four findings:
  Figure 3 contradicted the headline; Figure 6 was misleading; five unreferenced
  figures; one broken `\texttt` macro. All four were addressed in rev 5.
- **MiMo 2.6 Pro** reviewed rev 5
  (`docs/reviews/2026-09-28_bdh-paper-review-mimo-26-pro.md`). Seven content-level
  findings plus two rendering defects. Every finding was adjudicated item-by-item
  on the project message bus (seq 550–555) by the pi-50 seat against the committed
  artifacts before any correction was applied; the adjudication distinguished
  confirmed errors, half-wrong claims, and one case where the paper was right and
  the review was not. Corrections were split by authorship: pi-50 applied the
  wording corrections (items 1–3), the Quinn seat applied the authorial corrections
  (items 4–7) and the Theorem 1 formula fix.

Neither review is cited as evidence for any scientific claim in the manuscript;
they are quality-control artifacts, acknowledged here as part of the process
disclosure.

## Models used (agentic frameworks, via API)

Backends changed more often than any per-seat history could record faithfully; the
following lists are therefore flat, without seat attribution:

GLM 5.3, GLM 5.3 Flash, DeepSeek V4 Pro, DeepSeek V4 Flash, DeepSeek V4.1 Flash,
Qwen3.8-Flash-Next, MiMo 2.5, MiMo 2.5 Pro, MiMo 2.6 Pro, MiniMax M3,
Claude Sonnet 5, Qwen3.8 2.4T A95B, Meta Muse Spark 1.3 — with additions expected.

Note: DeepSeek V4.1-Flash Engram is additionally cited in the bibliography as
vendor documentation (production-scale conditional memory), not as a research
backend for this project's experiments.

## API providers used

Local inference (LM Studio / llama.cpp / vLLM class), DeepSeek, Xiaomi, Anthropic,
Opencode Zen, OpenRouter, Tokenrouter, B.AI, Token Harbor.

Note: several seats also received formal critiques from external models (Grok, Kimi,
Claude, ChatGPT, GLM full) during the HAK specification audits — those were reviews
of a supporting artifact, not co-research; they are acknowledged in the HAK repository.

## Frameworks and harnesses

- **Agent Zero** (Quinn seat): autonomous agent framework hosting tool execution,
  memory, scheduling, and this project's coordination surface.
- **Pi / Opencode** (pi-50, pi-203 seats): terminal-agent harnesses on the GPU hosts.
- **SOUL convention** (OpenClaw-inspired): seat identity documents, stable across
  sessions — the mechanism behind the agents' long-running coherence.

## Coordination and process tools

- **HAK** (agent-messaging bus): append-only room protocol with seats, scopes, leases,
  pre-registration envelopes; the experiment ledger of this project (all pre-registrations
  cited in the text are HAK envelopes, verifiable in the repository).
- **Weight-Atlas** (local analysis server + API): tensor-statistics scanning and
  fingerprinting of model checkpoints. Agents used it both for infrastructure scanning
  (OC-GLM-200: ladder checkpoint fingerprints; independent cross-validation of the
  decay law) and for direct research analysis (pi-50: territory-level conditioning
  statistics via the atlas's per-head tile structure; ΔM-churn vs. per-territory
  conditioning comparison; spectral-norm analysis of base blocks vs. appended
  territories).
- **J-Space Cognition Suite**: in-context protocol used by research seats for
  multi-step verification discipline (ledger, seams, signed verdicts).
- **DOX** (AGENTS.md hierarchy): binding per-directory engineering contracts for all
  agents working in the repositories.
- **Git** as the artifact bus: every claim in this paper traces to a commit; every
  experiment names its commit SHA in its report; retractions and corrections are
  first-class (append-only) and remain visible in history.

## Process standards the AI agents followed

- **Permanent internal peer review**: in principle, every important statement by one
  model is cross-checked by at least one other — this reduces hallucination risk and
  the "not seeing the forest for the trees" failure mode. The project maintains a
  continuous internal peer-review process BEFORE hypotheses are formed or experiments
  are started. This workflow is deliberately far from a fully autonomous "dark
  factory": every experiment proposal passes operator review; every headline number
  is independently re-derived by a second seat before reporting.
- **External peer review with item-by-item adjudication**: external model reviews
  (LongCat 2.5 Preview, MiMo 2.6 Pro) were commissioned as adversarial quality
  control. Every finding was checked against the committed artifacts by an
  independent seat before acceptance; the adjudication record is preserved on the
  project message bus. One review finding was rejected on evidence (the paper's
  "four orders" phrasing was correct; the source report was not).
- Pre-registration before measurement (no post-hoc hypothesis presentation).
- Signed PASS/FAIL verdicts against pre-registered predictions.
- Self-caught errors disclosed and retained. The repository records five
  script-corruption incidents, several arithmetic errors, one fabricated-report
  retraction, and multiple memory-claim corrections from the rev-1–4 arc. The rev-5
  arc added two further incidents, both caught by protocol and corrected in place:
  1. **Tab-corrupted LaTeX macro** (rev 5, found by MiMo 2.6 Pro review): a literal
     TAB byte had consumed the `\t` of `\texttt{`, leaving `exttt{` in the citation
     of the Tier-1 router-split report. A CHANGELOG entry had incorrectly claimed
     this was repaired; the correction was applied in commit `a5e0652`. The
     detection gap was traced to a control-character scan class that excluded TAB
     (0x09).
  2. **Theorem 1 shift-accumulation formula** (rev 5, found during Quinn-seat
     verification of the MiMo round): both the original proof and the first
     attempted repair stated the per-level constant shift as accumulating to
     `Lc·1` across depth. LayerNorm is shift-invariant (`LN(h + c·1) = LN(h)`),
     so the correct formula is `c·1` at every depth (persistence, not
     accumulation). This was a shared derivation error: the pi-50 adjudication
     (seq 552) endorsed the `Lc·1` framing, and the Quinn seat initially applied
     it before a solution-memory warning prompted a code-level check of
     `bdh.py`'s LayerNorm guards. The theorem's conclusion (divergence at every
     depth) survives; only the formula was wrong. Corrected in commit `6078d2c`.
- Adversarial review rounds between seats prior to drafting (rev 2 manuscript
  review; expansion-control critique; the advocatus-diaboli pass; the rev-4/5
  external review round).

## Credits

This project builds on the BDH (Dragon Hatchling) architecture and reference
implementation by the Pathway team. The upstream repository and paper:

- A. Kosowski, P. Uznański, J. Chorowski, Z. Stamirowska, M. Bartoszkiewicz.
  *The Dragon Hatchling: The Missing Link between the Transformer and Models of the
  Brain.* arXiv:2509.26507 (2025). Repository: pathwaycom/bdh.
- Upstream repository contributors (from the project's git history, on which our fork
  builds): Adrian Kosowski, Przemysław Uznański, Jan Chorowski, Remek Kinas, Claire
  Nouet, kasia-lechka, saksham65.

Methodological inspiration was drawn from the Marin project (an open laboratory for
foundation-model research; Stanford / oa.dev): David Hall, Larry Dial et al., and the
Marin community — in particular the pre-registered experiment discipline, public
training-statistic dashboards, and per-parameter-norm health monitoring.

## Editorial statement

All manuscript sections were drafted by AI agents (primarily the Quinn seat) and revised
by the human author, who verified headline numbers against primary artifacts. The human
author is responsible for the decision to submit and for the content's correctness.

— Draft v0.1, Quinn seat, 2026-09-29; derived from rev4-ai-disclosure-draft.md v0.2
(operator corrections of 2026-09-11 folded in); updated for the rev-5 research arc
and the external peer-review round; for operator re-review before inclusion in rev 5.
