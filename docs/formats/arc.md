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
- The engine looks assets up by name hash. The hash function is unknown, but it isn't needed to replace content in place.
- Data is contiguous in offset order, with no alignment or gaps. The last entry ends exactly at EOF.

## Contents

| Archive | Entries | Content |
|---|---|---|
| GRAPH0.ARC | 552 | 551 TIM2 + 1 unidentified record. Entry 77 is the dialogue font ([font.md](font.md)) |
| GRAPH1.ARC | 599 | 599 TIM2 |
| GRAPH2.ARC | 1980 | 988 TIM2 + 992 float32 records (coordinates; probably sprite layouts) |
| MUSIC.ARC | 102 | 68 `IECS` (Sony sound-bank headers) + 34 entries without a magic (probably the matching sample bodies) |

`GRAPH0.PAC` is the LZSS-compressed GRAPH0.ARC. Which of the two the engine loads is not yet known (Phase 3). Any change to GRAPH0.ARC must also be applied to the PAC.

## Tools

- `tools/extract/arc.py list|unpack`
- `tools/reinsert/arc_pack.py <dir> <out.arc>`: keeps hashes and buckets and recomputes offsets. Unchanged input is byte-identical for all four archives.
