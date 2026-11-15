# TP=2 bridge study: quantify the non-equivalence before any port

**Date:** 2026-11-15
**Status:** plan registered; execution starts only when TP=2 becomes a candidate.
Depends on: chat-prereg section 6 item 5 (registered 2026-11-15), graft-2 plan
section 4 (option C), probe report sections 12-13 (the memory wall and the
fullcov instrument).

---

## 1. Why this exists

TP=2 changes the reduction order. Every reduction-order change moves the loss by
some small amount, and our decisive claims live at exactly that scale:

| claim | magnitude | regime |
|---|---|---|
| P3 S1 bit-exact regression | 0.0000 to printed digits | single device |
| fullcov batch invariance | 2.2e-9 | single device |
| P2 "+0.044" | now known to be noise around 0 | single device |
| serving isolation | +0.0000 on 6 cells | single device |
| co-activation penalty | ~1.47 nats (merge) / 0.79 (P3 D-cell) | single device |

A TP=2 shift of 1e-4-1e-3 (the order Grok names) would be INVISIBLE on the
random-crop instrument (its single-run noise is ~0.05-0.10 nats) but well
ABOVE the fullcov noise floor (batch invariance 2.2e-9), so the fullcov
instrument **can see it** - and any larger shift too. What we lack is the
measured size on our own models.

**This study is the precondition for treating TP=2 numbers as comparable among
themselves, and for deciding whether they can ever be compared to the single-
device series.**

## 2. Design

One checkpoint, two regimes, identical config, one instrument.

| cell | checkpoint | mask | val | test |
|---|---|---|---|---|
| 1 | P3 last (mult 1024, step 10000) | 896 (old prefix) | fullcov | fullcov |
| 2 | P3 last | none (full width) | fullcov | fullcov |
| 3 | grow (step 0) | 896 | fullcov | fullcov |
| 4 | grow | none | fullcov | fullcov |

Each cell is evaluated **twice**: once single-device on `.52`, once under the TP=2
port on the target hardware. Same `--eval-deterministic --eval-batch-size 4`
and the same crops (fullcov is offset-driven, so both runs see byte-identical
input by construction).

**The mask boundary is the load-bearing detail.** At mult 1024 the old prefix is
57344 of 65536 neurons per head = 0.875. If the neuron axis N is sharded at the
midpoint (32768/32768), **shard 1 is entirely old neurons and shard 2 carries
the boundary**. That keeps the mask a plain contiguous cut, which is why the
chat-prereg registration prefers sharding heads or the residual dimension.

## 3. Gates

| gate | what | pass condition |
|---|---|---|
| T0 | Port runs one forward under TP=2 without shape errors; mask broadcasts across ranks | clean forward, no assertion |
| T1 | Cell 3 (grow, old prefix) matches its single-device value | \|Δ\| <= 5e-4 nats on val AND test |
| T2 | Cell 1 (P3, old prefix) matches | \|Δ\| <= 5e-4 nats |
| T3 | Frozen-prefix restore survives a training step under TP=2 (tiny model, 8 mixed steps) | post-step zh@old == parent value to printed digits, verified per rank |
| T4 | Mask semantics unchanged: masked neurons contribute exactly zero | elementwise check on both ranks |

T1/T2 are the equivalence question. T3 is the freeze question - the one Grok
flags as "easy to get subtly wrong", because a missed rank drifts silently.
T0/T4 are cheap preconditions.

**If T1/T2 fail at 5e-4 but hold at 2e-3, the honest reading is:** TP=2 has its
own noise floor, and every future TP=2 claim needs its own band. That is a
usable result, not a failure - but it must be registered as such before the run,
not after.

## 4. What this does not establish

- **Not a training-speed claim.** The study measures equivalence, not throughput.
- **Not a capacity claim.** No statement about how wide TP=2 lets us grow.
- **Not bit-exactness for the whole pipeline.** Only the four cells above; a
  different corpus or a different growth state would need its own row.
- **Not a replacement for re-baselining.** If TP=2 is adopted, the P0/P1/P3
  anchors are re-measured under TP=2 regardless of this study's outcome.

## 5. Cost and trigger

Execution: ~1 day of port work (the TP=2 implementation itself is the dominant
cost; the measurement is hours). Trigger: when the width forces it - i.e. when
a future growth step exceeds the single-device envelope even with the frozen
backup off. (Anchor correction 2026-11-15: the ORIGINAL graft-2 wall
(report section 12, 95.40 GiB) was removed by the wd-0 backup redundancy -
G-A2 measured 91.99 alloc / 96.40 reserved GiB at 1152 WITH backup off, and
graft #2 itself is running single-device right now. The next +128 steps
project ~+4 GiB of state and cross the 97.35 GiB cap; THAT is the forward
wall this study is gated on.)

**Preferred sharding axis, registered now:** heads or residual dimension, not N.
N is where the masks live.
