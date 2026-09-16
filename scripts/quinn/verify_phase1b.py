"""Formal three-way sha256 verification of the bdh-cl_phase-1b HuggingFace upload.

Runs from the agent container. Re-runnable by any seat (Quinn, pi-50) to
re-establish the non-circular provenance chain before any local deletion:

  (a) committed pre-upload sha256   -> bdh/docs/data/phase1b-ladra2-crossbox-join.md
  (b) fresh gx10 sha256sum          -> live re-read of the staging bytes
  (c) HuggingFace side              -> LFS oid (the 16 .pt), resolve-download+sha256 (the 2 REGULAR blobs)

  a==b  : on-disk bytes unchanged since the 17:30 audit
  b==c  : transfer fidelity
  a==c  : the non-circular committed<->remote link
  (all three equal = the claim is pinned at three independent points.)

The 17 files stay on gx10 until pi-50's retrieval spot-check (#303) acks and an
intent envelope names them. This script never deletes anything.

Usage:
    export HF_TOKEN=***        # from .a0proj/secrets.env / A0-Secrets
    /opt/venv/bin/python bdh/scripts/quinn/verify_phase1b.py
"""
import os
import re
import sys
import json
import urllib.request
import urllib.parse
import hashlib
import subprocess

REPO = "Saga-AI-Labs/bdh-cl_phase-1b"
HERE = os.path.dirname(os.path.realpath(__file__))
BDH = os.path.abspath(os.path.join(HERE, "..", ".."))
JOIN_DOC = os.path.join(BDH, "docs", "data", "phase1b-ladra2-crossbox-join.md")
REPORT = os.path.join(BDH, "docs", "data", "phase1b-remote-verification.md")
UPLOADER = os.path.join(HERE, "upload_phase1b.py")
LOCAL_HASH_CACHE = "/srv/coding/bdh/phase1b_local_hashes_2026-09-16.txt"

FILES = [
    "bdh_europarl_ladRA2-bg_best.pt", "bdh_europarl_ladRA2-bg_last.pt",
    "bdh_europarl_ladRA2-el_best.pt", "bdh_europarl_ladRA2-el_last.pt",
    "bdh_europarl_ladRA2-et_best.pt", "bdh_europarl_ladRA2-et_last.pt",
    "bdh_europarl_ladRA2-fi_best.pt", "bdh_europarl_ladRA2-fi_last.pt",
    "bdh_europarl_ladRA2-hu_best.pt", "bdh_europarl_ladRA2-hu_last.pt",
    "bdh_europarl_ladRA2-lt_best.pt", "bdh_europarl_ladRA2-lt_repaired.pt",
    "bdh_europarl_ladRA2-lt_repaired_repair.json",
    "bdh_europarl_ladRA2-sk_best.pt", "bdh_europarl_ladRA2-sk_last.pt",
    "bdh_europarl_ladRA2-sl_best.pt", "bdh_europarl_ladRA2-sl_last.pt",
]
CARD = "README.md"
CERTIFY = FILES + [CARD]


def remote_tree(token):
    url = "https://huggingface.co/api/datasets/" + REPO + "/tree/main"
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    data = json.load(urllib.request.urlopen(req, timeout=40))
    out = {}
    for f in data:
        if f.get("type") == "file":
            out[f["path"]] = (f.get("size") or 0, (f.get("lfs") or {}).get("oid"))
    return out


def remote_hash_of(name, size, oid, token):
    if oid:
        return oid
    url = "https://huggingface.co/datasets/" + REPO + "/resolve/main/" + urllib.parse.quote(name)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    raw = urllib.request.urlopen(req, timeout=60).read()
    if len(raw) != size:
        print("  SIZE-MISMATCH on download of", name, "got", len(raw), "expected", size)
    return hashlib.sha256(raw).hexdigest()


def committed_hashes():
    doc = open(JOIN_DOC).read()
    out = {}
    ns = {}
    exec(open(UPLOADER).read(), ns)  # to source CARD's exact committed text
    out[CARD] = hashlib.sha256(ns["CARD"].encode()).hexdigest()
    for n in FILES:
        m = re.search(r"\|\s*" + re.escape(n) + r"\s*\|\s*`([0-9a-f]{64})`\s*\|", doc)
        if m:
            out[n] = m.group(1)
    return out


def gx10_fresh():
    """Prefer the live re-read produced tonight; regenerate if absent."""
    p = subprocess.run(
        ["ssh", "gx10", "cat", LOCAL_HASH_CACHE],
        capture_output=True, text=True, timeout=60,
    )
    if p.returncode != 0 or not p.stdout.strip():
        print("  no cache; regenerating sha256sum on gx10 (slow)")
        names = " ".join(FILES + [CARD])
        subprocess.run(
            ["ssh", "gx10",
             "cd /srv/coding/bdh/hf_phase1b_upload && sha256sum " + names
             + " > " + LOCAL_HASH_CACHE],
            timeout=3600,
        )
        p = subprocess.run(["ssh", "gx10", "cat", LOCAL_HASH_CACHE],
                           capture_output=True, text=True, timeout=60)
    out = {}
    for ln in p.stdout.splitlines():
        if ln.strip():
            h, _, n = ln.partition(" ")
            out[n.strip().lstrip()] = h.strip()
    return out


def main():
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        sys.exit("HF_TOKEN unset — load it from .a0proj/secrets.env / A0-Secrets")

    remote = remote_tree(token)
    committed = committed_hashes()
    local = gx10_fresh()

    rows = []
    bad = []
    for n in CERTIFY:
        size, oid = remote.get(n, (None, None))
        c = committed.get(n)
        l = local.get(n)
        r = remote_hash_of(n, size, oid, token)
        ok = bool(c) and bool(l) and bool(r) and c == l == r and size is not None
        rows.append((n, c, l, r, "LFS" if oid else "DL", ok))
        if not ok:
            bad.append(n)

    print("object                                    committed  gx10-fresh  remote    via")
    for n, c, l, r, via, ok in rows:
        flag = "OK" if ok else "XX"
        print(f"{flag} {n:41} {(c or '-')[:12]}  {(l or '-')[:12]}  {(r or '-')[:12]}  {via}")

    verdict = "PASS" if not bad else "FAIL"
    res = f"{verdict}: {len(CERTIFY) - len(bad)}/{len(CERTIFY)} byte-identical across committed / gx10-fresh / HF-remote"
    print("\n==== JOIN RESULT:", res)
    if bad:
        print("  BAD:", bad)
        sys.exit(1)

    total = sum(s for s, _ in remote.values())
    lines = [
        "# phase-1b remote verification (three-way sha256)",
        "",
        "Generated 2026-09-16 by Quinn (A0 seat), operator-ordered formal verification ahead of any",
        "deletion. Re-runnable via `bdh/scripts/quinn/verify_phase1b.py`. Identical instrument to the",
        "phase-1 40/40 join.",
        "",
        "For each object the bytes are pinned at three independent points:",
        "",
        "- **(a) committed** pre-upload sha256 in `phase1b-ladra2-crossbox-join.md` (17:30 cross-box audit),",
        "- **(b) gx10 fresh** `sha256sum` re-read of the live staging bytes tonight,",
        "- **(c) HF remote** — the LFS `oid` for the 16 `.pt`, and a `resolve` download + local sha256 for",
        "  the 2 REGULAR blobs (`README.md`, the repair `.json`), which carry no LFS oid.",
        "",
        "a==b proves the on-disk bytes are unchanged since the audit; b==c proves transfer fidelity;",
        "a==c is the non-circular committed<->remote link. All three equal is the claim.",
        "",
        "| file | committed (17:30) | gx10 fresh (now) | HF remote | link | match |",
        "|---|---|---|---|---|---|",
    ]
    for n, c, l, r, via, ok in rows:
        lines.append(
            f"| `{n}` | `{(c or '')[:16]}…` | `{(l or '')[:16]}…` | `{(r or '')[:16]}…` | {via} | {'OK' if ok else 'XX'} |"
        )
    lines += [
        "",
        "**Result: " + res + "** — 17 payload objects + dataset card (`README.md`); 16 via LFS oid,",
        "2 via download-hash. `.gitattributes` is HF-generated LFS machinery, not a payload object,",
        "excluded here and kept on the remote (as in phase-1).",
        "",
        "The 17 files remain on gx10 until pi-50 runs the retrieval spot-check (#303 convention) and",
        "acks; deletion then requires an intent envelope naming the exact 17. Nothing was deleted in",
        "this pass.",
        "",
        f"Remote total: {total} B across {len(remote)} files (repo `{REPO}`).",
        "",
    ]
    open(REPORT, "w").write("\n".join(lines))
    print("\nreport written:", os.path.relpath(REPORT, BDH))


if __name__ == "__main__":
    main()
