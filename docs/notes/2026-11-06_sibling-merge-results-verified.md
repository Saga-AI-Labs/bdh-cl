# Sibling-merge results verified: all four core predictions fail; the mechanism is co-activation, not duplication

**Date:** 2026-11-06
**Addressed to:** the author of `docs/reports/2026-11-06_expert-merge-results.md`
**Evidence:** `out_c/expert_merge/eval_sibling.json` (raw), `b1_train.log` (18,611 steps, rc=0, final val_loss 1.1225 — both verified), `docs/plans/2026-11-05_expert-merge-prereg.md` v0.3
**Status:** verification + frame-check note. The report's verdict stands; three presentation items need correction, and one preregistered consequence now triggers.

## 1. Numbers verified

Every figure in the report's tables reproduces exactly from `eval_sibling.json`
(protocol line: seed 1234, block 512, 200 crops, mb 30 — matches §2.5 of the prereg):
parents 11.56/5.64/5.46/39.97 and 3.61/46.57/6.38/33.65, merged
11.40/24.47/11.48/31.99. P1 fails by +1.0006 nats, P2 by +0.9997. The training-run
claims check out against `b1_train.log`.

## 2. Three corrections (none change the verdict)

- **P3 uses a stale threshold.** The report tests ≤ 1.6966 — the v0.1 threshold.
  v0.3 sharpened P3 to ≤ **1.2479** (the ancestor merge's own legal nll), and v0.3
  explicitly kept P1–P5 unchanged. Against the frozen gate the failure is *stronger*:
  2.4406 − 1.2479 = **+1.19 nats**, not +0.74.
- **P1b is missing from the predictions table.** The home band (merged zh ≤ 2.03)
  fails too: 3.1975 → **+1.17 nats**. The correct tally is **four of four core
  predictions fail**, not three.
- **§4's gap column does not reproduce from its own table or the JSON.** Correct
  gaps (merged minus best parent, nats): expert **+1.15**, zh **+1.47**, legal
  **+0.74**, code **−0.05**. Two prose items with it: "the merge sits between the
  two parents" and "worse than the best parent on every domain" are wrong for code —
  merged 3.4654 is the **best of the three models on code** (B1 3.5159, zh_last
  3.6882) — and on expert the merge edges parent A (2.4336 vs 2.4476). These are
  0.01–0.05-nat effects against 1-nat failures and do not soften the verdict, but
  the sentence should say "three of four domains".

## 3. Frame-check: the prereg's mechanism model was wrong, in a specific way

P1's stated mechanism was "no bit-exact trunk duplication; zh neurons pristine in
parent-A." That reasoning assumed **duplication** was the damage mechanism of the
ancestor merge. The measurement says the damage mechanism is **co-activation**:
`x @ self.encoder` runs over all neurons of both halves and both halves' decoder
rows add to the output on every text. Topology only decides *how correlated* the two
halves' contributions are:

- Ancestor merge: the halves shared a bit-exact trunk, so their decoder rows agree
  where the text is in-distribution for either — mild dilution (+0.19/+0.47), and
  its legal gain (1.2479 < 1.6966) was **lineage correlation, not width**.
- Sibling merge: `expert_b1` is a full fine-tune that moved every neuron —
  uncorrelated rows, same additive forward — and the dilution is an order of
  magnitude larger (+1.00/+1.19/+1.47).

My "capacity monotonicity" reading of the ancestor merge's legal gain was therefore
wrong, and **P3's preregistered failure clause now triggers**: the five-domain width
gradient was a ladder-lineage artifact, not width. RBC-1 v0.4 (already pending with
the review's three corrections) must absorb this revision — that clause was written
into the prereg for exactly this case.

## 4. What the raw data adds beyond the report

- **B1's own numbers quantify catastrophic forgetting under the paper protocol:**
  zh 1.7306 → 3.8409 (**+2.11 nats**, 8.2×), legal +0.16, while expert dropped
  −1.16. A full fine-tune on 20 MB *without replay* buys a capability by selling the
  home language. Relevant for the chat prereg: any future specialist branch needs a
  replay mix (the August recipe had one; B1 deliberately followed the paper and
  didn't).
- **The expert capability survives the merge at the ~1 % level:** B1 gained 1.16
  nats on expert; through the pool, 0.014 nats remain (merged 2.4336 vs zh_last
  2.4476). Dilution factor ≈ 99 %. Pooling does not average capabilities — it
  buries them.

## 5. Consequences and the cheap next instruments

- **Decision table, stronger form — agreed:** routed routes win §4.3 on measured
  evidence. The pooled merge is not a scaling move at this width, the 10T/19-year
  arithmetic is moot at the mechanism level, and the chat prereg's §4.3 can now cite
  this measurement instead of the caution.
- **P5 (repaired-prune control) is still outstanding and is the cheapest decisive
  instrument left** (~slicing + one eval, no replay). §5 correctly names prune+replay
  as "the only remaining path to a positive result" — its no-replay control should
  run before anything else does.
- **Prune+replay's success criterion should be preregistered before it runs:**
  recovered ≥ best parent on both domains (zh 5.64 / legal 5.46). Anything less and
  the right move is serving the untouched parent — a recipe that must first justify
  itself against simply not doing it.
- **B2 (QAT A/B) is merge-independent** — P4 compares branches, not merges — but its
  GPU cost (~22 h) is now up against a changed landscape; Q1-probe-first ordering
  stands either way. Quinn's/operator's call.
- Optional mechanism probe (not blocking): a B1b with zh replay mixed into the
  branch corpus would test the correlation model directly — prediction, if the
  co-activation account is right: ancestor-like mild dilution instead of +1 nat.
  ~22 h GPU; only worth it if the result would change a decision.

— asb, 2026-11-06
