"""CLEAN ROOM: DKR textures drawn by our own code (no pixels from the game).

Everything readable is re-typeset with the project's stroke font in styles of
our own; multi-piece sprites (a word stored as horizontal strips positioned by
sprite-x/y) are drawn once on a shared canvas and cut into their strips.

all_overrides(kept, textures) -> [(relpath, RGBA float image, tag)]
"""
import json
import os

import numpy as np

from cleanroom.gfx import strokefont
from games.dkr import glyphs_dkr  # noqa: F401  (DKR glyph designs)
from games.dkr import sprites as spr
from games.dkr.fonts import _dilate

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ styles

STYLES = {
    # fill top, fill bottom, outline, shadow
    "word": ((255, 240, 70), (240, 60, 30), (120, 0, 60), (20, 0, 30)),
    "gold": ((255, 246, 110), (250, 150, 20), (90, 30, 0), (10, 5, 0)),
    "green": ((210, 255, 120), (40, 190, 60), (10, 60, 110), (0, 10, 20)),
    "white": ((255, 255, 255), (220, 225, 235), (30, 30, 40), (0, 0, 0)),
    "red": ((255, 110, 80), (220, 20, 20), (80, 0, 0), (10, 0, 0)),
    "yellow": ((255, 255, 120), (255, 200, 30), (140, 60, 0), (10, 5, 0)),
    "sign": ((255, 250, 110), (255, 190, 20), (190, 20, 20), (20, 0, 40)),
    "title_red": ((255, 80, 50), (190, 0, 10), (255, 226, 40), (70, 0, 0)),
    "title_blue": ((70, 120, 255), (40, 215, 90), (255, 226, 40), (0, 20, 60)),
}


def _resize(m, w, h):
    """Bilinear resample of a coverage mask to (h, w)."""
    H, W = m.shape
    if H == 0 or W == 0:
        return np.zeros((h, w), np.float32)
    ys = (np.arange(h) + 0.5) * H / h - 0.5
    xs = (np.arange(w) + 0.5) * W / w - 0.5
    y0 = np.clip(np.floor(ys).astype(int), 0, H - 1)
    x0 = np.clip(np.floor(xs).astype(int), 0, W - 1)
    y1, x1 = np.minimum(y0 + 1, H - 1), np.minimum(x0 + 1, W - 1)
    fy = np.clip(ys - y0, 0, 1)[:, None]
    fx = np.clip(xs - x0, 0, 1)[None, :]
    return (m[y0][:, x0] * (1 - fx) + m[y0][:, x1] * fx) * (1 - fy) + (m[y1][:, x0] * (1 - fx) + m[y1][:, x1] * fx) * fy


def text_mask(text, w, h, weight=0.11):
    """Coverage mask (h, w) with `text` stretched to fill the box."""
    if h < 24:
        pass
    rh = max(12, h * 2)
    line = strokefont.render_line(text, rh, aspect=0.95, thickness=max(1.0, rh * weight), gap=rh * 0.08)
    ys, xs = np.nonzero(line > 0.05)
    if not len(xs):
        return np.zeros((h, w), np.float32)
    line = line[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return np.clip(_resize(line, w, h), 0, 1)


def styled(mask_full, style, ow=1, shadow=1, box=None):
    """Paint a coverage mask: shadow, outline, gradient fill. box = (y0, y1)
    rows the gradient spans (defaults to the mask's own extent)."""
    fill0, fill1, oc, sc = (np.asarray(c, np.float32) for c in STYLES[style])
    h, w = mask_full.shape
    img = np.zeros((h, w, 4), np.float32)
    outline = np.clip(_dilate(mask_full, ow), 0, 1) if ow > 0 else mask_full
    if shadow:
        sh = np.zeros_like(outline)
        sh[shadow:, shadow:] = outline[:-shadow, :-shadow]
        img[..., :3] = sc
        img[..., 3] = sh * 230
    a = outline[..., None]
    img[..., :3] = img[..., :3] * (1 - a) + oc * a
    img[..., 3] = np.maximum(img[..., 3], outline * 255)
    ys = np.nonzero(mask_full.max(1) > 0)[0]
    y0, y1 = box or ((ys.min(), ys.max()) if len(ys) else (0, h))
    t = np.clip((np.arange(h, dtype=np.float32) - y0) / max(1, y1 - y0), 0, 1)[:, None, None]
    fill = fill0 * (1 - t) + fill1 * t
    # a bright highlight line in the upper third reads as "shiny"
    fa = np.clip(mask_full * 1.25, 0, 1)[..., None]
    img[..., :3] = img[..., :3] * (1 - fa) + fill * fa
    img[..., 3] = np.maximum(img[..., 3], fa[..., 0] * 255)
    return img


def word_image(text, w, h, style, pad=None, weight=0.11):
    pad = pad if pad is not None else max(1, min(w, h) // 10)
    ow = 1 if h < 24 else 2
    sh = 1 if h < 20 else 2
    inner_w, inner_h = max(1, w - 2 * pad - ow - sh), max(1, h - 2 * pad - ow - sh)
    m = np.zeros((h, w), np.float32)
    m[pad:pad + inner_h, pad:pad + inner_w] = text_mask(text, inner_w, inner_h, weight)
    return styled(m, style, ow, sh)


# ------------------------------------------------------------------ briefs

def briefs():
    return json.load(open(os.path.join(HERE, "hud_text.json"), encoding="utf-8"))


def sprite_canvas(pieces):
    x0 = min(p["x"] for p in pieces)
    y0 = min(p["y"] for p in pieces)
    x1 = max(p["x"] + p["w"] for p in pieces)
    y1 = max(p["y"] + p["h"] for p in pieces)
    return x0, y0, x1 - x0, y1 - y0


def cut(canvas, pieces, x0, y0):
    for p in pieces:
        yield p["rel"], canvas[p["y"] - y0:p["y"] - y0 + p["h"], p["x"] - x0:p["x"] - x0 + p["w"]].copy()


def rocket_box(digit, w, h):
    img = np.zeros((h, w, 4), np.float32)
    img[..., :3] = (215, 20, 20)
    img[..., 3] = 255
    img[:2, :, :3] = img[:, :2, :3] = (255, 230, 60)
    img[-2:, :, :3] = img[:, -2:, :3] = (120, 0, 0)
    t = word_image(digit, w - 4, h - 4, "yellow", pad=1, weight=0.13)
    a = t[..., 3:] / 255.0
    img[2:-2, 2:-2, :3] = img[2:-2, 2:-2, :3] * (1 - a) + t[..., :3] * a
    return img


def rounded_rect(w, h, r):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    dx = np.maximum(0, np.maximum(r - xx, xx - (w - r)))
    dy = np.maximum(0, np.maximum(r - yy, yy - (h - r)))
    return np.clip(r + 0.5 - np.hypot(dx, dy), 0, 1)


def panel(text, w, h, selected=True):
    """Menu option label: a rounded orange panel with white lettering."""
    top, bot, edge = ((255, 200, 70), (225, 110, 10), (255, 245, 170)) if selected else         ((180, 105, 40), (120, 55, 10), (80, 35, 0))
    m = rounded_rect(w, h, min(4, h // 3))
    inner = np.zeros_like(m)
    inner[1:-1, 1:-1] = rounded_rect(w - 2, h - 2, min(3, h // 3))
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    img = np.zeros((h, w, 4), np.float32)
    img[..., :3] = np.asarray(edge, np.float32)
    fill = np.asarray(top, np.float32) * (1 - t) + np.asarray(bot, np.float32) * t
    a = inner[..., None]
    img[..., :3] = img[..., :3] * (1 - a) + fill * a
    img[..., 3] = m * 255
    tw = word_image(text, w - 4, h - 4, "white", pad=1, weight=0.12)
    ta = tw[..., 3:] / 255.0
    img[2:-2, 2:-2, :3] = img[2:-2, 2:-2, :3] * (1 - ta) + tw[..., :3] * ta
    return img


def sign(text, w, h, bg=((70, 50, 190), (30, 20, 110)), border=(250, 210, 40), style="sign"):
    """A framed track/name sign: gradient panel, yellow rim, lettering on one
    or two lines (split at the middle space when that reads bigger)."""
    img = np.zeros((h, w, 4), np.float32)
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    img[..., :3] = np.asarray(bg[0], np.float32) * (1 - t) + np.asarray(bg[1], np.float32) * t
    img[..., 3] = 255
    r = max(1, h // 16)
    for sl in ((slice(0, r), slice(None)), (slice(h - r, h), slice(None)), (slice(None), slice(0, r)), (slice(None), slice(w - r, w))):
        img[sl[0], sl[1], :3] = border
    words = text.split(" ")
    lines = [text]
    if len(words) > 1 and len(text) * h / 2 > w * 1.1:
        k = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
        lines = [" ".join(words[:k]), " ".join(words[k:])]
    ih, iw = h - 2 * r - 2, w - 2 * r - 2
    lh = ih // len(lines)
    for i, line in enumerate(lines):
        tw = word_image(line, iw, lh, style, pad=1, weight=0.1)
        a = tw[..., 3:] / 255.0
        y = r + 1 + i * lh
        img[y:y + lh, r + 1:r + 1 + iw, :3] = img[y:y + lh, r + 1:r + 1 + iw, :3] * (1 - a) + tw[..., :3] * a
    return img


def title_logo(w=160, h=64):
    """Our own two-line logo: DIDDY KONG over RACING (a star in the O)."""
    img = np.zeros((h, w, 4), np.float32)
    top_h = int(h * 0.52)
    for text, style, y0, y1, x0, x1 in (("DIDDY KONG", "title_red", 1, top_h, 1, w - 1),
                                        ("RACING", "title_blue", top_h - 2, h - 1, int(w * 0.16), int(w * 0.84))):
        m = np.zeros((h, w), np.float32)
        m[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = text_mask(text, x1 - x0 - 4, y1 - y0 - 4, 0.085)
        layer = styled(m, style, ow=2, shadow=2)
        a = layer[..., 3:] / 255.0
        img[..., :3] = img[..., :3] * (1 - a) + layer[..., :3] * a
        img[..., 3] = np.maximum(img[..., 3], layer[..., 3])
    return img


def star_tile(w, h, bg):
    """A yellow five-point star on a coloured tile (banner ends)."""
    import math
    img = np.zeros((h, w, 4), np.float32)
    img[..., :3] = bg
    img[..., 3] = 255
    pts = []
    for k in range(10):
        r = 0.42 if k % 2 == 0 else 0.18
        a = math.radians(-90 + 36 * k)
        pts.append((0.5 + r * math.cos(a), 0.52 + r * math.sin(a)))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xs, ys = (xx + 0.5) / w, (yy + 0.5) / h
    inside = np.zeros((h, w), bool)
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        cond = ((yi > ys) != (yj > ys)) & (xs < (xj - xi) * (ys - yi) / (yj - yi + 1e-9) + xi)
        inside ^= cond
        j = i
    img[inside, :3] = (255, 220, 40)
    return img


BANNERS = {"orange": [220, 50, 30], "orange2": [220, 50, 30], "green": [40, 160, 60],
           "snowy": [50, 110, 220], "snowy2": [50, 110, 220]}


def banners(sizes):
    """START banners over the finish line: tiles _1 and _2 carry the word."""
    for v, bg in BANNERS.items():
        base = "textures/3d/common/finish_line_flag_%s_" % v
        t1, t2 = base + "1.png", base + "2.png"
        if t1 in sizes and t2 in sizes and sizes[t1][1] == sizes[t2][1]:
            yield [t1, t2], "START", bg


def all_overrides(kept, textures):
    sizes = {k: (v["w"], v["h"]) for k, v in textures.items()}
    B = briefs()
    out = []
    sp = spr.sprites(kept, sizes)
    for rel, b in B["sprites"].items():
        frames = sp.get(rel)
        if not frames:
            continue
        texts = b["frames"] if "frames" in b else [b["text"]] * len(frames)
        for pieces, text in zip(frames, texts):
            if not pieces:
                continue
            x0, y0, w, h = sprite_canvas(pieces)
            if b.get("kind") == "rocket":
                canvas = rocket_box(text, w, h)
            else:
                canvas = word_image(text, w, h, b.get("style", "word"), weight=b.get("weight", 0.11))
            for prel, img in cut(canvas, pieces, x0, y0):
                out.append((prel, img, "hud text"))
    for rel, b in B["textures"].items():
        if rel not in sizes:
            continue
        w, h = sizes[rel]
        if b.get("kind") == "rocket":
            img = rocket_box(b["text"], w, h)
        elif b.get("kind") == "panel":
            img = panel(b["text"], w, h, b.get("selected", True))
        elif b.get("kind") == "sign":
            if "group" in b:                 # one sign spread over several textures, left to right
                ws = [sizes[g][0] for g in b["group"]]
                big = sign(b["text"], sum(ws), h, **b.get("args", {}))
                x = 0
                for g, gw in zip(b["group"], ws):
                    out.append((g, big[:, x:x + gw].copy(), "sign"))
                    x += gw
                continue
            img = sign(b["text"], w, h, **b.get("args", {}))
        elif b.get("kind") == "star_tile":
            img = star_tile(w, h, b.get("bg", [220, 50, 30]))
        else:
            img = word_image(b["text"], w, h, b.get("style", "word"), pad=b.get("pad"), weight=b.get("weight", 0.11))
            if "bg" in b:
                bg = np.zeros_like(img)
                bg[..., :3] = b["bg"]
                bg[..., 3] = 255
                a = img[..., 3:] / 255.0
                bg[..., :3] = bg[..., :3] * (1 - a) + img[..., :3] * a
                img = bg
        if b.get("flip"):                     # stored upside-down (flipped-image)
            img = img[::-1].copy()
        out.append((rel, img, "hud text"))
    for group, text, bg in banners(sizes):
        ws = [sizes[g][0] for g in group]
        h = sizes[group[0]][1]
        canvas = np.zeros((h, sum(ws), 4), np.float32)
        canvas[..., :3] = bg
        canvas[..., 3] = 255
        tw = word_image(text, sum(ws) - 4, h - 8, "sign", pad=1, weight=0.11)
        a = tw[..., 3:] / 255.0
        canvas[4:h - 4, 2:-2, :3] = canvas[4:h - 4, 2:-2, :3] * (1 - a) + tw[..., :3] * a
        x = 0
        for g, gw in zip(group, ws):
            out.append((g, canvas[:, x:x + gw].copy(), "banner"))
            x += gw
    strips = ["textures/2d/menu/title_%d.png" % i for i in range(10)]
    if all(r in sizes for r in strips):
        logo = title_logo(sum(sizes[r][0] for r in strips), sizes[strips[0]][1])
        x = 0
        for r in strips:
            w = sizes[r][0]
            out.append((r, logo[:, x:x + w].copy(), "title logo"))
            x += w
    return out
