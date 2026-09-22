# Scaling-readiness probes - interim report (P0, P1a, P2)

- Date: 2026-09-22 (UTC) - Seat: A0-Quinn
- Pre-registration: `docs/plans/2026-09-22_scaling-readiness-gaps-and-probes-prereg.md` (76dd597)
- Erratum applied: `docs/plans/2026-09-22_scaling-readiness-erratum.md` (ac6d046)
- Scope covered: P0, P1a, P2. Not covered: P1b, P3 (training spend, run after this report).
- Raw artifacts: `out_c/scaling_readiness/` (gitignored, md5-pinned below).

## 1. P0 - eval scale-up and dedup: CONFIRM

Pre-registration: `2026-09-22_scaling-readiness-p0-prereg.md`. Report: `2026-09-22_scaling-readiness-p0-report.md` (commit 0f27eee).

At N=1000 crops the leak rate and the serving cost both hold inside the frozen
band: leak 5.2% (seed-2) / 6.3% (reference) against 5-10%, cost 8.2% / 8.6%
against the 12% ceiling. Verdict CONFIRM as pre-registered.

Erratum E1 (applied, disclosed): the pre-registration claimed the first 200 byte
ranges of the N=1000 draws are "identical by construction" to the N=200 draws.
That is wrong - `g = torch.Generator().manual_seed(1234)` is created ONCE before
the domain loop and each domain draws `torch.randint(hi, (args.crops,))`, so the
draw sequence shifts with `crops`. Measured: only `prose` reproduced; `legal` did
not. The overlap assertion was therefore reported, not silently skipped.

## 2. P1a - best vs last serving: _last remains the default

Pre-registration: `2026-09-22_scaling-readiness-p1a-prereg.md` (682bd02).
Run: 16 evals, all rc=0, size 483-491B (no stubs), `pairs_failed=0`, driver
md5 1e2eac77881234bf348c1c3cdedd5b4f.

Frozen gate G2 passed on all four reference `_last` runs: the printed
trained-domain ppl at the trained width reproduces the committed ablation figure
to 0.01 (1.41 / 4.90 / 2.40 / 2.20). This is the pre-eval proof that instrument
and measurement agree.

Frozen rule: the serving checkpoint of a cell is the one with the lower
trained-domain ppl at the trained width; `best` wins only if it is better by at
least 0.02 ppl, ties go to `_last`. Result: `best` wins 0 of 8 pairings (the bar
for switching was 6 of 8).

| cell | ladder | best | last | delta (last-best) | serves |
| --- | --- | --- | --- | --- | --- |
| prose__math | seed-2 | 1.43 | 1.41 | -0.02 | last |
| prose__math | reference | 1.42 | 1.41 | -0.01 | last |
| prose__code | seed-2 | 5.57 | 4.92 | -0.65 | last |
| prose__code | reference | 5.51 | 4.90 | -0.61 | last |
| math__ga | seed-2 | 2.37 | 2.36 | -0.01 | last |
| math__ga | reference | 2.41 | 2.40 | -0.01 | last |
| prose__legal | seed-2 | 2.24 | 2.20 | -0.04 | last |
| prose__legal | reference | 2.21 | 2.20 | -0.01 | last |

The largest gap is `prose__code`, where `_best` is worse by 0.65 (seed-2) and
0.61 (reference); the rest sit inside noise. Serving rule frozen: `_last` stays
the serving checkpoint for all scaling evals. The parent-plan's expectation that
`_best` usually serves better is refuted by this measurement.

Artifact md5s (guest, `out_c/scaling_readiness/p1a/`): 16 files, 483-491 B,
pulled to `/tmp/p1a/` for the table above.

## 3. P2 - harness hardening and O(K) cost

### 3.1 Storage integrity harness (`scripts/storage_check.py`)

Built from the exact set `pipeline/train.py:197-203` plus embed/lm_head:
`enc[:, :, :n_old]`, `encv[:, :, :n_old]`, `dec[:, :n_old, :]` viewed as
`(n_head, N, -1)`, `embed.weight`, `lm_head`. Compared BIT-EXACT against the
checkpoint named by the ckpt's own `cfg["init_from"]`; the grown columns and the
width-sized rotary buffer `attn.freqs` are deliberately NOT compared. `n_old` is
derived, never guessed: `n_head`, `n_embd` and the multipliers come from each
ckpt's cfg, `n_old = init_mult * n_embd // n_head`. CPU-only by construction
(`CUDA_VISIBLE_DEVICES` cleared before torch import), so the harness can never
contend for a claimed GPU.

The eight grown `_last` checkpoints: all `STORAGE_INTEGRITY_OK`, regions=5,
failed=0. Derived widths match the known ladders exactly: 8192 -> 12288
(prose__math), 8192 -> 10240 (prose__code), 8192 -> 14336 (prose__legal),
12288 -> 16384 (math__ga), identical on both ladders.

Counter-probes (the part that makes the harness worth something), on
`harvest/..._prose__legal_last.pt`:

| input | verdict | rc |
| --- | --- | --- |
| intact checkpoint | STORAGE_INTEGRITY_OK, failed=0 | 0 |
| one element bumped in the frozen region (`encoder[0,0,0] += 1`) | STORAGE_INTEGRITY_FAILED, failed=1 | 1 |
| one element bumped in the trainable region (`encoder[0,0,14335] += 1`) | STORAGE_INTEGRITY_OK, failed=0 | 0 |

The harness separates exactly the two regions it claims to separate: a frozen
bit flip is caught, a trainable bit flip is not a failure.

Open disclosure: the pre-registration says "PASS on all 8 existing grown
checkpoints"; the grown set is ambiguous - 16 files exist (8 `_last` + 8
`_best`). Checked: the 8 `_last` files (the serving checkpoints per section 2).

### 3.2 Driver guards (`scripts/driver_guards.py`)

Five pre-eval asserts, the G3 footgun: `block_size == 512` (not the 128
default), `--domains` present (the 295B stub trap), output > 300 B, checkpoint
md5 pinned, every route a whole multiple of `n_head`. Self-test: every trap
fires, `GUARDS_SELFTEST_OK`, rc=0; the guards also pass on good input.

### 3.3 O(K) scan-cost projection

Same protocol both runs, only the number of routed prefixes varied: 50 crops,
window 128, mb 30, batch 4, five domains; routes chosen so that every width is
divisible by `n_head=8` and at most `N_full`, so no clamping distorts the cost.

| K | rc | wall s | out bytes |
| --- | --- | --- | --- |
| 5 | 0 | 40.9 | 728 |
| 23 | 0 | 156.3 | 1821 |

Ratio 3.82 against a linear expectation of 23/5 = 4.60: the scan is linear to
sublinear in K. Slope 6.411 s per route, projection to K=40: about 265 s per
eval. Reading of the pre-registration's `FLAG_SUPERLINEAR` (>2.5x) is defective
as written: the threshold 2.5 cannot be tested against all measured route counts
(both runs, K=5 and K=23, ratio 3.82 against a proportional 4.60) without
flagging every linear scan. Measured and reported as it says: NOT superlinear.
No P-A1 risk flag from this measurement.

Open disclosure (deviation from the pre-registration): the pre-registration names
"RA2b-lt 23 routes, existing checkpoint" as the K=23 carrier. That checkpoint
does not exist on the guest: `ls out/*RA2b*` reports `No such file or directory`,
count 0. Timed instead on an existing grown checkpoint
(`harvest/bdh_textmix_harv-prose__legal_last.pt`, md5
d94686ad9f90d4750ba8d02b88ffd9ea) with synthetic route lists of length 5 and
23. The cost driver is the number of routed prefixes, not which checkpoint they
belong to; the substitution is disclosed here.

Artifact md5s (guest, `out_c/scaling_readiness/p2/`): `ok_K5.txt`
dbb894fdc19f36710906442883ffd097, `ok_K23.txt` c948e740f8f361db1ad7ea3b61a0829d.

## 4. Consequences for the A1-K20 gate

The gate of the pre-registration is P0 CONFIRM and P2 harness PASS with a linear
O(K) slope and a frozen P1 serving rule. All three hold. The P3 leg of the gate
is not yet run; it is the next item. Nothing here authorizes a claim beyond what
was measured: no p-values, no semantic-generalization, one seed family.

## 5. Coordination

- P0 bus: intent/done through m_bdh-cl_0000000439; P1a intent m_bdh-cl_0000000440;
  P2 intent m_bdh-cl_0000000441, m_bdh-cl_0000000443.
- GPU claimed exclusive for P1a and for the O(K) runs, released after each
  (HTTP 204, active scopes empty, card idle 287 MiB / 0%, no processes).
- Open process (P1a): the driver was started before the claim returned 201; the
  claim itself had to be corrected first (422 - `client_msg_id` is a server-owned
  field and was rejected in the body). Disclosed as it says: the run was briefly
  unclaimed.
