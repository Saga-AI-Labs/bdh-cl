"""housekeeping_scan.py — compaction round in one read-only diff.

Background: append-only growth + per-phase checkpoints make the training hosts a
log that grows; HuggingFace is cold storage; "cleanup" is compaction. Each round so
far was a manual expedition (ssh both boxes, sha-join, classify). The durable
manifests committed under docs/data/ are the cache that makes round N+1 a diff, not
a re-hash. This tool automates the diff and the safe-to-delete classification. IT
DELETES NOTHING. A human reads the report and issues an intent envelope naming the
exact files (HAK protocol, the #298 pattern) before anything is removed.

Truth rule for deletion (learned the hard way from pi-50's #290 .metadata trap):
  the committed manifest is a CACHE that lets us SKIP re-hashing — it is NOT the
  proof that a file is safe to delete. "Safe to delete from box A" is decided live:
  the file must exist on BOTH boxes with the same size (so a copy survives), and with
  --hash the same sha256. A stale manifest line never authorises a delete on its own.

Usage (run from the agent container, which holds the ssh config for both hosts):
  python3 scripts/quinn/housekeeping_scan.py            # read-only report
  python3 scripts/quinn/housekeeping_scan.py --hash     # + cross-box sha256 on candidates
"""
import argparse
import os
import subprocess
import sys

# Hosts that hold checkpoint output. Aliases resolve via ~/.ssh/config in the agent
# container. out_paths differ per host layout. Nothing is written to either host.
HOSTS = {
    "gx10":   ("gx10",     "/srv/coding/bdh/out"),
    "r4090":  ("bdh-4090", "/media/data/coding/bdh/out"),
}
# The box that is the "long-term local" side — a duplicate is deleted from the
# smaller box only if the survivor is on the larger, non-bottleneck box.
SURVIVOR_HOST = "r4090"
PRUNE_HOST = "gx10"

REPO = os.environ.get("BDH_REPO", "/a0/usr/projects/saga_quinn/bdh")
MANIFESTS = {
    "phase1_ra2b": "docs/data/phase1-upload-checksums.md",
    "phase1b_ladra2": "docs/data/phase1b-ladra2-crossbox-join.md",
}


def ssh_run(alias, cmd, timeout=120):
    full = ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", alias, cmd]
    try:
        p = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        return p.stdout
    except Exception as e:  # noqa: BLE001 - report and continue, scan is best-effort
        print("  ssh error on %s: %s" % (alias, repr(e)[:160]), file=sys.stderr)
        return ""


def list_out(alias, path):
    """Return {name: size} of files directly under a host's out dir (read-only)."""
    cmd = 'find %s -maxdepth 1 -type f -printf "%%s %%f\\n" 2>/dev/null' % path
    out = ssh_run(alias, cmd)
    d = {}
    for line in out.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2 and parts[0].isdigit():
            d[parts[1]] = int(parts[0])
    return d


def load_manifest_names():
    """First table column of each committed manifest -> set of known filenames."""
    known = {}
    for tag, rel in MANIFESTS.items():
        p = os.path.join(REPO, rel)
        names = set()
        if os.path.isfile(p):
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line.startswith("|") and "." in line:
                    first = line.split("|")[1].strip()
                    if first.endswith((".pt", ".json")):
                        names.add(first)
        known[tag] = names
    return known


def main():
    ap = argparse.ArgumentParser(description="read-only gx10/.200 checkpoint compaction diff")
    ap.add_argument("--hash", action="store_true",
                    help="confirm size-matched candidates with cross-box sha256 (slow, IO-light)")
    args = ap.parse_args()

    print("== housekeeping scan (%s) ==" % ("+hash" if args.hash else "sizes only"))
    listings = {}
    for host, (alias, path) in HOSTS.items():
        print("listing %s (%s)..." % (host, path))
        listings[host] = list_out(alias, path)
        print("  %d files, %.1f GiB" % (
            len(listings[host]), sum(listings[host].values()) / 1024**3))

    known = load_manifest_names()
    known_all = set().union(*known.values()) if known else set()

    A = listings[PRUNE_HOST]   # gx10 (candidate deletions)
    B = listings[SURVIVOR_HOST]

    dup_sizes = []   # present on both, same size -> delete PRUNE side (copy survives)
    keep_prune = []  # only on PRUNE -> must NOT delete until replicated
    only_surv = []   # only on SURVIVOR -> irrelevant here
    for n, sz in sorted(A.items()):
        if n in B:
            if B[n] == sz:
                dup_sizes.append(n)
            else:
                print("  [!] size differs across boxes: %s %d vs %d -> inspect" % (n, sz, B[n]))
        else:
            keep_prune.append(n)
    only_surv = [n for n in B if n not in A]

    print()
    print("--- on %s only (KEEP / needs replication, do NOT delete): %d files, %.1f GiB ---"
          % (PRUNE_HOST, len(keep_prune), sum(A[n] for n in keep_prune) / 1024**3))
    for n in keep_prune:
        tag = "" if n in known_all else "  <== NEW, not in any manifest"
        print("  KEEP %s (%.1f GiB)%s" % (n, A[n] / 1024**3, tag))

    print()
    print("--- %s==%s same size (SAFE-TO-DELETE %s side, survivor on %s): %d files, %.1f GiB ---"
          % (PRUNE_HOST, SURVIVOR_HOST, PRUNE_HOST, SURVIVOR_HOST, len(dup_sizes),
             sum(A[n] for n in dup_sizes) / 1024**3))
    for n in dup_sizes:
        src = "ledger" if n in known_all else "NEW-size-only"
        print("  DUP  %s (%.1f GiB)  [%s]" % (n, A[n] / 1024**3, src))

    if args.hash:
        print()
        print("--- cross-box sha256 confirm on %d size-matched candidates (nice+ionice) ---" % len(dup_sizes))
        confirmed, rejected = [], []
        for n in dup_sizes:
            ha = ssh_run(HOSTS[PRUNE_HOST][0],
                         'nice -n19 ionice -c3 sha256sum %s/%s 2>/dev/null | cut -d" " -f1'
                         % (HOSTS[PRUNE_HOST][1], n))
            hb = ssh_run(HOSTS[SURVIVOR_HOST][0],
                         'nice -n19 ionice -c3 sha256sum %s/%s 2>/dev/null | cut -d" " -f1'
                         % (HOSTS[SURVIVOR_HOST][1], n))
            ha, hb = ha.strip(), hb.strip()
            if ha and ha == hb:
                confirmed.append(n)
            else:
                rejected.append((n, ha[:12], hb[:12]))
                print("  SHA-MISMATCH %s (do NOT delete): %s vs %s" % (n, ha[:12], hb[:12]))
        print("  sha-confirmed safe: %d/%d" % (len(confirmed), len(dup_sizes)))

    print()
    print("NOTE: this tool deleted nothing. Turn the SAFE-TO-DELETE list into an intent")
    print("envelope naming exact files; get peer ack; only then rm. The 'only on %s' set"
          % PRUNE_HOST)
    print("is what still needs a remote/backup copy before any future space grab.")


if __name__ == "__main__":
    main()
