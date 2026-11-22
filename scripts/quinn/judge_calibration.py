#!/usr/bin/env python3
"""Judge certification harness for judge_set_v1 (chat prereg section 4.4a/4.4b).

This replaced the 10-item first run's harness. That run produced four non-judge
failures (two label traps, one token-budget null, two rubric-compressed ties) and
showed the harness predated the frozen protocol:

  - max_tokens 512 was below a reasoning judge's needs (observed 111-509 reasoning
    tokens/call; 512 produced a null on the hardest row). Now 2048, with one
    auto-retry at 4096 on finish_reason=length before recording a null.
  - the reasoning channel was truncated at 400 chars in the log; it is now logged
    untruncated, because it is the failure-diagnosis field.
  - the system prompt is the frozen rubric from judge_set_v1/README.md section 2
    (all five anchors), not an improvised one.
  - the endpoint fingerprint is recorded in the run meta: endpoint identity is part
    of the judge's audit trail, and a re-quantized endpoint is a different judge
    until re-certified.
  - items are loaded from data/evals/judge_set_v1/cert_items.json; this file no
    longer carries its own item set, so the frozen set is the single source.

Run shape (README section 3):
  - temperature 0.0
  - one pass over all 30 items x 6 variants (180 rows)
  - three full repeats on the items marked "stability": true (the 10-item
    subslice), for the exact-match and +/-1 rates
  - call order fixed, seed fixed (the seed is recorded; the endpoint does not
    accept a seed parameter, so stability is measured across repeats, not
    requested determinism)

Certification criteria (README section 4) are computed and printed per language
slice as well as overall.

Usage:
    python scripts/quinn/judge_calibration.py \\
        --base-url http://192.168.178.200:1234/v1 \\
        --model gemma-4-31b-it \\
        --set data/evals/judge_set_v1/cert_items.json \\
        --out out_c/judge_calibration/cert.json \\
        --log out_c/judge_calibration/cert.log
"""

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

# Frozen rubric, judge_set_v1/README.md section 2. Changing this requires a new
# set version.
SYSTEM_PROMPT = (
    "You grade chat answers strictly. Reply ONLY with a JSON object "
    '{"score": <integer 1-5>, "reason": "<short string>"}. No other text, no markdown.\n'
    "Anchors:\n"
    "5 = correct, complete, and satisfies every stated constraint (audience, language, format)\n"
    "4 = correct with a minor gap or a slight constraint miss\n"
    "3 = correct but substantially incomplete\n"
    "2 = partially flawed or contains a notable error\n"
    "1 = wrong, misleading, or ignores the instruction"
)

MAX_TOKENS = 2048
RETRY_TOKENS = 4096
REPEATS = 3


def endpoint_fingerprint(base_url, timeout=20):
    """Best-effort identity of the served endpoint."""
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/models",
                                    timeout=timeout) as r:
            models = json.loads(r.read().decode())
        ids = sorted(m.get("id", "") for m in models.get("data", []))
        digest = hashlib.sha256("|".join(ids).encode()).hexdigest()[:16]
        return {"model_list_sha256_16": digest, "model_count": len(ids)}
    except Exception as e:
        return {"error": "%s: %s" % (type(e).__name__, e)}


def call_judge(base_url, model, instruction, answer, timeout=600):
    """One judge request with one retry on length. Returns (score, detail, latency)."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Instruction:\n" + instruction + "\n\nAnswer:\n" + answer},
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
            return None, {"error": "%s: %s" % (type(e).__name__, e),
                         "attempts": attempt}, time.time() - t0

        choice = (raw.get("choices") or [{}])[0]
        msg = choice.get("message", {}) or {}
        content = (msg.get("content") or "").strip()
        finish = choice.get("finish_reason")
        score = None
        m = re.search(r'\{\s*"score"\s*:\s*(\d)', content)
        if m:
            score = int(m.group(1))

        detail = {
            "content": content,
            "reasoning": msg.get("reasoning_content") or "",
            "finish_reason": finish,
            "usage": raw.get("usage"),
            "attempts": attempt,
            "max_tokens_used": tokens,
        }
        last = detail
        # retry only when the reasoning channel ate the whole budget
        if finish == "length" and attempt == 1:
            continue
        return score, detail, time.time() - t0
    return last.get("score_parsed") if False else None, last, time.time() - t0


def criteria(rows):
    """Certification criteria from README section 4, over a row list."""
    def scores(label):
        return [r["score"] for r in rows if r["variant"] == label and r["score"] is not None]

    good = scores("good")
    short = scores("short_correct")
    long_wrong = scores("long_wrong")
    planted = scores("planted_error")
    audience = scores("audience_violation")
    bad = scores("bad")

    out = {}
    out["n"] = len(rows)
    if good and short:
        out["separation_gap"] = round(sum(good) / len(good) - sum(short) / len(short), 3)
        out["separation_good_ge4_pct"] = round(100 * sum(1 for s in good if s >= 4) / len(good), 1)
        out["separation_pass"] = (out["separation_gap"] >= 0.8
                                  and out["separation_good_ge4_pct"] >= 80)
    if long_wrong:
        out["brevity_long_wrong_le2_pct"] = round(100 * sum(1 for s in long_wrong if s <= 2) / len(long_wrong), 1)
        out["brevity_mean"] = round(sum(long_wrong) / len(long_wrong), 3)
        out["brevity_pass"] = (out["brevity_long_wrong_le2_pct"] >= 80
                               and out["brevity_mean"] <= 2.5)
    if planted:
        out["fact_le3_pct"] = round(100 * sum(1 for s in planted if s <= 3) / len(planted), 1)
        out["fact_eq5_pct"] = round(100 * sum(1 for s in planted if s == 5) / len(planted), 1)
        out["fact_pass"] = out["fact_le3_pct"] >= 80 and out["fact_eq5_pct"] == 0
    if audience:
        out["constraint_le3_pct"] = round(100 * sum(1 for s in audience if s <= 3) / len(audience), 1)
        out["constraint_pass"] = out["constraint_le3_pct"] >= 80
    if bad:
        out["floor_eq1_pct"] = round(100 * sum(1 for s in bad if s == 1) / len(bad), 1)
        out["floor_mean"] = round(sum(bad) / len(bad), 3)
        out["floor_pass"] = out["floor_eq1_pct"] >= 70 and out["floor_mean"] <= 1.5

    # ordinal order per item
    by_item = {}
    for r in rows:
        by_item.setdefault(r["item_id"], {})[r["variant"]] = r["score"]
    ok, total = 0, 0
    for v in by_item.values():
        if v.get("good") is not None and v.get("short_correct") is not None \
                and v.get("bad") is not None:
            total += 1
            if v["good"] >= v["short_correct"] >= v["bad"]:
                ok += 1
    out["ordinal_items_ok"] = ok
    out["ordinal_items_total"] = total
    out["ordinal_pass"] = total > 0 and ok == total
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--set", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", required=True)
    ap.add_argument("--resume", action="store_true",
                    help="read existing rows from --out and skip completed calls")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    def log(line):
        with open(args.log, "a") as f:
            f.write(line + "\n")
        print(line, flush=True)

    dataset = json.load(open(args.set))
    items = dataset["items"]
    stability_ids = {it["item_id"] for it in items if it.get("stability")}

    log("### judge certification start %s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    log("endpoint: %s | model: %s" % (args.base_url, args.model))
    log("set: %s | items: %d | variants/item: %d" % (args.set, len(items),
                                                      len(items[0]["variants"])))
    log("knobs: temperature=0.0 max_tokens=%d retry=%d repeats_on_stability=%d"
        % (MAX_TOKENS, RETRY_TOKENS, REPEATS))
    fp = endpoint_fingerprint(args.base_url)
    log("endpoint fingerprint: %s" % json.dumps(fp))

    rows = []
    done = set()
    if args.resume and os.path.exists(args.out):
        try:
            prev = json.load(open(args.out))
            rows = prev.get("rows", [])
            done = {(r["item_id"], r["variant"], r["repeat"]) for r in rows}
            log("resume: %d rows from %s, %d calls already done"
                % (len(rows), args.out, len(done)))
        except Exception as e:
            log("resume: could not read %s (%s: %s) -- starting fresh"
                % (args.out, type(e).__name__, e))
            rows = []

    total_calls = 0
    skipped = 0
    for it in items:
        reps = REPEATS if it["item_id"] in stability_ids else 1
        log("\n=== %s [%s] stability=%s repeats=%d ==="
            % (it["item_id"], it["lang"], it.get("stability", False), reps))
        log("INSTRUCTION: %s" % it["instruction"])
        if it.get("constraint"):
            log("CONSTRAINT: %s" % it["constraint"]["text"])
        # checkpoint after each item so --resume can pick up mid-run
        def _save_checkpoint():
            try:
                with open(args.out, "w") as f:
                    json.dump({"meta": {"endpoint": args.base_url, "model": args.model,
                                "set": args.set, "set_status": dataset.get("status"),
                                "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
                                "endpoint_fingerprint": fp, "max_tokens": MAX_TOKENS,
                                "retry_tokens": RETRY_TOKENS, "repeats": REPEATS,
                                "total_calls": total_calls, "in_progress": True},
                       "rows": rows}, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

        for v in it["variants"]:
            for rep in range(1, reps + 1):
                total_calls += 1
                tag = "%s/%s rep%d" % (it["item_id"], v["label"], rep)
                if (it["item_id"], v["label"], rep) in done:
                    skipped += 1
                    log("  --- %s (skipped, already done) ---" % tag)
                    continue
                log("  --- %s ---" % tag)
                log("  ANSWER: %s" % v["text"])
                score, detail, latency = call_judge(args.base_url, args.model,
                                                   it["instruction"], v["text"])
                log("  JUDGE content: %s" % detail.get("content"))
                log("  JUDGE reasoning: %s" % detail.get("reasoning"))
                log("  JUDGE finish=%s attempts=%s tokens=%s usage=%s"
                    % (detail.get("finish_reason"), detail.get("attempts"),
                       detail.get("max_tokens_used"), detail.get("usage")))
                log("  JUDGE score=%s | latency %.1fs" % (score, latency))
                rows.append({
                    "item_id": it["item_id"], "lang": it["lang"],
                    "variant": v["label"], "repeat": rep,
                    "score": score, "finish_reason": detail.get("finish_reason"),
                    "attempts": detail.get("attempts"),
                    "usage": detail.get("usage"),
                    "latency_s": round(latency, 2),
                    "instruction": it["instruction"],
                    "answer": v["text"],
                    "judge_content": detail.get("content"),
                    "judge_reasoning": detail.get("reasoning"),
                })

        _save_checkpoint()

    log("\n### criteria (all rows, one pass = repeat 1 only)")
    pass1 = [r for r in rows if r["repeat"] == 1]
    overall = criteria(pass1)
    for k, v in sorted(overall.items()):
        log("  %-28s %s" % (k, v))

    log("\n### criteria per language (repeat 1)")
    per_lang = {}
    for lang in ("en", "de", "zh"):
        c = criteria([r for r in pass1 if r["lang"] == lang])
        per_lang[lang] = c
        log("  [%s] separation=%s brevity=%s fact=%s constraint=%s floor=%s ordinal=%s"
            % (lang, c.get("separation_pass"), c.get("brevity_pass"),
               c.get("fact_pass"), c.get("constraint_pass"),
               c.get("floor_pass"), c.get("ordinal_pass")))

    # stability: only stability items, repeats 1..3
    stab = [r for r in rows if r["item_id"] in stability_ids]
    exact = within1 = 0
    pairs = 0
    for it_id in stability_ids:
        for v in {r["variant"] for r in stab if r["item_id"] == it_id}:
            seq = [r["score"] for r in sorted(stab, key=lambda x: x["repeat"])
                   if r["item_id"] == it_id and r["variant"] == v]
            if len(seq) >= 2 and None not in seq:
                pairs += 1
                exact += (max(seq) == min(seq))
                within1 += (max(seq) - min(seq) <= 1)
    stability = {"pairs": pairs,
                 "exact_match_pct": round(100 * exact / pairs, 1) if pairs else None,
                 "within_1_pct": round(100 * within1 / pairs, 1) if pairs else None,
                 "pass": bool(pairs and 100 * exact / pairs >= 70 and 100 * within1 / pairs >= 95)}
    log("\n### stability (stability subslice, %d pairs)" % pairs)
    for k, v in stability.items():
        log("  %-20s %s" % (k, v))

    out = {"meta": {"endpoint": args.base_url, "model": args.model,
                    "set": args.set, "set_status": dataset.get("status"),
                    "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
                    "endpoint_fingerprint": fp, "max_tokens": MAX_TOKENS,
                    "retry_tokens": RETRY_TOKENS, "repeats": REPEATS,
                    "total_calls": total_calls},
           "criteria_all": overall, "criteria_per_lang": per_lang,
           "stability": stability, "rows": rows}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    log("\nwrote %s (%d rows, %d calls, %d skipped by resume)"
        % (args.out, len(rows), total_calls, skipped))


if __name__ == "__main__":
    main()
