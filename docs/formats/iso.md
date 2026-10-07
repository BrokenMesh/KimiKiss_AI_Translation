# Disc image and other files

ISO9660 with a UDF 1.02 bridge, 618,944 sectors of 2048 bytes. 24 files. `tools/extract/iso_extract.py` extracts them to `build/orig/` and writes `build/orig_manifest.json` with each file's path, LBA, size and SHA-1, sorted by LBA.

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

## UDF bridge

The image is an ISO9660 + UDF bridge made by a "DVD-ROM GENERATOR" tool. Both file systems describe the same files; this was parsed read-only from the clean image with `tools/build/udf.py` and is verified by `tools/qa/check_iso_udf.py` (decision D-014).

### Descriptors

| Item | Sector | Notes |
|---|---|---|
| ISO9660 PVD | 16 | Volume space size 618,944 (both byte orders) |
| Volume recognition | 18, 19, 20 | `BEA01`, `NSR02`, `TEA01` (NSR02 = UDF 1.02) |
| AVDP | 256 and 618,943 (last sector) | Main VDS at 32 (16 sectors), reserve VDS at 48 |
| VDS (both copies) | 32..37 and 48..53 | PVD (tag 1), partition descriptor (5), LVD (6), unallocated space (7), terminator (8); identical in both copies |
| LVID | 64 (+ terminator at 65) | Integrity type "close"; size table = partition length; free-space table 0; unique id 0xFFFFFFFF; 24 files, 4 directories (root included); min read/write UDF 1.02 |
| Partition 0 | starts at 265, length 618,678 | Ends at 618,943 (exclusive). The trailing AVDP at 618,943 is outside it |
| FSD | block 0 (sector 265) | Root directory ICB: block 6, length 316 |
| Terminator after FSD | sector 266 | Its tag location is the absolute sector 266, not the partition-relative block 1 |

Logical block size 2048. All block numbers in file entries, allocation descriptors, FIDs and tag locations of FSD/FE/FID are relative to the partition start (265). Tag locations of the AVDP, VDS and LVID are absolute sectors. Partition contents are `+NSR02`, access type 1 (read only), partition flags 1.

### File entries and allocation descriptors

- Every directory and file uses a plain File Entry (tag 261), not an Extended File Entry (tag 266). ICB strategy 4, one ICB, flags `0x0630`: allocation descriptor type 0 = **short_ad** (8 bytes: `u32` length with the extent type in the top 2 bits, `u32` block number).
- Each FE is one sector: 176-byte fixed part, 132 bytes of extended attributes (an extended attribute header, tag 262, plus one `*UDF FreeEASpace` implementation-use attribute), then the allocation descriptors. Descriptor length 316, so the tag CRC length is 300.
- File type 5 (regular file) or 4 (directory). Permissions `0x14A5`, link count 1, uid and gid -1.
- Every file has exactly one short_ad, extent type 0 (recorded and allocated). The largest, `VOICE.AFS` (809 MB), is below the 1 GiB - 1 limit of one extent, so no file is split.
- Information length is the exact byte size, logical blocks recorded is the size in sectors rounded up.
- Directory data sits in its own block, a run of FIDs: parent FID first (characteristics 0x0A), then one FID per entry with a CS0 name (`0x10` prefix: UTF-16BE, no version suffix, e.g. `SCRIPT.IMG`, not `SCRIPT.IMG;1`). Each directory fits in one block (blocks 2 to 5 for the root, `MODULES`, `GRAPH`, `SOUND`).

### Are file data extents shared with ISO9660?

Yes. The UDF block of every file is exactly the ISO9660 LBA minus 265, and the lengths are equal (for example `SYSTEM.CNF`: ISO9660 LBA 299 / UDF block 34; `SCRIPT.IMG`: LBA 1200 / block 935). There is one copy of the data. Only the two sets of metadata (ISO9660 directory records, UDF FE + allocation descriptor) have to be kept in step. The directories themselves are not shared (ISO9660 directory extents at LBA 262 to 264 and the root, UDF directory blocks 2 to 5).

### Tag checksum and CRC rules

- Tag (16 bytes): identifier, version 2, checksum, serial 0, CRC, CRC length, location. Checksum = sum of tag bytes 0 to 15 except byte 4, modulo 256.
- CRC is CRC-ITU-T (polynomial 0x1021, initial value 0, no reflection or final xor) over the bytes after the tag. The CRC length is written in the tag:
  - AVDP, PVD, partition descriptor, LVD, unallocated space descriptor, LVID, FSD: 2032 (the whole sector after the tag, not the 496 or so the spec's descriptor length gives). The terminating descriptors (tag 8) have CRC length 2032 with CRC 0 (CRC of zeros is 0).
  - FE: 300 (descriptor length 316 - 16). FID: descriptor length - 16, padded to 4 bytes (24 for the parent FID).
- A checker must use the CRC length stored in the tag, not the length the specification names. `udf.seal_tag` keeps the stored length and recomputes CRC and checksum.

### What a patch changes

For each rewritten or relocated file `tools/build/iso_patch.py` updates, besides the ISO9660 record: FE information length, logical blocks recorded, the short_ad (length, block = new LBA - 265), then the FE tag CRC and checksum. Nothing else in the UDF tree depends on a file's position or size (FIDs hold only the FE block).

Relocation is bounded by the end of the UDF partition (sector 618,943), not by the ISO9660 volume size: the last sector holds the trailing AVDP. The 10,248 free sectors between the end of `VOICE.IDX` (608,695) and the partition end hold the relocated files (about 21 MB; the current build uses about 1.8 K sectors). If a build ever needs more, `iso_patch.py` grows the image: it extends the file, moves the trailing AVDP to the new last sector (zeroing the old one unless data now covers it), and updates the ISO9660 volume space size, the partition length in both partition descriptors, and the LVID size table. This path was exercised with a 30 MB and a 3 MB test file; the checker passed and the file contents read back identical through the UDF extents.

Not covered because the image has none: Extended File Entries are parsed (`udf.Entry`) but untested; files with several extents or embedded data are refused by the patcher.
