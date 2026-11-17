"""Mask-aware generation check (graft-2 plan section 5; P3 deployment verdict
9505ab3): does generate() honor the neuron mask, and does the domain-aware
serving map produce the right language?

Cells on the P3 last checkpoint (mult 1024; old prefix = mult 896):

  1. zh prompt    x old-mask  : the chat serving path for zh. The old-only
                                mask IS the base model (S1 bit-exact), which
                                produced zh text on zh prompts -> expect a
                                high share of bytes >= 0x80 (zh UTF-8).
  2. zh prompt    x full width: the documented failure (P3 zh@0 samples are
                                fluent English legal despite the 0.013-nat TF
                                zh edge) -> expect ~0 high bytes.
  3. legal prompt x full width: normal serving -> English legal (~0 high bytes).
  4. legal prompt x old-mask  : base-on-legal control -> English legal.

Prompts: a real zh prompt cut from the zh HELD-OUT split (the same 30 MB carve
the evals use - no train bytes in the prompt), plus the fixed "\\n = The "
prompt regime for like-for-like reading against the registered post cells.

Metric per cell: share of generated (non-prompt) bytes >= 0x80 - zh UTF-8 text
is high, ASCII English ~0 - plus the decoded sample. Sampling is multinomial
(unseeded, like the registered sample regime); the check is about LANGUAGE,
not exact tokens.

Usage:
    python scripts/gen_serve_check.py <ckpt> [--mask-old-mult 896] \
        [--tokens 120] [--temperature 0.8] [--topk 3]
"""
import os
import sys

import torch

sys.path.insert(0, ".")

from pipeline.data import _prepare_textmix
from pipeline.merge import load_model_mmap


def hi_byte_share(b: bytes) -> float:
    return sum(x >= 0x80 for x in b) / len(b) if b else 0.0


@torch.no_grad()
def sample(model, prompt: bytes, mask, device, tokens, temperature, top_k) -> bytes:
    idx = torch.tensor(list(prompt), dtype=torch.long, device=device).unsqueeze(0)
    out = model.generate(idx, max_new_tokens=tokens, temperature=temperature,
                         top_k=top_k, neuron_mask=mask)
    return bytes(out.to(torch.uint8).cpu().squeeze(0).tolist())


def main():
    a = sys.argv[1:]
    def arg(flag, default):
        return a[a.index(flag) + 1] if flag in a else default
    ckpt_path = a[0]
    mask_mult = int(arg("--mask-old-mult", "896"))
    tokens = int(arg("--tokens", "120"))
    n_samples = int(arg("--samples", "3"))
    temperature = float(arg("--temperature", "0.8"))
    top_k = int(arg("--topk", "3"))

    device = torch.device("cuda")
    model, cfg_d = load_model_mmap(ckpt_path)
    model = model.to(device).eval()
    C = model.config
    nh, D = C.n_head, C.n_embd
    N = C.mlp_internal_dim_multiplier * D // nh
    n_keep = mask_mult * D // nh

    masks = {"full": None}
    dtype = next(model.parameters()).dtype
    if 0 < n_keep < N:
        old = torch.zeros(N, device=device, dtype=dtype)
        old[:n_keep] = 1.0
        masks["old"] = old
        print(f"mask: keep {n_keep} of {N} neurons per head "
              f"(mult {mask_mult} prefix, activation dtype {dtype})")
    keep_1024 = 1024 * D // nh
    if 0 < keep_1024 < N:
        m1024 = torch.zeros(N, device=device, dtype=dtype)
        m1024[:keep_1024] = 1.0
        masks["1024"] = m1024
        print(f"mask: keep {keep_1024} of {N} neurons per head (mult 1024 prefix)")

    blocks, _, _, _ = _prepare_textmix("zh:data/europarl/xscript_zh.txt", 30)
    zh_prompt = bytes(blocks["zh"]["val"][:80])
    legal_prompt = b"\n = The "
    code_prompt = None
    if os.path.exists("data/textmix2/code.txt"):
        with open("data/textmix2/code.txt", "rb") as f:
            f.seek(28_000_000)  # val carve region of the 30-MB read
            code_prompt = f.read(80)

    cells = [
        ("zh-prompt x old-mask  (chat serving path)", zh_prompt, "old"),
        ("zh-prompt x full      (documented failure)", zh_prompt, "full"),
        ("legal-prompt x full   (normal serving)", legal_prompt, "full"),
        ("legal-prompt x old-mask (base control)", legal_prompt, "old"),
        ("code-prompt x full    (third-domain serving)", code_prompt, "full"),
        ("code-prompt x old-mask (base control)", code_prompt, "old"),
    ]

    # Mixed-content cells (the registered open regime): English system
    # prompt + the SAME zh content, three en:zh byte ratios with zh fixed
    # at 80 B (1:1 -> 80 B en, 2:1 -> 160 B en, 1:2 -> 40 B en). The
    # English part is a realistic chat system prompt, repeat-and-truncated
    # to the target length - the register question is the experiment.
    SYS = (b"You are a helpful assistant. Answer in the same language as "
           b"the user's message.\n\nUser: ")
    zh_len = len(zh_prompt)
    for label, en_len in (("1:1", zh_len), ("2:1", 2 * zh_len),
                          ("1:2", zh_len // 2)):
        p = (SYS * 4)[:en_len] + zh_prompt
        cells.append((f"mixed {label} (en{en_len}+zh{zh_len}) x full", p, "full"))
        cells.append((f"mixed {label} (en{en_len}+zh{zh_len}) x old-mask", p, "old"))
        cells.append((f"mixed {label} (en{en_len}+zh{zh_len}) x mask-1024", p, "1024"))

    print(f"gen-serve check | {ckpt_path} | {n_samples} x {tokens} tokens/cell | "
          f"temperature {temperature} | top_k {top_k}")
    verdicts = []
    for name, prompt, mk in cells:
        if mk not in masks:
            print(f"\n[{name}] SKIPPED (mask not applicable)")
            continue
        print(f"\n[{name}]\n    prompt: {prompt[:24]!r}...")
        shares = []
        for s in range(n_samples):
            out_b = sample(model, prompt, masks[mk], device, tokens, temperature, top_k)
            cont = out_b[len(prompt):]
            share = hi_byte_share(cont)
            shares.append(share)
            print(f"    #{s} hi-byte {share:.2%}  {cont.decode('utf-8', errors='backslashreplace')!r}")
        mean_share = sum(shares) / len(shares)
        print(f"    -> mean hi-byte {mean_share:.2%}  (zh ~high, ASCII English ~0)")
        verdicts.append((name, mean_share))

    print("\n--- reading guide (registered expectations) ---")
    print("cell 1 high + cell 2 low  : serving map works; failure persists full-width")
    print("cell 1 low                : old-mask does NOT restore zh behavior -> STOP")
    print("cell 3 low                : normal serving intact (positive control)")
    print("cell 4 low                : base control sane (English legal)")
    print("mixed x full high         : static map survives the English system prompt")
    print("mixed x full low + mask hi: static map leaks English -> mask or window routing needed")
    print("mixed x old high          : base keeps Chinese; a full-leak comes from the trained block")


if __name__ == "__main__":
    main()
