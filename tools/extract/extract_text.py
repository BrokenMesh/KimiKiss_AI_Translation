#!/usr/bin/env python3
"""Extract every Japanese text constant from unpacked SCF scripts to JSON.

Usage: extract_text.py <script_dir> <out_dir>

<script_dir> is the output of `img.py unpack`. Writes one <name>.json per
script that has text. Each record:

  file          SCRIPT.IMG member, e.g. "MAO_TFO.scf"
  offset        byte offset of the constant's type tag inside the member
  id            "<member>:<path>", path = constant index, dotted into arrays
  speaker       K2_Script field name of the receiver that displays it (`:`)
  text          Shift-JIS text as Unicode; each ASCII control code in braces
  control_codes the braced tokens, in order
  byte_budget   original encoded length (informational; strings are
                length-prefixed and the archive is rebuilt, so not a limit)
  route         three-letter file prefix (MAO, ASU, ...) or "system"
  context_prev  previous record's text in the same member
  context_next  next record's text in the same member

Records stay in constant-pool order, which follows first use in the script.
"""
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scf  # noqa: E402

TEXT = 5
SYMBOL = 7
CODE = re.compile(
    r'V\d+|W\d+|N[mn]|Fe\d+m\d+|Fe\d+|Fm\d+|F\d+|E[coh]?|Ti\d+|Ts\d+|S[dp]?'
    r'|M[och]?|P\d+|As\d+|Br\d+t\d+|Bt\d+|B\d*|[bc]\d+|m\d+|R\d*|T[\d.]*|.')
ASCII_RUN = re.compile(r'[\x21-\x7e]+')
JAPANESE = re.compile(r'[^\x00-\x7f]')
ROUTE = re.compile(r'^([A-Z]{3})_')


def brace(text):
    """Wrap each ASCII control token in braces; return (text, tokens)."""
    tokens = []

    def repl(m):
        parts = CODE.findall(m.group())
        tokens.extend(parts)
        return ''.join('{' + p + '}' for p in parts)

    return ASCII_RUN.sub(repl, text), tokens


def unbrace(text):
    return re.sub(r'\{([^{}]*)\}', r'\1', text)


def constant_offsets(data, parsed):
    """Map constant path -> byte offset of its type tag."""
    r = scf.Reader(data)
    r.take(6)
    r.blob16()
    r.blob16()
    scf._fields(r)
    scf._fields(r)
    scf._methods(r)
    scf._methods(r)
    offsets = {}

    def walk(path):
        offsets[path] = r.pos
        t = r.u8()
        if t in scf.NO_PAYLOAD:
            return
        if t in scf.FIXED_PAYLOAD:
            r.take(scf.FIXED_PAYLOAD[t])
        elif t == scf.ARRAY:
            for k in range(r.u16()):
                walk(f'{path}.{k}')
        else:
            r.blob16()

    for i in range(r.u16()):
        walk(str(i))
    return offsets


def speakers(parsed, field_names):
    """Map top-level constant index -> set of speaker names.

    A displayed line compiles to <push receiver> <push const> <send ':' 1>:
      receiver  one byte, a K2_Script field id (0x0A = PLY, 0x0D = MAO, ...)
      push      0x50 <u8 index> or 0x51 <u16 LE index>
      send      0x30 0x01 <u8 index of the ':' selector constant>
    """
    colon = [i for i, (t, v) in enumerate(parsed['constants'])
             if t == SYMBOL and v == b':']
    out = {}
    if not colon or colon[0] > 0xFF:
        return out
    send = b'\x30\x01' + bytes([colon[0]])
    pattern = re.compile(rb'(.)(?:\x50(.)|\x51(..))' + re.escape(send), re.S)
    for _, _, code in parsed['methods'] + parsed['methods2']:
        for m in pattern.finditer(code):
            idx = m.group(2)[0] if m.group(2) is not None else struct.unpack('<H', m.group(3))[0]
            name = field_names.get(m.group(1)[0])
            if name:
                out.setdefault(idx, set()).add(name)
    return out


def iter_text(constants, prefix=''):
    for i, (t, v) in enumerate(constants):
        path = f'{prefix}{i}'
        if t == scf.ARRAY:
            yield from iter_text(v, path + '.')
        elif t == TEXT:
            yield path, v


def main():
    script_dir, out_dir = sys.argv[1:3]
    index = json.load(open(os.path.join(script_dir, 'index.json')))
    k2 = scf.parse(open(os.path.join(script_dir, 'K2_Script.scf'), 'rb').read())
    field_names = {fid: name.decode('ascii') for fid, name in k2['fields2']}
    os.makedirs(out_dir, exist_ok=True)
    total = 0
    for member in index['members']:
        name = member['name']
        data = open(os.path.join(script_dir, name + '.scf'), 'rb').read()
        parsed = scf.parse(data)
        offsets = constant_offsets(data, parsed)
        spk = speakers(parsed, field_names)
        m = ROUTE.match(name)
        route = m.group(1) if m else 'system'
        records = []
        for path, raw in iter_text(parsed['constants']):
            text = raw.decode('cp932')
            if not JAPANESE.search(text):
                continue
            if '{' in text or '}' in text:
                raise ValueError(f'{name}:{path} contains a brace; pick another escape')
            braced, tokens = brace(text)
            if unbrace(braced).encode('cp932') != raw:
                raise ValueError(f'{name}:{path} does not round-trip through cp932')
            top = int(path.split('.')[0])
            records.append({
                'file': name + '.scf', 'offset': offsets[path], 'id': f'{name}:{path}',
                'speaker': '/'.join(sorted(spk[top])) if top in spk and '.' not in path else None,
                'text': braced, 'control_codes': tokens, 'byte_budget': len(raw),
                'route': route,
            })
        for i, rec in enumerate(records):
            rec['context_prev'] = records[i - 1]['text'] if i > 0 else None
            rec['context_next'] = records[i + 1]['text'] if i + 1 < len(records) else None
        if records:
            with open(os.path.join(out_dir, name + '.json'), 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=1)
                f.write('\n')
            total += len(records)
    print(f'{total} records -> {out_dir}')


if __name__ == '__main__':
    main()
