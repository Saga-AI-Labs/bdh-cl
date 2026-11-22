#!/usr/bin/env python3
"""Key 2 judge runner - three dimensions, blind, JSON out.

Scores rows from one of the key-2 reference or verdict files with the frozen
rubric in `data/evals/key2_rubric_v1.json`:

  scale      out/key2_calibration/reference_scale.jsonl
  positive   out/key2_calibration/reference_positive.jsonl
  generated  out/key2_calibration/gen_3.62b.jsonl (and later the host file)

The input row must carry an id, a prompt (or instruction) and a sample (or
answer). The judge sees only the prompt and the sample; ids, labels and arm
names stay out of the payload.

Protocol (rubric section 8):
  - temperature 0.0, max_tokens 2048, one retry at 4096 on length or parse
    failure, then NULL (not a silent drop);
  - full judge content and reasoning are stored;
  - endpoint fingerprint is part of the run meta;
  - --resume skips ids already present in the output.

Aggregation (mean+floor, blind re-score) is a separate analysis step; this script
only produces the per-item scores.

Usage:
    .venv/bin/python scripts/quinn/key2_judge.py \
        --base-url http://192.168.178.51:8888/v1 \
        --model Qwen3.8-Flash-Next \
        --input out/key2_calibration/reference_positive.jsonl \
        --out out/key2_calibration/qwen_reference_positive.json \
        --log out/key2_calibration/qwen_reference_positive.log

Dry run (prints the system-prompt hash and the first payload):
    .venv/bin/python scripts/quinn/key2_judge.py --input ... --dry-run
"""

import argparse
import hashlib
import json
import os
import re
import time
import urllib.request

RUBRIC = "data/evals/key2_rubric_v1.json"
MAX_TOKENS = 2048
RETRY_TOKENS = 4096


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def endpoint_fingerprint(base_url, timeout=20):
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/models",
                                    timeout=timeout) as r:
            models = json.loads(r.read().decode())
        ids = sorted(m.get("id", "") for m in models.get("data", []))
        return {"model_list_sha256_16": hashlib.sha256("|".join(ids).encode()).hexdigest()[:16],
                "model_count": len(ids)}
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, e)}


def parse_scores(content):
    """Return (coherence, relevance, language, reason) or None."""
    if not content:
        return None
    start, end = content.find("{"), content.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(content[start:end + 1])
            vals = []
            for k in ("coherence", "relevance", "language"):
                v = obj.get(k)
                if not isinstance(v, int) or not 1 <= v <= 5:
                    raise ValueError(k)
                vals.append(v)
            return vals[0], vals[1], vals[2], str(obj.get("reason", ""))
        except Exception:
            pass
    vals = []
    for k in ("coherence", "relevance", "language"):
        m = re.search(r'"%s"\s*:\s*([1-5])' % k, content)
        if not m:
            return None
        vals.append(int(m.group(1)))
    m = re.search(r'"reason"\s*:\s*"([^"]*)"', content)
    return vals[0], vals[1], vals[2], m.group(1) if m else ""


def call_judge(base_url, model, system_prompt, prompt, sample, timeout=900):
    user = "Prompt:\n" + prompt + "\n\nText:\n" + sample
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "max_tokens": MAX_TOKENS,
    }
    t0 = time.time()
    last = None
    for attempt, tokens in enumerate((MAX_TOKENS, RETRY_TOKENS), 1):
        payload["max_tokens"] = tokens
        req = urllib.request.Request(
            base_url.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = json.loads(r.read().decode())
        except Exception as e:
            detail = {"error": "%s: %s" % (type(e).__name__, e),
                      "attempts": attempt,
                      "max_tokens_used": tokens}
            last = detail
            if attempt == 1:
                continue
            return None, detail, time.time() - t0
        choice = (raw.get("choices") or [{}])[0]
        msg = choice.get("message", {}) or {}
        content = (msg.get("content") or "").strip()
        finish = choice.get("finish_reason")
        parsed = parse_scores(content)
        detail = {
            "content": content,
            "reasoning": msg.get("reasoning_content") or "",
            "finish_reason": finish,
            "usage": raw.get("usage"),
            "attempts": attempt,
            "max_tokens_used": tokens,
        }
        last = detail
        if parsed is None and attempt == 1:
            continue
        if finish == "length" and attempt == 1:
            continue
        if parsed is None:
            return None, last, time.time() - t0
        c, r, l, reason = parsed
        return (c, r, l), dict(detail, reason=reason), time.time() - t0
    return None, last, time.time() - t0


def row_prompt_sample(row):
    prompt = row.get("prompt") or row.get("instruction")
    sample = row.get("sample_text")
    if sample is None:
        sample = row.get("answer")
    if not prompt or sample is None:
        raise SystemExit("row %r has no prompt/instruction or sample/answer" % row.get("id"))
    return prompt, sample


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--base-url")
    ap.add_argument("--model")
    ap.add_argument("--out")
    ap.add_argument("--log")
    ap.add_argument("--rubric", default=RUBRIC)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rubric_doc = json.load(open(args.rubric))
    system_prompt = rubric_doc["system_prompt"]
    system_sha = hashlib.sha256(system_prompt.encode()).hexdigest()
    rubric_sha = sha256_file(args.rubric)
    rows = load_rows(args.input)
    if not rows:
        raise SystemExit("no rows in %s" % args.input)
    if args.limit:
        rows = rows[: args.limit]

    ids = [r.get("id") for r in rows]
    if any(not i for i in ids):
        raise SystemExit("every row needs an id")
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate ids in %s" % args.input)

    if args.dry_run:
        p, s = row_prompt_sample(rows[0])
        print(json.dumps({
            "input": args.input,
            "input_sha256": sha256_file(args.input),
            "rows": len(rows),
            "rubric": args.rubric,
            "rubric_sha256": rubric_sha,
            "system_prompt_sha256": system_sha,
            "system_prompt_bytes": len(system_prompt.encode()),
            "first_id": rows[0].get("id"),
            "first_prompt": p[:120],
            "first_sample": s[:120],
        }, indent=2))
        return

    if not args.base_url or not args.model or not args.out:
        raise SystemExit("--base-url, --model and --out are required unless --dry-run")
    args.log = args.log or (os.path.splitext(args.out)[0] + ".log")
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.log) or ".", exist_ok=True)

    def log(line):
        with open(args.log, "a") as f:
            f.write(line + "\n")
        print(line, flush=True)

    fp = endpoint_fingerprint(args.base_url)
    out = {"meta": {
        "endpoint": args.base_url,
        "model": args.model,
        "input": args.input,
        "input_sha256": sha256_file(args.input),
        "rubric": args.rubric,
        "rubric_sha256": rubric_sha,
        "system_prompt_sha256": system_sha,
        "temperature": 0.0,
        "max_tokens": MAX_TOKENS,
        "retry_tokens": RETRY_TOKENS,
        "endpoint_fingerprint": fp,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }, "rows": []}

    done = set()
    if args.resume and os.path.exists(args.out):
        try:
            prev = json.load(open(args.out))
            out["rows"] = prev.get("rows", [])
            done = {r["id"] for r in out["rows"]}
            log("resume: %d rows from %s" % (len(done), args.out))
        except Exception as e:
            log("resume: could not read %s (%s); starting fresh" % (args.out, e))

    log("### key2 judge start %s" % out["meta"]["started_at"])
    log("endpoint: %s | model: %s | fingerprint: %s"
        % (args.base_url, args.model, json.dumps(fp)))
    log("input: %s | rows: %d | sha256: %s"
        % (args.input, len(rows), out["meta"]["input_sha256"]))
    log("rubric: %s | system_prompt_sha256: %s" % (args.rubric, system_sha))

    for i, row in enumerate(rows, 1):
        rid = row["id"]
        if rid in done:
            log("[%d/%d] %s skipped (resume)" % (i, len(rows), rid))
            continue
        prompt, sample = row_prompt_sample(row)
        log("\n=== %s ===" % rid)
        log("PROMPT: %s" % prompt)
        log("TEXT: %s" % sample)
        scores, detail, latency = call_judge(
            args.base_url, args.model, system_prompt, prompt, sample
        )
        log("JUDGE content: %s" % detail.get("content"))
        log("JUDGE reasoning: %s" % detail.get("reasoning"))
        log("JUDGE finish=%s attempts=%s tokens=%s usage=%s"
            % (detail.get("finish_reason"), detail.get("attempts"),
               detail.get("max_tokens_used"), detail.get("usage")))
        log("JUDGE scores=%s | latency %.1fs" % (scores, latency))
        out["rows"].append({
            "id": rid,
            "dataset": row.get("dataset") or os.path.basename(args.input),
            "family": row.get("family"),
            "gate": row.get("gate"),
            "label": row.get("label") or row.get("variant"),
            "prompt": prompt,
            "sample": sample,
            "coherence": scores[0] if scores else None,
            "relevance": scores[1] if scores else None,
            "language": scores[2] if scores else None,
            "reason": detail.get("reason"),
            "finish_reason": detail.get("finish_reason"),
            "attempts": detail.get("attempts"),
            "usage": detail.get("usage"),
            "latency_s": round(latency, 2),
            "judge_content": detail.get("content"),
            "judge_reasoning": detail.get("reasoning"),
            "system_prompt_sha256": system_sha,
        })
        if len(out["rows"]) % 10 == 0:
            with open(args.out, "w") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)

    out["meta"]["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    out["meta"]["rows"] = len(out["rows"])
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    log("\nwrote %s (%d rows)" % (args.out, len(out["rows"])))


if __name__ == "__main__":
    main()
