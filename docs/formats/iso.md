# Disc image and other files

ISO9660, 618,944 sectors of 2048 bytes. 24 files. `tools/extract/iso_extract.py` extracts them to `build/orig/` and writes `build/orig_manifest.json` with each file's path, LBA, size and SHA-1, sorted by LBA.

## File classification

| File | Size | Magic | Role |
|---|---|---|---|
| `SYSTEM.CNF` | 57 | text | Boot config: `BOOT2 = cdrom0:\SLPS_258.50;1` |
| `FCACHE.TXT` | 90 | text | Lists GRAPH0/1/2.ARC, MUSIC.ARC, VOICE.AFS (probably files whose directory entries are cached at boot) |
| `SLPS_258.50` | 1,839,732 | `\x7fELF` | Main executable. MIPS R5900, one load segment at `0x00100000` (filesz 1,834,760, memsz 3,072,240) |
| `SCRIPT.IMG` | 1,855,749 | u32 size + LZSS | All scripts and text ([img.md](img.md), [scf.md](scf.md)) |
| `MODULES/IOPRP310.IMG` | 278,353 | `RESET`/`ROMDIR` | IOP replacement image (Sony) |
| `MODULES/*.IRX` (12) | 5–104 KB | `\x7fELF` | IOP modules: CDVD streaming, CRI ADX, MIDI and sound synth, memory card, pad, SIO2 |
| `GRAPH/GRAPH0.ARC` | 5,573,460 | ARC | UI textures and font ([arc.md](arc.md), [font.md](font.md)) |
| `GRAPH/GRAPH0.PAC` | 1,825,235 | u32 size + LZSS | LZSS copy of GRAPH0.ARC |
| `GRAPH/GRAPH1.ARC` | 172,408,980 | ARC | 599 TIM2 (likely backgrounds and event CGs) |
| `GRAPH/GRAPH2.ARC` | 238,868,920 | ARC | 988 TIM2 + sprite layouts (likely character sprites) |
| `SOUND/MUSIC.ARC` | 13,304,240 | ARC | Sound banks |
| `SOUND/VOICE.AFS` | 809,453,568 | `AFS\0` | CRI AFS of 16 nested AFS banks (voice clips) |
| `SOUND/VOICE.IDX` | 104,800 | none | u16[52,400] voice id → clip index (0xFFFF = none), 5,592 distinct clips |

Only `SCRIPT.IMG`, `SLPS_258.50`, `GRAPH0.ARC`/`GRAPH0.PAC`, and possibly some GRAPH1/2 textures need changes for the translation.
