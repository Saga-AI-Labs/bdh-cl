"""Sonde-B-free phase-1b upload: 17 single-copy ladRA2 files (88 GiB) to
Saga-AI-Labs/bdh-cl_phase-1b on HuggingFace. Runs on gx10.

Does three things in order: hardlink-staging (zero extra bytes on disk, same
partition /srv/coding), write the dataset card (README.md in the staging folder),
then upload_large_folder with XET enabled (phase-1's verified path).

NOTHING is deleted from gx10 by this script. The source files stay until the
remote is verified — that is the whole point of phase-1b (provenance for the
ladRA2 run names cited in bdh/docs).
"""
import os
import time

os.environ.pop("HF_HUB_DISABLE_XET", None)  # XET on (measured faster on phase-1)

SRC = "/srv/coding/bdh/out"
STAGE = "/srv/coding/bdh/hf_phase1b_upload"
REPO = "Saga-AI-Labs/bdh-cl_phase-1b"
TOKEN_FILE = "/srv/coding/bdh/.hf_token"

FILES = [
    "bdh_europarl_ladRA2-bg_best.pt",
    "bdh_europarl_ladRA2-bg_last.pt",
    "bdh_europarl_ladRA2-el_best.pt",
    "bdh_europarl_ladRA2-el_last.pt",
    "bdh_europarl_ladRA2-et_best.pt",
    "bdh_europarl_ladRA2-et_last.pt",
    "bdh_europarl_ladRA2-fi_best.pt",
    "bdh_europarl_ladRA2-fi_last.pt",
    "bdh_europarl_ladRA2-hu_best.pt",
    "bdh_europarl_ladRA2-hu_last.pt",
    "bdh_europarl_ladRA2-sk_best.pt",
    "bdh_europarl_ladRA2-sk_last.pt",
    "bdh_europarl_ladRA2-sl_best.pt",
    "bdh_europarl_ladRA2-sl_last.pt",
    "bdh_europarl_ladRA2-lt_best.pt",
    "bdh_europarl_ladRA2-lt_repaired.pt",
    "bdh_europarl_ladRA2-lt_repaired_repair.json",
]

CARD = """---
license: mit
tags:
- continual-learning
- language-modeling
- research
- pytorch
---

# BDH Continual-Learning phase-1b checkpoints (RA2, single-copy subset)

17 PyTorch checkpoints from the RA2 route-aware growth ladder — the 20-phase
continual-learning run over 20 European languages (europarl corpora) that
precedes RA2b and whose run names (`ladRA2-*`) are cited throughout `bdh/docs`.

This repo contains exactly those files of the RA2 ladder that exist in a single
place (on the gx10 training host) and therefore cannot be reclaimed locally
until replicated here: the bg, el, et, fi, hu, sk, sl language best+last pairs
(14 files), the final-phase lt_best.pt, and the decay-leak boundary-repair
artefacts lt_repaired.pt and lt_repaired_repair.json. The remaining 25 RA2
files have byte-identical copies on a second host and are therefore not part of
this upload.

## Contents

- `bdh_europarl_ladRA2-<lang>_{best,last}.pt` — 7 languages x 2 = 14 files
- `bdh_europarl_ladRA2-lt_best.pt` — final phase (lt) of the ladder
- `bdh_europarl_ladRA2-lt_repaired.pt` + `.json` — boundary-repair artefacts

Total: 17 files, ~88 GiB.

## Loading

Pipeline-native PyTorch `.pt` files, not safetensors, not loadable via
transformers `AutoModel`. Model architecture and loading code live in
`Saga-AI-Labs/bdh-cl` (`pipeline/`, `bdh.py`).

## Provenance

Produced by the Saga AI Labs BDH continual-learning research line (RA2 ladder,
final report and decay-leak repair measurement). License: Pathway MIT, see the
source repository's LICENSE.md. These are provenance snapshots for reproducing
published phase-1 numbers; no independent claims are attached to this set.
"""


def log(m):
    print(time.strftime("%H:%M:%S") + " " + str(m), flush=True)


def main():
    if not os.path.isdir(SRC):
        raise SystemExit("missing source directory: " + SRC)
    os.makedirs(STAGE, exist_ok=True)

    missing = []
    total = 0
    for name in FILES:
        s = os.path.join(SRC, name)
        if not os.path.isfile(s):
            missing.append(name)
            continue
        sz = os.path.getsize(s)
        total += sz
        d = os.path.join(STAGE, name)
        if os.path.exists(d):
            log("staged (exists): " + name)
            continue
        os.link(s, d)
        log("linked: " + name + " (" + format(sz, ",") + " B)")
    if missing:
        raise SystemExit("FATAL missing sources: " + ", ".join(missing))
    log("staging total: " + format(total, ",") + " B = " + str(round(total / 1024**3, 1)) + " GiB")

    card_path = os.path.join(STAGE, "README.md")
    open(card_path, "w").write(CARD)
    log("card written: " + card_path)

    token = os.environ.get("HF_TOKEN", "").strip()
    if not token and os.path.exists(TOKEN_FILE):
        token = open(TOKEN_FILE).read().strip()
    if not token:
        raise ValueError("HF_TOKEN env unset and no token file at " + TOKEN_FILE)
    if not token:
        raise SystemExit("empty token file — aborting before upload")
    from huggingface_hub import HfApi

    api = HfApi(token=token)
    log("whoami: " + api.whoami()["name"])
    log("starting upload_large_folder -> " + REPO)
    api.upload_large_folder(
        repo_id=REPO,
        folder_path=STAGE,
        repo_type="dataset",
    )
    log("done - all files uploaded")


if __name__ == "__main__":
    main()
