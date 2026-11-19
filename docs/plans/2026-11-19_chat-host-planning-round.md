# Chat host program - planning round detail (2026-11-19)

**Purpose.** The planning-round input (`docs/notes/2026-11-18_chat-planning-round-input.md`)
lists what is settled and what must be decided. This document turns that list
into an ordered plan: the decision cascade, the cost of each branch, the gates,
and the one item that blocks everything else.

**Status.** Plan, not prereg. Nothing here authorizes a run; the run starts only
after the round produces the decision record (section 6).

---

## 1. What is settled and must not be reopened

| item | state | source |
|---|---|---|
| Composition operator | routed growth + hard mask, bit-exact isolation | probe report sections 13-15 |
| Graft #2 | PASS, 4 bit-exact cells over 36 h | `03556a7` |
| Serving map (realistic mixed prompts) | `legal->full`, `code->full`, `zh->mask-1024` | report third deployment revision |
| Direct 3.62B scaling | excluded by arithmetic (~51 years) | report 18.3 |
| NLL as coherence proxy | excluded; section 18 is the counterexample | report 18 |
| Overfitting | measured out | report 17 |
| Word-salad cause | token-view starvation (0.18 sightings/block) | report 17 |
| Judge topology | Qwen (Spark) + Gemma (4090); Deepseek = 2nd team seat | planning input addenda 6.1 |
| TP=2 | out of scope, trigger registered | planning input addenda 6.2 |

## 2. The cascade - one item blocks the rest

```
Key 2 (coherence instrument)  --->  host pilot  --->  graft phase
        frozen, hashed               shape + budget     route-aware
```

**Key 2 first.** The planning input states it directly: until key 2 exists, the
host program is blocked by design. Without a frozen, sample-based coherence
rubric, no pilot result is scoreable, and the only available instrument (NLL
against the 6-gram) is the one section 18 disproved.

**Key 1 (statistical floor)** is necessary but not sufficient. It is a cheap
pre-filter, not the verdict.

## 3. The six decisions, with cost and dependency

### D1 - Key 2 specification (blocking)

| element | options | note |
|---|---|---|
| rubric | per-sample score, frozen dimensions | must be registered before any host run |
| prompt source | held-out documents (openings in neither carve) | contamination control |
| count | e.g. 50-200 samples | trades cost vs stability |
| decoding | deterministic (greedy or fixed seed) | t=0.8/top-k 3 amplifies salad |
| threshold | numeric, set before the run | not tunable after |
| judge topology | Qwen + Gemma local seats; Deepseek as 2nd team seat | bias rule excludes LongCat/GLM |
| hash | frozen rubric + prompt set hash | provenance |

**Cost:** rubric authoring + one certification pass, ~1 day. **This is the only
decision that gates the host.**

### D2 - Pilot shape

| option | params | data | wall clock (one-pass) | route-aware |
|---|---|---|---|---|
| A | 50M | 1 GB | ~3 d | ~6 d |
| B | 100M / 4 layers | 2 GB | 8.4 d | ~17 d |
| C | 100M / 6 layers | 2 GB | 12.4 d | ~25 d |
| D | 10M | 200 MB | ~3 h | ~6 h |

All measured on the Spark (`bench_100m.log`). The route-aware column is the
**2.0x** two-pass factor - the cost interaction registered in addenda 6.4.

### D3 - Pretraining order

| order | cost | what it tests |
|---|---|---|
| one-pass pretrain, then graft | 1.0x | the loop late; cheaper first leg |
| route-aware from step 0 | 2.0x | the loop at the start; doubles the leg |

Registered bound 2.0x; to be replaced by a measured pilot step. **Grok's
recommendation (one-pass first) is the cheaper option, but it is a decision,
not a default.**

### D4 - Depth arm (conditional)

Matched-parameter 4 vs 8 layers at 50-100M. **Run only if key 2 fails while
key 1 passes (outcome B).** Cost: 8.4 vs ~16.7 d one-pass at 100M/2 GB.

### D5 - Data mix

~2.1 GB usable on disk. zh dominates by volume. A register mix is a decision,
not a default. Candidates: Europarl zh 1.3 GB, wikitext-103 516 MB,
textmix/files 215 MB, textmix2 109 MB, expert 23 MB.

### D6 - Stop rules

Budget cap per arm, the A/B/C scoring rule, and what happens on outcome C
(token-view budget re-opened, prereg item 6).

### D7 - Item 8 (SFT ordering) - currently floating

A registered testable claim, not scheduled by the round: ~2-5k synthetic
pairs, a fresh block, ~2k steps, ~6-7 h at 3.62B / ~1 h at 100M. The round
must schedule it or defer it explicitly.

## 4. Sequence (the only order that respects the cascade)

```
1. D1  freeze key 2 (rubric, prompts, decoding, threshold, hash)
2. D2+D3  select pilot shape and order, with the cost interaction
3. run host pilot  ->  score with key 2
4. D4  depth arm only on outcome B
5. D7  item 8 scheduled or deferred
6. graft phase on the competent host
```

## 5. Gates

| gate | what | pass |
|---|---|---|
| G1 | key 2 frozen and hashed | rubric + prompt hash committed |
| G2 | pilot result scoreable | key 1 and key 2 both applied |
| G3 | host coherent | key 2 threshold met |
| G4 | graft worth it | host clears key 1 and key 2 |

## 6. What the round must produce

1. A decision record that freezes key 2 with a hash.
2. The pilot shape and its budget (D2 x D3, costs taken together).
3. The A/B/C thresholds numerically.
4. The name of the first run as the transfer instrument for the diagnosis.
5. An explicit schedule-or-defer for item 8.

## 7. Explicitly not in this plan

- Direct 3.62B scaling (arithmetic).
- TP=2 (trigger: a coherent host that does not fit one box).
- BPE (registered architecture decision, item 7; needs its own round).
- QAT (gated on the FP32 plateau, QAT v2 section 8).
- NLL as a coherence instrument.
- Sample-reading as evidence.
