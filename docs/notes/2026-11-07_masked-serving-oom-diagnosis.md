# Masked-serving OOM diagnosis: fp32 mask promotes every masked tensor to fp32; plus 30 GB of unused KV-state

**Date:** 2026-11-07
**Addressed to:** the author of `scripts/quinn/serving_eval.py` and `out_c/expert_merge/mini_mask_a.py`
**Evidence:** `out_c/expert_merge/serving_eval.log`, `mini_mask_a.log`, kernel OOM records (`journalctl -k`, quoted below), checkpoint cfg (`k_sparse_ratio=0.0`, `n_layer=4`, mult 1792), `bdh.py` lines 250–288
**Status:** diagnosis only — I have not edited your scripts or `bdh.py`, and run nothing on the GPU.

## 1. What the kills actually are

No Python traceback in either log is the first clue: these are **global kernel OOM kills** (SIGKILL), the same unified-pool pattern as `7975858`'s rc=137. `journalctl -k` shows three python kills, each with ~307.8 GB total_vm (the CUDA unified-memory mapping):

- Nov 6 22:50:11 — python (UID 1001) killed; two small python helpers (UID 1000) died as collateral
- Nov 7 00:30:02 — python killed; the `upload_k25_hybrid` run was still active until 00:30
- Nov 7 03:40:21 — python killed; `nvitop` and several system daemons killed in the same cascade

Timeline matches the logs: `serving_eval` (00:29) died in `mask_a` batch 1 after joint ran 400 crops cleanly; `mini_mask_a` (03:40) died in batch 2 after batch 1 succeeded (nll 1.5496).

## 2. Root cause: the mask multiply promotes bf16 → fp32

Both scripts build the mask as `torch.zeros(N, device=device)` — **float32**. `bdh.py` then does (lines 255, 270):

```python
x_sparse = x_sparse * neuron_mask.view(1, 1, 1, -1)   # bf16 * fp32 -> fp32
```

Type promotion makes every masked activation **fp32, i.e. double size**. At B=2, T=512, N=114,688/head, one (B,nh,T,N) tensor is 3.76 GB bf16 → **7.52 GB fp32**. The promotion propagates:

| tensor | joint (bf16) | masked (fp32-promoted) |
|---|---|---|
| x_sparse / y_sparse (each) | 3.76 GB | 7.52 GB |
| xy_sparse + reshape copy (each) | 3.76 GB | 7.52 GB |
| rope on Q (fp32 intermediates) | transient ~7.5–15 GB | transient ~15–30 GB |
| **KV-state, 4 layers × k-cache** | **15.05 GB** | **30.10 GB** |

The state line is the sleeper: `Attention.forward` returns `{"k": QR_k, "v": V}` with `QR_k` (B,nh,T,N) built **from the masked Q**, so the state inherits the fp32 dtype too. Per-layer live set grows from ~26–30 GB to ~45–50 GB; with the 22.55 GB model the masked-mode peak lands around **95–110 GB on a 121 GB unified pool** — versus ~65–75 GB for joint. Joint fits; masked sits on the cliff, and page-cache/allocator noise decides which batch dies. That is exactly the observed pattern: joint 400/400 clean, mask_a dead in batch 1; mini_mask_a batch 1 squeaked by, batch 2 died.

It also explains a standing observation: `merge_probe_eval.py` runs joint at `batch=4` — states 30 GB + live ~53 GB + model ≈ 105 GB. It survived twice, but it was always one concurrent upload away from the same kill (and one was running at 00:30).

Side note: I checked the top-k path first (`_k_sparse_relu`'s int64 index tensor would be 15 GB at ratio 0.25) — **moot for this checkpoint**: cfg says `k_sparse_ratio=0.0`, so the forward runs plain ReLU. `n_layer=4`, not 16; state cost is 4×3.76=15 GB bf16, not 60 GB.

## 3. Fixes, in order of value

**(a) One line per script — make the mask bf16** (`serving_eval.py` lines 171/173, `mini_mask_a.py` line 18):

```python
mask_a = torch.zeros(N, device=device, dtype=torch.bfloat16); mask_a[:half] = 1.0
```

0 and 1 are exact in bf16, so numerics are unchanged (the joint numbers in your log already match `eval_sibling.json` exactly: 2.4336 / 3.1975). Masked-mode peak drops back to roughly joint + one transient ≈ 70–75 GB.

**(b) `bdh.py`: let eval callers skip the state.** `BDH.forward` unconditionally accumulates `new_layers` (lines 236, 263, 287) — 15 GB bf16 / 30 GB fp32 that every eval script throws away via `logits, _, _`. A backwards-compatible flag removes it entirely:

```python
def forward(self, idx, targets=None, state=None, neuron_mask=None, collect_state=True):
    ...
    if collect_state:
        new_layers.append(layer_new_state)
    ...
    return logits, loss, ({"pos": pos + T, "layers": new_layers} if collect_state else None)
```

Default `True` keeps `generate()` and training untouched. With (a)+(b) the masked peak is ~40–50 GB — roomy enough to keep batch 2, and `merge_probe_eval` gets real margin at batch 4.

**(c) `serving_eval.py`: release the cache between modes.** After 400 joint crops the allocator holds ~65 GB of cached bf16 blocks; the masked path (even fixed) wants slightly different block sizes on top. One line at the top of the mode loop:

```python
for mode_name, mask in modes:
    torch.cuda.empty_cache()
```

**(d) Operational:** don't co-schedule large uploads (the k25 stage upload was live at the 00:30 kill) or nvitop with these evals; on a unified-memory box they share the same 121 GB the model is breathing from.

## 4. What this means for the routed-routes measurement

Nothing bad: the fix changes memory, not semantics. Joint results already reproduced the report's numbers bit-for-bit, and once (a)–(c) are in, `mask_a` / `mask_b` / `transfer` / `mixed` should complete at batch 2 — completing the §4.3 routed-routes evidence chain with the isolation numbers the sibling-merge report could only argue for.

— asb, 2026-11-07

---

## Update 2026-11-07 later: measured — bf16 mask alone was not enough; stateless fix verified, and mask_a recovers parent A exactly

Quinn applied (a)+(c) locally (bf16 masks, `empty_cache` in the modes loop) and the
fixed run **still died**: global OOM at 05:02:24, `NVRM: NV_ERR_NO_MEMORY` already
4 s before the killer fires. Two findings from the kernel dump worth keeping: on
GB10 the CUDA pool is **invisible in process RSS** (at kill time anon ≈ 54 MB, page
cache ≈ 0, free ≈ 130 MB — the whole 121 GB sits in NVRM-managed pages, system-wide
traceable only via `sec_pagetables` ≈ 250 MB), and the remaining overhead that tips
it over is item (b): the never-used KV-state, 4 layers × (2,16,512,114688) bf16 =
15.05 GB live until forward end, plus allocator cache on top.

Fixes now landed (operator authorized direct edits): `bdh.py` gained
`collect_state=True` (default; training/`generate()` untouched) and the mask
multiply is dtype-hardened (`.to(x_sparse.dtype)`), so no future fp32 mask can
promote; both eval call sites pass `collect_state=False`. CPU checks: logits
bit-identical with/without state, state carry unaffected, fp32 mask no longer
promotes.

**Verified end-to-end on the GPU** (`mini_mask_a.py`, exit 0, ~37 GB pool margin
throughout):

```
RESULT mask_a zh: nll 1.7306 | ppl 5.64 | crops 100
```

That is **exactly parent A's zh score** from `eval_sibling.json` (1.7306 / 5.64,
same protocol seed/crops). So on the identical merged checkpoint: joint forward
3.1975 on zh (+1.47 nats over best parent) vs routed/masked **1.7306** — the mask
recovers the parent capability **completely**; the cross-talk lives only in the
additive joint path. This is the cleanest measured datapoint yet for §4.3
routed-routes: masking removes 100 % of the interference, which matches the
co-activation mechanism (zeroed activations contribute zero decoder rows; the
per-head score sums are unchanged). Full mode table (mask_b, transfer, mixed) is
`serving_eval.py`'s run now that it no longer OOMs.

— asb, 2026-11-07

