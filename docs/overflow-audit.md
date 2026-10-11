# Overflow audit: what longer text uses up, and what happens when it runs out

Question (2026-10-11): which fixed-size resources does the English text use more of than the Japanese, what happens when each one runs out, and what stops that from crashing the game. Addresses are EE addresses in `SLPS_258.50`. Measurements were taken in PCSX2 through PINE with the issue #9 Day 7 save (the save itself is not in the repository). Decision log entry: D-042.

## Why English needs more

- Every character on screen is one sprite (`FontChar`/`FontCharEx` → `Sprite_CreateFontChar`, `0x00109540`), and every sprite asks for GS packets each frame.
- The English font is proportional and narrow. A 552 px dialogue line holds about 50 English characters against 24 Japanese ones, so a full screen of English has about twice as many sprites. The backlog shows up to three window pages (9 lines), which is about 450 English glyphs against 216 Japanese.
- In total the script holds 1,624,481 English characters against 950,238 Japanese (D-027).

## Resources

| Resource | Size | Cost of one English character | Lowest seen (English) | When it runs out | Protection |
|---|---|---|---|---|---|
| Draw packet pool `0x002c0620` | 512 KB, minus the 4 KB sink; holds about two frames | glyph + shadow packet each frame, about 1.5 KB over the two frames in flight (D-040) | 3.5 KB free (end of a school day), 5.6 KB (backlog), 56 KB (topic bag) | the allocator returns 0 | **D-041 guard**: the sprite is skipped for that frame. Before D-041, a write at address 0 (the issue #9 freeze, the topic bag crash). |
| Sprite handles (manager `0x002c06c0`, `+0x30`) | 513 slots; slot 0 is reserved | one per glyph | 99 free (conversation with a portrait and the backlog) | `Sprite_Create*` returns handle 0 | **Already safe.** Slot 0 has id 0 and the manager's null object (`+0x28`), whose kill method is `jr ra` (`0x00189060`). Every operation on handle 0 does nothing, so the glyph is simply not drawn. |
| Sprite pool `0x002c06c0` | 384 KB, 128-byte units | 0x234 bytes = 5 units | 113 KB free | the allocator returns 0, and the 46 constructor sites write to it without a check | **Bounded by the handles.** A sprite takes a handle before its memory. After its own tables (slot table 0x381c, layer table, null object: 14.8 KB), the pool holds 2,956 units, and 512 sprites of 5 units need 2,560. It can only run out if the live sprites average more than 5.77 units: about 99 of the largest picture sprites (0x3f8 bytes, 9 units) at once. Text sprites are exactly 5 units. |
| Glyph cache (`g_GlyphCache`, VRAM) | 208 slots | one slot per distinct code on screen | 167 free | `GlyphCache_Alloc` (`0x0017f308`) returns 0 and the glyph is uploaded over slot 0 (a wrong glyph, no crash) | **Unreachable**: English uses about 95 distinct glyphs plus a few Japanese symbols. Released glyphs stay cached until reused. |
| C heap (newlib malloc) | about 35 KB free in total (0.03 MB in bins, 5-9 KB at the top) | two 8-byte objects per glyph sprite (`GlyphCache_Acquire`, `0x00105068`), about 32 bytes with chunk overhead | 35 KB | `operator new` returns 0 and is not checked | **Bounded by the handles**: 513 × 32 bytes = 16 KB at most, the same bound as the Japanese game. |
| VM object space (`malloc(0x940000)`) | 9.25 MiB | text constants 2 bytes per character (D-027); one `FontChar` object per glyph | 0.26 MB free in this audit, 0.10 MB in D-027 | collect, compact, retry, then `exit(1)` (`0x00112920`) | Margin only. Text constants cost 0.09 MB more than the Japanese at boot. The per-glyph objects are bounded by the handles. No guard can add memory that does not exist. |
| VM object handles (`0x00112c44`) | 155,000 | one per object | about 50,000 spare (D-040) | `0x00113258` retries collection forever | Margin only. Not reachable by text. |

## Script-side buffers

- `Vector` grows on demand: `Vector >> atPut` catches `ArrayIndexOutOfBoundsException`, copies into an array twice the size and stores again. The text queues of `TextWindow` (200), `TextLine` (30), `LogLine` (80), `DeckView >> setName:` (6) and the backlog page lists (3) are Vectors.
- The fixed `Array`s in the text classes are layout tables, not character buffers: `DialogBox` 9 frame parts, `DeckView` 16 cards, `ShioriListItem` 12, `NameEntryEdit` 6 slots, `DeckEdit` 4, `LogPage` 100 pages (indexed modulo 100), and `LogPage >> putLine:`'s 4 fields of one message. None is indexed by character count.
- The message window wraps in the build and starts a new page at run time when the next message does not fit (D-024). A line that is still too long only leaves the box; it does not write past any buffer.

## Save data and native strings

- Save header: 256 bytes. Names are bounded, and the patched `ShioriData >> serialize` shortens its own copy if needed (D-016).
- Save body: 9,984 bytes per slot. It holds no translated text, only the player's names. The issue #9 Day 7 body is 8,397 bytes.
- No native code copies script text into a C buffer (`docs/phase-4-elf-strings.md`). The only native string, the `icon.sys` title, is unchanged.

## Variable-size draw requests

The D-041 sink is 4 KB, and a larger request on a full pool still returns 0. The request sizes:
- Entry +0x08 is called with 1 or 2 quadword counts (sprite and window draws) and from `0x001085f0` with a count capped below 31 (`0x001084b8`): at most 560 bytes.
- Entry +0x18 is called with 80 (`0x00108b1c`) and from `0x001080f0`, a method of the polygon interface (vtable entry `0x002a9368`) whose count comes from its caller.
- Text packets have fixed sizes. Text cannot produce a request larger than the sink.

## Change made: spaces are not drawn (D-042)

- 15.3% of the English characters are spaces (197,021 of 1,286,744 outside control codes). Each one created a blank sprite. It cost a handle, 640 bytes of sprite pool, a glyph cache slot and two draw packets per frame, and showed nothing.
- `TextWindow.putChar.asm` (dialogue) and `LogLine.putChar.asm` (backlog) now advance the cursor for code `0x8540` and create no sprite. Wrapping is unchanged: the wrap test still runs before the space. `fontList`/`fList` are only appended to, faded, moved and erased, never indexed, so a missing entry changes nothing else. Ruby is placed by cursor X, not by list index.
- `TextLine`/`TextLineC` (menus, choices, labels) are unchanged: `setText:` reuses its glyph objects by character index, and these texts are short.

## Measurements (release build, issue #9 Day 7 save, PCSX2)

| Screen | Draw pool free (largest block) | Sprite handles free | Sprite pool free | VM free |
|---|---|---|---|---|
| Main menu | 505 KB | 441 | 333 KB | 0.35 MB |
| Night menu | 444 KB | 377 | 292 KB | 0.32 MB |
| Topic bag editor, scrolling | 56 KB (50 KB) | 272 | 225 KB | 0.27 MB |
| Day 8 dialogue | 452 KB | 397 | 263 KB | 0.27 MB |
| Backlog, short lines, scrolling | 5.6 KB (2.3 KB) | 271 | 224 KB | 0.31 MB |
| Conversation with a portrait, then the backlog | 26 KB (4.9 KB) | 99 | 114 KB | 0.26 MB |
| End of the school day (scene change) | 3.5 KB (1.4 KB) | 407 | 311 KB | 0.32 MB |

Over six rounds of play with the backlog opened each round, the D-041 sink was never written. The draw pool still comes within a few KB of full, and the guard is what keeps a fuller screen from freezing.

## Not changed

- **Pool sizes.** The C heap has about 35 KB free in total, and the other large blocks are the VM object space and picture buffers. There is no free memory to move into the draw pool.
- **Sprite pool null checks.** The 46 constructor sites would each need a code cave, and the handle bound above already keeps text from reaching the pool limit.
- **VM exhaustion.** `exit(1)` stays. The measured margin is 0.10 MB at the lowest, and text does not grow without bound during play.
