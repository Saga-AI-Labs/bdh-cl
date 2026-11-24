"""Check the frozen key-2 prompts for word-8-gram overlap with the host corpus.

Rubric 8.7: "Check each prompt for an 8-gram overlap with the host corpus."
The prompts are frozen, so a hit is a recorded finding, not a reason to edit
them silently. The rule is the last eight words of the prompt (the whole prompt
if shorter) as an exact byte phrase; a single space joins the words, matching
the authored form.

Usage:
  .venv/bin/python scripts/quinn/key2_prompt_contamination.py \
      --corpus data/host/fineweb_train.txt --out out/host/prompt_contamination.json
"""

import argparse
import datetime
import hashlib
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", default="data/evals/key2_prompts_v1.json")
    ap.add_argument("--corpus", default="data/host/fineweb_train.txt")
    ap.add_argument("--out", default="out/host/prompt_contamination.json")
    args = ap.parse_args()

    doc = json.load(open(args.prompts))
    items = doc["prompts"] if isinstance(doc, dict) and "prompts" in doc else doc
    corpus = open(args.corpus, "rb").read()
    hits = []
    for it in items:
        raw = it["prompt"].encode("utf-8")
        words = raw.split()
        needle = b" ".join(words[-8:]) if len(words) >= 8 else raw
        off = corpus.find(needle)
        if off >= 0:
            hits.append({"id": it["id"], "needle": needle.decode("utf-8", "replace"),
                         "offset": off})
    h = hashlib.sha256(corpus).hexdigest()
    out = {
        "schema": "key2_prompt_contamination_v1",
        "date": datetime.date.today().isoformat(),
        "prompts": len(items),
        "corpus": args.corpus,
        "corpus_bytes": len(corpus),
        "corpus_sha256": h,
        "rule": "last 8 words of each prompt (whole prompt if shorter), exact byte phrase",
        "hits": hits,
        "result": "clean" if not hits else "hits",
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    print(f"{len(items)} prompts | {len(hits)} word-8-gram hits | "
          f"{'clean' if not hits else 'FINDING'}")
    for hit in hits[:10]:
        print("  ", hit["id"], "|", hit["needle"])
    print("wrote", args.out)


if __name__ == "__main__":
    main()
