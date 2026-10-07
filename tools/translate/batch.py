#!/usr/bin/env python3
"""Translation batches: export scenes for a translator model, import its answers, prepare a build dir.

  batch.py export  <text_dir> <scene_or_file> <out.jsonl> [--context N] [--include-translated]
                   [--glossary PATH] [--limits PATH]
  batch.py import  <text_dir> <in.jsonl> [--force] [--normalize] [--dry-run] [--limits PATH]
  batch.py prepare <text_dir> <out_dir> [--limits PATH]

<scene_or_file> is a scene name (ASU_DAT_A), a file name, a path to a .json, a glob on names
(ASU_*, *) or a comma separated list. If <out.jsonl> is an existing directory or ends in '/', one
file per scene is written there.

export writes one JSON object per line (see docs/phase-5-pipeline.md for the fields). Lines that
already have a translation are left out unless --include-translated. import reads lines that carry
"id" and "translation" and writes the translation into text/*.json. It validates everything first
and writes nothing if any line is bad. prepare copies a text dir and replaces every translation by
the text to reinsert (dialogue word-wrapped, ConfirmDialog lines wrapped), so that
reinsert_text.py / build.sh can use the result directly.
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rules  # noqa: E402


def scene_of(path):
    return os.path.splitext(os.path.basename(path))[0]


def neighbours(recs, i, n):
    def brief(r):
        d = {'id': r['id'], 'speaker': r['speaker'], 'ja': r['text']}
        if r.get('translation'):
            d['en'] = r['translation']
        return d
    return ([brief(r) for r in recs[max(0, i - n):i]], [brief(r) for r in recs[i + 1:i + 1 + n]])


def limit_view(lim):
    keys = ('kind', 'display', 'lines', 'first_px', 'cont_px', 'max_px', 'choices', 'label_px', 'note')
    out = {k: lim[k] for k in keys if lim.get(k) is not None}
    # px numbers are for the width table at scale 1.0 except ConfirmDialog (scale 0.75): the numbers
    # below are already in the units the width table uses, nothing to convert by hand.
    return out


def cmd_export(a):
    paths = rules.resolve_files(a.text_dir, [a.scene])
    limits = rules.load_limits(a.limits)
    terms = rules.load_glossary(a.glossary)
    if not terms:
        print('note: no glossary loaded (missing or empty); glossary hits left out', file=sys.stderr)
    labels = rules.speaker_labels(rules.index_dir(a.text_dir))
    per_scene = a.out.endswith('/') or os.path.isdir(a.out)
    if per_scene:
        os.makedirs(a.out, exist_ok=True)
    total = skipped = 0
    out = None if per_scene else open(a.out, 'w', encoding='utf-8')
    try:
        for p in paths:
            recs = rules.load_json(p)
            scene = scene_of(p)
            if per_scene:
                out = open(os.path.join(a.out, scene + '.jsonl'), 'w', encoding='utf-8')
            for i, r in enumerate(recs):
                lim = rules.limit_for(r, limits, labels)
                if lim['kind'] == 'skip' or (r.get('translation') and not a.include_translated):
                    skipped += 1
                    continue
                prev, nxt = neighbours(recs, i, a.context)
                row = {
                    'id': r['id'], 'scene': scene, 'route': r['route'], 'speaker': r['speaker'],
                    'ja': r['text'], 'control_codes': r['control_codes'],
                    'prev': prev, 'next': nxt, 'limit': limit_view(lim),
                    'glossary': [{'ja': t['ja'], 'en': t['en'], 'note': t['note']}
                                 for t in terms if t['ja'] in rules.BRACED.sub('', r['text'])],
                    'translation': r.get('translation'),
                }
                out.write(json.dumps(row, ensure_ascii=False) + '\n')
                total += 1
            if per_scene:
                out.close()
    finally:
        if out and not per_scene:
            out.close()
    print(f'{total} lines exported from {len(paths)} file(s), {skipped} skipped '
          f'(translate=false or already translated) -> {a.out}')


def read_jsonl(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            s = line.strip()
            if not s or s.startswith('```'):
                continue
            try:
                row = json.loads(s)
            except ValueError as e:
                raise SystemExit(f'{path}:{n}: not JSON ({e})')
            if not isinstance(row, dict):
                raise SystemExit(f'{path}:{n}: expected an object')
            rows.append((n, row))
    return rows


def cmd_import(a):
    rows = read_jsonl(a.jsonl)
    limits = rules.load_limits(a.limits)
    files = {}
    by_id = {}
    for p in rules.resolve_files(a.text_dir):
        recs = rules.load_json(p)
        files[p] = recs
        for r in recs:
            by_id[r['id']] = (p, r)
    errors, todo, seen = [], {}, set()
    skipped_null = overwritten = 0
    for n, row in rows:
        rid = row.get('id')
        tr = row.get('translation', row.get('en'))
        where = f'{a.jsonl}:{n}'
        if rid not in by_id:
            errors.append(f'{where}: unknown id {rid!r}')
            continue
        if rid in seen:
            errors.append(f'{where}: duplicate id {rid}')
            continue
        seen.add(rid)
        if tr is None:
            skipped_null += 1
            continue
        if not isinstance(tr, str) or not tr.strip():
            errors.append(f'{where}: {rid}: empty or non-string translation')
            continue
        if a.normalize:
            tr = rules.normalize_typography(tr)
        lim = limits.get(rid)
        if lim is not None and not lim.get('translate'):
            errors.append(f'{where}: {rid}: translate=false in limits.json ({lim["display"]}); not imported')
            continue
        rec = by_id[rid][1]
        if rec.get('translation') and rec['translation'] != tr:
            if not a.force:
                errors.append(f'{where}: {rid}: already has a translation (use --force to overwrite)')
                continue
            overwritten += 1
        todo[rid] = tr
    if errors:
        for e in errors[:50]:
            print('ERROR', e, file=sys.stderr)
        if len(errors) > 50:
            print(f'... and {len(errors) - 50} more', file=sys.stderr)
        raise SystemExit(f'import refused: {len(errors)} problem(s), nothing written')
    changed = 0
    for p, recs in files.items():
        dirty = False
        for r in recs:
            if r['id'] in todo and r.get('translation') != todo[r['id']]:
                r['translation'] = todo[r['id']]
                dirty = True
                changed += 1
        if dirty and not a.dry_run:
            rules.write_records(p, recs, like=p)
    print(f'{changed} translation(s) {"would be " if a.dry_run else ""}written '
          f'({overwritten} overwritten, {skipped_null} null skipped, {len(rows)} lines read)')
    print('next: tools/qa/check_translation.py', a.text_dir)


def cmd_prepare(a):
    limits = rules.load_limits(a.limits)
    index = rules.index_dir(a.text_dir)
    labels = rules.speaker_labels(index)
    os.makedirs(a.out_dir, exist_ok=True)
    n = changed = 0
    for p in rules.resolve_files(a.text_dir):
        recs = rules.load_json(p)
        for r in recs:
            if r.get('translation'):
                lim = rules.limit_for(r, limits, labels)
                new = rules.prepare_text(r['translation'], lim)
                n += 1
                if new != r['translation']:
                    r['translation'] = new
                    changed += 1
        rules.write_records(os.path.join(a.out_dir, os.path.basename(p)), recs, like=p)
    print(f'{n} translations prepared, {changed} rewrapped -> {a.out_dir}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export')
    e.add_argument('text_dir')
    e.add_argument('scene')
    e.add_argument('out')
    e.add_argument('--context', type=int, default=3, help='neighbours before and after (default 3)')
    e.add_argument('--include-translated', action='store_true')
    e.add_argument('--glossary')
    e.add_argument('--limits')
    i = sub.add_parser('import')
    i.add_argument('text_dir')
    i.add_argument('jsonl')
    i.add_argument('--force', action='store_true', help='overwrite existing translations')
    i.add_argument('--normalize', action='store_true', help='replace curly quotes, ellipsis, dashes by ASCII')
    i.add_argument('--dry-run', action='store_true')
    i.add_argument('--limits')
    pr = sub.add_parser('prepare')
    pr.add_argument('text_dir')
    pr.add_argument('out_dir')
    pr.add_argument('--limits')
    a = ap.parse_args()
    {'export': cmd_export, 'import': cmd_import, 'prepare': cmd_prepare}[a.cmd](a)


if __name__ == '__main__':
    main()
