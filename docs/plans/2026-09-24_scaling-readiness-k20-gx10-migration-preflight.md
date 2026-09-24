# K20 migration preflight to gx10 - code transfers, two hard blockers remain

- Date: 2026-09-24. Seat: A0-Quinn.
- Operator GO: "Wir ziehen auf den gx10 um, wenn das geht."
- Source host: bdh-4090 (`.200`), `gpu://rtx4090` exclusive claim, ladder A stopped at
  the phase-12/13 boundary (11 of 11 P5 PASS).
- Target host: gx10-50ef, aarch64, NVIDIA GB10 (capability 12.1), driver 580.178.04,
  torch 2.13.0+cu130 with CUDA available, unified memory 121 GB.
- Status: preflight on the measured state; the migration is technically possible.
  The gx10 card was occupied by pi-50's Qwen vLLM during the first measurement and
  has since been released: 0 compute apps, 0 % GPU, 3 GB of 121 GB unified memory
  used, 118 GB available. Nothing transferred, nothing trained, no shared claim
  taken in this step.

## 1. What transfers cleanly (measured)

| file | 4090 md5 | gx10 md5 | equal |
| --- | --- | --- | --- |
| bdh.py | da6eff444d51dfbbfa1b95d8c1a05c5d | da6eff444d51dfbbfa1b95d8c1a05c5d | yes |
| pipeline/train.py | 3ad7848ded61f35ee292bc24d5c728e4 | 3ad7848ded61f35ee292bc24d5c728e4 | yes |
| pipeline/config.py | 904b69549d953d72017126549ed2a2e1 | 904b69549d953d72017126549ed2a2e1 | yes |
| pipeline/data.py | c45ea50de77b44c7816e9636e782461e | c45ea50de77b44c7816e9636e782461e | yes |
| scripts/eval_router.py | 73832ecd08f24eded93a98a74572be6e | 73832ecd08f24eded93a98a74572be6e | yes |
| scripts/p5_inchain_check.py | 4456a8ecfbd503e02a306cc3475b494e | 4456a8ecfbd503e02a306cc3475b494e | yes |

The gx10 checkout is at `/srv/coding/bdh` at HEAD `e6bf35919d1ef453f94b017c0e51d2e6a49a7463`,
same commit as the 4090 guest. The OOM site (`bdh.py` lines 105 and 126, `rope`) is
therefore the same code on both hosts; there is no fork to reconcile.

Data already present on gx10: `data/textmix/wikitext-103-raw/wiki.train.raw`
(540,568,191 B) and `data/europarl/europarl-v7.et-en.et.txt` (91,510,232 B).

## 2. Transfer list (sizes measured on the 4090)

| item | bytes | present on gx10 |
| --- | --- | --- |
| bdh_textmix_k20-A-it_last.pt (phase-12 checkpoint) | 4,531,027,472 | no |
| data/textmix2/code.txt | 40,529,764 | no |
| data/textmix2/latex.txt | 40,006,401 | no |
| data/textmix2/legal.txt | 40,347,823 | no |
| data/europarl/xscript_zh.txt | 1,289,893,407 | no |
| data/europarl/DGT.en-ga.ga.txt | 55,409,138 | no |
| out_c/scaling_readiness/k20/ (ladder A phases 2-12, best+last+p5+routdiag) | 66,463,664,571 | no |

Two transfer scopes are possible. The strict minimum to resume is the phase-12
`last` checkpoint plus the five corpus files: about 6.0 GB. The full record (copy
the whole ladder-A output directory, so every older `best`/`last` is also present
on gx10) is about 71 GB. Both sizes exclude the new checkpoints the remaining
phases will write: the 13 remaining phases of ladder A need about 66 GB (3.6 GB as
best+last at mult 512 growing to about 9 GB at mult 896), and both ladders would
need 672 GB.

## 3. Blocker A - the target GPU is occupied by another seat

Measured on gx10 at preflight:

```
NVIDIA GB10
compute apps: 3660292 VLLM::Worker 93,027 MiB
               3660640 /usr/bin/python3 288 MiB
unified memory: 121 GB total, 106 GB used, 2.2 GB free, 18 GB available
swap: 16 GB, 481 MiB used
process: vllm serve Mia-AiLab/Qwen3.8-Flash-Next-NVFP4 ... --served-model-name
         qwen3.8-flash-next-stock --gpu-memory-utilization 0.786
         --max-num-seqs 8 --max-model-len 262144 --kv-cache-dtype fp8
watcher: files/memwatch.sh vllm-fn-tp1 6 (elapsed 9424 s)
```

pi-50 reported on the bus (seq 465) that the Qwen stock arm is resident and that
its MMLU result is one item apart from GLM with the determinism gate failed, so a
full 100-sample re-run is owed on both arms. Stopping that service is not my
decision and is not done here.

## 4. Blocker B - disk capacity

```
/dev/nvme0n1p2  916 G total, 693 G used, 177 G free (80 % used)
```

177 GB free covers a ladder-A resume (about 71 GB including the transferred
phase-12 checkpoint and the existing phase outputs) with room for the 13
remaining phases, but not both ladders. The existing K20 directory on the 4090
already weighs 66,463,664,571 B for 11 phases; the last phase alone writes about
9 GB as `best`+`last`.

## 5. Timing baseline must be re-measured

The 0.094 s per width unit model and the 1.5x K1 stop rule come from RTX 4090
measurements. The GB10 is different hardware with a different memory subsystem.
Before any product phase, the first phase on gx10 must establish its own wall
clock; the K1 threshold applies to that measured baseline, not to the 4090 number.
The phase-13 form is the natural probe: grow 32 from the transferred phase-12
checkpoint, 2000 steps first (a quarter of the production budget) to avoid a
24-hour K1 false trigger, then the full 10,000 if the ratio holds.

## 6. What has to happen before the first gx10 training step

1. **Operator or pi-50 decision** on the Qwen vLLM service on gx10. K20 cannot
   run while 93 GB of the card and 106 GB of unified memory are held. This is a
   cross-seat action and is deliberately not taken here.
2. **Disk**: decide whether ladder A resumes on gx10 (71 GB transfer plus about
   66 GB for the remaining phases) or whether both ladders move (672 GB, not
   possible on the current 177 GB free). Freeing space is a separate decision.
3. **Transfer** of the five missing corpus files, the phase-12 checkpoint and the
   ladder-A output directory from bdh-4090 to gx10. Minimum scope: the five corpus
   files plus the phase-12 checkpoint, about 6.0 GB, checked for all six items by
   md5 on both sides after the copy. The older ladder-A checkpoints stay on the
   4090 unless the full record is wanted.
4. **Host claim**: a `host://gx10` claim (or the gx10's GPU asset, if one is
   registered) before any transfer write and before the probe. The HAK charter
   requires a claim for shared-resource writes; the gx10 asset registry showed no
   entry, so the URI has to be decided and announced.
5. **Preflight probe** with a fresh 4090-vs-gx10 wall-clock baseline and a
   peak-VRAM reading, under the claim, with output to `/tmp` only.

## 7. What is not claimed here

No claim about gx10 throughput, no claim that K20 fits on the GB10, no claim
that the OOM disappears on the other host. The GB10 has 121 GB of unified memory
against a 24 GB card, so the working set that killed phase 13 on the 4090
(about 22-24 GB) is very likely to fit, but "very likely" is not a measurement.
The probe in step 5 is that measurement.

## 8. Ship

English, ASCII, newline-terminated; the j-space ship gate must report the
outgoing register holds. Bus: this preflight is posted as a status envelope in
`bdh-cl` naming the two blockers and the cross-seat decision needed.
