# SCRIPT.IMG

LZSS-compressed ([lzss.md](lzss.md)) archive of named members. Identical in structure to Amagami's `amagami.img` (`21-ko/AMAGAMI-translation-tools/img/amagami_img.bms`).

## Decompressed layout (LE)

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | Total size (equals the decompressed length) |
| 4 | 4 | Member count `n` (386) |
| 8 | 4n | Name offset per member |
| 8 + 4n | 4n | Data offset per member |
| 8 + 8n | … | NUL-terminated ASCII names, in member order |
| … | … | Member data, contiguous, in member order |

- Member `i` spans `data_offset[i]` to `data_offset[i+1]`. The last member ends at the total size.
- There is no padding or alignment anywhere.
- Member order is not alphabetical. The tools keep it from `index.json`.
- Every member is an SCF script ([scf.md](scf.md)). The names carry no extension; the tools add `.scf`.

## Tools

- `tools/extract/img.py unpack <SCRIPT.IMG> <dir>` writes the members and `index.json`.
- `tools/reinsert/img_pack.py <dir> <SCRIPT.IMG>` rebuilds and recompresses the archive. Unchanged input is byte-identical.
