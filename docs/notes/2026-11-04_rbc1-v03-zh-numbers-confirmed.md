# RBC-1 v0.3: zh crop 91 numbers confirmed, status upgraded to confirmed artifact

**Date:** 2026-11-04
**Addressed to:** the author of `docs/plans/2026-11-02_router-bias-correction-escalation-prereg.md` (RBC-1 v0.3, commit `155facf`)
**Evidence:** commit `a551532`; `docs/reports/data/corpus_purity/anomalies_20261104.json`
**Status:** note, not an amendment. RBC-1 is unedited.

## The crop-91 numbers are exact

v0.3 reports the per-route early-window scores for zh crop 91. Checked against the
stored score vectors:

| window | route 57344 | route 8192 | v0.3 | measured |
|---|---|---|---|---|
| 128 | 2.3374 | 2.6310 | zh wins | **2.3374 / 2.6310** |
| 384 | 2.1577 | 2.0146 | base wins | **2.1577 / 2.0146** |

Four of four values agree to four decimals, and the "95 % ASCII (488/512 bytes)" figure
matches the independent census (`ascii_byte_share 0.953125`).

## Status upgrade: candidate -> confirmed

v0.3 calls crop 91 a **"label artifact candidate"** and names a verification path. That
path has now been walked:

| check | implementation | result |
|---|---|---|
| protocol crops | `scripts/corpus_purity_census.py` (v0.3's own tool) | crops 50 and 91 anomalous |
| window view | `scripts/quinn/corpus_purity_audit.py` | offsets 28,365,496 and 29,547,559 |
| all other corpora | both | 24 of 25 clean |

Two independent implementations agree. Crop 91 is English UNCCD text inside
`xscript_zh.txt`, not an ambiguous boundary case. **Confirmed, not candidate.**

## Three corrections for v0.4

**1. The tally is 17:1, not 17:2.** With crop 91 read against its content, it routes
*wrongly* at 128 and *correctly* at 384. The window corrected a label-driven decision
rather than breaking a correct one. One genuine break remains: legal crop 39, which v0.3
already identifies as ordinary for its corpus.

**2. "H2 holds with a measurable side effect" becomes "H2 holds; the one apparent side
effect was a label error."** On corpora whose labels match their content: 17 removed, 0
introduced over 800 paired crops.

**3. The per-corpus control precondition stays, but for a different reason.** It is not
there because the window creates noise; it is there because a window change can expose a
mislabeled corpus, and that finding depends on the label being audited. The precondition
should read: **audit the labels before interpreting a disagreement with them.**

## What v0.3 gets right and should keep

- **The two-species framing** is sharper than my report's wording: "one label artifact,
one real boundary. Neither supports 'the window creates noise.'" That sentence should
survive into v0.4 unchanged.
- **The capacity-monotonicity reading of the 128 result.** zh wins at 128 on breadth, not
on content; the diagnosis is correct.
- **Corpus purity per crop as a training-data selection criterion.** This is the most
valuable carryover for the target model and is already in the chat prereg.

## One addition worth carrying into v0.4

The window-256 third point is now measured: legal 19/9/5, code 4/3/2 across 128/256/384.
The slope flattens (-10, then -4) but does not reach zero, and four legal crops (36, 108,
110, 185) are wrong at all three windows. Those four are the floor a larger block could
not lower. That matters for the protocol recommendation: "route at 384" is safe on
clean corpora, but 384 does not make routing exact.
