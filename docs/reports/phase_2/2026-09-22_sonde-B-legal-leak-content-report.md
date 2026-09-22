# Sonde B - legal-leak content probe report

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: **COMPLETE**
Result of the pre-registered run of record: `docs/plans/2026-09-22_sonde-B-legal-leak-content-prereg.md`
Thread narrative: `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-thread-report.md`
The result it interrogates: `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-window-report.md`

---

## 0. The question, and the answer in one line

The window probe left 7 (seed-2) and 5 (reference) legal crops still routing downward at scoring window
384, against 193 and 195 stayers. The operator asked what distinguishes those crops by content, length,
or corpus position.

**Answer: nothing measured here does.** No declared content, word-shape, or position feature separates
the surviving leakers from the stayers on both ladders. The honest conclusion is that the residual half
of the flip is **not explained by crop content or position as measured in this probe** - which is a
result, not a failure to find one.

## 1. What was fixed before measuring

The pre-registration declared, before any content was read:

- the crop-to-byte map must be rebuilt by consuming the seeded sampler in domain order (legal is the
  **fourth** draw: prose, code, math, legal, ga), because the generator is consumed sequentially;
- crop **length is not a variable** - every crop is `block_size` = 512 bytes by construction, so
  word-shape statistics are the honest stand-in for what the request called "length";
- the feature list, the separating rule (leaker median outside the stayers' p5-p95 interval **and** the
  same direction on **both** ladders), and the statement that at n=7 and n=5 no rate and no p-value are
  claimed.

## 2. The map, and its validation

The sampler is `arr = np.frombuffer(read(mb*1e6)[-2_000_000:], uint8)`, `hi = len(arr) - bs - 1`,
`torch.randint(hi, (200,), generator=g)`. All five corpora exceed 30 MB, so every domain reads exactly
30,000,000 bytes and every tail is exactly 2,000,000 bytes: **`hi` = 1,999,487 for all five**.

- Rebuilt **twice**: once on the guest with the torch that ran the evaluations (2.13.0+cu130), once
  locally from the fetched tails (2.4.0+cpu).
- **200 of 200 legal offsets identical across the two runs** - a genuine cross-version check, since
  the two environments differ in torch and numpy major-minor.
- Corpus identity recorded in the same run: prose `8a2d5ab8...`, code `82fe4bf1...`, math `6a1a069e...`,
  legal `0135960429085039dbe5385f649e75fe` (matches the pinned hash), ga `e170553d...`.
- CPU only. No GPU was claimed: the sampler is CPU torch.

## 3. Result 1 - no separating feature (D1)

Feature medians for leakers vs the stayers' 5th-95th percentile interval, per ladder. Frozen rule:
separating only if the leaker median falls **outside** that interval **and** the same direction is seen
on both ladders.

| feature | seed-2 | reference | verdict |
|---|---|---|---|
| letters | inside | inside | not separating |
| digits | inside | inside | not separating |
| space | inside | inside | not separating |
| punct | inside | inside | not separating |
| highbit | inside | inside | not separating |
| newlines | inside | inside | not separating |
| entropy | inside | inside | not separating |
| uniq | inside | inside | not separating |
| mean_word | inside | inside | not separating |
| max_word | inside | inside | not separating |
| words | inside | inside | not separating |
| offset | inside | inside | not separating |
| distance_to_end | inside | inside | not separating |
| abs_margin | **below** (0.0180 vs p5 0.0219) | inside (0.0263 vs p5 0.0231) | not separating |
| late_delta | inside | inside | not separating |

**SEPARATING features: NONE.**

The last two rows are the arithmetic already known from the earlier probes, included only as a
consistency check. They behave exactly as the frozen rule should make them behave: `late_delta` is
positive and similar on both ladders (median 0.0263 and 0.0320 - leakers are usually served worse at
the width the router chose), while `abs_margin` clears the interval on seed-2 alone and therefore fails
the both-ladders condition. That is the same near-boundary, ladder-dependent picture the margin probe
reported at window 128, and the window-384 medians above show the same thing: `late_delta` 0.0263
and 0.0320 on the two ladders, `abs_margin` outside the interval on seed-2 only. **It is not
promoted here**, because the frozen rule requires both ladders.

## 4. Result 2 - no positional structure (D3)

Leaker byte offsets within the 2,000,000-byte sampling window (`hi` = 1,999,487):

- seed-2 (7): `113608, 116189, 1165654, 1169289, 1188563, 1389391, 1391448` - span **1,277,840**
- reference (5): `113608, 540028, 848796, 848837, 1275670` - span **1,162,062**

Frozen rule: separating only if the span is under 5,000 bytes on both ladders. **Verdict: not
separating.** The leakers are spread across most of the window on both ladders.

## 5. Two descriptive details the offsets did expose

Reported because the probe declared position as a feature, and both are computed from the offsets
that the two independent rebuilds produced identically (200 of 200, section 2), not eyeballed. Neither survives the frozen rule and neither is promoted.

1. **Exactly one byte range leaks on both ladders: offset 113608.** It is crop 149 on seed-2 and also
   crop 149 on the reference ladder - the only surviving leaker shared by the two ladders, and it
   routes downward on both. Every other surviving leaker is ladder-specific.
2. **On the reference ladder two leakers overlap heavily:** crops 41 (848796) and 131 (848837) share
   471 of 512 bytes, 92 percent. Merging them, the reference ladder's 5 leakers cover only **4 distinct
   byte ranges**. Effective independent n on the reference ladder is therefore 4, not 5 - which makes
   the negative result slightly stronger, not weaker.

## 6. Resolution against the pre-registered outcomes

- **D1 (feature separation): NONE.** No content, word-shape, or position feature separates on both
  ladders. The two arithmetic features behave as expected and are not promoted.
- **D2 (arithmetic sanity): values on the line.** |margin| median leakers 0.0180 / 0.0263 against
  stayers 0.0857 / 0.0838; leakers served worse at the chosen width 5/7 and 4/5. The pipeline gives
  the same arithmetic as the earlier probes.
- **D3 (position): not separating.** Spans 1,277,840 and 1,162,062 bytes against a 5,000-byte threshold.
- **D4 (withdrawn crops):** the previously-withdrawn crops 114 and 161 sit inside the surviving
  leakers' feature ranges (114: letters 0.799, entropy 4.266, mean_word 5.08; 161: letters 0.717,
  entropy 4.760, mean_word 4.82; surviving medians 0.79 / 4.40 / 4.64). Nothing distinguishes them from
  the crops that still leak, which is consistent with the window probe: they stopped leaking because
  the window grew, not because their content is different.
- **Map validation:** 200 of 200 offsets identical across torch versions (torch 2.13.0+cu130 on the
  guest, 2.4.0+cpu locally).

## 7. What this means, and what it does not

**It means:** the surviving downward flips are **not a content signal**. They are not specific words,
numbers, punctuation patterns, entropy levels, lengths, or positions in the corpus. Combined with the
window result (the leak attenuates with window length but does not vanish), the residual half of the
flip looks like a property of the **scoring arithmetic near the decision boundary**, not of the text
being scored.

**It does not mean** the flip is unexplainable. It means the explanation is not in the crop bytes as
this probe measured them - byte histograms, word runs, and offsets. Not covered here: how the early-window
score is composed across positions (per-token contributions near the boundary), and whether the two
prefixes' scores differ in shape rather than in level. Both are instrument-side questions, not
content-side ones.

**Limits of this sample:** n was 7 and 5; nothing here can rule out a content effect too small to appear at
this sample size. The result is a bound, not a proof of absence.

P1 remains falsified at 189 against band {191..199}; the ablation and window results stand as reported.

## 8. Provenance of record

- Raw: `out_c/sondeB/harvest/leakcontent_w384.txt` (38 lines, md5 `9e730274cb07fc81a6bd37aa26572488`),
  `out_c/sondeB/harvest/leakcontent_offsets.txt` (200 lines, md5 `6fb994425e328c0c6271dc1fd1793ebf`) -
  both copied to the guest at the pre-registered path with matching hashes.
- Analysis: `out_c/sondeB/leakcontent_analyze.py` (frozen D1-D4 rules coded literally, asserts the
  dump-derived leaker sets equal the pre-registered baselines before comparing); `out_c/sondeB/leakmap_guest.py`
  (guest map rebuild); the local rebuild consumes the five fetched 2 MB tails.
- Pre-reg `fc7896e6`; inputs are the window-384 dumps of the window probe (`494fe52` / `9cd5df68`).
- Read: the full analyzer output, the guest map output including all five corpus md5s, the local map
  comparison (MISMATCH_COUNT 0), and the overlap computation.
- Check not run: no tokenizer-based features (byte-level only); no per-position decomposition of the
  early-window score. Both named in section 7 as the content-side probe's limits.
