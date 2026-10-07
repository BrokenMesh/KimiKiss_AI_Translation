#!/usr/bin/env python3
"""Translate scenes through the Anthropic API instead of agent sessions (D-026).

One request per part of a scene (at most --part records to translate, with the lines already
translated as "~" context). The fixed prefix (translator brief, glossary rules, the reviewed pilot,
the route notes) is sent as a cached system prompt. Answers are imported with batch.py import
--normalize; lines that then FAIL check_translation.py are sent once more with the error.

  api_translate.py plan   [--scenes SPEC] [--part N]            # parts and a cost estimate, no calls
  api_translate.py run    [--scenes SPEC] [--part N] [--batch] [--budget USD] [--effort E]
  api_translate.py repair [--scenes SPEC]                       # resend FAIL lines with the error

The API key comes from $ANTHROPIC_API_KEY or the file named by $ANTHROPIC_API_KEY_FILE.
Work files (exports, requests, answers, usage) go to build/api/. Nothing is committed by this tool.
"""
import argparse, glob, json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, 'build', 'api')
MODEL = 'claude-sonnet-5-5'
PRICE = {'in': 2.0, 'out': 10.0, 'cache_read': 0.20, 'cache_write': 2.50}   # USD per MTok, standard
REC = re.compile(r'^(~?)([A-Za-z0-9_]+:\d+(?:\.\d+)?) ')

SYSTEM_TAIL = """
# Your task now

You get one part of one scene in the batch format described above (lines starting with "~" are
context, already translated; lines under "# context before:" are the Japanese just before this part,
for context only). Translate every record without "~". Answer with JSON Lines only: one object
{"id": ..., "translation": ...} per line, one line per record, nothing before or after, no code
fences. Keep every control code exactly. Follow the brief, the glossary rules, the tone table and the
route notes; the pilot below shows the target quality and voice.
"""


def sh(*args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)


def api_key():
    k = os.environ.get('ANTHROPIC_API_KEY')
    if not k and os.environ.get('ANTHROPIC_API_KEY_FILE'):
        k = open(os.environ['ANTHROPIC_API_KEY_FILE']).read().strip()
    if not k:
        sys.exit('no API key: set ANTHROPIC_API_KEY or ANTHROPIC_API_KEY_FILE')
    return k


def scenes_todo(spec):
    out = []
    names = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, 'text', '*.json')))
    pats = spec.split(',') if spec else ['*']
    import fnmatch
    for n in names:
        if any(fnmatch.fnmatch(n, p) for p in pats):
            out.append(n)
    return out


def export(scene):
    os.makedirs(os.path.join(WORK, 'export'), exist_ok=True)
    path = os.path.join(WORK, 'export', scene + '.txt')
    r = sh('tools/translate/batch.py', 'export', 'text', scene, path, '--format', 'text')
    if r.returncode:
        sys.exit(r.stderr)
    return open(path, encoding='utf-8').read().split('\n')


def split_parts(lines, part):
    """-> list of (text, ids_to_translate). Header and glossary lines go into every part."""
    head = [l for l in lines if l.startswith('#')]
    recs, cur = [], None
    for l in lines:
        if l.startswith('#') or not l.strip():
            continue
        m = REC.match(l)
        if m:
            cur = [m.group(2), m.group(1) == '~', [l]]
            recs.append(cur)
        elif cur is not None:
            cur[2].append(l)
    parts, i = [], 0
    while i < len(recs):
        j, n = i, 0
        while j < len(recs) and (n < part or recs[j][1]):
            n += not recs[j][1]
            j += 1
        chunk = recs[i:j]
        ids = [r[0] for r in chunk if not r[1]]
        if ids:
            before = recs[max(0, i - 6):i]
            body = head[:]
            if before:
                body.append('# context before:')
                body += ['#   ' + x for r in before for x in r[2]]
            body += [x for r in chunk for x in r[2]]
            parts.append(('\n'.join(body), ids))
        i = j
    return parts


def route_of(scene):
    return scene.split('_')[0] if '_' in scene else 'SYS'


def system_prompt(route):
    brief = open(os.path.join(ROOT, 'tools/translate/TRANSLATOR.md'), encoding='utf-8').read()
    gl = open(os.path.join(ROOT, 'docs/glossary.md'), encoding='utf-8').read().split('\n')[:218]
    pilot = sh('tools/translate/batch.py', 'show', 'text', 'PLY_PRO').stdout
    fixed = [{'type': 'text', 'text': brief + '\n\n# Glossary rules (docs/glossary.md, sections 0-2)\n\n'
              + '\n'.join(gl) + '\n\n# Pilot scene PLY_PRO, reviewed (Japanese and English)\n\n' + pilot
              + SYSTEM_TAIL, 'cache_control': {'type': 'ephemeral', 'ttl': '1h'}}]
    notes = os.path.join(ROOT, 'docs/route-notes', route + '.md')
    if os.path.exists(notes):
        fixed.append({'type': 'text', 'text': '# Route notes (keep these decisions)\n\n'
                      + open(notes, encoding='utf-8').read(), 'cache_control': {'type': 'ephemeral', 'ttl': '1h'}})
    return fixed


def request_params(scene, text, effort, max_tokens):
    return {'model': MODEL, 'max_tokens': max_tokens, 'system': system_prompt(route_of(scene)),
            'output_config': {'effort': effort},
            'messages': [{'role': 'user', 'content': text}]}


def cost(u, batch=False):
    f = 0.5 if batch else 1.0
    return f * (u.get('input_tokens', 0) * PRICE['in'] + u.get('output_tokens', 0) * PRICE['out']
                + u.get('cache_read_input_tokens', 0) * PRICE['cache_read']
                + u.get('cache_creation_input_tokens', 0) * PRICE['cache_write']) / 1e6


def parse_answers(text, ids):
    out, want = [], set(ids)
    for l in text.split('\n'):
        l = l.strip()
        if not l.startswith('{'):
            continue
        try:
            o = json.loads(l)
        except json.JSONDecodeError:
            continue
        if o.get('id') in want and isinstance(o.get('translation'), str):
            out.append({'id': o['id'], 'translation': o['translation']})
    return out


def import_answers(name, rows, force=False):
    os.makedirs(os.path.join(WORK, 'answers'), exist_ok=True)
    path = os.path.join(WORK, 'answers', name + '.jsonl')
    with open(path, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    args = ['tools/translate/batch.py', 'import', 'text', path, '--normalize'] + (['--force'] if force else [])
    r = sh(*args)
    if r.returncode:   # one bad line refuses the file: import line by line
        ok = 0
        for row in rows:
            p1 = path + '.one'
            open(p1, 'w', encoding='utf-8').write(json.dumps(row, ensure_ascii=False) + '\n')
            ok += sh(*args[:3], p1, *args[4:]).returncode == 0
        return ok
    return len(rows)


def log_usage(entry):
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, 'usage.jsonl'), 'a') as f:
        f.write(json.dumps(entry) + '\n')


def spent():
    p = os.path.join(WORK, 'usage.jsonl')
    return sum(json.loads(l)['usd'] for l in open(p)) if os.path.exists(p) else 0.0


def all_parts(a):
    jobs = []
    for sc in scenes_todo(a.scenes):
        if not os.path.exists(os.path.join(ROOT, 'text', sc + '.json')):
            continue
        for k, (text, ids) in enumerate(split_parts(export(sc), a.part)):
            jobs.append((f'{sc}.p{k + 1}', sc, text, ids))
    return jobs


def cmd_plan(a):
    jobs = all_parts(a)
    n = sum(len(j[3]) for j in jobs)
    chars = sum(len(j[2]) for j in jobs)
    # rough: 45 output tokens per line + as much again for reasoning; input ~1 token per 1.3 chars
    est_out = n * 90
    est = (est_out * PRICE['out'] + chars / 1.3 * PRICE['in'] + len(jobs) * 30000 * PRICE['cache_read']) / 1e6
    print(f'{len(jobs)} requests, {n} lines to translate, ~{est:.2f} USD standard, ~{est / 2:.2f} USD batch (rough)')


def cmd_run(a):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key())
    jobs = all_parts(a)
    done_p = os.path.join(WORK, 'done.txt')
    done = set(open(done_p).read().split()) if os.path.exists(done_p) else set()
    jobs = [j for j in jobs if j[0] not in done]
    print(f'{len(jobs)} requests to send; spent so far {spent():.2f} USD', flush=True)
    if a.batch:
        reqs = [{'custom_id': j[0].replace(':', '_').replace('.', '-'), 'params': request_params(j[1], j[2], a.effort, a.max_tokens)} for j in jobs]
        bymap = {r['custom_id']: j for r, j in zip(reqs, jobs)}
        if a.batch_id:   # collect an earlier batch; its requests must match the current parts
            b = client.messages.batches.retrieve(a.batch_id)
        else:
            b = client.messages.batches.create(requests=reqs)
            open(os.path.join(WORK, 'batch_id.txt'), 'w').write(b.id)
        print('batch', b.id, flush=True)
        while client.messages.batches.retrieve(b.id).processing_status != 'ended':
            time.sleep(60)
        for res in client.messages.batches.results(b.id):
            j = bymap.get(res.custom_id)
            if j is None:
                continue
            if res.result.type != 'succeeded':
                print('FAILED', j[0], res.result.type, flush=True)
                continue
            finish(j, res.result.message, True, done_p)
        return
    for j in jobs:
        if spent() >= a.budget:
            print(f'budget {a.budget} USD reached, stopping', flush=True)
            break
        with client.messages.stream(**request_params(j[1], j[2], a.effort, a.max_tokens)) as s:
            msg = s.get_final_message()
        finish(j, msg, False, done_p)


def finish(j, msg, batch, done_p, force=False):
    name, sc, _, ids = j
    text = ''.join(b.text for b in msg.content if b.type == 'text')
    rows = parse_answers(text, ids)
    n = import_answers(name, rows, force)
    u = msg.usage.model_dump()
    usd = cost(u, batch)
    log_usage({'part': name, 'lines': len(ids), 'answered': len(rows), 'imported': n, 'usd': usd,
               'stop': msg.stop_reason, **{k: u.get(k) for k in ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')}})
    if n == len(ids):
        with open(done_p, 'a') as f:
            f.write(name + '\n')
    print(f'{name}: {n}/{len(ids)} imported, {usd:.3f} USD, total {spent():.2f} USD, stop={msg.stop_reason}', flush=True)


def cmd_repair(a):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key())
    files = scenes_todo(a.scenes)
    out = os.path.join(WORK, 'check.json')
    sh('tools/qa/check_translation.py', 'text', '--files', *files, '--json', out)
    fails = [r for r in json.load(open(out))['results'] if r.get('status') == 'FAIL']
    print(len(fails), 'FAIL lines', flush=True)
    by_scene = {}
    for r in fails:
        by_scene.setdefault(r['id'].split(':')[0], []).append(r)
    for sc, rs in by_scene.items():
        recs = {x['id']: x for x in json.load(open(os.path.join(ROOT, 'text', sc + '.json')))}
        body = ['These translations failed the checker. Give a corrected translation for each, same JSONL format.']
        for r in rs:
            body.append(json.dumps({'id': r['id'], 'japanese': recs[r['id']]['text'], 'current': r.get('en'),
                                    'problems': [x['msg'] for x in r['reasons'] if x['level'] == 'FAIL']}, ensure_ascii=False))
        with client.messages.stream(**request_params(sc, '\n'.join(body), a.effort, a.max_tokens)) as s:
            msg = s.get_final_message()
        finish((f'{sc}.repair', sc, '', [r['id'] for r in rs]), msg, False, os.path.join(WORK, 'repair_done.txt'), force=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('cmd', choices=['plan', 'run', 'repair'])
    p.add_argument('--scenes', default='')
    p.add_argument('--part', type=int, default=150)
    p.add_argument('--batch', action='store_true')
    p.add_argument('--budget', type=float, default=20.0)
    p.add_argument('--effort', default='medium')
    p.add_argument('--max-tokens', type=int, default=32000)
    p.add_argument('--batch-id', default='', help='run --batch: collect this batch instead of creating one')
    a = p.parse_args()
    {'plan': cmd_plan, 'run': cmd_run, 'repair': cmd_repair}[a.cmd](a)


if __name__ == '__main__':
    main()
