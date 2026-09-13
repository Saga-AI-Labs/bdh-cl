# Tier 1: disjoint-crop router split — results

**Author:** A0-Quinn · **Date:** 2026-09-13
**Pre-registration:** bdh/6bf28f5 (`scripts/quinn/tier1_router_split.py`, gates in the docstring, fixed before any number existed) · **Bus kickoff:** #256
**Run:** gx10 (GB10), 04:34–07:09 CEST, eval-only, GPU idle-to-idle · **Checkpoint:** `out/bdh_europarl_ladRA2b-lt_last.pt` (6.9 GB; sha256 prefix `cada61d7…` verified earlier against the manifest) · **Data:** Europarl v7, one side per domain, last-2-MB held-out window split in two disjoint halves.

## Why this exists

The fourth external review claimed routing is circular: the router selects on the first 128 tokens of a crop and serves the remaining 384 of the *same* crop, so `routed == acquisition` might flatter itself. Rev 4.6 names that property in prose (routed **is** oracle serving at 100 % accuracy). Tier 1 turns the prose into a measurement: does a route chosen on crops the serving phase never saw still resolve to the true prefix width?

## Design (from the pre-registration)

Per domain, crops are drawn from two disjoint halves of a 2 MB held-out window. **Selection crops** (early half, 30) choose one fixed route per domain by mean early-position NLL. **Test crops** (late half, 30) are served under that fixed route, and additionally online (per-test-crop argmin, the paper protocol), oracle (the domain's true width), and joint (full width).

| Gate | Definition | Result |
|---|---|---|
| G1 | fixed route == oracle width on all 20 domains | **20/20 PASS** |
| G2 | fixed-test perplexity in the online-vs-oracle band | fixed/oracle == online/oracle == 1.0000 on all 20 (by construction, see note) |
| G3 | fixed-test perplexity within the +4.3 % / +8.0 % routed-cost band of rev 4.6 | **partially met — see below** |
| G4 | selection and test crops disjoint by index range | held (max selection offset + block ≤ mid < min test offset) |

## G1 — the answer to the reviewer

A route chosen **only** from the disjoint selection crops resolves to the true acquisition width for all 20 domains (en→8192, es→10240, …, lt→47104). Selection generalizes crop-to-crop; the `routed == oracle` statement is not a same-crop artifact.

## The 1.0000 note (read this before distrusting the result)

`fixed/oracle == online/oracle == 1.0000` everywhere is **by construction, not a miracle**: on every test crop, fixed, online, and oracle all serve the same prefix width, so all three means of the late-position NLL are identical. The informative number is the G1 assignment (20/20), not the perplexity ratios. Do not read the exact 1.0000 as corroborating evidence; it is an algebraic consequence of G1 + oracle agreement.

## G3 — honest, not shiny

Fixed-route perplexity against each domain's own acquisition exit (from `docs/reports/data/2026-09-05_ra2b_acquisition.csv`):

| domain | fixed ppl | exit | Δ | domain | fixed ppl | exit | Δ |
|---|---|---|---|---|---|---|---|
| en | 2.365 | 2.29 | +3.3 % | it | 3.066 | 2.89 | +6.1 % |
| es | 2.620 | 2.42 | +8.3 % | et | 3.681 | 3.26 | +12.9 % |
| pl | 3.195 | 3.04 | +5.1 % | el | 6.236 | 6.36 | −2.0 % |
| fr | 2.494 | 2.43 | +2.6 % | sk | 3.636 | 3.58 | +1.6 % |
| de | 2.965 | 2.73 | +8.6 % | sv | 3.162 | 3.08 | +2.7 % |
| cs | 3.783 | 3.48 | +8.7 % | ro | 3.320 | 3.26 | +1.9 % |
| da | 2.932 | 2.85 | +2.9 % | nl | 3.158 | 3.07 | +2.9 % |
| pt | 2.826 | 2.66 | +6.2 % | sl | 3.596 | 3.50 | +2.7 % |
| fi | 3.410 | 2.98 | +14.4 % | lt | 3.972 | 3.83 | +3.7 % |
| hu | 3.066 | 2.88 | +6.5 % | bg | 6.564 | 6.09 | +7.8 % |

Median **+5.1 %**, range −2.0 % (el) to +14.4 % (fi). Five domains exceed +8 % (es, de, cs, et, fi).

**What this is:** a 30-test-crop sample from one disjoint window half, not the 40-crop protocol behind the manuscript's +4.3 %/+8.0 % statement. The wider spread is plausibly crop-window variance, but that is an interpretation — the measurement itself is only that the Tier-1 fixed-route serve lies between −2 % and +14 % of the acquisition exit on this sample. The manuscript's routed-cost band is unaffected in direction (fixed serving still costs small percentages), but **the +8.0 % upper bound should not be quoted as if this sample confirmed it**; it was not re-tested at the manuscript's 40-crop setting.

## What changed in the manuscript (recommendation)

- §5 Routing: the oracle clause may now add "and a disjoint-crop run confirms the assignment (20/20; bdh/b0febc3, Tier 1)".
- The +4.3 %/+8.0 % band: no change to the numbers in the manuscript; do **not** merge the Tier-1 G3 sample into it (30 ≠ 40 crops).
- §open problems: not needed — no falsifier triggered (fixed never exceeded online anywhere).

## Verdict

G1 and G4 clean. G2 is an algebraic 1.0 and carries no independent evidence. G3 is a partial miss on a smaller protocol and is reported as such. Nothing about the reviewer's circularity concern survives contact with the data: routing on unseen crops resolves perfectly. The result is one small strengthening sentence in the manuscript, not a new headline.

- A0-Quinn, 2026-09-13
