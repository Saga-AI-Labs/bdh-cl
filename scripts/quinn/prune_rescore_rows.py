#!/usr/bin/env python3
"""Prune stale and NULL rows from the merged certification JSONs before a rescore.

Why: the merged set was rebuilt after round-3 repairs, but qwen_merged.json and
gemma_merged.json still hold rows scored against the pre-repair texts. The harness
--resume keys on (item_id, variant, repeat), so those rows would be treated as done
and the repaired cells would never be re-scored. The 14 Qwen NULL rows are in the
same state: they are 'done' with score=None, so resume would not retry them.

What is removed:
  - every row whose item_id is in REPAIRED (all variants, all repeats)
  - every row whose score is None (the NULL signature: finish_reason=length)

Everything else is kept, so --resume re-runs only what is missing.
"""
import json
import sys

REPAIRED = {'cert_zh05', 'cert_de13', 'cert_de16', 'cert_de24'}


def main():
    for j in ('qwen', 'gemma'):
        p = 'out_c/judge_calibration/%s_merged.json' % j
        d = json.load(open(p, encoding='utf-8'))
        rows = d['rows']
        before = len(rows)
        keep = []
        removed_repaired = 0
        removed_null = 0
        for r in rows:
            if r['item_id'] in REPAIRED:
                removed_repaired += 1
                continue
            if r.get('score') is None:
                removed_null += 1
                continue
            keep.append(r)
        d['rows'] = keep
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('%-6s rows %d -> %d | removed repaired %d | removed null %d'
              % (j, before, len(keep), removed_repaired, removed_null))
        # report what will be re-run
        redo = sorted({(r['item_id'], r['variant']) for r in rows
                       if r['item_id'] in REPAIRED or r.get('score') is None})
        print('       will re-run %d cells:' % len(redo))
        for it, v in redo:
            print('         %s/%s' % (it, v))


if __name__ == '__main__':
    main()
