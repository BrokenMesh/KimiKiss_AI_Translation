#!/usr/bin/env python3
"""Replace the Japanese text in GRAPH0.ARC textures with English (D-019).

Usage: redraw.py <GRAPH0.ARC> <out_dir> [--preview DIR] [--debug] [--only N,N,...]

For every label in labels.tsv the original TIM2 entry is decoded, the Japanese
text is erased, the English text is drawn in the same style and the picture is
re-quantized to the texture's own palette. Palette, size and every pixel
outside the text boxes stay as they were, so the new TIM2 has the same length
and the ARC offsets do not move.

Inputs (both tracked, neither contains image data):
  labels.tsv  entry, japanese, english, notes. "|" in english is a line break.
              Several rows with the same entry are the lines of one texture,
              in the order of layout.tsv's `line` column.
  layout.tsv  entry, line, bg, box, align, opts. Only needed when the label
              is not plain text on a transparent background filling the whole
              texture.
                bg    how the background is told from the text, a comma list of
                      T (alpha 0), mode (the most frequent colour in the box),
                      ring (the colours that make up the box's outline) and
                      rgb:RRGGBB (one palette colour), e.g. "mode,T".
                box   x0,y0,x1,y1 (end exclusive): the area the old text sits
                      in and the new text may use. "auto": the whole
                      texture, or for bg=mode the bounding box of the
                      background colour (a button's interior).
                align t (centre on the old text), c (centre of the box).
                opts  key=value;... : font (Inter weight), smax (largest size
                      in px), xmin/xmax (clip the auto box), fill=RRGGBB (force
                      the fill colour), outline=RRGGBB,.. (ring colours, fill
                      outwards), rings=N (at most N outline rings), squeeze=F (narrowest horizontal
                      squeeze, default 0.85; 1 = never squeeze),
                      style=plain|outline|shadow, shadow=dx,dy.

Method: the pixels in the box that are not background are the old text.
Their style is read from the palette colours: the colour of the thickest part
is the fill, the colours around it are the outline rings, or, when they sit
only on one side, a shadow. The old text is replaced by the nearest background
pixel in the same row (then column). The English text is drawn with Inter at
the largest size that fits (squeezed up to 15 % before the size drops), with
the same outline/shadow, and each pixel is mapped to the nearest colour of the
palette entries the texture already used.

Needs Pillow, numpy and an Inter OTF (system fonts or $INTER_DIR; the font
is licensed under the SIL OFL, see tools/font/LICENSE-Inter.txt).
"""
import itertools
import json
import os
import sys

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit('tools/texture/redraw.py needs Pillow and numpy (pip install pillow numpy)')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', 'extract')]
import arc  # noqa: E402
import tim2  # noqa: E402

FONT_DIRS = [os.environ.get('INTER_DIR', ''), '/usr/share/fonts/opentype/inter',
             '/usr/share/fonts/truetype/inter', os.path.join(HERE, '..', 'font')]
CAP = 0.727            # Inter cap height / em
SQUEEZE = 0.85         # narrowest horizontal squeeze before the size drops


def font_file(weight):
    for d in FONT_DIRS:
        p = os.path.join(d, f'Inter-{weight}.otf') if d else ''
        if p and os.path.exists(p):
            return p
    raise SystemExit(f'Inter-{weight}.otf not found (set INTER_DIR)')


def read_tsv(path):
    rows, head = [], None
    for line in open(path, encoding='utf-8').read().split('\n'):
        if not line or line.startswith('#'):
            continue
        cols = line.split('\t')
        if head is None:
            head = cols
            continue
        cols += [''] * (len(head) - len(cols))
        rows.append(dict(zip(head, cols)))
    return rows


def load_labels(path=os.path.join(HERE, 'labels.tsv'), layout=os.path.join(HERE, 'layout.tsv')):
    """-> {entry: [line dict]} with labels joined to their layout."""
    lay = {(int(r['entry']), int(r['line'])): r for r in read_tsv(layout)}
    out = {}
    for r in read_tsv(path):
        e = int(r['entry'])
        n = len(out.setdefault(e, []))
        l = lay.get((e, n), {})
        opts = dict(kv.split('=', 1) for kv in l.get('opts', '').split(';') if kv)
        out[e].append({'entry': e, 'line': n, 'japanese': r['japanese'], 'english': r['english'],
                       'notes': r['notes'], 'bg': l.get('bg', 'T'), 'box': l.get('box', 'auto'),
                       'align': l.get('align', 't') or 't', 'opts': opts})
    return out


# ---------------------------------------------------------------- bitmap helpers

def shift(m, dx, dy):
    """out[y, x] = m[y - dy, x - dx], zero outside."""
    h, w = m.shape
    out = np.zeros_like(m)
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = \
        m[max(-dy, 0):h + min(-dy, 0), max(-dx, 0):w + min(-dx, 0)]
    return out


def dilate(m, d, kind='cheb'):
    """Binary or grey dilation; 'round' leaves out the far corners (pixel-art outline)."""
    offs = [(i, j) for i in range(-d, d + 1) for j in range(-d, d + 1)
            if kind == 'cheb' or i * i + j * j <= d * d + d]
    out = m.copy()
    for i, j in offs:
        out = np.maximum(out, shift(m, i, j))
    return out


def depth_map(n):
    """Chebyshev distance of every True pixel to the nearest False pixel (outside = False)."""
    p = np.pad(n, 1)
    depth = np.zeros(p.shape, int)
    cur, k = p.copy(), 1
    while cur.any():
        inner = cur.copy()
        for i, j in itertools.product((-1, 0, 1), repeat=2):
            if i or j:
                inner &= shift(cur, i, j)
        depth[cur & ~inner] = k
        cur, k = inner, k + 1
    return depth[1:-1, 1:-1]


# ---------------------------------------------------------------- texture model

class Tex:
    def __init__(self, blob):
        self.t = tim2.parse(blob)
        t = self.t
        self.w, self.h = t['w'], t['h']
        self.idx = np.frombuffer(t['indices'], np.uint8).reshape(self.h, self.w).copy()
        pal = np.array(t['palette'], float)
        self.rgb = pal[:, :3]
        self.a = np.minimum(pal[:, 3], 128) / 128
        keys = {}
        self.uid_of = np.zeros(len(pal), int)
        for i, (r, g, b, a) in enumerate(t['palette']):
            self.uid_of[i] = keys.setdefault((0, 0, 0, 0) if a == 0 else (r, g, b, min(a, 128)), len(keys))
        used = np.bincount(self.idx.ravel(), minlength=len(pal)) > 0
        self.cand = np.flatnonzero(used)                    # palette entries the picture uses
        clear = [i for i in self.cand if self.a[i] == 0]
        self.clear_idx = int(max(clear, key=lambda i: (self.idx == i).sum())) if clear else None

    def uid(self, sub=None):
        return self.uid_of[self.idx if sub is None else sub]

    def blob(self):
        t = self.t
        return tim2.build(t['header'], self.w, self.h, t['bpp'], t['swizzled'], t['palette'],
                          self.idx.tobytes())

    def to_image(self, scale=1, bgcol=(96, 96, 112)):
        rgba = np.zeros((self.h, self.w, 4))
        rgba[..., :3] = self.rgb[self.idx]
        al = self.a[self.idx]
        base = np.array(bgcol, float)
        rgb = rgba[..., :3] * al[..., None] + base * (1 - al[..., None])
        im = Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8), 'RGB')
        return im.resize((self.w * scale, self.h * scale), Image.NEAREST) if scale != 1 else im


# ---------------------------------------------------------------- analysis

def background_mask(tex, spec, box):
    x0, y0, x1, y1 = box
    sub = tex.idx[y0:y1, x0:x1]
    uid = tex.uid(sub)
    alpha0 = tex.a[sub] == 0
    bg = np.zeros(sub.shape, bool)
    for part in spec.split(','):
        part = part.strip()
        if part == 'T':
            bg |= alpha0
        elif part == 'mode':
            vals, cnt = np.unique(uid[~alpha0], return_counts=True)
            if len(vals):
                bg |= uid == vals[cnt.argmax()]
        elif part.startswith('rgb:'):
            want = np.array([int(part[4 + i:6 + i], 16) for i in (0, 2, 4)])
            bg |= (np.abs(tex.rgb[sub] - want).sum(-1) <= 6) & ~alpha0
        elif part == 'ring':
            edge = np.zeros(sub.shape, bool)
            edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
            vals, cnt = np.unique(uid[edge], return_counts=True)
            for v, c in zip(vals, cnt):
                if c >= 0.05 * edge.sum():
                    bg |= uid == v
        else:
            raise ValueError(f'bad bg spec {part!r}')
    return bg


def auto_box(tex, line):
    if line['box'] != 'auto':
        box = [int(v) for v in line['box'].split(',')]
    elif 'mode' in line['bg']:
        uid = tex.uid()
        opaque = tex.a[tex.idx] > 0
        vals, cnt = np.unique(uid[opaque], return_counts=True)
        ys, xs = np.nonzero(uid == vals[cnt.argmax()])
        box = [xs.min(), ys.min(), xs.max() + 1, ys.max() + 1]
    else:
        box = [0, 0, tex.w, tex.h]
    if 'xmax' in line['opts']:
        box[2] = int(line['opts']['xmax'])
    if 'xmin' in line['opts']:
        box[0] = int(line['opts']['xmin'])
    return [int(v) for v in box]


def analyse(tex, box, bg, opts=None):
    """Read the old text's style from the pixels that are not background.

    Returns a dict: n (text mask), fill (rgb, alpha), fill_bbox, text_bbox, outline (ring
    colours from the fill outwards), shadow ((dx, dy), colour) or None.
    """
    x0, y0, x1, y1 = box
    sub = tex.idx[y0:y1, x0:x1]
    uid = tex.uid(sub)
    n = ~bg
    info = {'n': n, 'outline': [], 'shadow': None}
    if not n.any():
        return info
    ys, xs = np.nonzero(n)
    info['text_bbox'] = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    solid = n & (tex.a[sub] >= 0.99)
    depth = depth_map(n)
    deep = max(1, round(0.6 * depth.max()))
    pool = solid & (depth >= deep)
    if not pool.any():
        pool = solid if solid.any() else n
    vals, cnt = np.unique(uid[pool], return_counts=True)
    fill_uid = vals[cnt.argmax()]
    forced = None
    if opts and 'fill' in opts:                 # forced fill colour, e.g. fill=ffffff
        forced = np.array([int(opts['fill'][i:i + 2], 16) for i in (0, 2, 4)], float)
        cand = np.unique(uid[solid])
        fill_uid = min(cand, key=lambda u: np.linalg.norm(tex.rgb[sub[solid & (uid == u)][0]] - forced))
    fset = n & (uid == fill_uid) & solid
    fi = sub[fset][0]
    fill = tex.rgb[fi]
    if forced is not None and np.linalg.norm(fill - forced) > 30:
        fill = forced                            # the colour is not in the text (it is the background)
    info['fill'] = (tuple(fill), 1.0 if forced is not None else float(tex.a[fi]))
    fy, fx = np.nonzero(fset)
    info['fill_bbox'] = (fx.min(), fy.min(), fx.max() + 1, fy.max() + 1)
    if opts and 'outline' in opts:               # explicit ring colours, fill outwards
        info['outline'] = [tuple(float(int(c[i:i + 2], 16)) for i in (0, 2, 4)) for c in opts['outline'].split(',')]
        k = len(info['outline'])
        tb = info['text_bbox']
        info['fill_bbox'] = (tb[0] + k, tb[1] + k, tb[2] - k, tb[3] - k)
        return info
    # solid pixels that merely blend the fill into an opaque background are anti-aliasing
    blend = np.zeros(n.shape, bool)
    bgv = np.unique(uid[bg & (tex.a[sub] > 0)]) if bg.any() else []
    for v in bgv:
        pix = sub[bg & (uid == v)][0]
        seg = tex.rgb[pix] - fill
        rgb = tex.rgb[sub]
        t = np.clip(((rgb - fill) @ seg) / max(1.0, seg @ seg), 0, 1)
        dist = np.linalg.norm(rgb - (fill + t[..., None] * seg), axis=-1)
        blend |= dist < 45
    valid = n & solid & ~fset & ~blend
    prev, shadow_cols, out_cols, base = fset, [], [], fset
    info['back'] = []
    for d in range(1, 6):
        grown = dilate(prev, 1)
        ring = grown & ~prev & valid
        inner = prev
        prev = grown
        if ring.sum() < 6:
            break
        v, c = np.unique(uid[ring], return_counts=True)
        pix = sub[ring & (uid == v[c.argmax()])][0]
        colour = tuple(tex.rgb[pix])
        rf = shift(inner, -1, 0) | shift(inner, 0, -1) | shift(inner, -1, -1)
        back = (ring & rf).sum() / ring.sum()
        info['back'].append(round(float(back), 2))
        if back < 0.2:
            shadow_cols.append(colour)
        elif not shadow_cols:
            out_cols.append(colour)
            base = grown
        else:
            break
    if depth_map(fset).max() <= 1:             # thin strokes cannot carry a thick outline
        out_cols = out_cols[:1]
    info['outline'] = out_cols
    if shadow_cols:
        sh_pix = valid & ~base
        best, off = 0.1, (1, 1)
        for dx, dy in [(1, 1), (1, 0), (0, 1), (2, 2), (2, 1), (1, 2), (2, 0), (0, 2), (3, 3), (0, 3), (3, 0)]:
            m = max(abs(dx), abs(dy))
            ext = np.zeros_like(fset)
            for k in range(1, m + 1):
                ext |= shift(base, round(k * dx / m), round(k * dy / m))
            ext &= ~base
            iou = (ext & sh_pix).sum() / max(1, (ext | sh_pix).sum())
            if iou > best + 1e-9:
                best, off = iou, (dx, dy)
        info['shadow'] = (off, shadow_cols[0])
    return info


# ---------------------------------------------------------------- erase

def erase(tex, box, bg, n):
    """Replace the text pixels by the nearest background pixel in their row, then column."""
    x0, y0, x1, y1 = box
    h, w = n.shape
    sub = tex.idx[y0:y1, x0:x1].copy()
    out = sub.copy()
    ext = 3
    mixed = rows = 0
    dom = None
    if bg.any():
        v, c = np.unique(sub[bg], return_counts=True)
        dom = v[c.argmax()]
    elif tex.clear_idx is not None:
        dom = tex.clear_idx
    for y in range(h):
        xs = np.flatnonzero(n[y])
        if not len(xs):
            continue
        rows += 1
        left_ok = np.flatnonzero(bg[y])
        for x in xs:
            cand = []
            ls = left_ok[left_ok < x]
            rs = left_ok[left_ok > x]
            if len(ls):
                cand.append((x - ls[-1], sub[y, ls[-1]]))
            if len(rs):
                cand.append((rs[0] - x, sub[y, rs[0]]))
            if not cand:
                # no background in this row: look in the column, then just outside the box
                cs = np.flatnonzero(bg[:, x])
                up, dn = cs[cs < y], cs[cs > y]
                if len(up):
                    cand.append((y - up[-1], sub[up[-1], x]))
                if len(dn):
                    cand.append((dn[0] - y, sub[dn[0], x]))
            if not cand:
                src = tex.idx[y0 + y, x0 - 1] if x0 > 0 else (tex.idx[y0 + y, x1] if x1 < tex.w else dom)
                cand.append((99, src))
            out[y, x] = min(cand, key=lambda t: t[0])[1]
        if len(ls := left_ok[left_ok < xs[0]]) and len(rs := left_ok[left_ok > xs[-1]]):
            if tex.uid_of[sub[y, ls[-1]]] != tex.uid_of[sub[y, rs[0]]]:
                mixed += 1
    return out, (mixed / rows if rows else 0.0)


# ---------------------------------------------------------------- drawing

def render_mask(lines, weight, size, squeeze):
    font = ImageFont.truetype(font_file(weight), size)
    pitch = round(size * 1.12)
    base0 = int(size * 1.3)
    wmax = int(max(font.getlength(s) for s in lines)) + 8
    img = Image.new('L', (wmax, base0 + pitch * len(lines) + int(size)), 0)
    dr = ImageDraw.Draw(img)
    for k, s in enumerate(lines):
        dr.text((4, base0 + k * pitch), s, font=font, fill=255, anchor='ls')
    if squeeze < 1:
        img = img.resize((max(1, round(img.width * squeeze)), img.height), Image.BILINEAR)
    arr = np.asarray(img, float) / 255
    ys, xs = np.nonzero(arr > 0.04)
    return arr, (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1), base0, pitch


def paint(dst_rgb, dst_a, rgb, cov):
    out_a = cov + dst_a * (1 - cov)
    safe = np.where(out_a > 0, out_a, 1)
    out = (np.array(rgb, float) * cov[..., None] + dst_rgb * (dst_a * (1 - cov))[..., None]) / safe[..., None]
    return out, out_a


def nearest_palette(t_rgb, t_a, cp_rgb, cp_a, chunk=2048):
    """Nearest palette colour for each target colour.

    t_rgb (n, 3) in 0..255 and t_a (n,) in 0..1; cp_* the same for the
    candidates. Distance = squared difference of the premultiplied RGB plus
    0.6 x (255 x alpha difference)^2. -> (index into the candidates (n,),
    distance (n,)). Chunked so a whole picture of distinct colours fits in memory.
    """
    pick = np.zeros(len(t_a), int)
    dist = np.zeros(len(t_a))
    cp = (cp_rgb * cp_a[:, None])[None]
    for i in range(0, len(t_a), chunk):
        r, a = t_rgb[i:i + chunk], t_a[i:i + chunk]
        d2 = (((r * a[:, None])[:, None, :] - cp) ** 2).sum(-1)
        d2 += (255 * (a[:, None] - cp_a[None])) ** 2 * 0.6
        pick[i:i + chunk] = d2.argmin(1)
        dist[i:i + chunk] = d2.min(1)
    return pick, np.sqrt(dist)


def draw_text(tex, box, idx_sub, info, line, report):
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    lines = line['english'].split('|')
    opts = line['opts']
    style = opts.get('style', 'auto')
    outline = info['outline'] if style in ('auto', 'outline') else []
    shadow = info['shadow'] if style in ('auto', 'shadow') else None
    if 'shadow' in opts:
        dx, dy = (int(v) for v in opts['shadow'].split(','))
        shadow = ((dx, dy), shadow[1] if shadow else (9, 9, 9))
    fill_rgb, fill_a = info['fill']
    weight = opts.get('font') or ('Bold' if outline or shadow else 'SemiBold')
    fb = info['fill_bbox']
    hf = fb[3] - fb[1]
    tb = info['text_bbox']
    if len(lines) > 1:
        smax = float(opts.get('smax', max(9, (tb[3] - tb[1]) / len(lines))))
    else:
        smax = float(opts.get('smax', max(9, 1.15 * hf)))

    def geometry(size):
        scale = min(1.0, size / smax)       # outline and shadow thin out with the text
        depth = max(1, min(round(len(outline) * scale), int(size // 8), int(opts.get('rings', 9)))) if outline else 0
        sh = None
        if shadow:
            (dx, dy), _ = shadow
            m = max(abs(dx), abs(dy))
            k = max(1, round(m * scale))
            sh = (round(dx * k / m), round(dy * k / m), k)
        sdx, sdy = (sh[0], sh[1]) if sh else (0, 0)
        return depth, sh, (depth + max(0, -sdx), depth + max(0, sdx), depth + max(0, -sdy), depth + max(0, sdy))

    chosen = None
    size = smax
    while size >= 6:
        depth, sh, (pl, pr, pt, pb) = geometry(size)
        arr, ink, base0, pitch = render_mask(lines, weight, size, 1.0)
        iw, ih = ink[2] - ink[0], ink[3] - ink[1]
        if ih <= bh - pt - pb:
            k = (bw - pl - pr - 2) / iw
            if k >= float(opts.get('squeeze', SQUEEZE)):
                chosen = (size, min(1.0, k))
                break
        size -= 0.5
    if chosen is None:
        chosen = (6.0, SQUEEZE)
        report['flags'].append('does not fit at 6 px')
    size, sq = chosen
    depth, sh, (pl, pr, pt, pb) = geometry(size)
    arr, ink, base0, pitch = render_mask(lines, weight, size, sq)
    iw, ih = ink[2] - ink[0], ink[3] - ink[1]
    if size < 0.5 * smax or size < 9:
        report['flags'].append(f'small text ({size:.1f} px)')
    report.update(size=size, squeeze=round(sq, 2), weight=weight, outline=depth,
                  shadow=sh and sh[:2])
    cx = (x0 + (tb[0] + tb[2]) / 2) if line['align'] == 't' else (x0 + x1) / 2
    cy = y0 + (fb[1] + fb[3]) / 2 if line['align'] == 't' else (y0 + y1) / 2
    cap = size * CAP
    base_y = cy + cap / 2 - (len(lines) - 1) * pitch / 2
    ox = int(round(cx - (ink[0] + ink[2]) / 2))
    oy = int(round(base_y - base0))
    ox = min(max(ox, x0 + pl + 1 - ink[0]), x1 - pr - 1 - ink[2])
    oy = min(max(oy, y0 + pt - ink[1]), y1 - pb - ink[3])
    cov = np.zeros((bh, bw))
    ah, aw = arr.shape
    sx0, sy0 = ox - x0, oy - y0
    cx0, cy0 = max(0, -sx0), max(0, -sy0)
    cx1, cy1 = min(aw, bw - sx0), min(ah, bh - sy0)
    cov[sy0 + cy0:sy0 + cy1, sx0 + cx0:sx0 + cx1] = arr[cy0:cy1, cx0:cx1]
    cov = np.minimum(1.0, cov * 1.3)           # crisper strokes at UI sizes
    rgb = np.zeros((bh, bw, 3))
    rgb[:] = tex.rgb[idx_sub]
    al = tex.a[idx_sub].copy()
    touched = np.zeros((bh, bw), bool)
    if sh:
        base_cov = dilate(cov, depth, 'round') if depth else cov
        sdx, sdy, k = sh
        scov = np.zeros_like(cov)
        for j in range(1, k + 1):
            scov = np.maximum(scov, shift(base_cov, round(j * sdx / k), round(j * sdy / k)))
        rgb, al = paint(rgb, al, shadow[1], scov)
        touched |= scov > 0.02
    for d in range(depth, 0, -1):
        rcov = dilate(cov, d, 'round')
        rgb, al = paint(rgb, al, outline[min(d, len(outline)) - 1], rcov)
        touched |= rcov > 0.02
    rgb, al = paint(rgb, al, fill_rgb, cov * fill_a)
    touched |= cov > 0.02
    # quantize to the palette entries the texture uses
    cand = tex.cand
    cp_rgb, cp_a = tex.rgb[cand], tex.a[cand]
    ys, xs = np.nonzero(touched)
    t_rgb, t_a = rgb[ys, xs], al[ys, xs]
    pick = cand[nearest_palette(t_rgb, t_a, cp_rgb, cp_a)[0]]
    clear = tex.clear_idx
    if clear is not None:
        pick = np.where(t_a < 0.02, clear, pick)
    out = idx_sub.copy()
    out[ys, xs] = pick
    inside = (ox + ink[0] >= x0 and ox + ink[2] <= x1 and oy + ink[1] >= y0 and oy + ink[3] <= y1)
    if not inside:
        report['flags'].append('clipped by the box')
    return out


# ---------------------------------------------------------------- one texture

def redraw_texture(blob, lines, debug=None):
    tex = Tex(blob)
    reports = []
    for line in lines:
        box = auto_box(tex, line)
        x0, y0, x1, y1 = box
        rep = {'entry': line['entry'], 'line': line['line'], 'english': line['english'],
               'box': box, 'flags': []}
        bg = background_mask(tex, line['bg'], box)
        info = analyse(tex, box, bg, line['opts'])
        if not info['n'].any():
            rep['flags'].append('no text found in the box')
            reports.append(rep)
            continue
        if debug is not None:
            debug.append((box, info['n']))
        rep['bg_share'] = round(float(bg.mean()), 2)
        if bg.mean() < 0.15:
            rep['flags'].append('background covers under 15 % of the box (art-heavy)')
        erased, mixed = erase(tex, box, bg, info['n'])
        rep['mixed_rows'] = round(mixed, 2)
        if mixed > 0.3:
            rep['flags'].append(f'background differs left/right on {mixed:.0%} of text rows')
        out = draw_text(tex, box, erased, info, line, rep)
        tex.idx[y0:y1, x0:x1] = out
        reports.append(rep)
    new = tex.blob()
    if len(new) != len(blob):
        raise ValueError('redrawn TIM2 changed size')
    return new, reports


# ---------------------------------------------------------------- driver

def redraw_arc(arc_data, entries=None, preview=None, debug=False, skip=()):
    """-> ({entry: new TIM2 bytes}, [reports]); entries in `skip` (hand-made overrides) are left out."""
    labels = load_labels()
    a = arc.parse(arc_data)
    new, reports = {}, []
    for e, lines in sorted(labels.items()):
        if (entries and e not in entries) or e in skip:
            continue
        ent = a['entries'][e]
        blob = arc_data[ent['offset']:ent['offset'] + ent['size']]
        dbg = [] if debug else None
        out, rep = redraw_texture(blob, lines, dbg)
        new[e] = out
        reports += rep
        if preview:
            save_preview(preview, e, blob, out, lines, rep, dbg)
    return new, reports


def save_preview(directory, e, old, new, lines, reports, dbg):
    os.makedirs(directory, exist_ok=True)
    a, b = Tex(old), Tex(new)
    sc = 3 if a.w <= 200 else 2 if a.w <= 330 else 1
    ia, ib = a.to_image(sc), b.to_image(sc)
    if dbg:
        dr = ImageDraw.Draw(ia, 'RGBA')
        for box, n in dbg:
            dr.rectangle([box[0] * sc, box[1] * sc, box[2] * sc - 1, box[3] * sc - 1], outline=(255, 0, 0, 255))
            ys, xs = np.nonzero(n)
            for y, x in zip(ys, xs):
                dr.rectangle([(box[0] + x) * sc, (box[1] + y) * sc, (box[0] + x + 1) * sc - 1,
                              (box[1] + y + 1) * sc - 1], fill=(255, 0, 255, 90))
    pad = 14
    img = Image.new('RGB', (ia.width * 2 + 3 * 8, ia.height + pad + 8), (28, 28, 32))
    img.paste(ia, (8, pad))
    img.paste(ib, (ia.width + 16, pad))
    flags = '; '.join(f for r in reports for f in r['flags'])
    text = f"{e}  {' / '.join(l['japanese'] for l in lines)} -> {' / '.join(l['english'] for l in lines)}"
    if flags:
        text += f'   [{flags}]'
    ImageDraw.Draw(img).text((8, 1), text, fill=(255, 255, 0) if flags else (200, 255, 200))
    img.save(os.path.join(directory, f'GRAPH0_{e:04d}.png'))


def make_sheets(directory, per=14, width=1500):
    """Stack the per-texture previews into sheet_NN.png (flagged ones are labelled in yellow)."""
    files = sorted(f for f in os.listdir(directory) if f.startswith('GRAPH0_') and f.endswith('.png'))
    for old in os.listdir(directory):
        if old.startswith('sheet_'):
            os.remove(os.path.join(directory, old))
    for n, i in enumerate(range(0, len(files), per)):
        ims = [Image.open(os.path.join(directory, f)) for f in files[i:i + per]]
        x = y = rh = 0
        pos = []
        for im in ims:
            if x + im.width > width:
                x, y, rh = 0, y + rh + 6, 0
            pos.append((im, x, y))
            x += im.width + 6
            rh = max(rh, im.height)
        sheet = Image.new('RGB', (width, y + rh), (10, 10, 10))
        for im, px, py in pos:
            sheet.paste(im, (px, py))
        sheet.save(os.path.join(directory, f'sheet_{n:02d}.png'))


def main():
    args = sys.argv[1:]
    opts = {'--preview': None, '--only': None}
    debug = '--debug' in args
    args = [a for a in args if a != '--debug']
    for k in opts:
        if k in args:
            i = args.index(k)
            opts[k] = args[i + 1]
            del args[i:i + 2]
    if len(args) != 2:
        sys.exit(__doc__)
    src, out_dir = args
    only = {int(v) for v in opts['--only'].split(',')} if opts['--only'] else None
    new, reports = redraw_arc(open(src, 'rb').read(), only, opts['--preview'], debug)
    if opts['--preview']:
        make_sheets(opts['--preview'])
    os.makedirs(out_dir, exist_ok=True)
    for e, blob in new.items():
        with open(os.path.join(out_dir, f'{e:04d}.tm2'), 'wb') as f:
            f.write(blob)
    with open(os.path.join(out_dir, 'report.json'), 'w') as f:
        json.dump(reports, f, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    flagged = {r['entry'] for r in reports if r['flags']}
    print(f'{len(new)} textures redrawn, {len(flagged)} flagged')


if __name__ == '__main__':
    main()
