# Phase 4: text in textures

The first inventory (`phase-4-textures.tsv`, a fast-model triage) has many misread labels; `tools/texture/labels.tsv` (read at 3–5× zoom) supersedes it for text and translations.

Inventory made by exporting every TIM2 texture (`tools/extract/tim2.py`, `arc.py`) to PNG and triaging contact sheets (20 tiles per sheet) by eye. The per-texture list is `phase-4-textures.tsv` (file, size, class, visible text, note).

| Archive | Textures | With Japanese text |
|---|---|---|
| `GRAPH0.ARC` | 551 | 109 |
| `GRAPH1.ARC` | 599 | 0 |
| `GRAPH2.ARC` | 988 | 0 |

- All hits are in `GRAPH0`: UI labels (locations such as 体育館, 花壇; periods such as 昼休み; subjects such as 理科; actions such as 手を握る; menu items such as 文字速度, はい/いいえ, 次へ進む/決定).
- `GRAPH1` and `GRAPH2` are backgrounds, event CG tiles and sprite sheets. A spot check of a `GRAPH2` sheet confirmed CG tiles only.
- Triage was done at thumbnail scale by a fast model, so very small text can be missed. The Phase 4 coverage pass (screenshots of every screen) is the backstop.
- Classes: TEXT = UI text to redraw in English; UNSURE = check by hand. No texture was classed as ART (text drawn into a picture).
- Redrawing: `GRAPH0` entries are rewritten in place together with the font (entry 77) by `tools/texture/apply_graph0.py`; see "Redrawing" below.

## Redrawing (D-019)

`tools/texture/redraw.py` replaces the Japanese text in the `GRAPH0` textures during the build; `tools/texture/apply_graph0.py` writes the font (entry 77) and the redrawn textures into `GRAPH0.ARC`/`PAC` in one pass (`tools/build/build.sh` calls it). No image data is tracked: the build redraws from the original archive that it extracts from the verified ISO.

**Inputs** (tracked, text only):

- `tools/texture/labels.tsv`: `entry` (GRAPH0 index), `japanese`, `english`, `notes`. `|` in `english` is a line break. Several rows with one entry are the lines of one texture. `REVIEW` in the notes marks an uncertain translation, `CHECK-ART` a result that needs a look.
- `tools/texture/layout.tsv`: only for textures that are not plain text on a transparent background. Per line: how the background is told from the text (`bg`), the box the old text sits in and the new text may use (`box`), alignment, and options (font weight, largest size, forced fill colour, outline colours, shadow). Columns are described in the header of `redraw.py`.

**Method**, per label:

1. Text pixels are the pixels of the box that are not background (`T` = alpha 0, `mode` = the most frequent colour, `rgb:` = named palette colours, `ring` = colours of the box outline).
2. The style is read from them: the fill colour is the colour of the thickest part; opaque colours around it form the outline rings (outermost last) unless they sit only on the lower right, then they are a shadow. Pixels that only blend the fill into an opaque background are ignored. Strokes thinner than 3 px keep one ring.
3. The old text is erased by copying the nearest background pixel in the same row, then the same column. The ratio of text rows whose left and right background differ is reported (`mixed_rows`); above 30 % it is flagged as a gradient or art background.
4. The English text is drawn with Inter (Bold with outline or shadow, SemiBold without; BoldItalic for the level-up oval) at the largest size at which it fits the box, starting at 1.15 x the height of the Japanese fill. The text may be squeezed horizontally by up to 15 % before the size drops. Outline and shadow thin out with the size. The text is centred on the old text, and the ink stays inside the box.
5. Every touched pixel is mapped to the nearest colour (premultiplied RGB plus alpha) of the palette entries the texture already uses. The palette, the size, the header and all pixels outside the boxes are unchanged, so the TIM2 has the same length and no ARC offset moves.

**Result.** 82 of the 109 textures carry Japanese text and are redrawn (84 text lines). The other 27 hold no Japanese: digits (55, 332, 378, 379, 394, 502), Latin class labels (352, 489, 493, 364), art (24, 62, 353, 430, 439, 492, 368, 15), bars, frames and arrows (346, 365, 442, 363, 397, 381, 391, 39, 434). The class and text columns of `phase-4-textures.tsv` are unreliable (from a thumbnail pass): many readings are wrong, for example 親備室 is 保健室, 水合費 is 校舎裏, 菜々 in entry 386 is 水着, 345 is a memo label. `labels.tsv` was made from the pictures themselves at 3x to 5x.

**Check.** `python3 tools/qa/test_graph0_textures.py build/orig/GRAPH/GRAPH0.ARC [build/work/GRAPH0.PAC]`: the 469 untouched entries are byte-identical, every redrawn entry keeps header, palette and size and differs from the original only inside its boxes, the build is deterministic, and the PAC decompresses to the built archive. The test ISO builds. Not yet seen in the emulator.

**Previews.** `python3 tools/texture/redraw.py build/orig/GRAPH/GRAPH0.ARC build/tex_out --preview qa/tex/redraw [--debug] [--only 12,31]` writes one `GRAPH0_NNNN.png` per texture (original left, new right, yellow title = flagged) and `sheet_NN.png` contact sheets. `--debug` shades the detected text pixels and draws the box. `qa/` is not tracked.

**Needs a human** (the automatic flags are only 37 and 453):

| Entry | Problem |
|---|---|
| 453 (LIKE, FRIENDS) | Small italic captions inside heart/note art: the background under the old text is rebuilt from the sides, leaving smears; the captions are legible but ugly. Best redrawn by hand. |
| 28, 376 | The label tab overlaps the border of the panel below it; 376 loses the teal dash that ran under the old text. |
| 433 | "Stylish" in 80 x 32 is heavy and the letters touch. Shorter wording or a hand-set font would help. |
| 351 | "Wall/paper" on two lines at 10 px in a 40 x 32 texture. |
| 37, 336, 392, 449, 477, 481, 436 | Text on plaques is smaller than the kanji (14 to 15 px) but clean. Check against the real UI. |
| 2, 31, 331, 387, 432, 496 | Place names on the orange splash are clean; "Prep Room" (12 px) and "Infirmary" are the smallest. |
| 345, 361, 362, 48, 438 | Reading or meaning uncertain (see `REVIEW`); not an image problem. |

Translation review: names (16, 429, 487, 539) use given name or Hepburn order only as a guess; 354 and 481 say "Garden" for 花壇 so that the map tag fits.

## First in-game check (coverage walk, stopped early)

- The test build boots with `SCRIPT.IMG` and `GRAPH0.PAC` relocated, reaches the title, main menu, name entry and the prologue.
- Redrawn textures show in game on the main menu and settings panel: Continue, Text Speed, Yes, Wall paper, OK, Back.
- Still Japanese on the same screen: the メインメニュー header, the menu items はじめから / ひきつぎ / 設定, and the settings rows 振動, 音声, なし, 初期設定に戻す. They are not in `labels.tsv`, so the first inventory missed them; they need to be located (texture or script string) and added.
