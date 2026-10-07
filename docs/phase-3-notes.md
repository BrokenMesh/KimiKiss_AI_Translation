# Phase 3 notes: executable (SLPS_258.50) reverse engineering

Addresses are Ghidra/EE addresses. Names below were applied in the Ghidra project (private, not in the repo).

## File access (Gate input for relocating SCRIPT.IMG)

- `0x00103540` `main`: after subsystem init it calls `open_file_stream("SCRIPT.IMG", 0)` at `0x00103598` (string at `0x002B16E0`). Other callers of `open_file_stream`: `0x00104410`, `0x0010B7E0`.
- Open chain: `open_file_stream` (`0x001014d8`) -> `0x0011EB80` -> `0x0011EBC8` -> `0x0011EA68` -> `0x00125920` -> `0x00125990`.
- The I/O layer is CRI middleware ("dvCi"). Strings: `E0092901:fname is null.(dvCiGetFileSize)`, `E0092902:can't find file.(dvCiGetFileSize)`, `DVCI: sceCdSearchFile failed. "%s"`, `E0092911:sceCdSearchFile fail.(dvCiOpen)`.
- `dvCiGetFileSize` (`0x001318D0`) and `dvCiOpen` (`0x00131FF8`) both resolve a file by name with `sceCdSearchFile`, so the game takes position and size from the ISO9660 directory entry. No hard-coded sector numbers were seen on this path.

Conclusion: a grown `SCRIPT.IMG` can be placed anywhere on the disc if its directory entry (extent LBA, size) is updated. Still to confirm in emulation: patched ISO with `SCRIPT.IMG` relocated boots and loads scripts.

## Open items

- SCF interpreter dispatch, text draw, glyph lookup, line wrap and advance width: not yet located.
