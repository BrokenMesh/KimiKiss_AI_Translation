# Size budget

Volume: 618944 sectors (1,267,597,312 bytes); DVD-5 capacity 2295104 sectors.

| File | LBA | Size | Slot | Slack | Rebuilt | Fits |
|---|---|---|---|---|---|---|
| SYSTEM.CNF | 299 | 57 | 2,048 | 1,991 |  |  |
| FCACHE.TXT | 300 | 90 | 2,048 | 1,958 |  |  |
| SLPS_258.50 | 301 | 1,839,732 | 1,841,152 | 1,420 |  |  |
| SCRIPT.IMG | 1200 | 1,855,749 | 1,857,536 | 1,787 |  |  |
| MODULES/CDVDSTM.IRX | 2107 | 33,521 | 34,816 | 1,295 |  |  |
| MODULES/CRI_ADXI.IRX | 2124 | 77,693 | 77,824 | 131 |  |  |
| MODULES/EZMIDI.IRX | 2162 | 49,396 | 51,200 | 1,804 |  |  |
| MODULES/IOPRP310.IMG | 2187 | 278,353 | 278,528 | 175 |  |  |
| MODULES/LIBSD.IRX | 2323 | 30,085 | 30,720 | 635 |  |  |
| MODULES/MCMAN.IRX | 2338 | 103,677 | 104,448 | 771 |  |  |
| MODULES/MCSERV.IRX | 2389 | 7,713 | 8,192 | 479 |  |  |
| MODULES/MODHSYN.IRX | 2393 | 63,005 | 63,488 | 483 |  |  |
| MODULES/MODMIDI.IRX | 2424 | 21,941 | 22,528 | 587 |  |  |
| MODULES/MSIFRPC.IRX | 2435 | 8,105 | 8,192 | 87 |  |  |
| MODULES/PADMAN.IRX | 2439 | 45,925 | 47,104 | 1,179 |  |  |
| MODULES/SDRDRV.IRX | 2462 | 9,161 | 10,240 | 1,079 |  |  |
| MODULES/SIO2MAN.IRX | 2467 | 5,217 | 6,144 | 927 |  |  |
| GRAPH/GRAPH0.ARC | 2470 | 5,573,460 | 5,574,656 | 1,196 |  |  |
| GRAPH/GRAPH0.PAC | 5192 | 1,825,235 | 1,826,816 | 1,581 |  |  |
| GRAPH/GRAPH1.ARC | 6084 | 172,408,980 | 172,410,880 | 1,900 |  |  |
| GRAPH/GRAPH2.ARC | 90269 | 238,868,920 | 238,870,528 | 1,608 |  |  |
| SOUND/MUSIC.ARC | 206905 | 13,304,240 | 13,305,856 | 1,616 |  |  |
| SOUND/VOICE.AFS | 213402 | 809,453,568 | 809,453,568 | 0 |  |  |
| SOUND/VOICE.IDX | 608643 | 104,800 | 21,096,448 | 20,991,648 |  |  |

Free after last file: 10249 sectors inside the volume; 1676160 more sectors before DVD-5 capacity.

SCRIPT.IMG: 1,855,749 bytes compressed, 4,204,839 bytes decompressed (the RAM the engine needs to hold it, if it loads the whole archive).

SLPS_258.50 load segments:

| vaddr | filesz | memsz | end | flags |
|---|---|---|---|---|
| 0x00100000 | 1,834,760 | 3,072,240 | 0x003ee0f0 | 0x7 |

ELF free space (code caves) is not measured yet; see Phase 3.

## Analysis

- **SCRIPT.IMG cannot grow in place.** It has 1,787 bytes of slack before `MODULES/CDVDSTM.IRX`. English text will make it larger, so the rebuilt archive must move to the free area after `VOICE.IDX`: 10,249 sectors inside the current volume, and the volume can grow toward DVD-5 capacity. Relocation only works if the ELF finds files through the ISO directory (for example `sceCdSearchFile`) rather than hard-coded LBAs. Check this in Phase 3.
- **GRAPH0.ARC and GRAPH0.PAC** have 1,196 and 1,581 bytes of slack. A redrawn font of the same dimensions keeps both sizes unchanged for the ARC; the PAC's compressed size will change and may need relocating too.
- **RAM:** SCRIPT.IMG decompresses to 4,204,839 bytes. If the engine holds the whole archive in memory, translated text growth comes out of EE RAM. The current Japanese text is 1,577,256 bytes of Shift-JIS. Phase 3 must find the buffer size the engine allocates for it.
- **ELF:** one RWX load segment, `0x00100000`–`0x003EE0F0` (memsz exceeds filesz by 1,237,480 bytes of BSS). Code caves are still to be found in Phase 3.

Regenerate with `python3 tools/qa/size_report.py build/orig_manifest.json build/orig [rebuilt_dir]`.
