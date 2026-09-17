#!/usr/bin/env python3
"""Probe S: frozen factual recall experiment using the actual pipeline growth path."""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
import dataclasses
from datetime import datetime, timezone
import fcntl
import gc
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
import torch.nn.functional as F
import pipeline.train as training
from pipeline.config import Config, build_model

PROTOCOL = 'docs/plans/2026-09-17_probe-s-semantic-addressing.md'
SOURCES = [PROTOCOL, 'scripts/quinn/probe_s_semantic.py', 'bdh.py',
           *[f'pipeline/{name}.py' for name in ('train', 'data', 'config', 'run', '__init__')]]
TEMPLATES = {
    'T1': 'the {relation} of {entity} is ',
    'T2': 'for {entity}, {relation} has value ',
    'C1': '{entity} has {relation} equal to ',
    'P1': 'for {entity}, the value of {relation} is ',
    'P2': 'the value for {relation} of {entity} is ',
}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def hashes():
    return {p: sha(ROOT / p) for p in SOURCES}


def event(out, phase, **values):
    row = dict(time=datetime.now(timezone.utc).isoformat(), phase=phase, **values)
    with open(out / 'events.jsonl', 'a') as f:
        f.write(json.dumps(row, allow_nan=False) + '\n')
    print(json.dumps(row), flush=True)


def words(prefix, n):
    return [prefix + chr(97 + i // 26) + chr(97 + i % 26) for i in range(n)]


def corpus(toy=False):
    rng = random.Random(717 if toy else 17092026)
    ne, nr, na = (4, 2, 4) if toy else (32, 16, 64)
    entities, relations, answers = (words(p, n) for p, n in zip(
        ('t', 'u', 'w') if toy else ('m', 'r', 'v'), (ne, nr, na)))
    ep, rp = list(range(ne)), list(range(nr))
    rng.shuffle(ep)
    rng.shuffle(rp)
    facts = []
    for territory in ('A', 'B'):
        pairs = [(e, r) for i, e in enumerate(entities) for j, r in enumerate(relations)
                 if ('A' if (ep[i] + rp[j]) % 2 == 0 else 'B') == territory]
        pool = answers * (len(pairs) // na)
        rng.shuffle(pool)
        for (e, r), a in zip(pairs, pool):
            facts.append(dict(entity=e, relation=r, answer=a, territory=territory))
    queries = []
    for territory in ('A', 'B'):
        subset = [f for f in facts if f['territory'] == territory]
        for i, fact in enumerate(subset):
            for tid in TEMPLATES:
                if tid == 'C1' and i >= (2 if toy else 32):
                    continue
                split = 'train' if tid.startswith('T') else 'validation' if tid == 'C1' else 'test'
                query = '\n' + TEMPLATES[tid].format(**fact)
                queries.append(dict(fact, template=tid, split=split, query=query,
                                    text=query + fact['answer'] + '.'))
    manifest = dict(toy=toy, facts=facts, queries=queries)
    validate_manifest(manifest)
    return manifest


def validate_manifest(m):
    lookup = {(f['entity'], f['relation']): f for f in m['facts']}
    assert len(lookup) == len(m['facts'])
    sets = {s: {q['query'] for q in m['queries'] if q['split'] == s}
            for s in ('train', 'validation', 'test')}
    assert not sets['train'] & sets['test']
    assert not sets['train'] & sets['validation']
    assert not sets['test'] & sets['validation']
    for q in m['queries']:
        fact = lookup[q['entity'], q['relation']]
        assert fact['answer'] == q['answer'] and fact['territory'] == q['territory']
        assert len(q['query'].encode('ascii')) + 16 <= 128
        assert q['answer'] not in q['query'].replace(',', ' ').split()
        assert q['text'].encode('ascii') == q['query'].encode('ascii') + q['answer'].encode('ascii') + b'.'
    for key in ('entity', 'relation', 'answer'):
        assert Counter(f[key] for f in m['facts'] if f['territory'] == 'A') == Counter(
            f[key] for f in m['facts'] if f['territory'] == 'B')
    if not m['toy']:
        assert len(m['facts']) == 512
        assert {s: len(v) for s, v in sets.items()} == dict(train=1024, validation=64, test=1024)


def uint8(raw):
    return np.frombuffer(raw, dtype=np.uint8)


class ByteRouter:
    """Content-aware order-5 query likelihood; answer/label not accepted."""
    def __init__(self, manifest):
        self.counts = {r: defaultdict(Counter) for r in ('A', 'B')}
        for q in manifest['queries']:
            if q['split'] != 'train':
                continue
            raw = uint8(q['text'].encode('ascii')).tobytes()
            for i in range(1, len(raw)):
                self.counts[q['territory']][raw[max(0, i-4):i]][raw[i]] += 1

    def scores(self, query):
        if not isinstance(query, np.ndarray) or query.dtype != np.uint8 or query.ndim != 1:
            raise TypeError('Byte router requires a one-dimensional uint8 array')
        raw = query.tobytes()
        assert len(raw) > 1
        result = {}
        for r in ('A', 'B'):
            total = 0.
            for i in range(1, len(raw)):
                c = self.counts[r].get(raw[max(0, i-4):i], {})
                total -= math.log((c.get(raw[i], 0) + .1) / (sum(c.values()) + 25.6))
            result[r] = total / (len(raw)-1)
        return result


def select(scores):
    assert all(math.isfinite(v) for v in scores.values())
    return min(scores, key=lambda k: (scores[k], k))


class FactRows:
    """Fresh independent rows; padding ignored; no test material in pipeline."""
    def __init__(self, manifest, territory, seed, guard=lambda: None):
        self.rows = {s: [q['text'].encode('ascii') for q in manifest['queries']
                         if q['territory'] == territory and q['split'] == s]
                     for s in ('train', 'validation')}
        self.rows['val'] = self.rows.pop('validation')
        self.train = uint8(b''.join(self.rows['train']))
        self.val = uint8(b''.join(self.rows['val']))
        self.test = None
        self.generators = {s: torch.Generator().manual_seed(seed+n)
                           for s, n in (('train', 10), ('val', 20))}
        self.guard = guard

    def get_batch(self, split, block_size, batch_size, device):
        self.guard()
        rows = self.rows[split]
        ix = torch.randint(len(rows), (batch_size,), generator=self.generators[split])
        chosen = [rows[int(i)] for i in ix]
        size = max(map(len, chosen))-1
        assert size <= block_size
        x = torch.zeros((batch_size, size), dtype=torch.long)
        y = torch.full_like(x, -100)
        for i, raw in enumerate(chosen):
            a = torch.from_numpy(uint8(raw).astype(np.int64))
            x[i, :len(a)-1], y[i, :len(a)-1] = a[:-1], a[1:]
        return x.to(device), y.to(device)


def config(out, grown=False, smoke=False, tiny=False):
    steps = 2 if smoke else 2000 if grown else 4000
    return Config(dataset='probe_s', n_layer=2, n_embd=16 if tiny else 256,
        n_head=2 if tiny else 4, mlp_internal_dim_multiplier=4 if tiny else 128,
        grow_mult=(2 if tiny else 32) if grown else 0, dropout=0., block_size=128,
        batch_size=8, max_iters=steps, learning_rate=.001, min_lr=.0001,
        warmup_iters=100, lr_decay_iters=steps, weight_decay=.1, beta1=.9, beta2=.95,
        grad_clip=1., eval_interval=500, eval_iters=4, log_interval=1 if smoke else 25,
        compile=False, device='cuda', dtype='bfloat16',
        seed=(719 if grown else 718) if smoke else (17092028 if grown else 17092027),
        out_dir=str(out), run_name='grown' if grown else 'base',
        route_aware=grown, route_alpha=1., freeze_attn=True,
        carry_state=False, sequential_batches=False, k_sparse_ratio=0.)


def masks(model, n_old):
    n = model.encoder.shape[-1]
    b = torch.zeros(n, device=model.encoder.device)
    b[n_old:] = 1
    a = 1-b
    assert torch.equal(a+b, torch.ones_like(a)) and not torch.any(a*b)
    assert int(a.sum()) == n_old and int(b.sum()) == n-n_old
    return dict(A=a, B=b)


def old_parts(model, n_old):
    return dict(encoder=model.encoder[:, :, :n_old],
        encoder_v=model.encoder_v[:, :, :n_old],
        decoder=model.decoder.view(model.config.n_head, model.encoder.shape[-1], -1)[:, :n_old],
        embed=model.embed.weight, head=model.lm_head, freqs=model.attn.freqs[..., :n_old])


def train_phase(cfg, manifest, out, base_path=None):
    """Data adapter and assertion hooks only: updates remain pipeline-owned."""
    source = torch.load(base_path, map_location='cpu', weights_only=False) if base_path else None
    n_old = source['cfg']['mlp_internal_dim_multiplier'] * cfg.n_embd // cfg.n_head if source else None
    if base_path:
        cfg.init_from = str(base_path)
    audit = dict(steps=0, exact_checks=0, masked_gradient_checks=0, decay_observed=False)
    captured, snapshots, hooks = {}, {}, []
    original_loader, original_build, original_save = training.load_dataset, training.build_model, training.save_checkpoint
    original_adam = torch.optim.AdamW

    def guard():
        if not source or 'model' not in captured:
            return
        model = captured['model']
        current = old_parts(model, n_old)
        if not snapshots:
            sd = source['model_state']
            expected = dict(encoder=sd['encoder'], encoder_v=sd['encoder_v'],
                decoder=sd['decoder'].view(cfg.n_head, n_old, -1),
                embed=sd['embed.weight'], head=sd['lm_head'], freqs=sd['attn.freqs'])
            snapshots.update({k: v.to(cfg.device).clone() for k, v in expected.items()})
            assert not model.embed.weight.requires_grad and not model.lm_head.requires_grad
            masks(model, n_old)
            captured['tail'] = model.encoder[..., n_old:].detach().clone()
        for k, v in current.items():
            assert torch.equal(v, snapshots[k]), f'frozen tensor changed after restore: {k}'
        audit['exact_checks'] += 1

    def checked_build(c):
        model = original_build(c)
        captured['model'] = model
        def before(module, args, kwargs):
            state = kwargs.get('state', args[2] if len(args) > 2 else None)
            assert state is None, 'unrelated context leaked into forward'
        def after(module, args, output):
            if output[1] is not None:
                assert torch.isfinite(output[1]), 'nonfinite pipeline loss'
        hooks.extend([model.register_forward_pre_hook(before, with_kwargs=True),
                      model.register_forward_hook(after)])
        return model

    def checked_adam(*args, **kwargs):
        opt = original_adam(*args, **kwargs)
        def pre(optimizer, args, kwargs):
            if source:
                model = captured['model']
                for key in ('encoder', 'encoder_v'):
                    assert torch.count_nonzero(getattr(model, key).grad[..., :n_old]) == 0
                grad = model.decoder.grad.view(cfg.n_head, model.encoder.shape[-1], -1)
                assert torch.count_nonzero(grad[:, :n_old]) == 0
                audit['masked_gradient_checks'] += 1
        def post(optimizer, args, kwargs):
            audit['steps'] += 1
            if source:
                current = old_parts(captured['model'], n_old)
                audit['decay_observed'] |= not torch.equal(current['encoder'], snapshots['encoder'])
            if audit['steps'] % cfg.log_interval == 0:
                event(out, cfg.run_name + '_step', step=audit['steps'], budget=cfg.max_iters)
        hooks.extend([opt.register_step_pre_hook(pre), opt.register_step_post_hook(post)])
        return opt

    def checked_save(*args, **kwargs):
        guard()
        original_save(*args, **kwargs)

    data = FactRows(manifest, 'B' if source else 'A', cfg.seed, guard)
    try:
        training.load_dataset = lambda _: data
        training.build_model = checked_build
        training.save_checkpoint = checked_save
        torch.optim.AdamW = checked_adam
        event(out, cfg.run_name + '_start', config=dataclasses.asdict(cfg))
        training.train(cfg)
        guard()
        assert audit['steps'] == cfg.max_iters
        if source:
            assert audit['masked_gradient_checks'] == cfg.max_iters and audit['decay_observed']
            assert not torch.equal(captured['tail'], captured['model'].encoder[..., n_old:])
            audit['new_encoder_changed'] = True
        path = Path(training.checkpoint_path(cfg, 'last'))
        audit['checkpoint'] = str(path)
        audit['checkpoint_sha256'] = sha(path)
        dump(out / (cfg.run_name + '_checks.json'), audit)
        event(out, cfg.run_name + '_complete', **audit)
        return path
    finally:
        training.load_dataset, training.build_model, training.save_checkpoint = original_loader, original_build, original_save
        torch.optim.AdamW = original_adam
        for h in hooks:
            h.remove()
        captured.clear()
        snapshots.clear()
        gc.collect()
        torch.cuda.empty_cache()


def load(path):
    ck = torch.load(path, map_location='cpu', weights_only=False)
    model = build_model(Config(**ck['cfg'])).to('cuda').eval()
    model.load_state_dict(ck['model_state'])
    return model


@torch.inference_mode()
def logits(model, raw, mask, amp=True):
    assert len(raw) <= 128
    x = torch.tensor(list(raw), dtype=torch.long, device='cuda').unsqueeze(0)
    with torch.autocast('cuda', dtype=torch.bfloat16, enabled=amp):
        output = model(x, neuron_mask=mask)[0][0].float()
    assert torch.isfinite(output).all()
    return output


def greedy(predict, query):
    result = b''
    for _ in range(16):
        nxt = int(predict(query + result)[-1].argmax())
        result += bytes([nxt])
        if nxt == 46:
            break
    return result


def exact(pred, answer):
    return pred == answer.encode('ascii') + b'.'


def answer_nll(predict, query, answer):
    target = answer.encode('ascii') + b'.'
    all_logits = predict(query + target[:-1])
    scores = all_logits[len(query)-1:len(query)+len(target)-1]
    y = torch.tensor(list(target), device=scores.device)
    assert scores.shape[0] == len(target)
    return float(F.cross_entropy(scores, y, reduction='sum'))


def a2_scores(model, query, routes):
    # Query bytes only. No target answer or factual metadata crosses this API.
    result = {}
    for r, mask in routes.items():
        scores = logits(model, query, mask)
        y = torch.tensor(list(query[1:]), device=scores.device)
        result[r] = float(F.cross_entropy(scores[:-1], y))
    return result


def route_record(model, byte, row, routes):
    query = row['query'].encode('ascii')
    bs = byte.scores(uint8(query))
    a2 = a2_scores(model, query, routes)
    return dict(byte=select(bs), a2=select(a2), byte_nll=bs, query_nll=a2)


def synthetic_checks():
    query, target = b'\nquery: ', b'abc.'
    def perfect(raw):
        z = torch.full((len(raw), 256), -9., dtype=torch.float64)
        for i in range(len(raw)):
            j = i-(len(query)-1)
            z[i, target[j] if 0 <= j < len(target) else 32] = 9.
        return z
    assert greedy(perfect, query) == target
    assert exact(target, 'abc') and not exact(b'abd.', 'abc') and not exact(b'abc', 'abc')
    assert not exact(b'a.', 'abc') and not exact(b'abc..', 'abc')
    value = answer_nll(perfect, query, 'abc')
    expected = len(target) * math.log1p(255 * math.exp(-18))
    assert abs(value-expected) < 1e-6, (value, expected)
    def nonstop(raw):
        z = torch.zeros(len(raw), 256)
        z[:, 97] = 1
        return z
    assert greedy(nonstop, query) == b'a'*16
    raw = bytes(range(256))
    assert uint8(raw).tobytes() == raw
    byte = ByteRouter(corpus(True))
    try:
        byte.scores(np.array([1, 2], dtype=np.int64))
    except TypeError:
        pass
    else:
        raise AssertionError('int64 accepted by byte router')
    return dict(full_answer_exact=True, full_answer_nll=True, delimiter_cap=True, uint8=True)


def functional(base, grown, manifest, out):
    first = [q for q in manifest['queries'] if q['territory'] == 'A' and q['template'] == 'T1'][:4]
    bm = load(base)
    expected = [logits(bm, q['query'].encode('ascii'), None, False).cpu() for q in first]
    n_old = bm.encoder.shape[-1]
    del bm
    torch.cuda.empty_cache()
    gm = load(grown)
    route = masks(gm, n_old)['A']
    errors = []
    for q, old in zip(first, expected):
        current = logits(gm, q['query'].encode('ascii'), route, False).cpu()
        errors.append(float((current-old).abs().max()))
        torch.testing.assert_close(current, old, atol=1e-4, rtol=1e-4)
    result = dict(atol=1e-4, rtol=1e-4, max_abs=max(errors), prefixes=len(first))
    dump(out / 'functional_check.json', result)
    event(out, 'functional_check', **result)
    return gm, masks(gm, n_old)


def invariance(model, byte, queries, routes):
    for row in queries:
        original = route_record(model, byte, row, routes)
        mutated = dict(row, answer='zzz', territory='B' if row['territory'] == 'A' else 'A')
        changed = route_record(model, byte, mutated, routes)
        assert original == changed, 'answer/label changed routing'


def evaluate(model, manifest, out, routes=None, base=False):
    byte = ByteRouter(manifest)
    counters = defaultdict(Counter)
    rows = [q for q in manifest['queries'] if q['split'] in ('train', 'test')
            and (not base or q['territory'] == 'A')]
    path = out / ('base_queries.jsonl' if base else 'queries.jsonl')
    with open(path, 'x') as f:
        for i, row in enumerate(rows):
            raw = row['query'].encode('ascii')
            chosen = {} if base else route_record(model, byte, row, routes)
            if not base:
                # Substitution check for every scientific query before using its target.
                assert chosen == route_record(model, byte, dict(row, answer='zzz'), routes)
            candidates = {'full': None} if base else dict(routes, full=None)
            readings = {}
            for name, mask in candidates.items():
                predict = lambda raw, mask=mask: logits(model, raw, mask)
                pred = greedy(predict, raw)
                readings[name] = dict(prediction_hex=pred.hex(), prediction=pred.decode('ascii', 'backslashreplace'),
                    exact=exact(pred, row['answer']), answer_nll_sum=answer_nll(predict, raw, row['answer']))
            group = row['split'] + '_' + row['territory']
            c = counters[group]
            c['n'] += 1
            c['oracle'] += readings['full' if base else row['territory']]['exact']
            c['full'] += readings['full']['exact']
            if not base:
                for r in ('a2', 'byte'):
                    c[r+'_route'] += chosen[r] == row['territory']
                    c[r+'_exact'] += readings[chosen[r]]['exact']
            record = dict(row, routing=chosen, readings=readings)
            f.write(json.dumps(record, allow_nan=False) + '\n')
            f.flush()
            if (i+1) % 32 == 0:
                event(out, 'base_eval' if base else 'eval', completed=i+1, total=len(rows))
    summary = {k: dict(n=c['n'], **{m: c[m]/c['n'] for m in (
        ('oracle', 'full') if base else ('oracle', 'full', 'a2_route', 'byte_route', 'a2_exact', 'byte_exact'))})
        for k, c in counters.items()}
    dump(out / ('base_scores.json' if base else 'scores.json'), summary)
    return summary


def gates(scores, base_scores):
    acquired = all(scores['train_'+r]['oracle'] >= .8 for r in ('A', 'B'))
    transfer = all(scores['test_'+r]['oracle'] >= .8 for r in ('A', 'B'))
    pooled = {k: sum(scores['test_'+r][k] for r in ('A', 'B'))/2
              for k in ('a2_route', 'byte_route', 'a2_exact', 'byte_exact')}
    labels = []
    if base_scores['train_A']['oracle'] < .8:
        labels.append('base_acquisition_failure')
    elif scores['train_A']['oracle'] < .8:
        labels.append('retention_failure')
    if scores['train_B']['oracle'] < .8:
        labels.append('B_acquisition_failure')
    if acquired and not transfer:
        labels.append('paraphrase_transfer_failure_not_storage_failure')
    return dict(acquisition=acquired, P_S1=transfer, P_S2=pooled['a2_route'] >= .85,
        P_S4=scores['train_A']['oracle'] >= .75,
        S_PASS=acquired and transfer and pooled['a2_route'] >= .85,
        routing_falsifier=acquired and transfer and pooled['a2_route'] <= .60,
        surface_baseline_no_advantage=(pooled['byte_route'] >= pooled['a2_route'] or
                                      pooled['byte_exact'] >= pooled['a2_exact']),
        pooled=pooled, failure_labels=labels)


def freeze(out, manifest, configs):
    current = hashes()
    for rel in SOURCES:
        destination = out / 'frozen_source' / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / rel).read_bytes())
    deps = sorted(f'{d.metadata["Name"]}=={d.version}' for d in importlib.metadata.distributions())
    (out / 'dependencies.txt').write_text('\n'.join(deps)+'\n')
    dump(out / 'manifest.json', manifest)
    dump(out / 'configs.json', [dataclasses.asdict(c) for c in configs])
    for territory in ('A', 'B'):
        rows = [q['text'] for q in manifest['queries'] if q['split'] == 'train' and q['territory'] == territory]
        raw = b''.join(s.encode('ascii') for s in rows)
        uint8(raw).tofile(out / f'corpus_{territory}.uint8')
        assert (out / f'corpus_{territory}.uint8').read_bytes() == raw
    dump(out / 'freeze.json', dict(source_hashes=current,
        artifact_hashes={p.name: sha(p) for p in out.iterdir() if p.is_file()},
        git_head=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        git_status=subprocess.check_output(['git','status','--short'], cwd=ROOT, text=True),
        python=sys.version, torch=torch.__version__, cuda=torch.version.cuda,
        gpu=torch.cuda.get_device_name(), host=os.uname().nodename,
        time=datetime.now(timezone.utc).isoformat()))
    event(out, 'frozen', source_hashes=current)


def run(args):
    out = args.out.resolve()
    assert out.is_relative_to(ROOT / 'out_c' / 'probe_s'), 'output must stay in Probe S tree'
    out.mkdir(parents=True, exist_ok=False)
    (out / 'pid').write_text(str(os.getpid())+'\n')
    (out / 'status.txt').write_text('running\n')
    def expired(signum, frame):
        raise TimeoutError('bounded smoke exceeded 900 seconds')
    if args.smoke:
        signal.signal(signal.SIGALRM, expired)
        signal.alarm(900)
    lock = open(ROOT / 'out_c/followup_gpu.lock', 'a')
    rc = 1
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert torch.cuda.is_available()
        torch.set_num_threads(4)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        checks = synthetic_checks()
        if not args.smoke:
            assert args.smoke_from, 'successful smoke attestation required'
            attestation = json.loads((args.smoke_from / 'checks.json').read_text())
            assert attestation['passed'] and attestation['source_hashes'] == hashes()
            assert (args.smoke_from / 'exit_status.txt').read_text().strip() == '0'
        manifest = corpus(args.smoke)
        for tiny in ([True, False] if args.smoke else [False]):
            phase = out / ('tiny' if tiny else 'production_shape') if args.smoke else out
            phase.mkdir(exist_ok=True)
            base_cfg = config(phase, smoke=args.smoke, tiny=tiny)
            grow_cfg = config(phase, grown=True, smoke=args.smoke, tiny=tiny)
            grow_cfg.init_from = training.checkpoint_path(base_cfg, 'last')
            freeze(phase, manifest, [base_cfg, grow_cfg])
            bp = train_phase(base_cfg, manifest, phase)
            base_scores = None
            if not args.smoke:
                model = load(bp)
                base_scores = evaluate(model, manifest, phase, base=True)
                del model
                torch.cuda.empty_cache()
            gp = train_phase(grow_cfg, manifest, phase, bp)
            model, routes = functional(bp, gp, manifest, phase)
            if args.smoke:
                invariance(model, ByteRouter(manifest), manifest['queries'], routes)
                # Exercise full reader/output path on toy facts only.
                evaluate(model, manifest, phase, routes)
            else:
                scores = evaluate(model, manifest, phase, routes)
                dump(phase / 'gates.json', gates(scores, base_scores))
            del model
            gc.collect()
            torch.cuda.empty_cache()
        checks.update(passed=True, source_hashes=hashes(), smoke=args.smoke)
        dump(out / 'checks.json', checks)
        rc = 0
        event(out, 'complete', smoke=args.smoke)
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        traceback.print_exc()
        raise
    finally:
        signal.alarm(0)
        (out / 'exit_status.txt').write_text(str(rc)+'\n')
        (out / 'status.txt').write_text('complete\n' if rc == 0 else 'failed\n')
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--smoke-from', type=Path)
    run(parser.parse_args())
