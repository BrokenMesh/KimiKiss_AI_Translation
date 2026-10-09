#!/usr/bin/env python3
"""Apply the in-place code patches in patches/elf/ to the game executable (D-027).

  elf_patch.py <clean SLPS_258.50> <out SLPS_258.50> [patch_dir]
  elf_patch.py --assemble [patch_dir]     regenerate each patch's "hex" from its .s (needs llvm-mc)

Then the [[sprite]] blocks of translation/textures.toml (D-035) are written into the
sprite table (tools/texture/sprites.py; the original GRAPH/GRAPH0.ARC next to the clean
executable is read to check them).

patch_dir/patches.json lists {name, vaddr, size, orig_sha1, source, hex}. A patch replaces
`size` bytes at `vaddr`; the original bytes there must hash to `orig_sha1`, so a patch never
lands on a different executable. The new code is padded with nops to `size`. The file size
does not change.
"""
import hashlib, json, os, struct, subprocess, sys, tempfile

NOP = b'\0\0\0\0'


def segments(elf):
    phoff, = struct.unpack_from('<I', elf, 0x1C)
    phnum, = struct.unpack_from('<H', elf, 0x2C)
    for i in range(phnum):
        _, off, vaddr, _, filesz = struct.unpack_from('<5I', elf, phoff + 32 * i)
        yield off, vaddr, filesz


def file_offset(elf, vaddr, size):
    for off, base, filesz in segments(elf):
        if base <= vaddr and vaddr + size <= base + filesz:
            return off + vaddr - base
    raise ValueError(f'{vaddr:#x}+{size:#x} is not inside a loaded segment')


def assemble(src):
    with tempfile.TemporaryDirectory() as d:
        s, o, b = (os.path.join(d, n) for n in ('p.s', 'p.o', 'p.bin'))
        open(s, 'w').write('        .text\n' + open(src).read())
        subprocess.run(['llvm-mc', '--triple=mipsel-unknown-none', '-mcpu=mips4', '-filetype=obj',
                        s, '-o', o], check=True)
        subprocess.run(['llvm-objcopy', '-O', 'binary', '-j', '.text', o, b], check=True)
        return open(b, 'rb').read()


def main():
    if sys.argv[1] == '--assemble':
        pdir = sys.argv[2] if len(sys.argv) > 2 else 'patches/elf'
        path = os.path.join(pdir, 'patches.json')
        patches = json.load(open(path))
        for p in patches:
            code = assemble(os.path.join(pdir, p['source']))
            if len(code) > p['size']:
                sys.exit(f"error: {p['name']}: {len(code)} bytes > {p['size']}")
            p['hex'] = code.hex()
            print(f"{p['name']}: {len(code)} of {p['size']} bytes")
        json.dump(patches, open(path, 'w'), indent=1)
        open(path, 'a').write('\n')
        return
    src, out = sys.argv[1:3]
    pdir = sys.argv[3] if len(sys.argv) > 3 else 'patches/elf'
    elf = bytearray(open(src, 'rb').read())
    for p in json.load(open(os.path.join(pdir, 'patches.json'))):
        vaddr, size = int(p['vaddr'], 16), p['size']
        off = file_offset(elf, vaddr, size)
        got = hashlib.sha1(elf[off:off + size]).hexdigest()
        if got != p['orig_sha1']:
            sys.exit(f"error: {p['name']}: bytes at {vaddr:#x} hash {got}, expected {p['orig_sha1']}")
        code = bytes.fromhex(p['hex'])
        if len(code) > size or len(code) % 4:
            sys.exit(f"error: {p['name']}: bad code length {len(code)}")
        elf[off:off + size] = code + NOP * ((size - len(code)) // 4)
        print(f"{p['name']}: {vaddr:#010x} {len(code)}/{size} bytes")
    sprite_sizes(src, elf)
    open(out, 'wb').write(elf)


def sprite_sizes(src, elf):
    """Larger sprite canvases from translation/textures.toml (D-035)."""
    sys.path[:0] = [os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'texture')]
    import sprites
    import texdefs
    try:
        wanted = texdefs.load()['sprites']
        if not wanted:
            return
        graph0 = os.path.join(os.path.dirname(os.path.abspath(src)), 'GRAPH', 'GRAPH0.ARC')
        _, records = sprites.resolve(bytes(elf), open(graph0, 'rb').read(), wanted)
        sprites.patch_elf(elf, records)
    except (texdefs.TexDefError, sprites.SpriteError) as e:
        sys.exit(f'error: {e}')
    for r, (w, h) in records:
        print(f"sprite {r['id']} {r['name']}: {r['w']:g} x {r['h']:g} -> {w} x {h}")


if __name__ == '__main__':
    main()
