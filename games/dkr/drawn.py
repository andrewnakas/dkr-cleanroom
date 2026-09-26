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
        text = text.replace("0", "O")   # the slashed zero closes up when small
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
        else:
            img = word_image(b["text"], w, h, b.get("style", "word"), pad=b.get("pad"), weight=b.get("weight", 0.11))
        out.append((rel, img, "hud text"))
    return out
