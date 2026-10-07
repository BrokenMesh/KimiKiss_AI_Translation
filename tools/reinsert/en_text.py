"""English text encoding and word wrap for the dialogue window (D-012, D-013).

Translations keep control codes in braces ({W30}, {Nn}, ...). Outside braces:
  - printable ASCII becomes the custom Shift-JIS codes 0x8540..0x859F;
  - any other character (Japanese, full-width punctuation, the line break
    U+FF0F '／') is encoded as cp932, unchanged from the original engine.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'font'))
import encoding  # noqa: E402

BREAK = '／'
TOKEN = re.compile(r'\{[^{}]*\}|.', re.S)

# Message window geometry (docs/phase-3-text-engine.md)
LINE_PX = 552            # 586 - 2 * 17
INDENT_PX = 115          # putIndent: 5 after a speaker name, 5 * (24 - 1) (D-023; was 4 = 92 px)
PLATE_GAP_PX = 6         # line 1 starts at INDENT_PX, or this far after a wider plate (TextWindow.output0.asm)
FULL_PX = 23             # Japanese advance: fontW 24 + pitchX -1
NAME_PX = 120            # {Nn}/{Nm}: 8 typical English letters (D-016); wider names fall back to the engine overflow wrap


def widths():
    return json.load(open(os.path.join(HERE, '..', 'font', 'en_widths.json')))['widths']


def encode_translation(text):
    out = bytearray()
    for tok in TOKEN.findall(text):
        if tok.startswith('{') and len(tok) > 1:
            out += tok[1:-1].encode('ascii')
        elif ' ' <= tok <= '~':
            out += encoding.code_of(tok).to_bytes(2, 'big')
        else:
            out += tok.encode('cp932')
    return bytes(out)


def token_px(tok, w):
    if tok in ('{Nn}', '{Nm}'):
        return NAME_PX
    if tok.startswith('{') and len(tok) > 1:
        return 0
    if ' ' <= tok <= '~':
        return w[tok]
    return FULL_PX


def wrap(text, first_px=LINE_PX, cont_px=LINE_PX, w=None):
    """Greedy word wrap: replace spaces with '／' so no line exceeds its width.

    Existing '／' breaks are kept. A single word longer than a line is left
    for the engine's per-character overflow wrap.
    """
    w = w or widths()
    toks = TOKEN.findall(text)
    out, line_px, limit = [], 0, first_px
    word, word_px = [], 0

    def flush_word():
        nonlocal line_px, word, word_px
        out.extend(word)
        line_px += word_px
        word, word_px = [], 0

    for tok in toks + [None]:
        if tok is None or tok == ' ' or tok == BREAK:
            if line_px + word_px > limit and out:
                # break before this word: turn the preceding space into a break
                while out and out[-1] == ' ':
                    out.pop()
                out.append(BREAK)
                line_px, limit = 0, cont_px
            flush_word()
            if tok == BREAK:
                out.append(BREAK)
                line_px, limit = 0, cont_px
            elif tok == ' ':
                out.append(' ')
                line_px += w[' ']
        else:
            word.append(tok)
            word_px += token_px(tok, w)
    return ''.join(out)


def line_widths(text, w=None):
    w = w or widths()
    return [sum(token_px(t, w) for t in TOKEN.findall(line)) for line in text.split(BREAK)]
