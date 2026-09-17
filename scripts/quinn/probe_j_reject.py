#!/usr/bin/env python
"""Probe J: fixed byte-NLL rejection with independent source-region splits."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback

for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[name] = '2'
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from c_arms import ByteNGram, wilson

LANGS = 'en es pl fr de cs da pt fi hu bg it et el sk sv ro nl sl lt'.split()
PAIRS = {d: d + '-en' for d in LANGS}
PAIRS.update(en='de-en', de='de-en')
OOD = dict(lv='europarl-v7.lv-en.lv.txt', ga='DGT.en-ga.ga.txt',
           zh='xscript_zh.txt', ja='xscript_ja.txt', hi='xscript_hi.txt',
           iu='xscript_iu_syl.txt')
PROTOCOL = Path('docs/plans/2026-09-17_probe-j-reject.md')


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, data):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def offsets(lo, hi, seed, n=96, size=512):
    if lo < 0 or (hi - lo) // size < n:
        raise ValueError('Insufficient region for fixed nonoverlapping sample')
    slots = np.random.default_rng(seed).choice((hi-lo)//size, n, replace=False)
    out = sorted(int(lo + i*size) for i in slots)
    assert all(lo <= o and o+size <= hi for o in out)
    assert all(b >= a+size for a, b in zip(out, out[1:]))
    return out


def sample(path, lang, lo, hi, seed, source_hash, partition):
    rows = []
    with open(path, 'rb') as f:
        for off in offsets(lo, hi, seed):
            f.seek(off)
            raw = f.read(512)
            assert len(raw) == 512
            rows.append({'domain': lang, 'partition': partition,
                         'source': str(path), 'source_sha256': source_hash,
                         'region': [lo, hi], 'offset': off,
                         'sha256': hashlib.sha256(raw).hexdigest(),
                         'raw': np.frombuffer(raw, dtype=np.uint8)})
    return rows


def provenance(rows):
    return [{k: v for k, v in row.items() if k != 'raw'} for row in rows]


def score(model, pooled, classes, raw):
    assert raw.dtype == np.uint8 and raw.ndim == 1
    n = len(raw)
    values = [-model.logp(c, raw)/n for c in classes]
    i = int(np.argmin(values))
    best, cls = float(values[i]), classes[i]
    joint = -pooled.logp('pooled', raw)/n
    assert best > 0 and math.isfinite(joint)
    b = raw.tobytes()
    unseen = sum(b[j:j+4] not in model.ng[cls] for j in range(n-3))/(n-3)
    return {'predicted_domain': cls, 'best_nll': best,
            'pooled_nll': joint, 'ratio_descriptive': joint/best,
            'unseen4gram_descriptive': unseen}


def tally(rows, tau, id_data):
    accepted = [r for r in rows if r['best_nll'] <= tau]
    k, n = len(accepted), len(rows)
    rec = {'n': n, 'accepted': k, 'acceptance': k/n,
           'wilson95': list(wilson(k, n)),
           'mean_nll': float(np.mean([r['best_nll'] for r in rows])),
           'predicted_domains': dict(Counter(r['predicted_domain'] for r in rows))}
    rec['domain_mean_accepted'] = rec['mean_nll'] <= tau
    if id_data:
        rec['classification_correct'] = sum(r['domain'] == r['predicted_domain'] for r in rows)
        rec['accepted_classification_correct'] = sum(r['domain'] == r['predicted_domain'] for r in accepted)
        rec['accepted_classification_accuracy'] = rec['accepted_classification_correct']/k if k else None
    return rec


def selftest():
    a = np.frombuffer((b'alpha beta ' * 50)[:512], dtype=np.uint8)
    b = np.frombuffer((b'gamma delta ' * 50)[:512], dtype=np.uint8)
    m, p = ByteNGram(), ByteNGram()
    m.fit('a', [a]); m.fit('b', [b]); p.fit('pooled', [a, b])
    s = score(m, p, ['a', 'b'], a)
    assert len(bytes(a)) == 512
    manual = sum(math.log((m.ng['a'].get(bytes(a)[i:i+4], 0)+1)/
                         (m.cx['a'].get(bytes(a)[i:i+3], 0)+256)) for i in range(509))
    assert math.isclose(manual, m.logp('a', a), abs_tol=1e-12)
    assert math.isclose(s['ratio_descriptive'], s['pooled_nll']/s['best_nll'])
    assert offsets(1000, 100000, 2) == offsets(1000, 100000, 2)
    assert np.percentile([1., 2., 3.], 99, method='higher') == 3
    assert json.loads(json.dumps(s, allow_nan=False)) == s
    print('SELFTEST PASS', flush=True)


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    result = {'status': 'preflight', 'pid': os.getpid(),
              'protocol_sha256': digest(PROTOCOL), 'runner_sha256': digest(__file__),
              'dependency_sha256': digest(Path(__file__).with_name('c_arms.py')),
              'limitations': ['Known development languages, fresh byte regions only',
                              'Byte-disjoint regions do not guarantee document independence'],
              'blocked': {}}
    save(out/'result.json', result)
    partitions = {k: [] for k in ('train', 'calibration', 'id_test', 'ood')}
    base = Path('data/europarl')
    for li, lang in enumerate(LANGS):
        path = base/f'europarl-v7.{PAIRS[lang]}.{lang}.txt'
        length, sha = path.stat().st_size, digest(path)
        ranges = [(length-3000000, length-2000000),
                  (length-2000000, length-1700000),
                  (length-1300000, length-1000000)]
        for pi, part in enumerate(('train', 'calibration', 'id_test')):
            partitions[part] += sample(path, lang, *ranges[pi], 12000+100*pi+li, sha, part)
        print('[preflight] ID', lang, flush=True)
    for li, (lang, filename) in enumerate(OOD.items()):
        path = base/filename
        hi, sha = path.stat().st_size-2000000-1048576, digest(path)
        if hi < 96*512:
            result['blocked'][lang] = {'reason': 'No independent fixed-size head sample',
                                       'source': str(path), 'source_sha256': sha}
        else:
            partitions['ood'] += sample(path, lang, 0, hi, 13000+li, sha, 'ood')
    seen = {}
    conflicts = []
    for part, rows in partitions.items():
        for row in rows:
            prior = seen.setdefault(row['sha256'], part)
            if prior != part:
                conflicts.append({'sha256': row['sha256'], 'partitions': [prior, part]})
    save(out/'provenance.json', {k: provenance(v) for k, v in partitions.items()})
    if conflicts:
        result.update(status='BLOCKED_PREFLIGHT', duplicate_hash_conflicts=conflicts)
        save(out/'result.json', result)
        raise ValueError('Cross-partition exact duplicate content; no scores computed')
    model, pooled = ByteNGram(), ByteNGram()
    for lang in LANGS:
        model.fit(lang, [r['raw'] for r in partitions['train'] if r['domain'] == lang])
    pooled.fit('pooled', [r['raw'] for r in partitions['train']])

    def evaluate(part):
        scored = []
        for i, row in enumerate(partitions[part]):
            scored.append({**{k: v for k, v in row.items() if k != 'raw'},
                           **score(model, pooled, LANGS, row['raw'])})
            if (i+1) % 96 == 0:
                print('[score]', part, i+1, flush=True)
        save(out/f'{part}_scores.json', scored)
        return scored

    calibration = evaluate('calibration')
    tau = float(np.percentile([r['best_nll'] for r in calibration], 99, method='higher'))
    save(out/'frozen_threshold.json', {'tau': tau, 'method': 'higher', 'percentile': 99,
                                     'calibration_n': len(calibration),
                                     'protocol_sha256': result['protocol_sha256']})
    result.update(status='threshold_frozen', tau=tau,
                  calibration=tally(calibration, tau, True))
    save(out/'result.json', result)
    for part in ('id_test', 'ood'):
        rows = evaluate(part)
        result[part] = {'overall': tally(rows, tau, part == 'id_test'),
                        'domains': {d: tally([r for r in rows if r['domain'] == d], tau, part == 'id_test')
                                    for d in sorted(set(r['domain'] for r in rows))}}
        save(out/'result.json', result)
    result['J1'] = 'PASS' if result['id_test']['overall']['acceptance'] >= .95 else 'FAIL'
    admitted = [d for d, r in result['ood']['domains'].items() if r['domain_mean_accepted']]
    result['J2'] = 'FAIL' if admitted else 'PASS_ON_AVAILABLE_CELLS'
    result['suite_status'] = 'INCOMPLETE' if result['blocked'] else 'COMPLETE'
    result['status'] = 'complete'
    save(out/'result.json', result)
    print('DONE', result['J1'], result['J2'], result['suite_status'], flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['selftest', 'run'])
    ap.add_argument('--out', type=Path, default=Path('out_c/probe_j/run'))
    args = ap.parse_args()
    if args.mode == 'selftest':
        selftest()
    else:
        code = 1
        try:
            run(args.out)
            code = 0
        except Exception:
            traceback.print_exc()
        finally:
            if args.out.is_dir():
                (args.out/'EXIT').write_text(str(code)+'\n')
        sys.exit(code)
