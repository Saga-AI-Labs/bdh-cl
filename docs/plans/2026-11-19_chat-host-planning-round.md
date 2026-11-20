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
| TP=2 | out of scope, trigger registered | D8; planning input addenda 6.2 |
| Host language | **English-first**; de/zh/math/code attach as routed specialists later | D5 review 2026-11-19 |

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

## 3. The decisions, with cost and dependency

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

**Review 2026-11-20.** The binding specification is section 8 of
`docs/notes/2026-11-19_key2-coherence-rubric.md`: per-dimension mean + floor,
threshold from human answers + 3.62B salad, argue diagnostic. The options table
above is the pre-review menu; it is kept as the record, not as the current
specification. Its "held-out documents" prompt source and its 1-day cost are
superseded by the note's authored 133-prompt set (100 gate + 33 diagnostic)
and the ~2-2.5-day rubric + validation budget.

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

### D5 - Data mix *(superseded for the host 2026-11-19 - see review block)*

~2.1 GB usable on disk. zh dominates by volume. A register mix is a decision,
not a default. Candidates: Europarl zh 1.3 GB, wikitext-103 516 MB,
textmix/files 215 MB, textmix2 109 MB, expert 23 MB.

**Review 2026-11-19 (operator decision, with Grok's review): the host is
monolingual English; de and zh are routed specialists added later.**

Reasons, in order of weight:

- **Measured on the same architecture:** at 100M/90 MB, EN-only reaches EN
  held-out ppl 2.15 vs 2.33 for mixed EN/DE/ES at matched bytes; the report's
  own reading is "multilingual buys breadth, not depth" (report 2026-08-24,
  section 5b). The host needs depth in one register; breadth is what the
  routing machinery exists for.
- **Register, not just volume:** Europarl is parliamentary/political
  formulaic prose, the opposite of the expository/instructional text the
  host is for. It is also the boilerplate case where n-gram/NLL instruments
  read optimistically (report 18.4): a Europarl host would flatter the
  metric while learning the wrong register. **Europarl is excluded from host
  and specialist training**; it remains a historical diagnostic corpus only.
- **Attribution:** the first 100M run is the transfer instrument (prereg item
  9, A/B/C). Three languages make a failure unattributable (starvation
  transfer vs interference vs one bad corpus), and the worst-case gate (4.4)
  would be decided by the weakest language.

Caveat: E3/E6 measured Europarl ppl. The 2.15-vs-2.33 gap establishes the
breadth/depth direction at matched bytes, not its size on the new corpus, and
a DE-only arm was not run - the DE-specialist advantage is inferred from the
EN result by the same mechanism. The host decision rests on that direction
plus the register and attribution arguments, not on a predicted ppl.

Data consequence, with Europarl excluded:

| bucket | on disk | status |
|---|---|---|
| English host-eligible | wikitext-103 516 MB + Gutenberg 40 MB (~0.56 GB before overlap audit) | 3.6 epochs at 100M/2 GB; acquire ~1.4 GB more for a 2-GB one-epoch budget |
| German | Europarl 314 MB only | **no admissible corpus**; de specialist data-blocked |
| Chinese | Europarl 1.30 GB only | **no admissible corpus**; zh specialist data-blocked |
| code / legal / math | textmix2 109 MB, expert 23 MB | later specialists, kept out of the host |

The host acquisition target is high-quality English: FineWeb-Edu or equivalent
filtered educational web text, clean Wikipedia, public-domain literature. The
German graft is the plausible first attachment (shared Latin script; E6's
zero-shot DE ppl 21.8 shows weak but real transfer); zh is the larger jump and
comes after Chinese data exists.

### D5.1 Format and acquisition constraints of the two candidates

**FineWeb-Edu** (`HuggingFaceFW/fineweb-edu`, 5.84 TB). Educational-quality
filtered English web. The full set is not usable: at the measured Spark rates
(1,868-3,973 B/s at 100M, one-pass) even 1 GB is a multi-day leg, and 5.84 TB is
~2000x that. **The viable route is a subset, not the whole set.** Hugging Face
publishes randomly-sampled subsets; the open question is whether a sample
preserves the quality filter's distribution or skews it - that must be checked
with the purity census before use, not assumed.

**enwiki** (Wikimedia content exports, XML/bzip2). The format question is real:

| export | what it is | usable as training text? |
|---|---|---|
| `pages-articles.xml.bz2` | full article wikitext | yes, after wikitext extraction |
| `pages-meta-current.xml.bz2` | all namespaces incl. talk | noisy, needs filtering |
| `mediawiki_content_current` (the linked one) | content-history export | **not directly** - not article text |

The linked export is therefore not a training corpus in its raw form. If enwiki
is used, it is the `pages-articles` export plus a wikitext-to-plain-text step - a
parse-and-clean effort, not a download-and-use one.

**Recommended split by role:**

- **FineWeb-Edu subset as the primary host corpus** - already quality-filtered,
  already text-ready, no markup to strip. Start with a bounded sample (1-2 GB),
  run the purity census, expand only if clean.
- **enwiki as a clean secondary** - only the `pages-articles` export, with a
  wikitext extractor.
- **Gutenberg** as the license-clean control: small, but the one source with no
  licensing question and the builder already exists.

**Not on the list:** Europarl (excluded above), heavy legal/code/math (later
specialists), and any crawl whose quality filter is unknown - section 18 showed
that register statistics are not enough; the corpus has to be clean at the
source, not filtered afterwards.

**Key 1 must be rebuilt for this corpus.** The 0.8519 6-gram of report 18 is
measured on the 28-MB legal train carve / 1-MB legal val split; it is not a
statistical floor for an English host. The ngram mode of
`scripts/diag_context.py` is currently hard-coded to that legal carve (`LEGAL`
constant) and must take a corpus argument before it can produce the host
floor. That number - not 0.8519 - is key 1.

**Cost interaction.** 2 GB of views at 100M is 12.4 d (6 layers) / 8.4 d
(4 layers) one-pass, 2.0x route-aware. Grok's "2-8+ GB, several epochs" is
not in the D2 table: 8 GB of views at 100M is ~50 d uncompiled one-pass, and
several epochs over 8 GB unique is 100+ d. If multi-epoch exposure is
required, 50M at 4 GB of views (~2 epochs over 2 GB unique) extrapolates to
~12 d and is the affordable shape. The round must choose between one clean
epoch at 100M/2 GB and more epochs at 50M; it cannot have both within the
Spark budget.

### D6 - Stop rules

Budget cap per arm, the A/B/C scoring rule, and what happens on outcome C
(token-view budget re-opened, prereg item 6).

### D7 - Item 8 (SFT ordering) - currently floating

A registered testable claim, not scheduled by the round: ~2-5k synthetic
pairs, a fresh block, ~2k steps, ~6-7 h at 3.62B / ~1 h at 100M. The round
must schedule it or defer it explicitly.

### D8 - Hardware topology: one Spark; TP=2 not triggered

**Decision (2026-11-19, operator): the host program runs on one Spark.** TP=2
stays out of scope; the registered trigger is unchanged - a coherent host that
does not fit one box. One box is also the lower-power option, and it keeps the
first host run on the single-device baseline the whole series is measured
against.

Headroom, measured on the Spark (cap 97.35 GiB):

| case | peak, one box | share of cap |
|---|---|---|
| 100M one-pass, uncompiled | 23.1 GiB | 24 % |
| 100M route-aware (two-pass), uncompiled | 48.5 GiB | 50 % |
| 100M route-aware, compiled | 33.2 GiB | 34 % |
| 100M, 8 layers, route-aware | ~64 GiB (estimated) | ~66 % |
| 3.62B, b1/t512 | 91.99 GiB | 94 % |

Sources: `out_c/routed_probe/bench_100m.log` (2026-11-18 re-run at `94c91f2`),
`graft2/ga3_run/ga3.log`; the 8-layer row scales the 6-layer activation peak by
8/6 and is estimated, not measured.

**TP=2 is the wrong hedge for this diagnosis.** It adds memory and capacity;
the diagnosis is a data/coverage ratio - 5.12 MB of views on 3.62B parameters,
0.18 sightings per block per phase. The 3.62B model had 36x the planned host's
parameters and still produced salad. TP=2 moves parameters-per-seen-byte the
wrong way. The only near-cap case, 3.62B at 91.99 GiB, is excluded by time
(~51 years), not memory; a 1.5-2x TP=2 step rate leaves it in the decades.

**The first host run must stay identifiable.** A TP=2 run is not comparable to
the single-device series until the bridge study exists. The port adds per-rank
restore and mask-sharding risks; the P1 campaign hit three silent failures of
the restore class (`collect_state`, `eval_batch_size`, freq invariant). The
first 100M run is the transfer instrument (A/B/C); an uncalibrated topology
variable makes the outcome unattributable.

**Cheaper speed lever first.** `torch.compile` is measured at 2.1x: 2,182 ->
1,031 ms/step one-pass, 4,440 -> 2,100 two-pass, 16.6/33.2 GiB peak. If wall
clock binds, the order is compile -> 50M vs 100M -> TP=2 last.

**Second Spark role.** The second box is the Qwen judge seat for key 2. TP=2
would occupy both boxes for training and force the judge onto shared hardware;
one box per role is the simpler allocation.

**When to reopen (trigger, not date):**
1. the round selects a host >~300M, or a route-aware peak >80 GiB on one box;
2. the 50M/100M leg is wall-clock-infeasible even compiled (>30-60 d) and a
   measured TP=2 speedup >1.5x exists;
3. the product requires the 3.62B model (currently excluded by time);
4. the TP=2 bridge study shows non-equivalence within the accepted budget.

**Operator position (2026-11-19).** One Spark is preferred (lower power than
two). The eventual TP=2 transition is accepted as necessary at some later
point; it is crossed when the trigger fires, as a registered decision with a
re-baselined series - not as drift before the first host run.

## 4. Sequence (the only order that respects the cascade)

```
1. D1  freeze key 2 (rubric, prompts, decoding, threshold, hash)
2. D2+D3  select pilot shape and order, with the cost interaction
3. G0  freeze the protocol record (data, key 1, key 2, shape, A/B/C)
4. run host pilot  ->  score with key 1 + key 2
5. D4  depth arm only on outcome B
6. D7  item 8 scheduled or deferred
7. graft phase on the competent host
```

## 5. Gates

| gate | what | pass |
|---|---|---|
| G0 | protocol frozen before step 1 | data manifest + hashes, carve rule, host-corpus 6-gram NLL + margin + order-resolution shares, key-2 instrument, pilot shape, A/B/C thresholds all committed |
| G1 | key 2 frozen and hashed | rubric + prompt hash committed |
| G2 | pilot result scoreable | key 1 and key 2 both applied |
| G3 | host coherent | key 2 threshold met |
| G4 | graft worth it | host clears key 1 and key 2 |

**The freeze point is G0, not G1.** Key 1 is a rule, not a constant: the
section 18 6-gram was computed on the legal carve, and 0.8519 does not
transport to an English host. Recomputing it on the host's own carve and
freezing the number plus margin before step 1 is the rule working as intended.
Reusing 0.8519, choosing the margin after seeing the host NLL, or changing the
carve after the run is the protocol breach. After step 1, every G0 field is
versioned: a change is a new decision record (v2), and the run is scored under
the version it started with.

## 6. What the round must produce

1. A decision record that freezes key 2 with a hash.
2. The pilot shape and its budget (D2 x D3, costs taken together).
3. The A/B/C thresholds numerically.
4. The G0 freeze record: host data manifest and hashes, carve rule, host-corpus
   6-gram NLL + margin + order-resolution shares, and the key-2/shape/threshold
   hashes in one commit.
5. The name of the first run as the transfer instrument for the diagnosis.
6. An explicit schedule-or-defer for item 8.

## 7. Explicitly not in this plan

- Direct 3.62B scaling (arithmetic).
- TP=2 (not triggered; rationale, headroom and reopen conditions in D8).
- BPE (registered architecture decision, item 7; needs its own round).
- QAT (gated on the FP32 plateau, QAT v2 section 8).
- NLL as a coherence instrument.
- Sample-reading as evidence.
