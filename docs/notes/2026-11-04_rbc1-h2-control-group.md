# RBC-1 H2: control group shows a mechanism with side effects

**Date:** 2026-11-04
**Addressed to:** the author of `docs/plans/2026-11-02_router-bias-correction-escalation-prereg.md` (RBC-1 v0.2, commit `66f17e4`)
**Evidence:** `docs/reports/2026-10-31_k25w1024-routing-matrix-results.md`, section "H2 control group"; commit `e6db7e6`
**Status:** note, not an amendment. RBC-1 is unedited; this records data that arrived after v0.2 was written.

## CORRECTION (2026-11-04, same day): the zh control case was a corpus labelling error

The analysis below treats zh crop 91 as a side effect of the longer window and asks for
a per-corpus control step on that basis. The first half of that is wrong.

Crop 91 is English UNCCD agenda text inside `xscript_zh.txt`: 0.0 % CJK, 100.0 % Latin
characters. Two independent audits confirm it (`scripts/corpus_purity_census.py`, which
reports crops 50 and 91; `scripts/quinn/corpus_purity_audit.py`, which reports offsets
28,365,496 and 29,547,559). All other 24 corpora are clean in both.

Read against its content, crop 91 routes **wrongly** at window 128 (to Han) and
**correctly** at 384 (to the prose base). The longer window corrected a label-driven
decision; it did not break a correct one.

What survives of the argument below:

- **The count**: 17 fixed, 1 broken over 800 paired crops -- ratio **17:1**, not 8.5:1.
  The one break is legal crop 39, which is genuine.
- **The protocol recommendation still needs a precondition**, but the precondition is
  *corpus purity*, not a window control check. A window tuned on two domains remains a
  small sample, and the third point (256: legal 9, code 3) shows the curve flattening
  rather than ending.

What does not survive: the claim that zh demonstrates a side effect of the longer window.
That reading came from trusting a corpus label that had never been audited.

The lesson is narrower and more useful than "carry a control check": **audit the labels
before interpreting a disagreement with them.** A single crop that disagrees with its
domain may be the only correct measurement in the room.

## What v0.2 says about H2

> **H2 is confirmed, and the mechanism is sharper than section 0 anticipated.** Window 384
> on identical crop indices: legal 19 to 5 misroutes, code 4 to 2 -- 17 of 23 removed at
> zero additional compute. (lines 25-34)

Those figures are correct and unchanged. The framing is not: the run behind them covered
only the two domains that had misroutes at 128. A window that only removes errors cannot
show whether it also introduces them.

## The control group

math and zh were perfect at window 128 (200/200 each). Any error at 384 in those domains
is a side effect, since there was nothing to fix.

| domain | @128 wrong | @384 wrong | delta |
|---|---|---|---|
| legal | 19 | 5 | **-14** |
| code | 4 | 2 | **-2** |
| math | 0 | 0 | 0 |
| **zh** | **0** | **1** | **+1** |

Across 800 paired crops: 23 misroutes before, 8 after. **17 fixed, 2 broken** -- ratio
8.5:1. The second break is zh crop 91, which routes to 8192 at window 384, the base width
and the same destination as the legal misroutes.

## Two corrections to v0.2

**1. "H2 is confirmed" becomes "H2 holds with a measurable side effect."** The window
resolves genuine ambiguity in most cases and occasionally introduces a new error. Eight
misroutes remain where there were twenty-three; that is a large improvement, not a
solution.

**2. "Route at window 384 by default" needs a precondition.** The recommendation at
lines 46-47 is right about the trade but incomplete as a protocol. It should read:

> start from `block - 128`, then run a per-language control check before fixing it. If a
> corpus that was clean at the smaller window loses cases, the window is too large for
> that corpus.

Without the control step, a window tuned on two domains is exactly the position this
project has already had to retreat from three times: the R gate (n=3), the two-domain
generalist claim, and the 44-minute runtime estimate.

## What v0.2 gets right and should keep

- **H1 falsified by the five-domain correlations.** That reading is supported and my note
  of 2026-11-03 is folded in correctly, including the capacity-monotonicity alternative.
- **The thinner-boundary-band mechanism.** Median margin barely moves while p5 doubles;
  the correction from "larger margins" to "fewer crops near the boundary" is right.
- **"The fallback question mostly dissolves."** Mostly, not entirely: 8 misroutes remain
  and the surviving cases are the ones closest to the boundary. A gate is less necessary
  than v0.1 thought, not unnecessary.

## What this does not settle

- **Why exactly two crops break.** Both landing on the base width is suggestive; two
  cases are not a pattern.
- **Whether the 8.5:1 ratio holds at other block sizes.** Window is asserted below block
  size, and block size is a training decision, so 384 does not transfer; only the
  procedure does.
- **The window-256 third point.** v0.2 lists it as open and that is correct. It is now
  more valuable than before, because it would show whether the removal curve saturates
  before the two side-effect cases accumulate.

## Suggested v0.3 consequence

Keep the protocol recommendation, add the per-corpus control step, and restate H2 as
"confirmed with side effects" rather than "confirmed". The trade is good (8.5:1 at zero
compute) and worth recommending -- provided the recommendation carries its own check.
