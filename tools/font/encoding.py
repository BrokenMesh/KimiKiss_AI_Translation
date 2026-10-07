"""English encoding (decision D-012): printable ASCII <-> Shift-JIS row 9/10 codes.

Character index i = c - 0x20 (0..94). Code = 0x85 << 8 | t, where
t = 0x40 + i for i < 63, else 0x41 + i (trail byte 0x7F does not exist).
"""
FIRST, LAST = 0x20, 0x7E
LEAD = 0x85


def code_of(ch):
    i = ord(ch) - FIRST
    if not 0 <= i <= LAST - FIRST:
        raise ValueError(f'{ch!r} has no English glyph')
    return LEAD << 8 | (0x40 + i if i < 63 else 0x41 + i)


def char_of(code):
    lead, t = code >> 8, code & 0xFF
    if lead != LEAD or not (0x40 <= t <= 0x7E or 0x80 <= t <= 0x9F):
        return None
    i = t - 0x40 if t < 0x7F else t - 0x41
    return chr(FIRST + i)


def glyph_index(code):
    """Same mapping as SjisToGlyphIndex (0x0017f750) in the ELF."""
    lead, t = code >> 8, code & 0xFF
    base = (lead - 0x81) * 188 if lead < 0xE0 else (lead - 0xC1) * 188
    return base + (t - 0x40 if t < 0x7F else t - 0x41)


def encode(text):
    """English text -> Shift-JIS bytes using the custom codes."""
    return b''.join(code_of(ch).to_bytes(2, 'big') for ch in text)
