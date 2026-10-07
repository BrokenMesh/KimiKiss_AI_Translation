# Phase 4: text in textures

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
- Redrawing: `GRAPH0` entries are rewritten in place by the same path as the font (entry 77, `tools/font/apply_en_font.py`), so a texture editor only needs to keep each texture's size and palette.
