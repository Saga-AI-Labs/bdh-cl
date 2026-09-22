# Sonde B - legal-leak content probe pre-registration

Date: 2026-09-22 (UTC) - Seat: A0-Quinn (saga) - Status: DRAFT until frozen pre-run
Frozen design of record, written BEFORE any content-side measurement.

Companions:
- thread narrative: docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-thread-report.md
- the result this interrogates: docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-window-report.md
- operator GO: per-crop look at what distinguishes the surviving 7 and 5 leakers from the stayers.

---

## 0. What is being asked, and what I can actually measure

The window probe left 7 (seed-2) and 5 (reference) legal crops that still route downward at window 384,
against 193 and 195 stayers. The operator asked what distinguishes them by content, length, or corpus
position.

Two facts constrain the design before anything is computed:

1. **The existing dumps contain arithmetic only** (`crop_idx|scoreA|scoreB|margin|lateA|lateB|chosen`).
   Nothing about the crop text or its position is in them. A content probe therefore needs a map from
   crop index back to corpus bytes.
2. **Crop length is not a variable.** Every crop is `block_size` = 512 bytes by construction
   (`arr[i : i + bs]`), so "length in bytes" cannot distinguish anything. The nearest honest analogue
   is *word/token length statistics inside the crop*, which this probe includes.

## 1. Recovering the crop-to-byte map (no GPU needed)

`scripts/eval_router.py` draws crops as:

    arr = np.frombuffer(open(path,"rb").read(mb * 1_000_000)[-2_000_000:], dtype=np.uint8)
    hi  = len(arr) - bs - 1
    crops = stack([arr[i:i+bs] for i in torch.randint(hi, (crops,), generator=g)])

with `g = torch.Generator().manual_seed(1234)` created once and consumed **sequentially in domain
order** (prose, code, math, legal, ga). Legal is the fourth draw, so the map must be rebuilt by
consuming the three preceding draws first.

- Corpora: the five files at `data/textmix*` and `data/europarl/`, last 2,000,000 bytes each (that is
  all the sampler ever reads; `mb=30` truncates first, then the tail is taken).
- The legal corpus is byte-stable and pinned: md5 `0135960429085039dbe5385f649e75fe`.
- **Validation, declared before the run:** the map is rebuilt twice - once inside a guest-side script
  that mirrors the sampler lines verbatim, once locally from fetched tails. The two offset lists must
  agree on all 200 legal crops. If they disagree, the map is wrong, the probe is void, and the
disagreement is the finding.
- No GPU claim is required for any of this: the sampler is CPU torch.

## 2. Baseline being characterised

Per ladder, from the window-384 dumps (already measured, no re-run):

| ladder | leakers | stayers |
|---|---|---|
| seed-2 | 7 | 193 |
| reference | 5 | 195 |

Leaker sets at window 384: seed-2 `[80, 122, 135, 148, 149, 151, 164]`; reference `[41, 50, 131, 149, 166]`.

## 3. Features, declared in advance

All features are computed from the 512 bytes of the crop at its recovered offset.

**Content (byte-level, no tokenizer):**

- `letters` - fraction of ASCII letters
- `digits` - fraction of ASCII digits
- `space` - fraction of whitespace (space, tab, newline)
- `punct` - fraction of printable non-alphanumeric, non-space
- `highbit` - fraction of bytes >= 128 (the corpus is not guaranteed pure ASCII)
- `newlines` - count of `\n`
- `entropy` - Shannon entropy of the byte histogram, bits
- `uniq` - number of distinct byte values

**Word/token-shape (the honest stand-in for the constant 512-byte length):**

- `mean_word` - mean run length of consecutive non-space bytes
- `max_word` - longest such run
- `words` - count of such runs

**Position:**

- `offset` - byte offset within the 2,000,000-byte sampling window
- `distance_to_end` - `hi - offset`
- `cluster_span` - max minus min leaker offset, per ladder (a set-level statistic, see D3)

**Arithmetic, already measured at window 384 (reused, not recomputed):**

- `abs_margin` - `|scoreA - scoreB|`
- `late_delta` - `lateA - lateB` (positive means the chosen width serves that crop worse)

## 4. Declared comparisons and decision rules

For each ladder separately, each feature is compared leakers vs stayers. With n = 7 and n = 5 this is
descriptive only; **no test statistic and no p-value is claimed.**

- **D1 (feature separation):** for each feature, report the leaker median and the leakers' percentile
  position inside the stayers' distribution. A feature is called **separating** only if the leaker
  median falls outside the stayers' 5th-95th percentile interval AND the same direction holds on both
  ladders. Anything else is reported as **not separating**.
- **D2 (arithmetic sanity):** recompute `abs_margin` and `late_delta` from the dumps for leakers and
  stayers at window 384. Declared expectation, from the margin and window probes: leakers sit at low
  margins (near the decision boundary) and are usually served worse at the chosen width. This is a
  consistency check on the pipeline, not a new claim.
- **D3 (position):** report leaker offsets, their span, and where that span sits within the 2 M window.
  Declared as separating only if the leaker span is smaller than 5,000 bytes AND holds on both ladders.
- **D4 (overlap with the withdrawn core):** report whether the previously-withdrawn crops 114 and 161
  (which stopped leaking by window 384 on both ladders) differ from the surviving leakers on any
  separating feature. Descriptive.

## 5. What this probe cannot do, stated up front

- n = 7 and n = 5. It cannot establish a rate, a causal feature, or a predictive rule. It can only say
  whether the surviving leakers differ from the stayers on a declared feature enough to motivate a
  follow-up.
- If nothing separates, the honest conclusion is that the residual half of the flip is **not explained
  by crop content or position as measured here**, and that is a result worth reporting as such.
- It does not touch P1 (falsified at 189, band {191..199}), the ablation, or the window result's
  attenuation claim.

## 6. Expected cost and outputs

- Guest side: one CPU-only script (no GPU claim, no training, no writes to `out/` or `out_a/`).
- Local side: fetch five corpus tails (~10 MB), rebuild the map, compute features.
- Raw: `out_c/sondeB/harvest/leakcontent_w384.txt` (per-crop feature table, both ladders).
- Report: `docs/reports/phase_2/2026-09-22_sonde-B-legal-leak-content-report.md`
- Bus: intent before, done after, three-way SHA on both commits.
