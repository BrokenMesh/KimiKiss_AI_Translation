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

**Result.** First pass: 82 of the 109 textures on the fast-model list carried Japanese. The in-game coverage walk then showed many more labels, so the second pass looked at all 551 `GRAPH0` textures (and, at thumbnail scale, every `GRAPH1` and `GRAPH2` texture) by eye. Now **216 `GRAPH0` textures (220 text lines)** are redrawn. The class and text columns of `phase-4-textures.tsv` are unreliable: many readings are wrong (親備室 is 保健室, 水合費 is 校舎裏, entry 386 is 水着), and about half of the Japanese textures were not on it at all. `labels.tsv` was made from the pictures at 3x to 5x.

The other 335 entries (incl. the font and the non-TIM2 entry 396) hold no Japanese UI text: digits and Latin labels (class tags 1-A, 2-A, 2-B, 2-C, 3-C, BGM, SELECT, AUTO, PRESS START Button, ENTERBRAIN), icons, items, portraits, backgrounds, bubbles, frames and gradient bars. Textures that have kanji painted into the art are left alone: 262 (armband), 289 (合格 charm) and the title logo 178 (キミキス), which is a logo rather than a label.

**Check.** `python3 tools/qa/test_graph0_textures.py build/orig/GRAPH/GRAPH0.ARC [build/work/GRAPH0.PAC]`: the 335 untouched entries are byte-identical, every redrawn entry keeps header, palette and size and differs from the original only inside its boxes, the build is deterministic, and the PAC decompresses to the built archive. The test ISO builds. Not yet seen in the emulator.

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
- Still Japanese after the first build (main menu header, はじめから / ひきつぎ / 設定, 振動, 音声, なし, 初期設定に戻す; on the map the non-highlighted tags 図書, 屋上, 1年/2年/3年, 音楽, 家庭, 校庭, 食堂, 保健, the 日め day counter, the 休み1 and 放課後 slots, the ヒント and 設定 button guides, and the panel labels ベッド, 1年廊下): **all are textures in `GRAPH0`** and are now in `labels.tsv`. Every label has separate normal and highlighted textures, and often a third copy for the map panel and the period slots (for example 校庭: 9, 110, 311, 418; 保健: 223 and 336; 設定: 68 button guide, 154 menu item), so each was added by entry. No label of the list is a script string.

## Second inventory (all `GRAPH0`, `GRAPH1`, `GRAPH2`)

- **Added to `GRAPH0` (134 textures):** main menu (メインメニュー 545, はじめから 279, ひきつぎ 278 and 535, 設定 154, ロード 230 and 547, しおり 401, 初期設定に戻す 402, 振動 459, 音声 95, なし 232, 壁紙 102), the seven weekdays (月 219, 火 343, 水 79, 木 423, 金 457, 土 250, 日 21), the day counter 日め (151, "Day"), the period tabs (休み1 269, 放課後 215), the map tags in both states (1年 57 and 411 and 272, 2年 111 and 306 and 384, 3年 358, 図書 171 and 524, 屋上 153 and 513, 音楽 258, 家庭 88 and 283, 校庭 311 and 418, 食堂 60 and 246, 保健 223 and 336, 花壇 119, 体育館 10), the location panel (ベッド 217, 1年廊下 294, 2年廊下 549, 3年廊下 163, 渡り廊下 236, 理科室 273, 音楽室 145, 図書室 406, 家庭科室 440, 準備室 80 and 472, テラス 56, プール 75, 噴水 241, フェンス 507, 本棚 519, 校庭 110), button guides (ヒント 261, 設定 68, 次へ 369, 決定 398, 戻る 44, 削除 206, 消す 125, 移動 100, スクロール 179), action, subject and topic labels (about 60: ダンス, 先生, 化粧, 娯楽, 制服, 微笑む, ほめる, ...), six name plates (栗生 恵, 二見 瑛理子, 里仲 なるみ, 祇条 深月, 水澤 摩央, その他), the hint banners 94, 227, 536 and the "Go to this area?" dialog 304 (three lines). The full list is `labels.tsv`.
- **Naming.** 保健 (map tag, hover tag, period slot: 223, 336, 333) and 保健室 (31) are all "Infirmary"; 花壇 is "Garden", 体育館 "Gym", 校庭 "Schoolyard", 家庭(科室) "Home Ec", 1年/2年/3年 "Year N", the halls "Year N Hall". 保健 as a stat or subject, if one exists, would need its own texture and is not known.
- **Script strings, not textures** (not changed here): the memory-card messages (`SystemSave.json`, for example "MEMORY CARD ... はフォーマットされていません" seen in the coverage walk), `SaveMenu`, `NameEntry` ("メインメニューに戻りますか？") and the staff roll. They are in `text/*.json`.
- **Unresolved: 18 help pages in `GRAPH1`.** Full-screen 640 x 448 tutorial pages with Japanese headings and paragraphs, not touched: マッチング会話 (Matching Conversation) 58, 91, 164, 199, 287, 383, 472, 548, 568; 移動エリア選択 (Area Select) 84, 106, 188, 378, 403, 469, 566; 話題袋 (Topic Bag) 194, 215. They need the paragraphs translated and typeset (a separate job, not a label swap). Also in `GRAPH1`: 386 is a background with the アルバム bubble (top left); `redraw.py` works on `GRAPH0.ARC` only, so it is not done. Shop and sign text inside background art (里なか 72/539/503, カラオケ 376/481/598, 休憩所 337, 134) is painted into the picture and left as is.
- **`GRAPH2`:** character and CG tile sheets only; no Japanese UI text.
- **Small results to look at in game:** the map tags for 校庭 (311, 418) are 10 px ("Schoolyard"); 215 "After School" is 10 px; 351 "Wall/paper" 10 px; 223 and 336 "Infirmary" 12 to 13 px; 459 "Rumble" in 40 x 32. 151 reads "2 Day (Tue)" because the number is a separate sprite left of the word; reordering is a script change.
