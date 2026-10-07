# SCF scripts

Compiled classes of the engine's Smalltalk-like script language. Each member of `SCRIPT.IMG` is one class. Story scenes are classes such as `MAO_TFO`, whose base class is `K2_Script`. The engine library is also SCF: `Array`, `True`, `Compiler*`, `TextWindow`, `BackLog`, and so on.

## Container (LE)

| Field | Encoding |
|---|---|
| Magic | `SCF\x1a` |
| Flags | u8: `0x08` on 13 built-in classes (`Array`, `True`, `System`, ...), otherwise `0x00` |
| Version | u8: `4` |
| Class name, base class name | 2 × (u16 length, Shift-JIS bytes) |
| Fields | u16 n, then n × (u8 id, u16 length, name) |
| Fields 2 | Same layout. In `K2_Script` this holds the character slots (see below) |
| Methods | u16 n, then n × (u16 length, name, u16 argc, u16 code length, bytecode) |
| Methods 2 | Same layout |
| Constants | u16 n, then n × constant |

Constant: u8 type, then a payload.

| Type | Payload | Meaning |
|---|---|---|
| 0, 2, 4 | none | Probably nil / true / false (unconfirmed) |
| 1 | 4 bytes | int32 |
| 3 | 4 bytes | float32 |
| 5 | u16 length + Shift-JIS | Text: dialogue, menu strings, names |
| 6, 7 | u16 length + ASCII | Symbols. Type 7 holds selectors (`:`, `setFace`, `fadeWait`, ...) |
| 8 | u16 k, then k nested constants | Array |

`tools/extract/scf.py` parses and re-serializes all 386 members byte for byte.

### Difference from the Amagami parser

`21-ko/.../scf/parser_scf.py` reads constants until EOF instead of using the count, and treats type 8 as a 2-byte scalar. Because array children follow inline, that still walks every byte without error, which is why the unmodified tool "succeeds" on all 386 KimiKiss files. It loses the array structure, so a reinserter built on it could not rebuild arrays. Our parser fixes both issues.

## Bytecode

Decoded from the interpreter loop `VM_InterpretBytecode` (`0x00115458` in `SLPS_258.50`). `tools/extract/scfdis.py <file.scf> [method...]` disassembles methods with constants, instance-variable names and class-variable names resolved.

Stack values are tagged words: small integer `n` = `(n << 1) | 1`, nil = 0, false = 2, true = 4. "temp" slots hold the arguments first, then the locals. Jump offsets are relative to the opcode's own address.

| Op | Operands | Meaning |
|---|---|---|
| `00` | | padding (aligns u16 operands) |
| `01` | u8 | skips one byte (unused) |
| `02` / `03` | | return self / return top of stack |
| `04` / `05` | | dup / pop |
| `06` / `07` | | `~~` / `==` (identity) |
| `08` / `09` | u8 / u16 const, u8 slot | push class variable `slot` of the class in constant `const` |
| `0A` / `0B` | same | store class variable (pops) |
| `0C` / `0D` | | boolean and / or |
| `10`–`1F` | | `+ - * / % & | ^ = > < >= <= <> -U ~U`. Small integers take a fast path; anything else is sent as a message |
| `20` / `21` | u8 | push / store (pop) instance variable |
| `22` / `23` | u8 | push / store (pop) temp |
| `24` | s8 | push small integer |
| `25`, `26`, `28`, `29` | | push nil, self, true, false |
| `2A` | | push current exception |
| `2B` | | boolean not |
| `30` / `32` | u8 argc, u8 / u16 const | send the selector in constant `const` |
| `31` / `33` | same | send to super |
| `34` | u8 n | call native primitive `n` of the receiver's class |
| `40` / `41` | s8 / s16 | jump |
| `44` / `45` | s8 / s16 | pop; jump if false or nil |
| `50` / `51` | u8 / u16 | push constant |
| `60`–`63` | | raise error |
| `64` / `65` | | `at:` / `at:put:` (inferred from use) |
| `68` | | clear exception |
| `69` | s16 | push exception handler (try), handler at offset |
| `6A` | | pop exception handler |
| `6B` | | throw top of stack |
| `6C` | u8 n | push `n` nils (allocate locals) |
| `6D` | u16 | set line number (debug) |

A displayed line compiles to `08 cc ss` (class variable `ss` of `K2_Script`, the speaker), `50`/`51` text constant, `30 01 <':'>`. Strings are referenced by constant index, never by byte offset, so changing a string's length moves no code.

### Speakers

The receiver of `:` is a `K2_Script` class variable ("fields 2" slot), pushed with opcode `08`:

| Id | Slot | Id | Slot | Id | Slot |
|---|---|---|---|---|---|
| 0x09 | SYS (narration) | 0x11 | NAN | 0x19 | KEI |
| 0x0A | PLY (protagonist) | 0x12 | AKI | 0x1A | EX1 |
| 0x0B | YUM | 0x13 | TOM | 0x1B | EX2 |
| 0x0C | NAR | 0x14 | MEG | 0x1C | ETC |
| 0x0D | MAO | 0x15 | GUN | 0x1D | ETB |
| 0x0E | ASU | 0x16 | KAO | 0x1E | ETG |
| 0x0F | ERI | 0x17 | MAN | | |
| 0x10 | MIT | 0x18 | MIC | | |

Slots 4–8 are `CONFIG`, `BG`, `WIN`, `CAL` and `FG`. `extract_text.py` assigns a speaker to 34,542 of 36,172 text records (95.5%). Most of the rest are data tables: `EventTable`, `NameEntryList`, `StaffRoll`.

## Inline text codes

Text constants mix Shift-JIS with ASCII control codes. `／` (U+FF0F) is a line break. Token counts over all 36,172 extracted records (`#` is a number):

| Code | Tokens | Probable meaning |
|---|---|---|
| `V#` | 18,361 | Voice clip id |
| `W#` | 78,984 | Wait (frames) |
| `Nm`, `Nn` | 2,157 | Protagonist surname / given name |
| `E`, `Ec`, `Eo`, `Eh` | 6,416 | Eyes: blink, close, open, half |
| `F#`, `Fe#`, `Fe#m#`, `Fm#` | 6,207 | Face / expression / mouth |
| `M`, `Mo`, `Mc`, `Mh` | 273 | Mouth |
| `Ti#`, `Ts#`, `T#.#`, `T` | 975 | Text timing / effects |
| `B#`, `Sp`, `P#`, `c#`, `Sd`, `S`, `Br#t#`, `b#`, `As#`, `Bt#`, `m#` | 1,295 | Unknown (shake, blush, ...) |
| `R`, `R#` | 44 | Ruby (furigana): `R<base>R<n><reading>R` |

A few hundred stray ASCII characters remain: typos in the original script (`W` with no digits, a lone `1`), ASCII punctuation, and words in debug or system strings. `extract_text.py` braces each one individually, so the round trip stays lossless whatever they mean.

The parser is `Parson >> message:` (see `docs/phase-3-text-engine.md`). It dispatches on the first letter `W V T F B S E M P A N R` to `inlineComW` … `inlineComR`. Any other code from 59 (`;`) to 255 is dropped. `／` (`0x815E`) is a line break and `｜` (`0x8162`) is a pause ("inter"). The remaining meanings above are still inferred from context.

**Consequence for English:** every single-byte code from 59 up is a control code or dropped, and the window draws only codes above 256. English therefore has to be encoded as double-byte codes. Decision D-012 puts it in the free Shift-JIS rows 9–10.
