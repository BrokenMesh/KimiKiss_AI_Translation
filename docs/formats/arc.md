# ARC archives

`GRAPH/GRAPH0.ARC`, `GRAPH/GRAPH1.ARC`, `GRAPH/GRAPH2.ARC` and `SOUND/MUSIC.ARC`. These are hashed archives that store no file names.

## Layout (LE)

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | Entry count `n` |
| 4 | 4 | Header size, always `8 + 20n` (data starts here) |
| 8 | 2n | `bucket_len[n]`: entries per bucket |
| 8 + 2n | 2n | `bucket_start[n]`: first entry of each bucket (0 for empty buckets) |
| 8 + 4n | 16n | Entries: u32 flag (always 1), u32 hash, u32 offset, u32 size |

- An entry's bucket is `hash % n`, verified for every entry in all four archives.
- The engine looks assets up by the hash of `"<name>.tm2"` (`0x00176ea0`, D-035): `h = c0`, then `h = h * 0x3FAD + c` for every further byte, 32 bit, chars signed (all names are ASCII). The names come from strings in the executable (`sysgraph/menu_set2`, `icon_wadai/it%03d`); `python3 tools/texture/sprites.py names build/orig/SLPS_258.50 build/orig/GRAPH/GRAPH0.ARC` lists the 490 GRAPH0 entries they name.
- Data is contiguous in offset order, with no alignment or gaps. The last entry ends exactly at EOF.

## Contents

| Archive | Entries | Content |
|---|---|---|
| GRAPH0.ARC | 552 | 551 TIM2 + 1 unidentified record. Entry 77 is the dialogue font ([font.md](font.md)) |
| GRAPH1.ARC | 599 | 599 TIM2 |
| GRAPH2.ARC | 1980 | 988 TIM2 + 992 float32 records (coordinates; probably sprite layouts) |
| MUSIC.ARC | 102 | 68 `IECS` (Sony sound-bank headers) + 34 entries without a magic (probably the matching sample bodies) |

## How the archives are stored and loaded

- **GRAPH0**: `GRAPH0.ARC` is the directory and `GRAPH0.PAC` is the same archive LZSS-compressed ([lzss.md](lzss.md)). `LoadGraph0` (`0x00104410`) reads the directory from the ARC and the data from the PAC, so a change to a GRAPH0 entry must be made in both files (`tools/texture/apply_graph0.py` writes both).
- **GRAPH1 and GRAPH2**: no PAC and no compression. Every TIM2 entry is the raw texture inside `GRAPH1.ARC` / `GRAPH2.ARC` (the entry starts with `TIM2`; there is no per-entry LZSS either). `LoadGraph1` (`0x00104738`) and `LoadGraph2` (`0x00104928`) open the `.ARC` as a stream, like `LoadGraph0` opens its ARC; the string `GRAPH\GRAPH0.PAC` is referenced only by `LoadGraph0` (at `0x00104540`), and the other two loaders have no decompression step. This was read from the disassembly and is not yet seen in the emulator with a changed GRAPH1/2 entry.
- `LoadGraph0` allocates every entry with its size from the directory, so a GRAPH0 entry may change length if the archive is repacked (`sprites.grow_archive`, D-035; seen working in PCSX2).
- Replacing an entry with a same-size TIM2 moves nothing: write the new bytes at the entry's offset and leave the directory alone. `tools/texture/apply_graph12.py` does that for hand-edited textures (D-020); `iso_patch.py` then writes the whole file back in place (same size), which also leaves the UDF entry unchanged apart from its CRC.

## Tools

- `tools/extract/arc.py list|unpack`
- `tools/texture/overrides.py`, `apply_graph12.py`: PNG overrides for single entries ([../phase-4-textures.md](../phase-4-textures.md), D-020)
- `tools/reinsert/arc_pack.py <dir> <out.arc>`: keeps hashes and buckets and recomputes offsets. Unchanged input is byte-identical for all four archives.
