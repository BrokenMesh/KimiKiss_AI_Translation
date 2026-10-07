#!/usr/bin/env python3
"""Disassemble SCF method bytecode.

Usage: scfdis.py <file.scf> [method-name ...]

Opcode set decoded from the VM interpreter in SLPS_258.50 (FUN_00115458);
see docs/formats/scf.md. `at`/`at_put` (0x64/0x65) are
inferred from usage. Values on the stack are tagged words: small
integers are (n << 1) | 1, nil = 0, false = 2, true = 4.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import scf  # noqa: E402

BINOPS = ['+', '-', '*', '/', '%', '&', '|', '^', '=', '>', '<', '>=', '<=', '<>', '-U', '~U']

# opcode: (mnemonic, operand spec). Specs: b = u8, s = s8, h = u16, j = s8 jump,
# J = s16 jump, c = u8 constant index, C = u16 constant index.
OPS = {
    0x00: ('pad', ''), 0x01: ('op01', 'b'), 0x02: ('return_self', ''), 0x03: ('return_top', ''),
    0x04: ('dup', ''), 0x05: ('pop', ''), 0x06: ('not_identical', ''), 0x07: ('identical', ''),
    0x08: ('push_classvar', 'cb'), 0x09: ('push_classvar', 'Cb'),
    0x0A: ('store_classvar', 'cb'), 0x0B: ('store_classvar', 'Cb'),
    0x0C: ('and', ''), 0x0D: ('or', ''),
    0x20: ('push_ivar', 'b'), 0x21: ('store_ivar', 'b'), 0x22: ('push_temp', 'b'), 0x23: ('store_temp', 'b'),
    0x24: ('push_int', 's'), 0x25: ('push_nil', ''), 0x26: ('push_self', ''),
    0x28: ('push_true', ''), 0x29: ('push_false', ''), 0x2A: ('push_exception', ''), 0x2B: ('not', ''),
    0x30: ('send', 'bc'), 0x31: ('send_super', 'bc'), 0x32: ('send', 'bC'), 0x33: ('send_super', 'bC'),
    0x34: ('primitive', 'b'),
    0x40: ('jump', 'j'), 0x41: ('jump', 'J'), 0x44: ('jump_if_false', 'j'), 0x45: ('jump_if_false', 'J'),
    0x50: ('push_const', 'c'), 0x51: ('push_const', 'C'),
    0x60: ('error60', ''), 0x61: ('error61', ''), 0x62: ('error62', ''), 0x63: ('error63', ''),
    0x64: ('at', ''), 0x65: ('at_put', ''),
    0x68: ('clear_exception', ''), 0x69: ('try', 'J'), 0x6A: ('end_try', ''), 0x6B: ('throw', ''),
    0x6C: ('push_nils', 'b'), 0x6D: ('line', 'h'),
}
for i, name in enumerate(BINOPS):
    OPS[0x10 + i] = (f'op {name}', '')


def const_repr(c):
    t, p = c
    if t == 1:
        return str(struct.unpack('<i', p)[0])
    if t == 3:
        return f'{struct.unpack("<f", p)[0]:g}f'
    if t == 5:
        return '"' + p.decode('cp932', 'replace') + '"'
    if t in (6, 7):
        return ('#' if t == 7 else '') + p.decode('ascii', 'replace')
    if t == 8:
        return '{' + ', '.join(const_repr(x) for x in p) + '}'
    return {0: 'nil', 2: 'false', 4: 'true'}.get(t, f'?{t}')


def disasm(code, consts, ivars=None, classvars=None):
    ivars = ivars or {}
    pc, out = 0, []
    while pc < len(code):
        op = code[pc]
        name, spec = OPS.get(op, (f'?{op:02x}', ''))
        p, args, note = pc + 1, [], []
        for k in spec:
            if k in 'bcs':
                v = code[p] if k != 's' else struct.unpack_from('<b', code, p)[0]
                p += 1
            elif k == 'j':
                v = pc + struct.unpack_from('<b', code, p)[0]
                p += 1
            elif k == 'J':
                v = pc + struct.unpack_from('<h', code, p)[0]
                p += 2
            else:
                v = struct.unpack_from('<H', code, p)[0]
                p += 2
            if k in 'cC' and v < len(consts):
                note.append(const_repr(consts[v]))
            args.append(f'@{v:04x}' if k in 'jJ' else str(v))
        if op in (0x20, 0x21) and args and int(args[0]) in ivars:
            note.append(ivars[int(args[0])])
        if op in (0x08, 0x09, 0x0A, 0x0B) and classvars:
            cls = consts[int(args[0])][1] if int(args[0]) < len(consts) else b''
            note.append('.' + classvars.get(cls, {}).get(int(args[1]), '?'))
        out.append(f'  {pc:04x}: {code[pc:p].hex(" "):<12} {name} {", ".join(args)}'
                   + (f'    ; {" ".join(note)}' if note else ''))
        pc = p
    return out


def load_classvars(script_dir):
    """Map class name -> {slot id: name} from every SCF's fields2 table."""
    out = {}
    for f in os.listdir(script_dir):
        if f.endswith('.scf'):
            d = scf.parse(open(os.path.join(script_dir, f), 'rb').read())
            out[d['names'][0]] = {i: n.decode('cp932') for i, n in d['fields2']}
    return out


def main():
    d = scf.parse(open(sys.argv[1], 'rb').read())
    want = {w.encode() for w in sys.argv[2:]}
    ivars = {i: n.decode('cp932') for i, n in d['fields']}
    classvars = load_classvars(os.path.dirname(os.path.abspath(sys.argv[1])))
    print(f'class {d["names"][0].decode("cp932")} : {d["names"][1].decode("cp932")}')
    for table in ('methods', 'methods2'):
        for name, argc, code in d[table]:
            if want and name not in want:
                continue
            print(f'{table[:-1]} {name.decode("cp932")} argc={argc}')
            print('\n'.join(disasm(code, d['constants'], ivars, classvars)))


if __name__ == '__main__':
    main()
