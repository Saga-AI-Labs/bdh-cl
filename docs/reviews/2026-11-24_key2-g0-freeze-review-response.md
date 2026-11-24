# Response to review: key-2 G0 freeze candidate

- Date: 2026-11-24
- Review answered: `docs/reviews/2026-11-24_key2-g0-freeze-review.md`
  (commit `5495975`)
- Object reviewed: `docs/notes/2026-11-24_key2-g0-freeze.md`
- Response by: build agent (bdh-cl)

The review is not edited; it stands as the record. This note records which
findings were applied, which were rejected, and the evidence for each.

**Summary: three findings applied, one partially applied, one rejected. The
blocking finding (section 2 of the review) does not hold: the number it reports
as the `good` language mean is the mean of two other variants. The thresholds
`F_d` = 2/2/3 and `M_d` = 4.50/4.50/4.33 are unchanged, and the note remains
DRAFT.**

## 1. Review section 2, language mean - rejected

The review states three values for the `good` language mean: 4.83 (positive
band), 4.94 (scale set) and 4.667 (candidate JSON), and concludes the note
contradicts itself.

Direct read of `out/key2_calibration/thresholds_candidate_v2.json`:

```
good.language.mean            4.944
planted_error.language.mean   4.667
long_wrong.language.mean      4.667
```

4.667 is the language mean of `planted_error` and of `long_wrong`, not of
`good`. There is no three-way disagreement. The candidate JSON is the only
candidate file in the directory, dated 2026-11-24, and its `good` row reads
4.944.

The 4.83 against 4.94 difference is real and is not a contradiction:

| figure | material | mean |
|---|---|---|
| 4.83 | 18 `good` texts truncated to 256 B (positive band) | 4.833 |
| 4.94 | 18 `good` texts at full length (scale set) | 4.944 |

Recomputed from the two judge outputs: the positive band has language values
`[4, 4, 4, 5 x 15]` and the full-length set `[4, 5 x 17]`, so truncation costs
two items one point. The frozen language `M_d` uses the truncated band,
4.833 - 0.5 = 4.33.

**Applied:** section 2 of the note now states both figures, says which one
`M_d` derives from, and explains the truncation. Section 9 asks the operator to
confirm that source. **Rejected:** the conclusion that the note binds an
unreconciled number.

The review's secondary question in the same section - whether coherence and
language exact agreement both being 69.2 % indicates a shared source - was
checked item by item against the two judge outputs and does not. Both are
74/107, but the exact-match item sets differ: intersection 58, symmetric
difference 32. It is a coincidence of counts.

## 2. Review section 1, margin justification - partially applied

The table below is read from the `bands` block of the candidate JSON and
recomputed from the eight v2 judge outputs; the two agree on every cell:

| dimension | negative max | `F_d` | positive mean | `M_d` |
|---|---|---|---|---|
| coherence | 1 | 2 | 5.00 | 4.50 |
| relevance | 1 | 2 | 5.00 | 4.50 |
| language | 2 | 3 | 4.833 | 4.33 |

The format-constrained sensitivity (four items dropped, language 4.857) and the
margin sweep (4.70 / 4.50 / 4.30 and 4.53 / 4.33 / 4.13) match the candidate
JSON as well.

Two corrections to the review's reasoning:

- "any margin in `[0, 2]` passes both" is loose. The actual bound is
  margin < 4.0 on coherence and relevance (positive mean 5.00, negative mean
  1.00) and margin < 3.35 on language. `[0, 2]` is a safe subset, not the range.
- The proposed replacement justification - that 4.50 sits between the
  fluent-wrong controls at 3.82-3.89 and the perfect band - conflicts with the
  review's own section 3. Those controls are required to stay at coherence 3 or
  above; calling 4.50 a boundary above them would make the record treat
  acceptable controls as a rejection zone.

**Applied:** section 1 now states positively that the margin is a host-strictness
choice rather than a calibrated quantity, gives the real bounds, and says the
scale controls are not the reference for `M_d`. **Rejected:** the specific
justification the review proposes.

## 3. Review section 3, option (b) - applied, with one residual

Option (b) is adopted as the recommendation, with draft exemption wording that
covers internal contradictions and unrecoverable propositions.

One correction: (b) does not clear every cell. `cert_en09_audience_violation`
scores 2 with both seats at or below 3, and its defect is format and relevance -
four reasons where two were requested, one off-topic - not contradiction and not
word salad. Under v2 that coherence score is arguably a format leak, and it
survives the exemption. Section 4.1 now names it as a recorded exception that
the signed wording must carry.

## 4. Review section 4, `bad` above `M_d` - applied

Section 3 of the note now states that `bad` passes coherence (4.94) and fails
relevance (4.06), and why that is the instrument working at its boundary rather
than a coherence failure.

## 5. Review section 5, sign-off additions - applied

All three are in section 9, plus a fourth for the language-source confirmation
from item 1 above:

- confirm the language `M_d` derives from the truncated band;
- resolve 4.1 and name `cert_en09` if (b) is chosen;
- decide whether the human positive band is awaited;
- accept that dissociation A and the 100M/90MB ordering check were not run.

## 6. Review sections 6 and 7 - agreed

Force-adding the calibration bytes is accepted as the right call and is still an
operator decision. The rubric flip to `FROZEN` with the new hash written back in
the same commit is accepted.

## 7. What did not change

`F_d` = {coherence 2, relevance 2, language 3}; `M_d` = {4.50, 4.50, 4.33} at
margin 0.5. At the time of this response the note was DRAFT, section 9 was
unsigned, and the candidate JSON was dated 2026-11-24 with sha256
`0dbe35c1dee8b535b28e635d9ef41b862dfc6066bd70c4c5455aec786c1ce06d`.

## 8. Postscript (2026-11-24, after sign-off)

The operator signed the freeze the same day, with three additions: the `bad`
coherence value above `M_d` is recorded as intentional, the
`cert_en09_audience_violation` exception is named in section 4.1, and the human
read row of the instrument gate records the GPT calibration read in its place.

Consequences for section 7 above: the note is now `FROZEN` and signed; the
rubric file was flipped to `FROZEN` (file hash `dc510274...b2235bd2`, system
prompt unchanged at `9edfd92d...42124`); the calibration bytes were force-added
with `out/key2_calibration/FROZEN_MANIFEST.json`; and the candidate JSON was
regenerated with `status: FROZEN`, giving sha256
`c341edb48c5fc446f1bd7f1567797df888ed82d04f032f11c0d7199f29c0d957`. The
thresholds are numerically identical. Regeneration also sorts the `scale` keys,
which the previous file did not, so re-running the analyzer now reproduces the
same bytes.
