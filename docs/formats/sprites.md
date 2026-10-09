# Sprite table (SLPS_258.50)

The size at which a script `Sprite` is drawn comes from a table in the executable, not from the texture (D-035).

## Layout

152 records of 36 bytes at `0x001df1f0` (file offset `0x0e01f0`). The script's `Sprite new: id, ...` (`Sprite >> initialize` argc 4, primitive 1 at `0x00110b40` → `0x001090d0`) draws record `id`.

| Offset | Type | Field |
|---|---|---|
| 0 | u32 | pointer to the name (pattern), e.g. `sysgraph/menu_set2`, `icon_wadai/it%03d`; 0 for record 0 (a full-screen 640 x 448 entry) |
| 4 | u32 | 1 when the name has a number field (`%1d`, `%03d`, ...) filled in by the caller |
| 8 | f32 | u: left edge of the rectangle in the texture |
| 12 | f32 | v: top edge |
| 16 | f32 | w: width, also the width on screen |
| 20 | f32 | h: height, also the height on screen |
| 24 | u32 | `0x100` or `0x101` |
| 28 | u32 | 0..3 (unknown; 3 for `kaiwa/` records) |
| 32 | u32 | `0xffffffff`, or 0 for records with a texture offset |

- The texture is looked up by the name plus `.tm2` (hash in [arc.md](arc.md)).
- The quad is centred on the position given to `setPos:`. Checked in PCSX2 with record 121 (`menu_set2`, the settings label "Rumble" at x 412):
  - width 40 with an 80-px texture: the left 40 px are shown;
  - width 80: the whole texture, from x 372 to 452.
- `Sprite >> setTexRect:` (argc 4: u, v, w, h) changes the rectangle at run time; the name-entry cursor uses it.
- Some records take part of a shared texture (`sysgraph/maru128` at 512, 320; `sysgraph/cursor_base` at 416, 288). Some patterns are listed several times with different sizes (`sysgraph/txt_%03d`: 24 x 32, 32 x 24, 48 x 24, 64 x 24, 80 x 24).

## Tools

- `python3 tools/texture/sprites.py table build/orig/SLPS_258.50` lists the records.
- `python3 tools/texture/sprites.py names build/orig/SLPS_258.50 build/orig/GRAPH/GRAPH0.ARC` names the GRAPH0 entries by expanding every texture path in the executable.
- `[[sprite]]` blocks in `translation/textures.toml` give a record a larger size. The build pads the record's textures around their centre, repacks GRAPH0 and writes the new w, h (`apply_graph0.py`, `elf_patch.py`).
