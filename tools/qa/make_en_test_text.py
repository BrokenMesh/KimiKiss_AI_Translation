#!/usr/bin/env python3
"""Make a text directory with English test lines in the prologue (Phase 3 gate).

Usage: make_en_test_text.py <text_dir> <out_dir>

Copies <text_dir> and sets "translation" on the first narration lines of
PLY_PRO, the scene that runs right after New Game:
  1. a long line word-wrapped by en_text.wrap (word wrap at reinsertion),
  2. one unbroken word wider than the window (engine fallback wrap),
  3. every printable ASCII character (glyph and width check),
  4. English mixed with Japanese and a manual '／' break,
  5. a short line, to compare the backlog.
Phase 4 adds NameEntry:3, the name-entry confirm dialog (centred
TextLineC): narrow and wide letters, to check proportional menu text.
NameEntry:4 is a two-line ConfirmDialog message ('\\n' kept): the box must
follow the pixel width of the longer line (D-017).
GameParam:166/167 and K2_Script:13 are the default surname, given name and name
plate (D-016): English codes: Aihara, Kouichi (glossary D2) and the Aihara plate.
"""
import json
import os
import shutil
import string
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reinsert'))
import en_text  # noqa: E402

LINES = {
    'PLY_PRO:39': en_text.wrap('Summer vacation of my second year of high school was over. A little more '
                               'than a month went by with nothing at all, no new encounters, nothing.{W15}'),
    'PLY_PRO:42': 'Supercalifragilisticexpialidociousandthensomemorelettersuntilitoverflowsthewindow{W15}',
    'PLY_PRO:43': string.printable[:95].replace('{', '').replace('}', '') + '{W15}',
    'PLY_PRO:44': '…I have never been in love. 「キス」？／Kiss... What does a kiss feel like?{W15}',
    'PLY_PRO:45': 'Will time just keep flowing by like this?{W15}',
    'NameEntry:3': 'Use this name? little WWW',
    'NameEntry:4': 'Quit name entry and return\nto the main menu?',
    # Default names (D-016): surname, given name, and the protagonist's name plate.
    'GameParam:166': 'Aihara',
    'GameParam:167': 'Kouichi',
    'K2_Script:13': 'Aihara',
}


def main():
    src, out = sys.argv[1:3]
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(src, out)
    for name in sorted({k.split(':')[0] for k in LINES}):
        path = os.path.join(out, name + '.json')
        recs = json.load(open(path, encoding='utf-8'))
        for r in recs:
            if r['id'] in LINES:
                r['translation'] = LINES[r['id']]
                print(r['id'], en_text.line_widths(LINES[r['id']]), LINES[r['id']])
        json.dump(recs, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
