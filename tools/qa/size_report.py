#!/usr/bin/env python3
"""Size budget report: disc slots, SCRIPT.IMG, and the ELF's load segments.

Usage: size_report.py <manifest.json> <orig_dir> [rebuilt_dir]

<manifest.json> comes from iso_extract.py. A file's slot runs from its LBA to
the next file's LBA (or the volume end), so "slack" is how much it can grow
in place. With [rebuilt_dir], files present there are compared to their slot.
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extract'))
import lzss  # noqa: E402

SECTOR = 2048
DVD5_SECTORS = 2295104


def elf_segments(path):
    data = open(path, 'rb').read()
    phoff, = struct.unpack_from('<I', data, 0x1C)
    phentsize, phnum = struct.unpack_from('<HH', data, 0x2A)
    segs = []
    for i in range(phnum):
        p_type, off, vaddr, _, filesz, memsz, flags, _ = struct.unpack_from('<8I', data, phoff + i * phentsize)
        if p_type == 1:
            segs.append((vaddr, filesz, memsz, flags))
    return segs


def main():
    manifest_path, orig_dir = sys.argv[1:3]
    rebuilt_dir = sys.argv[3] if len(sys.argv) > 3 else None
    m = json.load(open(manifest_path))
    files = sorted(m['files'], key=lambda e: e['lba'])
    vol = m['volume_sectors']
    last_end = 0
    print(f'# Size budget\n\nVolume: {vol} sectors ({vol * SECTOR:,} bytes); '
          f'DVD-5 capacity {DVD5_SECTORS} sectors.\n')
    print('| File | LBA | Size | Slot | Slack | Rebuilt | Fits |')
    print('|---|---|---|---|---|---|---|')
    for i, e in enumerate(files):
        nxt = files[i + 1]['lba'] if i + 1 < len(files) else vol
        slot = (nxt - e['lba']) * SECTOR
        last_end = max(last_end, e['lba'] + -(-e['size'] // SECTOR))
        new = ''
        fits = ''
        if rebuilt_dir and os.path.exists(os.path.join(rebuilt_dir, e['path'])):
            n = os.path.getsize(os.path.join(rebuilt_dir, e['path']))
            new, fits = f'{n:,}', 'yes' if n <= slot else f'no (+{n - slot:,})'
        print(f"| {e['path']} | {e['lba']} | {e['size']:,} | {slot:,} | {slot - e['size']:,} | {new} | {fits} |")
    print(f'\nFree after last file: {vol - last_end} sectors inside the volume; '
          f'{DVD5_SECTORS - vol} more sectors before DVD-5 capacity.\n')

    img = open(os.path.join(orig_dir, 'SCRIPT.IMG'), 'rb').read()
    raw, _ = lzss.decompress(img)
    print(f'SCRIPT.IMG: {len(img):,} bytes compressed, {len(raw):,} bytes decompressed '
          '(the RAM the engine needs to hold it, if it loads the whole archive).\n')

    elf = [e for e in files if e['path'].startswith('SLPS_')][0]['path']
    print(f'{elf} load segments:\n')
    print('| vaddr | filesz | memsz | end | flags |')
    print('|---|---|---|---|---|')
    for vaddr, filesz, memsz, flags in elf_segments(os.path.join(orig_dir, elf)):
        print(f'| {vaddr:#010x} | {filesz:,} | {memsz:,} | {vaddr + memsz:#010x} | {flags:#x} |')
    print('\nELF free space (code caves) is not measured yet; see Phase 3.')


if __name__ == '__main__':
    main()
