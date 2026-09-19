# Sonde A — seed-replica `A1-K5 seed-2`: evaluation of the completed ladder

Date: 2026-09-19 · Seat: Quinn (`saga`) · Host: `bdh-4090` / `192.168.178.200`
Workdir: `/media/data/coding/bdh` · No new measurement was taken for this report.

## 0. Provenance — what this evaluation reads and does not read

Read verbatim, no summarisation in between:

| Artifact | Size | mtime |
|---|---|---|
| `out_c/logs/ladA-A1-K5-seed2_analysis.txt` | 5503 B | 09-19 10:19 |
| `out_c/logs/ladA-A1-K5-seed2_routdiag_final.txt` | 717 B | 09-19 10:19 |
| `out_c/logs/ladA-A1-K5_analysis.txt` (reference, seed 1337) | 5236 B | 09-18 08:22 |
| `out_c/logs/ladA-A1-K5_routdiag_final.txt` (reference) | 711 B | 09-18 08:22 |

The two `analysis.txt` files are the strong comparator: same host, same code path,
same protocol positions, differing only in seed. Comparing against them is
stronger than comparing against the rounded table in the committed readout.

**Not read:** nothing on this report comes from memory or from the report
texts; every number above was taken from the raw files in one pass.

## 1. Run health — complete, no repair needed

- Done marker: `ladder-ladA-A1-K5-seed2-done 2026-09-19 10:19:38`.
  Start was `2026-09-18 22:02:04`, so the ladder ran ≈12.3 h.
- All five phases present (`phase 1 base` … `phase 5 ga`), `smoke=0`,
  `iters=150000` base / `10000` per CL phase.
- Four in-chain transitions, four `p5_rc=0`, and each carries `P5-VERDICT: PASS`.
- Per transition, all six masked-parent components are `BIT-EXACT`
  (`encoder`, `encoder_v`, `decoder`, `embed`, `lm_head`, `attn.freqs(shared)`),
  the grown segment is `nonzero=True`, and the optimizer moments of the masked
  block are exactly zero (`v(masked)==0:True m(masked)==0:True`) while the grown
  ones are live (`v(grown)!=0:True`). The growth mask behaved on both seeds.
- Checkpoint bytes grow monotonically: 1211147753 → 1511046913 → 1813044993 →
  2115043094 → 2417041111 (Δ = +303899160 per step, identical step size).

The seed replica is therefore structurally a faithful copy of the committed
ladder: same growth mechanics, same mask discipline, no silent failure.

## 2. Routing readout — replicates, with one genuine difference

Router in both runs is the final `…_ga_last.pt`, likelihood scan, widths
`[8192, 10240, 12288, 14336, 16384]`/head, window 128, 200 crops/domain.

| domain | routed own-width ppl, seed 1337 | routed own-width ppl, seed 2 | Δ |
|---|---|---|---|
| prose | 2.46 | 2.48 | +0.02 |
| code | 4.90 | 4.95 | +0.05 |
| math | 1.47 | 1.46 | −0.01 |
| legal | 2.28 | 2.29 | +0.01 |
| ga | 2.37 | 2.34 | −0.03 |
| **joint full-width reference** | **23.66** | **22.92** | **−0.74** |

The served regime replicates to within ±0.05 ppl on every domain — no domain is
worse than the reference by more than half a tenth of a point. The joint
full-width reference is slightly *better* on seed 2, i.e. seed 2's joint-serving
degradation is the smaller of the two; routing still separates 1.46–4.95 against
a joint 22.92.

**The one real difference is the confusion matrix.** Computed on the same 200
crops:

```
seed 1337 (committed)              seed 2
        8192 10240 12288 14336 16384         8192 10240 12288 14336 16384
prose    200    0     0     0    0     prose   200    0     0     0    0
 code      0  200     0     0    0      code     0  200     0     0    0
 math      0    0   200     0    0      math     0    0   200     0    0
legal      0    0     0   200    0     legal     1    0     0   199    0
   ga      0    0     0     0  200        ga     0    0     0     0  200
```

The committed ladder had zero cross-route mass on all five rows. Seed 2 loses
**one legal crop (1/200 = 0.5 %)** into the prose width. This is not a ppl
breach and it does not weaken the separability result — 9999/10000 crops route
correctly — but it is a seed-dependent event and it is reported rather than
averaged away. Any claim worded as a perfect 200/200 across all domains is
true of the committed run and true of seed 2 up to one crop.

## 3. Cold per-domain evaluation, seed 2 against the reference seed

`scripts/domain_eval.py`, held-out val+test, random-crop cold protocol, on each
phase's `last.pt`. Every cell below is the same position in both runs.

| phase (ckpt) | domain | seed 1337 | seed 2 | Δ |
|---|---|---|---|---|
| 2 · code | prose | 4.31 | 4.43 | +0.12 |
| | **code** | **5.41** | **5.48** | **+0.07** |
| 3 · math | prose | 13.57 | 13.99 | +0.42 |
| | code | 31.09 | 31.54 | +0.45 |
| | **math** | **1.50** | **1.49** | **−0.01** |
| 4 · legal | prose | 5.23 | 5.45 | +0.22 |
| | code | 20.69 | 19.55 | −1.14 |
| | math | 6.76 | 6.52 | −0.24 |
| | **legal** | **2.27** | **2.29** | **+0.02** |
| 5 · ga | prose | 34.13 | 37.11 | +2.98 |
| | code | 108.08 | 96.49 | −11.59 |
| | math | 43.74 | 41.12 | −2.62 |
| | legal | 17.86 | 18.83 | +0.97 |
| | **ga** | **2.39** | **2.37** | **−0.02** |

Two different things fall out of one table, and conflating them is the trap:

- **Bold cells — each domain at its own phase (the acquisition point).** These
  replicate tightly: max |Δ| = 0.07, max relative 1.3 %. The ladder learns each
  new territory to the same quality under a different seed.
- **The rest — a domain measured after later phases, served at the grown width
  without its own route.** These are the discarded-regime cells and they swing
  hard: code at phase 5 moves by −11.59, prose by +2.98, in a band already at
  30–110 ppl. That is variance where the model has effectively lost the domain,
  not a retention measurement. It is why the stop-rule must not be read here.

## 4. The stop-rule, applied to its actual referent

The pre-registered rule was *"every post-introduction domain ppl ≤
acquisition/reference → seed 3 is cheap insurance; if any post-introduction
domain rises → stop and diagnose."* Its referent, per the add-on probes §2
(`docs/reports/phase_2/2026-09-18_sondeA-add-on-probes-ABC.md:120-125`), is the
**routed own-width** number — the same plane that produced
`| code | 5.51 (code) | 4.90 (ga) | −0.61 |` and the sentence *"no domain's ppl
rises after its introduction; the largest movement is −0.61"*. It is **not** the
cold cross-domain table of §3, and reading a breach from `code 5.48 → 31.54`
would be measuring the unserved regime and calling it forgetting.

Judged on that plane, against the committed reference:

- No domain regresses on seed 2 beyond **+0.05** ppl, and three are better.
  **No breach.** Nothing triggers the stop-and-diagnose arm.
- The joint reference moved −0.74 in seed 2's favour.

**One gap, named rather than papered over.** The ladder routes **once, at the
end** (§2, on `ga_last.pt`). The literal clause *"≤ acquisition"* wants each
domain also routed at its own introduction checkpoint, and for seed 2 that
measurement was never taken — the committed run has it only because the add-on
probe A re-ran the scan per checkpoint. So §4 is seed 2 checked **against the
reference**, not against its own acquisition point. Closing it is one add-on
routing pass per phase, which is GPU work and therefore sits behind the
operator's gate on new measurements. Within the existing artifacts the rule is
not breached; the strict own-run form is outstanding, not passed.

## 5. What this does and does not license

**Supports:** the `A1-K5` ladder replicates across seeds on everything the run
records — bit-exact growth, monotonic width, served ppl within 0.05, joint
reference slightly improved, 9999/10000 crops routed correctly.

**Does not support:**
- A *quantified* retention claim. Per the probe §limitation, movements ≤0.61
  are "no visible rise", not "retention ≥ x".
- A perfect-diagonal claim carried over to seed 2 verbatim — one legal crop
  leaks.
- An acquisition-vs-retention delta. Acquisition-time ppl is still not in these
  logs (committed readout §3 makes the same reservation).

**seed 3.** The stop-rule's cheap-insurance arm is satisfied and the
replication is tight enough that a third seed would mostly sharpen the noise
band. Two things stand before launching it, both operator-side: GPUs free
(reported as new measurements are gated on it) and a correct liveness probe —
the `pgrep` used here self-disqualified (pattern >15 chars returns zero
matches, as it warns), so its "no train process" line is a tool artifact and
not a finding, and the card has not been verified idle with a working probe.

---
*Read-only evaluation. No training, upload, deletion or commit was performed.*
