#!/usr/bin/env python3
"""Translation batches: export scenes for a translator model, import its answers, prepare a build dir.

  batch.py export  <text_dir> <scene_or_file> <out.jsonl> [--context N] [--include-translated]
                   [--glossary PATH] [--limits PATH] [--trans DIR]
  batch.py import  <text_dir> <in.jsonl> [--force] [--normalize] [--dry-run] [--limits PATH] [--trans DIR]
  batch.py prepare <text_dir> <out_dir> [--limits PATH] [--trans DIR]
  batch.py sync    <text_dir> [--trans DIR] [--accept-src] [--limits PATH] [--scene SPEC]
  batch.py show    <text_dir> <scene> [--trans DIR] [--id ID] [--limits PATH]
  batch.py migrate <text_dir> [--trans DIR] [--limits PATH] [--force]

text_dir holds the Japanese (text/*.json, local, gitignored). The English lives in the translation
store, translation/en/<SCENE>.txt (committed, tools/translate/store.py, docs/translation-format.md);
--trans DIR points elsewhere ('none' = no store, use only 'translation' fields found in text_dir).

<scene_or_file> is a scene name (ASU_DAT_A), a file name, a path to a .json, a glob on names
(ASU_*, *) or a comma separated list. If <out.jsonl> is an existing directory or ends in '/', one
file per scene is written there.

export writes one JSON object per line (see docs/phase-5-pipeline.md for the fields). Japanese comes
from text_dir, existing English from the store; lines that already have a translation are left out
unless --include-translated. import reads lines that carry "id" and "translation" and writes the
translation into the store (creating the scene file when missing), never into text_dir. It validates
everything first and writes nothing if any line is bad. prepare merges text_dir and the store and
replaces every translation by the text to reinsert (dialogue word-wrapped, ConfirmDialog lines
wrapped), so that reinsert_text.py / build.sh can use the result directly. sync creates or updates
the store files (adds missing records, keeps translations and comments, reports orphans and stale
source hashes). show prints Japanese and English of a scene. migrate moves 'translation' fields
out of text_dir into the store (one-off, for text dirs from before the store existed).
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rules  # noqa: E402
import store  # noqa: E402


def scene_of(path):
    return os.path.splitext(os.path.basename(path))[0]


def trans_dir_of(a):
    """The store directory from --trans: default translation/en, 'none' = no store (None)."""
    t = getattr(a, 'trans', None)
    if t is None:
        return store.DEFAULT_DIR
    return None if t.lower() == 'none' else t


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
    tdir = trans_dir_of(a)
    merged = store.merge(a.text_dir, tdir)
    labels = rules.speaker_labels({r['id']: r for recs in merged.values() for r in recs})
    per_scene = a.out.endswith('/') or os.path.isdir(a.out)
    if per_scene:
        os.makedirs(a.out, exist_ok=True)
    total = skipped = 0
    out = None if per_scene else open(a.out, 'w', encoding='utf-8')
    try:
        for p in paths:
            scene = scene_of(p)
            recs = merged[scene]
            if per_scene:
                ext = '.txt' if a.format == 'text' else '.jsonl'
                out = open(os.path.join(a.out, scene + ext), 'w', encoding='utf-8')
            if a.format == 'text':
                n, sk = write_compact(out, scene, recs, limits, labels, terms, a.include_translated)
                total += n
                skipped += sk
                if per_scene:
                    out.close()
                continue
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


def compact_tag(lim):
    """Per-line limit tag for the compact view; '' for ordinary dialogue (the header states that rule)."""
    k = lim['kind']
    if k == 'dialogue':
        return ''
    if k == 'choice':
        return f'[choice x{lim.get("choices")}, one line of {lim["max_px"]} px each, separated by \uff0f]'
    if k == 'confirm':
        return f'[dialog box: up to {lim["lines"]} lines of {lim["max_px"]} px, \\n allowed]'
    note = (lim.get('note') or '').strip()
    tag = f'[{k}: one line, max {lim["max_px"]} px'
    return tag + (f'; {note}]' if note and k == 'single' else ']')


def write_compact(out, scene, recs, limits, labels, terms, include_translated):
    """One scene as a script listing: a header, then 'id speaker [tag] japanese' per line. Lines already
    translated are shown with their English on a '=' line (context, or for revision with
    --include-translated). Returns (exported, skipped)."""
    rows, hits, n, skipped = [], [], 0, 0
    for r in recs:
        lim = rules.limit_for(r, limits, labels)
        if lim['kind'] == 'skip':
            skipped += 1
            continue
        done = bool(r.get('translation'))
        tag = compact_tag(lim) if (not done or include_translated) else ''
        rows.append(f'{"" if (not done or include_translated) else "~"}{r["id"]} {r["speaker"] or "-"}'
                    f'{" " + tag if tag else ""} {r["text"]}')
        if done:
            rows.append('  = ' + r['translation'].replace('\\', '\\\\').replace('\n', '\\n'))
        if not done or include_translated:
            n += 1
        plain = rules.BRACED.sub('', r['text'])
        hits += [t for t in terms if t['ja'] in plain and t not in hits]
    route = recs[0]['route'] if recs else '?'
    out.write(f'# scene {scene}  route {route}  lines to translate: {n}\n')
    out.write('# format: <id> <speaker> [limit tag] <japanese>. "~" before an id = already translated, context only;\n'
              '# its English follows on a "  = " line. Untagged lines are dialogue: max 3 lines, 437 px per line\n'
              '# for a spoken line (plate in front), 552 px for SYS narration and "-" (no plate).\n')
    for t in hits:
        out.write(f'# glossary: {t["ja"]} = {t["en"]}' + (f'  ({t["note"]})' if t.get('note') else '') + '\n')
    out.write('\n'.join(rows) + '\n')
    return n, skipped


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
    tdir = trans_dir_of(a)
    if tdir is None:
        raise SystemExit('import needs a translation directory (--trans none is not allowed)')
    by_id = {}      # id -> (scene, merged record)
    for scene, recs in store.merge(a.text_dir, tdir).items():
        for r in recs:
            by_id[r['id']] = (scene, r)
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
        if '\r' in tr:
            errors.append(f'{where}: {rid}: carriage return in translation')
            continue
        jp = store.japanese_chars(tr)
        if jp:
            errors.append(f'{where}: {rid}: Japanese or full-width characters {"".join(jp)!r}; the store '
                          f'(committed) must stay free of Japanese')
            continue
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
    per_scene = {}
    for rid, tr in todo.items():
        per_scene.setdefault(by_id[rid][0], {})[rid] = tr
    changed = 0
    for scene, items in sorted(per_scene.items()):
        path = store.scene_path(tdir, scene)
        existing = store.load_scene(path) if os.path.exists(path) else None
        recs = rules.load_json(os.path.join(a.text_dir, scene + '.json'))
        f, _ = store.sync_scene(scene, recs, existing, limits)
        entries = f.by_id()
        for rid, tr in items.items():
            e = entries[rid]
            if e.tr != tr:
                e.tr = tr
                changed += 1
            # written against today's Japanese: not stale any more
            e.src = store.src_hash(next(r['text'] for r in recs if r['id'] == rid))
            e.comments = [c for c in e.comments if not c.startswith(store.STALE_MARK)]
        if not a.dry_run:
            store.write_scene(path, f)
    print(f'{changed} translation(s) {"would be " if a.dry_run else ""}written to {tdir} '
          f'({overwritten} overwritten, {skipped_null} null skipped, {len(rows)} lines read)')
    print('next: tools/qa/check_translation.py', a.text_dir)


def cmd_prepare(a):
    limits = rules.load_limits(a.limits)
    merged = store.merge(a.text_dir, trans_dir_of(a))
    labels = rules.speaker_labels({r['id']: r for recs in merged.values() for r in recs})
    os.makedirs(a.out_dir, exist_ok=True)
    n = changed = 0
    for scene, recs in merged.items():
        for r in recs:
            store.strip_internal(r)
            if r.get('translation'):
                lim = rules.limit_for(r, limits, labels)
                new = rules.prepare_text(r['translation'], lim)
                n += 1
                if new != r['translation']:
                    r['translation'] = new
                    changed += 1
        like = os.path.join(a.text_dir, scene + '.json')
        rules.write_records(os.path.join(a.out_dir, scene + '.json'), recs, like=like)
    print(f'{n} translations prepared, {changed} rewrapped -> {a.out_dir}')


def cmd_sync(a):
    tdir = trans_dir_of(a)
    if tdir is None:
        raise SystemExit('sync needs a translation directory (--trans none is not allowed)')
    rep = store.sync(a.text_dir, tdir, rules.load_limits(a.limits), a.accept_src, [a.scene] if a.scene else None)
    for rid in rep['stale']:
        print(f'WARN stale src: {rid} was translated against a different Japanese line; kept, marked "# STALE src"')
    for rid in rep['orphans']:
        print(f'WARN orphan: {rid} is no longer in the extracted text; kept (marked "# ORPHAN")')
    for rid in rep['dropped']:
        print(f'note: untranslated entry {rid} is no longer exported; removed')
    for sc in rep['orphan_files']:
        print(f'WARN orphan file: {sc}.txt has no scene in {a.text_dir}; left alone')
    print(f'{rep["scenes"]} scene(s): {rep["files_created"]} file(s) created, {rep["files_changed"]} changed; '
          f'{len(rep["added"])} record(s) added, {rep["kept"]} translation(s) kept, {len(rep["stale"])} stale, '
          f'{len(rep["accepted"])} src accepted, {len(rep["refreshed"])} untranslated hash(es) refreshed, '
          f'{len(rep["orphans"])} orphan(s) -> {tdir}')


def cmd_show(a):
    paths = rules.resolve_files(a.text_dir, [a.scene])
    merged = store.merge(a.text_dir, trans_dir_of(a), [a.scene])
    limits = rules.load_limits(a.limits)
    shown = 0
    for p in paths:
        for r in merged[scene_of(p)]:
            if a.id and r['id'] != a.id:
                continue
            if not store.exported(r, limits):
                if a.id:
                    print(f'{r["id"]}  not translated (translate=false in limits.json)')
                    shown += 1
                continue
            stale = r.get('_src') and r['_src'] != store.src_hash(r['text'])
            print(f'{r["id"]}  [{r["speaker"] or "-"}]' + ('  STALE: Japanese changed since this line' if stale else ''))
            print(f'  JA  {r["text"]}')
            print(f'  EN  {r.get("translation", "")}'.replace('\n', '\\n').rstrip())
            print()
            shown += 1
    if not shown:
        raise SystemExit(f'no record {a.id!r} in {a.scene}' if a.id else f'nothing to show for {a.scene}')


def cmd_migrate(a):
    """Move 'translation' fields out of text/*.json into the store, then strip them from the json."""
    tdir = trans_dir_of(a)
    if tdir is None:
        raise SystemExit('migrate needs a translation directory')
    limits = rules.load_limits(a.limits)
    moved = conflicts = 0
    for p in rules.resolve_files(a.text_dir):
        recs = rules.load_json(p)
        if not any('translation' in r for r in recs):
            continue
        scene = scene_of(p)
        path = store.scene_path(tdir, scene)
        existing = store.load_scene(path) if os.path.exists(path) else None
        f, _ = store.sync_scene(scene, recs, existing, limits)
        entries = f.by_id()
        keep = set()
        for r in recs:
            tr = r.get('translation')
            e = entries.get(r['id'])
            if not tr:
                continue
            if e is None:
                print(f'WARN {r["id"]}: translate=false, translation dropped', file=sys.stderr)
                continue
            if store.japanese_chars(tr):
                print(f'WARN {r["id"]}: translation contains Japanese; left in the json, not moved',
                      file=sys.stderr)
                keep.add(r['id'])
                continue
            if e.tr and e.tr != tr and not a.force:
                print(f'WARN {r["id"]}: store already has a different line; kept (use --force to overwrite)',
                      file=sys.stderr)
                conflicts += 1
                keep.add(r['id'])
                continue
            e.tr = tr
            e.src = store.src_hash(r['text'])
            moved += 1
        store.write_scene(path, f)
        for r in recs:
            if r['id'] not in keep:
                r.pop('translation', None)
        rules.write_records(p, recs, like=p)
    print(f'{moved} translation(s) moved from {a.text_dir} into {tdir} ({conflicts} conflict(s)); '
          f'translation fields removed from the json files (except conflicts and lines with Japanese)')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    def common(p):
        p.add_argument('--trans', help='translation store directory (default translation/en; "none" = no store)')
        p.add_argument('--limits')

    e = sub.add_parser('export')
    e.add_argument('text_dir')
    e.add_argument('scene')
    e.add_argument('out')
    e.add_argument('--context', type=int, default=3, help='neighbours before and after (default 3)')
    e.add_argument('--include-translated', action='store_true')
    e.add_argument('--format', choices=('jsonl', 'text'), default='jsonl',
                   help='jsonl: one object per line with context (default); text: compact script listing per scene')
    e.add_argument('--glossary')
    common(e)
    i = sub.add_parser('import')
    i.add_argument('text_dir')
    i.add_argument('jsonl')
    i.add_argument('--force', action='store_true', help='overwrite existing translations')
    i.add_argument('--normalize', action='store_true', help='replace curly quotes, ellipsis, dashes by ASCII')
    i.add_argument('--dry-run', action='store_true')
    common(i)
    pr = sub.add_parser('prepare')
    pr.add_argument('text_dir')
    pr.add_argument('out_dir')
    common(pr)
    sy = sub.add_parser('sync')
    sy.add_argument('text_dir')
    sy.add_argument('--accept-src', action='store_true',
                    help='record the current Japanese hash for stale lines (after you checked them)')
    sy.add_argument('--scene', help='only this scene (name, glob or comma list)')
    common(sy)
    sh = sub.add_parser('show')
    sh.add_argument('text_dir')
    sh.add_argument('scene')
    sh.add_argument('--id')
    common(sh)
    mg = sub.add_parser('migrate')
    mg.add_argument('text_dir')
    mg.add_argument('--force', action='store_true', help='overwrite different lines already in the store')
    common(mg)
    a = ap.parse_args()
    {'export': cmd_export, 'import': cmd_import, 'prepare': cmd_prepare, 'sync': cmd_sync,
     'show': cmd_show, 'migrate': cmd_migrate}[a.cmd](a)


if __name__ == '__main__':
    main()
