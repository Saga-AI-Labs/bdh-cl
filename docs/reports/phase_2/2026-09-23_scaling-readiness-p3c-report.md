# Scaling readiness P3c - acquisition pairs and capacity ablation on the P3 ladder

Date: 2026-09-23 (guest local, ai box)
Seat: A0-Quinn
Status: complete, frozen verdicts applied as pre-registered
Pre-registration: `docs/plans/2026-09-23_scaling-readiness-p3c-prereg.md` (commit `8af5da4da21477363668dabe60d29f2d095c3005`)
Operator GO: "P3c + K20 als Referenz-Leiter klingt gut. Bitte vorbereiten und starten."

## 1. Question

P3 established that the mixed-domain ladder reaches K=8 with routing
accuracy 0.9931 and first-phase retention |delta| = 0.00, but it is a
mechanical pre-flight, not a capability proof: no matched pre-growth
comparison and no capacity-ablation test were taken (Pi-50, `m_bdh-cl_0000000455`).
This probe answers both, eval-only, on the existing checkpoints:

- **Acquisition.** For each phase `i`, is the ppl of domain `d_i` at its own
  width lower than the same domain's ppl on the pre-growth base checkpoint at
  the then-current width? The comparison is a matched pair: same corpus,
  same 200 crops, same window 128, same route width.
- **Capacity.** At the SAME checkpoint `ck_i`, is forcing the narrow route
  (`w_{i-1}`, which excludes the grown block) materially worse than the own
  width route (`w_i`)? If yes, the grown block carries load.

## 2. Instrument and controls

The instrument is `scripts/eval_router.py`, md5
`73832ecd08f24eded93a98a74572be6e`, on the guest unchanged. Driver
`/tmp/p3c_driver.sh`, md5 `337b5cbe271ea2758796578ad29a92f2`, verified identical on all sides, local and guest, before the launch. Every checkpoint was pinned by
md5 before its measurement and a mismatch aborts the run; all eight pins
matched, and the complete driver log carries the line `out_readonly=true`:
writes went only to `out_c/scaling_readiness/p3c/`, `out_a/` was read-only.

Pins, all equal to the pre-registration table:

| object | md5 | size |
| --- | --- | --- |
| base `A1-K5-seed2-base_last.pt` | `8680bd26ed55ddd2883bd077ad49e665` | 1211147753 |
| de `..._p3-de_last.pt` | `add1438f2dd673e3a0d8195e40acffcd` | 1511046577 |
| es | `d74921a9aa0049ae251bfbaffb9ecc41` | 1813044657 |
| pl | `e9707f8f88bed8c4fd1bf059ee0d4067` | 2115042737 |
| code | `89e90ecd7a8bb0c70e22d93a6447efa9` | 2417040859 |
| math | `081f95ba148deae32eb2f1f7cb683c0f` | 2719038939 |
| legal | `fd9f802d831f9e88e21206d448d9f4ff` | 3021037040 |
| ga | `8814ddc62d737e05c5c0b1fe221bd889` | 3323035057 |

Run window 10:26:50 to 10:31:35 guest local, 22 of 22 runs rc=0, each output
complete with the terminating `joint full-width reference: ppl` line, 318 to
327 bytes; the GPU claim `s_bdh-cl_000226_3e39d7` (exclusive,
`gpu://rtx4090`) was held for the whole window, renewed to 200 on each of the
three renewals, released with HTTP 204, and the registry shows no active
claims after the release; the card was idle at 287 MiB, 0 % with no
process left over.

Transfer proof: all 22 run outputs were re-hashed on the guest and locally
and compared file by file, zero mismatches (`ALL_MD5_MATCH`).

## 3. Control

`base @8192`, single route, domain `prose`: routed ppl **2.48**, joint
full-width reference 2.48, confusion diagonal 200/200. The pre-registered
expectation was 2.48 +/- 0.02, so F4 PASSES and the reading frame is
confirmed for all 22 runs of this probe, which share window 128, the 200
crops per domain, and the single seeded generator per domain.

## 4. Results

Routed ppl, window 128, 200 crops/domain, single route per run.
`gain = pre - served` (nats, positive means the grown checkpoint is better);
`load = narrow / served` (same checkpoint, narrow route excludes the grown
block).

| phase | pre (base, w_{i-1}) | served (ck_i, w_i) | narrow (ck_i, w_{i-1}) | gain | load ratio |
| --- | --- | --- | --- | --- | --- |
| de   | 13.5200 @8192  | 2.6000 @10240 | 13.5200 | 10.9200  | 5.2000 |
| es   | 11.6300 @10240 | 2.6400 @12288 | 26.3200 | 8.9900   | 9.9697 |
| pl   | 25.2500 @12288 | 3.0800 @14336 | 94.0000 | 22.1700  | 30.5195 |
| code | 165.2300 @14336| 6.5700 @16384 | 250.8700| 158.6600 | 38.1842 |
| math | 71.0600 @16384 | 1.7400 @18432 | 18.4100 | 69.3200  | 10.5805 |
| legal| 5.0800 @18432  | 2.5100 @20480 | 11.2400 | 2.5700   | 4.4781 |
| ga   | 27.1200 @20480 | 2.4800 @22528 | 49.1600 | 24.6400  | 19.8226 |

Against the frozen thresholds the verdicts are:

- **F1 acquisition, all seven phases: H-ACQ-POS.** Every gain is at least
  the 0.15-nat threshold, the smallest being legal at 2.57 nats, the largest
  code at 158.66 nats. No phase was worse on the grown checkpoint than on
  the base at the then-current width.
- **F2 capacity, all seven phases: H-LOAD.** Every load ratio is at or above
  the frozen 1.30 bound, the mildest legal at 4.4781, the most severe code
  at 38.1842. Across all seven phases the ablation removes the grown block
  and the ppl rises between 4.5x and 38x, so the block carries load.
- **F3 ladder verdict: PASS** - 7 of 7 in both dimensions.
- **F4 control: PASS** (2.48).

## 5. The `de` coincidence is a cross-check of the frozen region

For `de`, `pre` (base at 8192) and `narrow` (ck_de at 8192) are both exactly
13.5200. This is the expected behaviour and not an artefact: forcing the
route width 8192 excludes the grown `de` block (which occupies 8193..10240),
so all served positions are routed over the frozen prefix only, and the
frozen tensors are bit-identical between the two checkpoints by the P5
integrity guarantee. The two runs differ in the `joint` line - 13.52 on the
base against 2.60 on ck_de - because the joint reference scores the full
width of each checkpoint, which is exactly the quantity the load ratio
measures. The identity of the two routed numbers is therefore an
independent confirmation of the frozen-region guarantee.

For the other six phases `narrow > pre` holds throughout, as expected: at a
forced narrow width the grown block is present in the parameter space but
excluded from the route, and the misrouted domain degrades.

## 6. Reading for the K20 decision

The ladder is not a house of cards: each grown block carries real load, so
training the 19-phase K20 ladder remains the only way to reach its full
capacity, and eval-only shortcuts cannot substitute for it. At the same time
the acquisition gains are large and monotone in sign across all seven phases,
which is consistent with the P3 mechanism working as intended.

## 7. Scope and limits

Single seed, single ladder, 200 crops per domain, window 128 tokens;
descriptive, no p-values, no confidence intervals. The ppl figures are not
comparable across different windows, and only one window was used here.
The `narrow` runs of a phase and the `pre` run of the same domain share the
corpus and the crop offsets by construction (same generator, one draw per
domain, `crops` and `block_size` unchanged).
The analyzer verdict lines quoted in section 4 were produced locally by
`out_c/scaling_readiness/p3c_analyze.py` (md5 of its output
`6e14bde0c1cdbf5338a89aafcbf9c128`); the driver log on the guest carries the
name `p3c_analysis.txt` and md5 `94a7d7a1424fe460acc49350dfd77de1`. The two
files share a name and are not the same artefact; both are cited by hash.

## 8. Defects found and fixed during this run

- The run guard `bytes -lt 500` aborted the first attempt although the
  control output was complete at 318 bytes: the threshold was taken from
  two-route runs (483-491 B) and is too strict for single-route outputs.
  Replaced by the completeness marker `joint full-width reference: ppl`,
  which is the real test.
- The first hash comparison of the 22 transferred files proved nothing: the
  expected value was read from the wrong field (`want=` was empty). Rebuilt
  with named files, which then showed zero mismatches.
- The first copy of the driver log failed on a relative scp path; retried
  with the absolute path and the hash matched the guest.
- The intent envelope of the relaunch returned 409 (same `client_msg_id`,
  changed body). That is the tamper alarm working as documented; the first
  intent stands and names the pre-fix driver hash.

## 9. Artifacts

- driver log on the guest: `out_c/scaling_readiness/p3c/p3c_analysis.txt`
  (md5 `94a7d7a1424fe460acc49350dfd77de1`)
- 22 run outputs: `out_c/scaling_readiness/p3c/p3c_*.txt`, all verified
  identical local and guest
- analyzer: `out_c/scaling_readiness/p3c_analyze.py`, verdict md5
  `6e14bde0c1cdbf5338a89aafcbf9c128`
- pre-registration: `8af5da4da21477363668dabe60d29f2d095c3005`

## 10. Next

The K20 reference ladder (second seed alongside K5-seed2) is prepared and
launched as a separate training spend under the same operator GO; its cost
model is the 0.094 s per width unit measured in P3 (19 phases, 14.2 h per
ladder).
