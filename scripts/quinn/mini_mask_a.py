import sys, math, numpy as np, torch
sys.path.insert(0, ".")
from bdh import BDH, BDHConfig

CKPT = "out_c/expert_merge/zh_b1_merged.pt"
DOM = "data/europarl/xscript_zh.txt"

ckpt = torch.load(CKPT, map_location="cpu", weights_only=False, mmap=True)
cfg = BDHConfig(**{k: v for k, v in ckpt["cfg"].items()
                   if k in {f.name for f in __import__("dataclasses").fields(BDHConfig)}})
model = BDH(cfg); model.load_state_dict(ckpt["model_state"]); del ckpt
device = torch.device("cuda")
model = model.to(device).eval()

nh, D = cfg.n_head, cfg.n_embd
N = cfg.mlp_internal_dim_multiplier * D // nh
half = N // 2
mask = torch.zeros(N, device=device); mask[:half] = 1.0
print("mask_a: N=%d half=%d active=%d" % (N, half, int(mask.sum())), flush=True)

arr = np.frombuffer(open(DOM,"rb").read(30_000_000)[-2_000_000:], dtype=np.uint8)
data = torch.from_numpy(arr.astype(np.int64))
g = torch.Generator().manual_seed(1234)
idxs = [int(x) for x in torch.randint(len(arr)-513, (200,), generator=g)]

losses = []
with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
    for b0 in range(0, len(idxs), 2):
        ch = idxs[b0:b0+2]
        x = torch.stack([data[i:i+512] for i in ch]).to(device)
        y = torch.stack([data[i+1:i+513] for i in ch]).to(device)
        logits, _, _ = model(x, y, None, neuron_mask=mask)
        losses.append(torch.nn.functional.cross_entropy(
            logits.view(-1, logits.size(-1)), y.view(-1)).item())
        if (b0//2) % 25 == 0:
            print("  crop %3d/200 | batch nll %.4f" % (b0+2, losses[-1]), flush=True)
m = sum(losses)/len(losses)
print("RESULT mask_a zh: nll %.4f | ppl %.2f | crops %d" % (m, math.exp(m), len(idxs)), flush=True)
