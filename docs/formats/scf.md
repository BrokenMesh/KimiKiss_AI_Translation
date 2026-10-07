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

## Bytecode (partial)

Confirmed by matching operands to constant indices across all scripts:

| Bytes | Meaning |
|---|---|
| `50 ii` | Push constant `ii` (u8 index) |
| `51 lo hi` | Push constant (u16 LE index) |
| `30 nn ss` | Send selector constant `ss` with `nn` arguments |
| `08`–`1F` | Push field / slot by id. Used as the receiver of `:` |

A displayed line compiles to `<receiver> <push text> 30 01 <':'>`. Strings are referenced by constant index, never by byte offset, so changing a string's length moves no code.

Other opcodes (`05`, `06`, `0A`–`0D` in other positions, `24`, `26`, `6C`, ...) are not decoded yet.

### Speakers

The receiver of `:` is a `K2_Script` "fields 2" slot:

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

These meanings are inferred from context and have not been verified against the ELF's text parser.

**Consequence for English:** the engine reads ASCII inside text as control codes, so English cannot be inserted as plain ASCII. Phase 3 has to choose an encoding, for example remapped Shift-JIS codepoints rendered by a half-width or variable-width font, or an escape added to the parser.
