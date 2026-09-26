"""Clean-room DKR fonts: every glyph cell re-typeset with the project's own
stroke font (cleanroom.gfx.strokefont), placed by the kept font metadata
(fonts/game_fonts/*.meta.json: texture list, per-character uv + size).

Styles (our own, chosen to read like the game's):
  BigFont       chunky letters, yellow->orange fill, blue outline, drop shadow
  FunFont       magenta->red fill, yellow outline, dark shadow
  SmallFont     white, alpha = coverage (IA8)
  SubtitleFont  white, bolder, alpha = coverage (IA8)
"""
import json
import os

import numpy as np

from cleanroom.gfx import strokefont
from games.dkr import glyphs_dkr  # noqa: F401  (DKR glyph designs)

STYLES = {
    "BigFont": {"fill": ((255, 246, 60), (255, 128, 16)), "outline": (24, 44, 210), "shadow": (0, 0, 24),
                "th": 0.10, "ow": 2, "margin": 3},
    "FunFont": {"fill": ((255, 60, 200), (220, 20, 70)), "outline": (255, 236, 70), "shadow": (20, 0, 20),
                "th": 0.10, "ow": 1, "margin": 1},
    "SmallFont": {"white": True, "th": 0.09, "margin": 0},
    "SubtitleFont": {"white": True, "th": 0.12, "margin": 0},
}


def _dilate(m, r):
    out = m.copy()
    h, w = m.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > r * r + r:
                continue
            sh = np.zeros_like(m)
            ys, yd = (slice(max(0, dy), h), slice(0, h - max(0, dy))) if dy >= 0 else (slice(0, h + dy), slice(-dy, h))
            xs, xd = (slice(max(0, dx), w), slice(0, w - max(0, dx))) if dx >= 0 else (slice(0, w + dx), slice(-dx, w))
            sh[ys, xs] = m[yd, xd]
            np.maximum(out, sh, out=out)
    return out


def glyph_cell(font, ch, w, h):
    """RGBA float image (h, w) of one character in `font`'s style."""
    st = STYLES[font]
    img = np.zeros((h, w, 4), np.float32)
    mg = st["margin"]
    iw, ih = max(1, w - 2 * mg), max(1, h - 2 * mg)
    th = max(0.6, ih * st["th"])
    m = np.zeros((h, w), np.float32)
    g = strokefont.render(ch, iw, ih, thickness=th)
    m[mg:mg + ih, mg:mg + iw] = g
    if st.get("white"):
        img[..., :3] = 255
        img[..., 3] = np.clip(m * 1.4, 0, 1) * 255
        return img
    ow = st["ow"]
    outline = np.clip(_dilate(m, ow), 0, 1)
    shadow = np.zeros_like(outline)
    shadow[1:, 1:] = outline[:-1, :-1]
    # shadow, then outline, then fill (painter's order)
    for mask, col in ((shadow, st["shadow"]), (outline, st["outline"])):
        a = mask[..., None]
        img[..., :3] = img[..., :3] * (1 - a) + np.asarray(col, np.float32) * a
        img[..., 3] = np.maximum(img[..., 3], mask * 255)
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    c0, c1 = np.asarray(st["fill"][0], np.float32), np.asarray(st["fill"][1], np.float32)
    fill = c0 * (1 - t) + c1 * t
    a = np.clip(m * 1.3, 0, 1)[..., None]
    img[..., :3] = img[..., :3] * (1 - a) + fill * a
    img[..., 3] = np.maximum(img[..., 3], a[..., 0] * 255)
    return img


def font_textures(kept_root, sizes):
    """{texture relpath: RGBA float image} for every font atlas.
    sizes: {relpath: (w, h)} from the texture digests."""
    tex_meta = json.load(open(os.path.join(kept_root, "asset_textures_2d.meta.json"), encoding="utf-8"))
    sections = tex_meta["files"]["sections"]
    out = {}
    for font in STYLES:
        meta = json.load(open(os.path.join(kept_root, "fonts/game_fonts/%s.meta.json" % font), encoding="utf-8"))
        texnames = meta["textures"]
        # one region per (texture, u, v): prefer the uppercase / first-listed char
        regions = {}
        for ch, c in meta["characters"].items():
            ti = c["tex-index"]
            if ti < 0 or ti >= len(texnames) or not texnames[ti]:
                continue
            # uv are unsigned bytes stored signed in the metadata (-107 means 149)
            key = (ti, c["uv"]["u"] & 0xFF, c["uv"]["v"] & 0xFF)
            if key not in regions or (ch.isupper() and not regions[key][0].isupper()):
                regions[key] = (ch, c)
        for (ti, u, v), (ch, c) in regions.items():
            js = sections[texnames[ti]]["filename"]
            rel = "textures/2d/" + js[:-5] + ".png"
            if rel not in sizes:
                continue
            W, H = sizes[rel]
            if rel not in out:
                out[rel] = np.zeros((H, W, 4), np.float32)
            w, h = c["tex-size"].get("width", W), c["tex-size"]["height"]
            u0, v0 = u, v
            w, h = min(w, W - u0), min(h, H - v0)
            if w <= 0 or h <= 0:
                continue
            out[rel][v0:v0 + h, u0:u0 + w] = glyph_cell(font, ch, w, h)
    return out
