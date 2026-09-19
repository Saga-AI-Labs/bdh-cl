# Sonde A — seed-replica `A1-K5 seed-2`: evaluation of the completed ladder

Date: 2026-09-19 · Seat: Quinn (`saga`) · Host: `bdh-4090` / `192.168.178.200`
Workdir: `/media/data/coding/bdh` · §1–§3 and §5 are read-only, taken from the
committed artifacts with no new measurement. §4b is the one exception: it is a
new measurement, run under the operator's GO after this report's first version
was already committed, and the sentence that used to stand here — "no new
measurement was taken" — was by then false of its own document.

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
reference**, not against its own acquisition point. Closing it needed one
add-on routing pass per phase -- GPU work, so it sat behind the operator's gate
on new measurements. That pass was taken after the first version of this report
had already been committed, under the operator's GO, and it is §4b: the strict
own-run form is now measured and it holds. The sentence that closed this section
on first writing read *"outstanding, not passed"*, which was true of the
artifacts then and is not true of the document now -- so it is kept as a dated
statement of what §4 alone could see, and §4b is the later measurement that
closes it.

## 4b. The gap closed — intra-run acquisition scan, five passes

Operator GO taken for the missing measurement. Five `eval_router` passes over the
five committed `…_last.pt`, each against the full accumulated five-domain spec,
flags copied verbatim from the committed ladder's own routing call (`--routes
8192,10240,12288,14336,16384 --crops 200 --window 128 --batch 4`). Read-only on
the checkpoints, serial, no training, nothing written under `out/` or `out_a/`.
Artifacts `out_c/logs/ladA-A1-K5-seed2_acqroute_{base,code,math,legal,ga}.txt`,
sizes 719/718/719/719/717 B, one `acqroute_rc=0` each.

Served own-width ppl, one column per checkpoint (the value each domain gets
*routed to its own width* at that point in the ladder):

| checkpoint (domain introduced) | prose | code | math | legal | ga |
|---|---|---|---|---|---|
| base (**prose**) | **2.48** | 159.77 | 59.14 | 4.85 | 27.97 |
| code (**code**) | 2.48 | **4.95** | 15.06 | 4.27 | 20.17 |
| math (**math**) | 2.48 | 4.95 | **1.46** | 4.27 | 20.17 |
| legal (**legal**) | 2.48 | 4.95 | 1.46 | **2.29** | 20.17 |
| ga (**ga**) | 2.48 | 4.95 | 1.46 | 2.29 | **2.34** |

Bold = each domain at its own introduction checkpoint, i.e. its **acquisition
point**. The rule's clause *post-introduction ≤ acquisition* compares every cell
**at or right of** the bold one in its row against that bold value.

**On the valid field the comparison is equality, not tolerance.** prose 2.48→2.48,
code 4.95→4.95, math 1.46→1.46, legal 2.29→2.29 across every later checkpoint;
ga is measured only at its own point, 2.34. Every post-introduction movement is
**0.00** and no domain rises. The strict own-run form of the stop-rule is now
measured and **holds**. It is not a near-miss absorbed into a ±0.05 band: a
domain's served ppl does not move at all once introduced, because the phase that
owns it stops being touched — which is the P5 `BIT-EXACT` result re-expressed
through the router.

**The lower triangle is not a decline and must not be read as one.** `code 159.77`
at base is code *before it has ever been trained*, served at the prose width
because at base the router sends all five rows to 8192. Its acquisition value is
4.95 at the code checkpoint, not 159.77 at base. Reading `159.77 → 4.95` as a
drop, or `20.17 → 2.34` for ga as a drop, would compare a domain's untrained
pre-introduction state against its trained one — the same wrong-referent
operation as reading `5.48 → 31.54` as forgetting, mirrored. Only the bold
cell and the cells right of it are valid comparisons.

**Addressing arrives with the phases, visible in the confusion matrices.** At
base every row collapses onto 8192. Once code is introduced, code/math/ga move
onto 10240 and legal splits 50/150; once math is introduced math takes 12288 and
the split stays put; legal settles at 14336 and ga last at 16384. The one leak is
the stable `legal 1@8192` (199/200), present identically at the legal and the
final checkpoint — consistent with §2, seed-dependent, and not a ppl movement.

**Independent validation of the measurement itself.** The `ga` pass reproduces the
committed run's own final routing file line for line — 2.48 / 4.95 / 1.46 /
2.29 / 2.34 and joint 22.92 vs the 10:19 `…_routdiag_final.txt`. A second, hand-
run pass over the same checkpoints through a different script gives the committed
numbers, so the plane being judged is the plane the ladder reported.

**Method note, kept rather than tidied.** The first two tail passes (`legal`,
`ga`) came back `acqroute_rc=2` at 0 B GPU. The cause was in *my* driver, not the
data: a literal `\n` reached `argv` as `n n`, so `eval_router` got stray tokens and
never saw its flags — a form defect that took no GPU time and damaged nothing, and
the three completed passes were left untouched rather than re-run. They were
re-taken inline, one line per call. A claim of "five passes" that had papered over
this would have shipped a table with two cells from a broken invocation.

## 5. What this does and does not license

**Supports:** the `A1-K5` ladder replicates across seeds on everything the run
records — bit-exact growth, monotonic width, served ppl within 0.05, joint
reference slightly improved, 9999/10000 crops routed correctly.

**Does not support:**
- A *quantified* retention claim. Per the probe §limitation, movements ≤0.61
  are "no visible rise", not "retention ≥ x".
- A perfect-diagonal claim carried over to seed 2 verbatim — one legal crop
  leaks.
- An acquisition-vs-retention *delta* read as a forgetting rate. §4b supplies the
  acquisition column, so the comparison now exists — but its result is
  **equality**, and equality here is a statement about the ladder's update
  discipline (once a phase owns a width it stops being touched, hence P5
  `BIT-EXACT`, hence the served value cannot move), not a measured bound on
  forgetting dynamics. Movements ≤ 0.05 remain "no visible rise", not
  "retention ≥ x".

**seed 3.** The stop-rule's cheap-insurance arm is satisfied and the
replication is tight enough that a third seed would mostly sharpen the noise
band. Two things stand before launching it, both operator-side: GPUs free
(reported as new measurements are gated on it) and a correct liveness probe —
the `pgrep` used here self-disqualified (pattern >15 chars returns zero
matches, as it warns), so its "no train process" line is a tool artifact and
not a finding, and the card has not been verified idle with a working probe.

---
*Read-only evaluation. No training, upload, deletion or commit was performed.*
