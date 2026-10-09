#!/usr/bin/env python3
"""Texture names, the executable's sprite table, and larger sprite canvases (D-035).

Usage: sprites.py names <SLPS_258.50> <GRAPH0.ARC>     entry -> name list
       sprites.py table <SLPS_258.50>                  the sprite table
       sprites.py export <entry> <out.png> [orig dir]  original texture padded to the canvas
                                                       textures.toml gives it (a template for a
                                                       hand-made override)

Names. The GRAPH archives store no names, only a hash of "<name>.tm2"
(docs/formats/arc.md): h = c0, then h = h * 0x3FAD + c for every further byte, 32 bit
(the archive lookup, 0x00176ea0). The executable holds the names and name patterns
("sysgraph/menu_set2", "icon_wadai/it%03d"); expanding the patterns names 490 of the
551 GRAPH0 entries.

Sprite table. `Sprite new: id, ...` (script) draws record `id` of a table of 152
records of 36 bytes at 0x001df1f0: name pattern pointer, u32 flag (1 = the name has a
number in it), float x, y (unknown; 0 for most records, not a texture offset), w, h
(the size on screen),
u32 0x100, u32, u32 -1. The quad is centred on the sprite's position (checked in
PCSX2 with menu_set2: width 40 -> 80 grows 20 px to each side). The texture's own
TIM2 size is not used for the quad: a wider TIM2 with the old record is cut off.

Larger canvas. A `[[sprite]]` block of translation/textures.toml gives a record a new
w x h. The build then (1) pads every archive texture of that record to the new size
around its centre, so the old picture stays where it was on screen, (2) repacks
GRAPH0.ARC with the new entry lengths (the engine allocates each entry from the ARC
directory, LoadGraph0 0x00104410, so lengths may change) and (3) writes the new w, h
into the record. Records with x, y not 0 (meaning unknown, untested) or a name that
several records share are refused.
"""
import itertools
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'extract')]
import arc  # noqa: E402
import tim2  # noqa: E402

TABLE = 0x001df1f0      # sprite table in SLPS_258.50
RECORDS = 152
RECORD = 36
NAME_HASH_MUL = 0x3FAD


class SpriteError(Exception):
    pass


def name_hash(name):
    """ARC hash of a texture name (without .tm2; it is added here)."""
    s = (name + '.tm2').encode('ascii')
    h = s[0]
    for c in s[1:]:
        h = (h * NAME_HASH_MUL + c) & 0xffffffff
    return h


# ---------------------------------------------------------------- the executable

def _segments(elf):
    phoff, = struct.unpack_from('<I', elf, 0x1C)
    phnum, = struct.unpack_from('<H', elf, 0x2C)
    for i in range(phnum):
        _, off, vaddr, _, filesz = struct.unpack_from('<5I', elf, phoff + 32 * i)
        yield off, vaddr, filesz


def file_offset(elf, vaddr, size=1):
    for off, base, filesz in _segments(elf):
        if base <= vaddr and vaddr + size <= base + filesz:
            return off + vaddr - base
    raise SpriteError(f'{vaddr:#x} is not inside a loaded segment')


def cstring(elf, vaddr):
    o = file_offset(elf, vaddr)
    return elf[o:elf.index(b'\0', o)].decode('latin-1')


def read_table(elf):
    """-> [record dict] for the 152 records (id = list index)."""
    base = file_offset(elf, TABLE, RECORDS * RECORD)
    out = []
    for i in range(RECORDS):
        o = base + i * RECORD
        ptr, flag = struct.unpack_from('<II', elf, o)
        u, v, w, h = struct.unpack_from('<4f', elf, o + 8)
        out.append({'id': i, 'name': cstring(elf, ptr) if ptr else '', 'pattern': bool(flag),
                    'u': u, 'v': v, 'w': w, 'h': h, 'offset': o})
    if out[121]['name'] != 'sysgraph/menu_set2' or (out[121]['w'], out[121]['h']) != (40.0, 32.0):
        raise SpriteError('sprite table not where expected (is this SLPS_258.50 of SLPS-25850?)')
    return out


def name_patterns(elf):
    """Every string of the executable that looks like a texture path (with or without %d)."""
    return sorted({m.group().decode() for m in re.finditer(rb'(?<=\0)[a-zA-Z0-9_]+/[ -~]+?(?=\0)', elf)})


_FIELDS = {'%1d': [str(i) for i in range(10)], '%d': [str(i) for i in range(100)],
           '%02d': [f'{i:02d}' for i in range(100)], '%03d': [f'{i:03d}' for i in range(1000)],
           '%1x': [f'{i:x}' for i in range(16)], '%c': [chr(c) for c in range(32, 127)]}


def expand(pattern):
    """All names a pattern can produce (%s is skipped: no fixed set)."""
    parts = re.split(r'(%[0-9]*[a-z])', pattern)
    if any(p.startswith('%') and p not in _FIELDS for p in parts):
        return []
    opts = [_FIELDS[p] if p.startswith('%') else [p] for p in parts]
    return [''.join(c) for c in itertools.product(*opts)]


def entry_names(elf, arc_data):
    """-> {entry: name} for the entries of one archive whose name is in the executable."""
    by_hash = {e['hash']: e['index'] for e in arc.parse(arc_data)['entries']}
    out = {}
    for p in name_patterns(elf):
        for n in expand(p):
            i = by_hash.get(name_hash(n))
            if i is not None:
                out[i] = n
    return out


# ---------------------------------------------------------------- larger canvases

def pad_tim2(blob, w, h):
    """TIM2 padded to w x h around its centre with the texture's clear colour (or edge pixels)."""
    t = tim2.parse(blob)
    if t['bpp'] != 8:
        raise SpriteError(f'only 8bpp textures can be resized ({t["bpp"]}bpp)')
    ow, oh = t['w'], t['h']
    if w < ow or h < oh or (w - ow) % 2 or (h - oh) % 2:
        raise SpriteError(f'canvas {w} x {h}: must be at least {ow} x {oh} and grow by an even number '
                          'of pixels (the picture stays centred)')
    px = [list(t['indices'][y * ow:(y + 1) * ow]) for y in range(oh)]
    clear = [i for i, c in enumerate(t['palette']) if c[3] == 0]
    used = set(t['indices'])
    fill = next((i for i in clear if i in used), clear[0] if clear else None)
    dx, dy = (w - ow) // 2, (h - oh) // 2
    rows = []
    for y in range(h):
        sy = min(max(y - dy, 0), oh - 1)
        src = px[sy]
        row = []
        for x in range(w):
            sx = x - dx
            inside = 0 <= sx < ow and 0 <= y - dy < oh
            if inside:
                row.append(src[sx])
            else:
                row.append(fill if fill is not None else src[min(max(sx, 0), ow - 1)])
        rows.append(bytes(row))
    hdr = bytearray(t['header'])
    tex0, = struct.unpack_from('<Q', hdr, 40)          # GsTex0 of the picture header
    tw, th = (w - 1).bit_length(), (h - 1).bit_length()
    tex0 = (tex0 & ~(0xF << 26) & ~(0xF << 30)) | (tw << 26) | (th << 30)
    struct.pack_into('<Q', hdr, 40, tex0)
    return tim2.build(bytes(hdr), w, h, t['bpp'], t['swizzled'], t['palette'], b''.join(rows))


def resolve(elf, arc_data, sizes):
    """sizes {record name: (w, h)} -> ({entry: (w, h)}, [(record, (w, h))]); checks every rule."""
    table = read_table(elf)
    by_name = {}
    for r in table:
        by_name.setdefault(r['name'], []).append(r)
    by_hash = {e['hash']: e['index'] for e in arc.parse(arc_data)['entries']}
    entries, records = {}, []
    for name, (w, h) in sizes.items():
        recs = by_name.get(name)
        if not recs:
            raise SpriteError(f'[[sprite]] {name!r}: no sprite-table record has this name '
                              '(see `python3 tools/texture/sprites.py table build/orig/SLPS_258.50`)')
        if len(recs) > 1:
            raise SpriteError(f'[[sprite]] {name!r}: {len(recs)} records share this name with different sizes; '
                              'resizing one of them is not supported')
        r = recs[0]
        if r['u'] or r['v']:
            raise SpriteError(f'[[sprite]] {name!r}: the record has the unexplained values {r["u"]:g}, {r["v"]:g} '
                              '(docs/formats/sprites.md); resizing it is untested and not supported')
        names = expand(name) if r['pattern'] else [name]
        hits = [by_hash[name_hash(n)] for n in names if name_hash(n) in by_hash]
        if not hits:
            raise SpriteError(f'[[sprite]] {name!r}: none of its textures is in GRAPH0')
        for e in hits:
            entries[e] = (w, h)
        records.append((r, (w, h)))
    return entries, records


def grow_archive(arc_data, entry_sizes):
    """ARC with the given entries padded to their new size; offsets recomputed, hashes and buckets kept."""
    a = arc.parse(arc_data)
    ents, n = a['entries'], a['count']
    blobs = {e['index']: bytes(arc_data[e['offset']:e['offset'] + e['size']]) for e in ents}
    for i, (w, h) in entry_sizes.items():
        t = tim2.parse(blobs[i])
        if (t['w'], t['h']) != (w, h):
            blobs[i] = pad_tim2(blobs[i], w, h)
    if all(len(blobs[e['index']]) == e['size'] for e in ents):
        return bytes(arc_data)
    pos = 8 + 20 * n
    data, placed = bytearray(), {}
    for e in sorted(ents, key=lambda e: e['offset']):
        placed[e['index']] = (pos + len(data), len(blobs[e['index']]))
        data += blobs[e['index']]
    out = bytearray(arc_data[:8 + 4 * n])
    for e in ents:
        off, size = placed[e['index']]
        out += struct.pack('<4I', e['flag'], e['hash'], off, size)
    return bytes(out + data)


def patch_elf(elf, records):
    """Write the new w, h into the sprite records. elf: bytearray (changed in place)."""
    for r, (w, h) in records:
        o = r['offset'] + 16
        got = struct.unpack_from('<2f', elf, o)
        if got != (r['w'], r['h']):
            raise SpriteError(f'sprite {r["name"]}: record holds {got}, expected {(r["w"], r["h"])}')
        struct.pack_into('<2f', elf, o, float(w), float(h))


def main():
    args = sys.argv[1:]
    if args[:1] == ['names'] and len(args) == 3:
        names = entry_names(open(args[1], 'rb').read(), open(args[2], 'rb').read())
        for i in sorted(names):
            print(f'{i}\t{names[i]}')
    elif args[:1] == ['table'] and len(args) == 2:
        for r in read_table(open(args[1], 'rb').read()):
            print(f"{r['id']}\t{r['name'] or '-'}\t{r['w']:g} x {r['h']:g}" +
                  (f"\tat {r['u']:g},{r['v']:g}" if r['u'] or r['v'] else ''))
    elif args[:1] == ['export'] and len(args) in (3, 4):
        import texdefs
        orig = args[3] if len(args) == 4 else os.path.join(HERE, '..', '..', 'build', 'orig')
        elf = open(os.path.join(orig, 'SLPS_258.50'), 'rb').read()
        data = open(os.path.join(orig, 'GRAPH', 'GRAPH0.ARC'), 'rb').read()
        sizes, _ = resolve(elf, data, texdefs.load()['sprites'])
        data = grow_archive(data, sizes)
        e = arc.parse(data)['entries'][int(args[1])]
        with open(args[2], 'wb') as f:
            f.write(tim2.to_png(tim2.parse(data[e['offset']:e['offset'] + e['size']])))
        print(f'wrote {args[2]}')
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
