"""SCF script container: parse to a dict and serialize back byte-for-byte.

Layout (all integers LE), derived from 21-ko/AMAGAMI-translation-tools
scf/parser_scf.py and verified against all 386 KimiKiss scripts:

  magic      4 bytes  "SCF\\x1a"
  flags      u8       0x08 on built-in classes (Array, True, ...), else 0
  version    u8       4
  names      2 x (u16 len, Shift-JIS)          class name, base class
  fields     u16 n, n x (u8 id, u16 len, SJIS)
  fields2    u16 n, same layout
  methods    u16 n, n x (u16 len, name, u16 argc, u16 code_len, code)
  methods2   u16 n, same layout
  constants  u16 n, n x constant

Constant = u8 type + payload:
  0, 2, 4   none (nil/true/false, not yet confirmed)
  1         4 bytes (int32)
  3         4 bytes (float32)
  8         array: u16 k, then k nested constants
  other     u16 len + Shift-JIS bytes (5 = text, 6/7 = symbols)

The amagami parser read constants until EOF and treated type 8 as a 2-byte
scalar; that only works because the nested children follow inline.

Bytecode refers to constants by index, so changing a string's length does
not move any code.
"""
import struct

MAGIC = b'SCF\x1a'
NO_PAYLOAD = {0, 2, 4}
FIXED_PAYLOAD = {1: 4, 3: 4}
ARRAY = 8


class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def take(self, n):
        if self.pos + n > len(self.data):
            raise ValueError(f'read past end at {self.pos} (+{n})')
        b = self.data[self.pos:self.pos + n]
        self.pos += n
        return b

    def u8(self):
        return self.take(1)[0]

    def u16(self):
        return struct.unpack('<H', self.take(2))[0]

    def blob16(self):
        return self.take(self.u16())


def _fields(r):
    return [(r.u8(), r.blob16()) for _ in range(r.u16())]


def _methods(r):
    out = []
    for _ in range(r.u16()):
        name = r.blob16()
        argc = r.u16()
        code = r.blob16()
        out.append((name, argc, code))
    return out


def _constant(r):
    t = r.u8()
    if t in NO_PAYLOAD:
        return (t, b'')
    if t in FIXED_PAYLOAD:
        return (t, r.take(FIXED_PAYLOAD[t]))
    if t == ARRAY:
        return (t, [_constant(r) for _ in range(r.u16())])
    return (t, r.blob16())


def parse(data):
    r = Reader(data)
    if r.take(4) != MAGIC:
        raise ValueError('bad SCF magic')
    scf = {
        'header': r.take(2),
        'names': [r.blob16(), r.blob16()],
        'fields': _fields(r),
        'fields2': _fields(r),
        'methods': _methods(r),
        'methods2': _methods(r),
    }
    scf['constants'] = [_constant(r) for _ in range(r.u16())]
    if r.pos != len(data):
        raise ValueError(f'{len(data) - r.pos} trailing bytes at {r.pos}')
    return scf


def _blob16(b):
    if len(b) > 0xFFFF:
        raise ValueError(f'string of {len(b)} bytes exceeds u16 length')
    return struct.pack('<H', len(b)) + b


def _put_constant(out, t, payload):
    out.append(t)
    if t in NO_PAYLOAD:
        return
    if t in FIXED_PAYLOAD:
        if len(payload) != FIXED_PAYLOAD[t]:
            raise ValueError(f'constant type {t} needs {FIXED_PAYLOAD[t]} bytes')
        out += payload
    elif t == ARRAY:
        out += struct.pack('<H', len(payload))
        for ct, cp in payload:
            _put_constant(out, ct, cp)
    else:
        out += _blob16(payload)


def serialize(scf):
    out = bytearray(MAGIC) + scf['header']
    for n in scf['names']:
        out += _blob16(n)
    for key in ('fields', 'fields2'):
        out += struct.pack('<H', len(scf[key]))
        for fid, name in scf[key]:
            out += bytes([fid]) + _blob16(name)
    for key in ('methods', 'methods2'):
        out += struct.pack('<H', len(scf[key]))
        for name, argc, code in scf[key]:
            out += _blob16(name) + struct.pack('<H', argc) + _blob16(code)
    out += struct.pack('<H', len(scf['constants']))
    for t, payload in scf['constants']:
        _put_constant(out, t, payload)
    return bytes(out)
