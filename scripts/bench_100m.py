"""Throughput probe: measured bytes/s for a 100M BDH model on this box.

The review (2026-11-18) asks for the time axis of the cost table. The only
measured Spark number is the 3.62B campaign model (~44.8 B/s, p50 11,420
ms/step at b1/t512). The inverse route runs a 50-100M host, and its rate is
unmeasured on this hardware; the 2026-08-24 reference is 100M on an RTX 4090
at 230 ms/step b8/t512 (~17,800 B/s).

This probe instantiates the 100M config from that report (n_embd 512, n_head
8, mult 128, ~101M params), runs the training step exactly as the stateless
path in train.py (model(x, y, None, collect_state=False), bf16 autocast,
AdamW step included), and reports ms/step and bytes/s. Layer count is a flag
because BDH weights are shared across layers: depth changes compute, not
parameter count.

Usage:
  python scripts/bench_100m.py [--layers 6,4] [--batch 8] [--steps 50] [--compile] [--two-pass]
"""

import sys
import time

import torch

sys.path.insert(0, ".")

from pipeline.config import Config, build_model, param_count, resolve_dtype


def bench(n_layer: int, batch: int, steps: int, device, dtype,
          compiled: bool = False, two_pass: bool = False) -> None:
    cfg = Config(
        model="bdh", n_layer=n_layer, n_embd=512, n_head=8,
        mlp_internal_dim_multiplier=128, block_size=512, batch_size=batch,
        dropout=0.0,
    )
    model = build_model(cfg).to(device)
    n_params = param_count(model)
    if compiled:
        model = torch.compile(model)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-4)
    x = torch.randint(0, 256, (batch, 512), device=device)
    y = torch.randint(0, 256, (batch, 512), device=device)
    ctx = torch.amp.autocast(device_type="cuda", dtype=dtype)
    mask = None
    if two_pass:
        # route-aware shape: prefix pass (masked, 0.9) + full pass (0.1),
        # as in the P1 / graft training loop. Timing-only mask: 7/8 prefix.
        N = cfg.mlp_internal_dim_multiplier * cfg.n_embd // cfg.n_head
        mask = torch.zeros(N, device=device, dtype=dtype)
        mask[: 7 * N // 8] = 1.0

    for it in range(steps + 5):
        if it == 5:
            torch.cuda.synchronize()
            t0 = time.time()
        with ctx:
            if two_pass:
                _, prefix_loss, _ = model(x, y, None, neuron_mask=mask,
                                          collect_state=False)
                _, full_loss, _ = model(x, y, None, collect_state=False)
                loss = 0.9 * prefix_loss + 0.1 * full_loss
            else:
                _, loss, _ = model(x, y, None, collect_state=False)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    torch.cuda.synchronize()
    elapsed = time.time() - t0
    ms = 1000 * elapsed / steps
    bps = batch * 512 * steps / elapsed
    mode = "two-pass" if two_pass else "one-pass"
    print(f"n_layer {n_layer} | {n_params:,} params | b{batch}/t512 | "
          f"{mode} | compile {'on' if compiled else 'off'} | {ms:.0f} ms/step | "
          f"{bps:,.0f} B/s | peak "
          f"{torch.cuda.max_memory_allocated() / 2**30:.1f} GiB")


def main() -> None:
    a = sys.argv[1:]

    def arg(flag, default):
        return a[a.index(flag) + 1] if flag in a else default

    layers = [int(v) for v in arg("--layers", "6").split(",")]
    batch = int(arg("--batch", "8"))
    steps = int(arg("--steps", "50"))
    compiled = "--compile" in a
    two_pass = "--two-pass" in a
    device = torch.device("cuda")
    dtype = resolve_dtype(Config(), device)
    print(f"bench 100M | device {torch.cuda.get_device_name(0)} | dtype {dtype}")
    for n_layer in layers:
        bench(n_layer, batch, steps, device, dtype, compiled, two_pass)


if __name__ == "__main__":
    main()
