#!/usr/bin/env python3
"""Write text records back into SCF scripts.

Usage: reinsert_text.py <orig_script_dir> <json_dir> <out_dir>

For every <name>.json in <json_dir>, loads <orig_script_dir>/<name>.scf,
replaces each record's constant with its "translation" (or "text" when no
translation is present), and writes <out_dir>/<name>.scf. Members without a
JSON file are copied unchanged. index.json is copied so img_pack.py can
rebuild the archive in the original order.

Text is encoded as cp932 with braces stripped. The English encoding is
decided in Phase 3 and will replace encode_text().
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'extract'))
import scf  # noqa: E402
from extract_text import unbrace  # noqa: E402


def encode_text(text):
    return unbrace(text).encode('cp932')


def set_constant(constants, path, payload):
    parts = [int(p) for p in path.split('.')]
    for p in parts[:-1]:
        constants = constants[p][1]
    t, _ = constants[parts[-1]]
    if t != 5:
        raise ValueError(f'constant {path} is type {t}, not text')
    constants[parts[-1]] = (t, payload)


def main():
    orig_dir, json_dir, out_dir = sys.argv[1:4]
    os.makedirs(out_dir, exist_ok=True)
    index = json.load(open(os.path.join(orig_dir, 'index.json')))
    shutil.copy(os.path.join(orig_dir, 'index.json'), os.path.join(out_dir, 'index.json'))
    changed = 0
    for member in index['members']:
        name = member['name']
        src = os.path.join(orig_dir, name + '.scf')
        dst = os.path.join(out_dir, name + '.scf')
        jpath = os.path.join(json_dir, name + '.json')
        if not os.path.exists(jpath):
            shutil.copy(src, dst)
            continue
        parsed = scf.parse(open(src, 'rb').read())
        for rec in json.load(open(jpath, encoding='utf-8')):
            text = rec.get('translation') or rec['text']
            set_constant(parsed['constants'], rec['id'].split(':', 1)[1], encode_text(text))
            changed += 1
        with open(dst, 'wb') as f:
            f.write(scf.serialize(parsed))
    print(f'{changed} records written -> {out_dir}')


if __name__ == '__main__':
    main()
