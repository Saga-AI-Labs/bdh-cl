# Chat-model planning round - input (2026-11-18)

**Purpose.** The word-salad diagnosis now has numbers (report section 17-18).
This note is the input to the announced planning round: what is settled, what
the round must decide, and what it must not assume. It does not authorize a
run and does not replace the prereg (`2026-11-03_chat-model-prereg.md`).

## 1. What changed since prereg v0.2

| finding | number | source |
|---|---|---|
| Cause of the salad | token-view starvation is dominant: 5.12 MB of views per phase, 0.18 sightings per 512-B block, 0.37 cumulative on legal | report 16-17 |
| Not the cause | overfitting excluded (val/test gaps 0.007-0.061 nats); 512-B context secondary; zero dialogue categorical | report 17 |
| The network vs a count table | 1.1155 nats/byte @1024 vs 6-gram 0.8519 - **0.2635 nats above** a 6-gram on its own register | report 18 |
| Context use | all gain in the first ~64 bytes; bytes 64-511 add nothing; network wins on 0.4 % of positions | report 18 |
| Direct route | 72.4 GB at 3.62B / 44.8 B/s = **~51 years**; minimum 5.12 GB = ~3.6 years | report 18.3 |
| Inverse route | 100M/2 GB: 12.4 d uncompiled, 5.8 d compiled; 4 layers 8.4 d; 50M/1 GB ~3 d; 10M ~3 h | report 18.3 |
| Route-aware loop | measured **2.0x** the one-pass step (two forwards, one backward); 2-GB phase ~12-25 d uncompiled, ~6-12 d compiled | report 18.6 |

The diagnosis is specific to the 3.62B model on 5.12 MB of views. The 100M
host is a **hypothesis about transfer**, registered with outcomes A/B/C in
prereg item 9 - not a consequence of the diagnosis.

## 2. The gate is two-key; key 2 does not exist

Registered in prereg item 9:

- **Key 1, statistical floor.** NLL against the section 18 6-gram on the same
  carve and freeze. Necessary, **not sufficient**: the measured 3.62B model
  clears no floor yet still produces salad. A model that beats a 6-gram is not
  thereby coherent.
- **Key 2, coherence.** Sample-based, frozen rubric, held-out prompts
  (document openings in neither carve), deterministic decoding, threshold set
  before the first host run.

Key 2 candidates are prereg item 4 and the 4.4a judge topology. **Do not
assume 4.4b can simply be reused:** 4.4b is the frozen post-SFT composition
metric (60 items, two certified judges). Coherence of free generation is a
different object, and consuming 4.4b items early contaminates the composition
series. The round should decide: extend the judge set with a separate held-out
slice, or build a distinct instrument.

## 3. What the round must decide

1. **Key 2 specification.** Rubric, prompt source and count, decoding
   (temperature, top-k, max bytes), pass threshold, judge topology (local GLM
   endpoint vs cloud), and the frozen hash. This must land before the first
   host run; otherwise no result is scoreable.
2. **Pilot shape.** 50M/1 GB (~3 d one-pass) vs 100M/2 GB (~8.4 d at 4 layers,
   12.4 d at 6, one-pass); byte vs BPE arm (item 7; BPE needs ~8 GB of text or
   four epochs over 2 GB); 4 vs 6 layers as the baseline.
3. **Depth arm.** Matched-parameter 4 vs 8 layers (item 10; depth adds compute,
   not parameters). Cost at 100M/2 GB: 8.4 vs ~16.7 d one-pass. Run it only if
   key 2 fails while key 1 passes (outcome B) - not by default.
4. **Pretraining vs route-aware order.** One-pass host pretraining followed by
   a route-aware graft phase halves the pretraining cost but tests the loop
   late; route-aware from step 0 doubles the whole leg. Registered bound:
   2.0x, to be replaced by a measured pilot step.
5. **Data mix.** ~2.1 GB usable on disk: Europarl zh 1.3 GB, wikitext-103
   516 MB, textmix/files ~215 MB, textmix2 109 MB, expert 23 MB. zh dominates
   by volume; a register mix is a decision, not a default.
6. **Stop rules.** Budget cap per arm, the A/B/C scoring rule, and what
   happens on outcome C (token-view budget re-opened, item 6).

## 4. Not on the table

- **Direct 3.62B scaling.** Decades on this box; batch >1 does not exist at
  91.99 GiB peak. Any plan that requires it is out of scope.
- **NLL as a coherence proxy.** Section 18 is the counterexample.
- **"SFT presupposes fluency" as a premise.** It is a registered, testable
  claim (item 8), not an ordering rule.
- **Sample-reading as evidence.** Section 16: it does not register.

## 5. What the round should produce

A decision record that (a) freezes key 2 with a hash, (b) selects the pilot
shape and its budget, (c) states the A/B/C thresholds numerically, and (d)
names the first run as the transfer instrument for the diagnosis. Until (a)
exists, the host program is blocked by design, not by caution.

---

## 6. Addenda 2026-11-18 (review, with operator correction)

### 6.1 The judge topology for key 2 is settled, not open

Section 3.1 listed "local GLM endpoint vs cloud" as a decision. **The operator
corrected the reading:** the two-local-seat topology is **Qwen 3.8 Flash Next
(DGX Spark, TP=1) + Gemma 4 31B (RTX 4090)** - GLM was never a seat. The
GLM-host model is retired (quantization > 1/2 bit needs TP=2-TP=4, i.e. two
to four Sparks for one judge, plus a bias relation to a team seat). **Deepseek
v4.1 Flash takes over as the second team seat beside LongCat**; it is no more
related to Qwen or Gemma than GLM was, so the bias exclusion is unchanged.

What is still open is **not** the topology but the **key-2 instrument**: rubric,
prompt source, count, decoding, threshold, hash (section 3.1). The two local
seats are available; the cloud option is excluded by the bias rule.

### 6.2 TP=2 is registered as out of scope, with a trigger

**Not on the table now.** The diagnosis is a ratio: 3.62B parameters on 5.12 MB
of token-views. TP=2 adds capacity and memory; it does not add data, so it
moves the ratio the wrong way. The direct route is excluded by arithmetic
(72.4 GB / 44.8 B/s = ~51 years), and a 1.5-2x step-rate gain leaves it in the
decades. The inverse route fits one box at 23 GiB peak and needs no TP.

**Trigger, registered:** when a host that is coherent on the available data
does not fit one box. Not reached - the 100M/50M hosts fit. See
`docs/plans/2026-11-15_tp2-bridge-study.md` for the port's precondition
(bridge experiment + re-baseline), and chat prereg section 6 item 5.

### 6.3 Item 8 (SFT ordering) is a missing decision in section 3

"SFT presupposes fluency" is a registered, testable claim (prereg item 8:
~2-5k synthetic pairs, a fresh block, ~2k steps, ~6-7 h on the 3.62B model,
~1 h on a 100M host). **Section 3 lists six decisions and item 8 is not among
them.** The round must either schedule it or explicitly defer it; as written it
floats.

### 6.4 Section 3.2 and 3.4 interact - the pilot cost depends on the order

Section 3.2 quotes 50M/1 GB ~3 d and 100M/2 GB ~8.4/12.4 d; section 3.4
registers route-aware training at **2.0x** the one-pass step. **The quoted
numbers are one-pass.** If the round picks route-aware from step 0, the same
leg costs ~17 d (100M/2 GB, 4 layers, uncompiled) instead of 8.4. The two
decisions must be taken together; otherwise the round reads the cheaper number
and buys the expensive option.
