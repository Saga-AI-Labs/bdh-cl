#!/usr/bin/env python3
"""Build the branch corpus for the expert-merge prereg section 2.2.

Source: Project Gutenberg, public domain, downloaded directly from
gutenberg.org (reachable as of 2026-11-05). No HuggingFace LFS needed and
no 825 GiB Pile download.

Why Gutenberg: the prereg asks for the largest capability gap to the
Europarl-translationese trunk. The trunk base is wikitext-103 (English
Wikipedia, expository) plus Europarl phases. Gutenberg long-form narrative
fiction -- dialogue, first person, long-range plot coherence -- is a register
the trunk has never seen, while staying English so the merge does not confound
language with register.

Output layout:
  <out>/train.txt    ~90 % of bytes
  <out>/heldout.txt  fixed 10 % tail, split BEFORE training (prereg 2.2)
  <out>/manifest.json per-book sizes, source ids, strip statistics
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

# English-original long-form prose, all public domain in the US.
BOOKS = [
    (1342, "Pride and Prejudice"),
    (11, "Alice in Wonderland"),
    (1661, "Sherlock Holmes"),
    (2701, "Moby Dick"),
    (84, "Frankenstein"),
    (98, "A Tale of Two Cities"),
    (174, "The Picture of Dorian Gray"),
    (345, "Dracula"),
    (1260, "Jane Eyre"),
    (768, "Wuthering Heights"),
    (1400, "Great Expectations"),
    (1023, "Bleak House"),
    (158, "Emma"),
    (161, "Sense and Sensibility"),
    (105, "Persuasion"),
    (74, "Tom Sawyer"),
    (76, "Huckleberry Finn"),
    (120, "Treasure Island"),
    (43, "Jekyll and Hyde"),
    (16, "Peter Pan"),
    (113, "The Secret Garden"),
    (205, "Middlemarch"),
    (35, "The Time Machine"),
    (36, "The War of the Worlds"),
    (159, "Island of Doctor Moreau"),
    (1232, "The Last of the Mohicans"),
    (2097, "The Sign of the Four"),
    (244, "A Study in Scarlet"),
    (108, "The Return of Sherlock Holmes"),
    (834, "The Memoirs of Sherlock Holmes"),
    (863, "The Adventures of Sherlock Holmes"),
    (3289, "The Hound of the Baskervilles"),
    (1399, "Anna Karenina (Garnett)"),
    (2554, "Crime and Punishment (Garnett)"),
    (28054, "The Brothers Karamazov (Garnett)"),
    (600, "Notes from Underground"),
    (219, "Heart of Darkness"),
    (160, "The Awakening"),
    (1952, "The Yellow Wallpaper"),
    (932, "The Fall of the House of Usher"),
    (2148, "The Works of Poe Vol 1"),
    (1232, "Last of the Mohicans"),
    (521, "The Life of Lazarillo"),
    (829, "Gulliver's Travels"),
    (1041, "The Life and Opinions of Tristram Shandy"),
]

START_RE = re.compile(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)
END_RE = re.compile(r"\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)


def fetch(book_id, timeout=45):
    url = "https://www.gutenberg.org/cache/epub/%d/pg%d.txt" % (book_id, book_id)
    req = urllib.request.Request(url, headers={"User-Agent": "bdh-cl corpus builder"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def strip_gutenberg(raw):
    text = raw.decode("utf-8", errors="replace")
    m = START_RE.search(text)
    if m:
        text = text[m.end():]
    m = END_RE.search(text)
    if m:
        text = text[:m.start()]
    # collapse whitespace runs, keep paragraph structure
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/expert")
    ap.add_argument("--target-mb", type=float, default=22.0)
    ap.add_argument("--heldout-frac", type=float, default=0.10)
    ap.add_argument("--sleep", type=float, default=0.6)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    target = int(args.target_mb * 1_000_000)

    seen = set()
    parts = []
    manifest = []
    total = 0

    for book_id, title in BOOKS:
        if book_id in seen:
            continue
        seen.add(book_id)
        if total >= target:
            print("target reached (%s bytes), stopping" % format(total, ","))
            break
        try:
            raw = fetch(book_id)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
            print("  SKIP %5d %-42s %s" % (book_id, title, type(e).__name__))
            continue
        text = strip_gutenberg(raw)
        n = len(text.encode("utf-8"))
        if n < 50_000:
            print("  SKIP %5d %-42s too short (%s bytes after strip)" % (book_id, title, format(n, ",")))
            continue
        parts.append(text)
        total += n
        manifest.append({"id": book_id, "title": title, "bytes": n})
        print("  ok   %5d %-42s %9s bytes  (cum %s)" %
              (book_id, title, format(n, ","), format(total, ",")))
        time.sleep(args.sleep)

    if not parts:
        sys.exit("no books downloaded")

    blob = "\n\n".join(parts)
    raw_bytes = blob.encode("utf-8")
    n_total = len(raw_bytes)
    cut = int(n_total * (1 - args.heldout_frac))

    train = raw_bytes[:cut]
    held = raw_bytes[cut:]

    with open(os.path.join(args.out, "train.txt"), "wb") as f:
        f.write(train)
    with open(os.path.join(args.out, "heldout.txt"), "wb") as f:
        f.write(held)

    info = {
        "source": "project gutenberg, direct download 2026-11-05",
        "books": manifest,
        "books_used": len(manifest),
        "total_bytes": n_total,
        "train_bytes": len(train),
        "heldout_bytes": len(held),
        "heldout_frac": args.heldout_frac,
        "target_mb": args.target_mb,
    }
    with open(os.path.join(args.out, "manifest.json"), "w") as f:
        json.dump(info, f, indent=2)

    blocks = len(train) // 512
    print()
    print("books:        %d" % len(manifest))
    print("total:        %s bytes (%.1f MB)" % (format(n_total, ","), n_total / 1e6))
    print("train:        %s bytes (%.1f MB) = %s blocks of 512" %
          (format(len(train), ","), len(train) / 1e6, format(blocks, ",")))
    print("heldout:      %s bytes (%.2f MB)" % (format(len(held), ","), len(held) / 1e6))
    print()
    print("training cost at mult 896 (measured 7.74 s/step at batch 1 from phase zh):")
    for epochs in (1, 2):
        steps_b1 = blocks * epochs
        print("  %d epoch(s), batch 1: %s steps -> %.1f h (%.1f days)" %
              (epochs, format(steps_b1, ","), steps_b1 * 7.74 / 3600, steps_b1 * 7.74 / 86400))


if __name__ == "__main__":
    main()
