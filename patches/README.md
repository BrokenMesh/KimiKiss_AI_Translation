# Patches

## `scripts/` — SCF bytecode patches

One file per replaced method, in the assembler syntax of `tools/reinsert/scfasm.py`. Every file has a header:

- `; target: <Class> <method> argc=<n> table=<methods|methods2>`: the method that is replaced;
- `; original-sha1:`: the SHA-1 of the original bytecode, so a patch is never applied to the wrong input;
- `; reason:`: why the method is replaced.

`tools/reinsert/apply_script_patches.py <script_dir> patches/scripts` applies them during the build. `@EN_WIDTHS` expands to the width table from `tools/font/en_widths.json`. Original bytecode can be listed with `tools/extract/scfdis.py <Class>.scf <method>`; the new bytecode is the assembled patch.

| Patch | Original | New | Reason |
|---|---|---|---|
| `TextWindow.putChar.asm` | 96 bytes | 125 bytes | Variable-width English in the message window (D-011–D-013) |
| `LogLine.putChar.asm` | 104 bytes | 131 bytes | Same, in the backlog |

## ELF

None so far (D-011).
