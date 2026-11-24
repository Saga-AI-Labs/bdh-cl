# Review: Key-2 G0 freeze candidate

**Date:** 2026-11-24
**Reviewed object:** `docs/notes/2026-11-24_key2-g0-freeze.md` (status DRAFT)
**Machine record checked against:** `out/key2_calibration/thresholds_candidate_v2.json` on host `.53`
**Reviewer:** Quinn (saga profile)
**Verdict:** **Not LGTM as written.** The margins are defensible; three other points must be resolved before section 9 is signed.

---

## 1. Margins — keep, but replace the justification

The arithmetic is internally consistent. The registered rule is
`F_d = negative-band maximum + 1` and `M_d = positive-band mean - 0.5`, and the
three values follow from it:

| dimension | negative max | `F_d` | positive mean | `M_d` |
|---|---|---|---|---|
| coherence | 1 | 2 | 5.00 | 4.50 |
| relevance | 1 | 2 | 5.00 | 4.50 |
| language | 2 | 3 | 4.83 | 4.33 |

The format-constrained sensitivity (drop four items, language 4.86 → `M_d` 4.36)
and the margin sweep (4.70 / 4.50 / 4.30) both recompute correctly.

**The choice of 0.5 is not load-bearing for the calibration bands.** The bands
are separated by four points on coherence and relevance (positive 5, negative
1), so any margin in `[0, 2]` passes both. What the margin actually governs is
the host verdict, not the freeze.

**The substantive weakness is elsewhere: the middle is uncalibrated.** Between
`F_d = 2` and the positive minimum of 5 there is a three-point region on
coherence and relevance for which no reference exists. A host that is "half
good" lands exactly there, and the instrument has no statement about whether
3.5 is correct or wrong.

**Recommendation:** keep 0.5, but replace the sentence *"0.5 is the candidate
because the positive band is at ceiling and no evidence motivates either
alternative"* with a positive justification. One exists in the same document:
the scale-set controls `long_wrong` / `planted_error` / `audience_violation`
score 3.82–3.89 on coherence. **4.50 sits between those fluent-but-flawed
controls and the perfect band**, which is a principled placement rather than an
arbitrary one. Registering that would turn an admitted gap into a stated basis.

## 2. The language positive-band mean is stated three times, differently (blocking)

```
Freeze note section 2   language positive band mean   4.83
Freeze note section 3   `good` variant language        4.94
thresholds_candidate_v2.json  `good` variant           4.667
```

I read the candidate JSON directly on the training host. The `bad` variant
reconciles across all three (`4.833` here, `4.83` in the note); the `good`
variant does not. Section 4 of the note quotes both 4.83 (positive band) and
4.94 (`good`) without flagging the difference, and neither equals the machine
value.

This matters because `M_d` for language is derived from that mean. If the
positive band is 4.667 rather than 4.83, `M_d` moves by 0.17 — larger than the
entire margin sweep step the note itself reports.

**Required before signing:** reconcile the three numbers, state which source the
frozen `M_d` derives from, and correct the other occurrences.

**Second check point, same section:** coherence exact agreement and language
exact agreement are both reported as 69.2 %. That is possible, but a shared
source cannot be excluded and should be confirmed against the two judge outputs.

## 3. Section 4.1 — recommend option (b)

The fluent-wrong acceptance line requires `coherence >= 3`. Six cells fail it,
and the note correctly identifies why: under the v2 contradiction rule a
contradiction that breaks the main proposition is **correctly** scored 2, and
two of the six items are word salad by construction, where anchor 1 gives 1.
The judges are applying the rubric; the acceptance line predates it.

- **(a)** reading the check as a per-variant mean hides individual failures and
  contradicts the per-item floor the rest of the gate relies on.
- **(c)** holding the freeze is unnecessary: none of the six cells is in the
  positive or negative calibration band, so the thresholds do not move.
- **(b)** is the honest fix: scope the check to items that are not
  contradiction-by-construction. Recommend (b), with the exemption written out.

## 4. The `bad` variant exceeds the coherence threshold

```
`bad`:  coherence mean 4.94, min 4   ->   above M_d = 4.50
```

A deliberately bad answer passes the coherence gate. This is by design — the
rubric scores internal connectedness, not factual correctness — and relevance
catches it (`4.06 < 4.50`). But the frozen record should say so explicitly;
otherwise the value reads later as an instrument failure rather than a boundary
of what coherence measures.

## 5. Three additions to the section 9 sign-off list

1. **Resolve the language-band discrepancy** (4.83 / 4.94 / 4.667).
2. **Decide the human positive band.** Section 8 states that if the registered
   40 answers arrive before signing they become the primary band. That is a
   decision about the frozen threshold, not a footnote, and belongs in the list.
3. **Record that dissociation A and the 100M/90MB ordering check were not run.**
   Section 8 already says the freeze does not cover them; the sign-off should
   carry the same statement so the omission is visible at the signature.

## 6. Confirmed without reservation

- **Section 7 (force-add the calibration bytes): yes.** About 2.8 MB, and a hash
  without its bytes is only as durable as the disk. The note's own warning is
  correct.
- **Flipping the rubric to `FROZEN`: yes**, with the resulting file hash written
  back into section 6 in the same commit.

## 7. Summary

| item | disposition |
|---|---|
| margins 0.5 / floors 2,2,3 / means 4.50,4.50,4.33 | keep, reword the justification |
| language positive-band mean | **resolve before signing** |
| section 4.1 | resolve as (b) |
| `bad` coherence above `M_d` | state in the record |
| sign-off list | add three items |
| section 7 durability | accept |
| rubric freeze | accept |

The note is close. It is not yet safe to sign, because two of its own numbers
disagree and the freeze would bind whichever one was written last.
