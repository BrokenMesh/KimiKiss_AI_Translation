#!/usr/bin/env python3
"""Gate G3 check for the script pipeline.

Usage: test_text_roundtrip.py <orig SCRIPT.IMG>

1. Identity: unpack -> extract JSON -> reinsert -> pack must reproduce the
   input SCRIPT.IMG byte for byte.
2. Edit: lengthen one line; the rebuilt archive must decompress, parse, carry
   the new line, and leave every other member and constant unchanged.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(TOOLS, 'extract'))
import img  # noqa: E402
import lzss  # noqa: E402
import scf  # noqa: E402

sys.path.insert(0, os.path.join(TOOLS, 'reinsert'))
from en_text import encode_translation  # noqa: E402


def run(*args):
    subprocess.run([sys.executable, *args], check=True, stdout=subprocess.DEVNULL)


def pipeline(orig_img, work, edit=None):
    script, text, out = (os.path.join(work, d) for d in ('script', 'text', 'out'))
    run(os.path.join(TOOLS, 'extract', 'img.py'), 'unpack', orig_img, script)
    run(os.path.join(TOOLS, 'extract', 'extract_text.py'), script, text)
    if edit:
        edit(text)
    run(os.path.join(TOOLS, 'reinsert', 'reinsert_text.py'), script, text, out)
    rebuilt = os.path.join(work, 'SCRIPT.IMG')
    run(os.path.join(TOOLS, 'reinsert', 'img_pack.py'), out, rebuilt)
    return rebuilt


def members(img_bytes):
    data, _ = lzss.decompress(img_bytes)
    return {m['name']: data[m['offset']:m['offset'] + m['size']] for m in img.parse(data)}


def main():
    orig_img = sys.argv[1]
    orig = open(orig_img, 'rb').read()
    failures = 0

    with tempfile.TemporaryDirectory() as work:
        rebuilt = open(pipeline(orig_img, work), 'rb').read()
        if rebuilt == orig:
            print('PASS identity: rebuilt SCRIPT.IMG is byte-identical')
        else:
            print('FAIL identity: rebuilt SCRIPT.IMG differs')
            failures += 1

    target = 'MAO_TFO'
    new_text = ('{V0858}Oh, so that was what happened.{W80}{Ec}{W5}{F9}{Eo} '
                'Well then,{W30} I suppose it really can\'t be helped, can it?')

    def edit(text_dir):
        path = os.path.join(text_dir, target + '.json')
        recs = json.load(open(path, encoding='utf-8'))
        recs[6]['translation'] = new_text
        json.dump(recs, open(path, 'w', encoding='utf-8'), ensure_ascii=False)
        edit.record = recs[6]

    with tempfile.TemporaryDirectory() as work:
        rebuilt = open(pipeline(orig_img, work, edit), 'rb').read()
    before, after = members(orig), members(rebuilt)
    changed = [n for n in before if before[n] != after[n]]
    path = edit.record['id'].split(':', 1)[1]
    a, b = scf.parse(before[target]), scf.parse(after[target])
    idx = int(path)
    expect = encode_translation(new_text)
    others_same = all(a['constants'][i] == b['constants'][i]
                      for i in range(len(a['constants'])) if i != idx)
    if (changed == [target] and b['constants'][idx] == (5, expect) and others_same
            and a['methods'] == b['methods'] and a['methods2'] == b['methods2']):
        print(f'PASS edit: {edit.record["id"]} {edit.record["byte_budget"]} -> {len(expect)} bytes, '
              'nothing else changed')
    else:
        print(f'FAIL edit: changed members {changed}')
        failures += 1
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
