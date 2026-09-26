"""CLEAN ROOM: face / portrait textures painted from our own briefs
(face_briefs.json) with cleanroom.gfx.facepaint.

Brief extras: "_frame": true draws the HUD portrait tile first (blue gradient,
light rim) and keeps the result opaque; "keep_alpha": true uses the kept 2-bit
alpha outline instead of an opaque square.
"""
import json
import os

import numpy as np

from cleanroom.decomp.gen import h32, unpack_alpha2
from cleanroom.gfx import facepaint

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    raw = json.load(open(os.path.join(HERE, "face_briefs.json"), encoding="utf-8"))
    out = {}
    for k, b in raw.items():
        if k.startswith("_"):
            continue
        if "use" in b:
            base = dict(raw[b["use"]])
            base.update({x: y for x, y in b.items() if x != "use"})
            b = base
        out[k] = b
    return out


def _frame(w, h):
    img = np.zeros((h, w, 4), np.float32)
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    img[..., :3] = np.asarray((110, 170, 255), np.float32) * (1 - t) + np.asarray((25, 55, 170), np.float32) * t
    img[..., 3] = 255
    r = max(1, w // 20)
    img[:r, :, :3] = img[:, :r, :3] = (225, 235, 255)
    img[-r:, :, :3] = img[:, -r:, :3] = (130, 140, 170)
    return img


def render(rel, b, d):
    w, h = d["w"], d["h"]
    alpha = unpack_alpha2(d["alpha2"], w, h) if (b.get("keep_alpha") and "alpha2" in d) else None
    brief = dict(b)
    if b.get("_frame"):
        brief["base"] = {"grad": [[110, 170, 255], [25, 55, 170]]}
    tl = b.get("_tile")
    if tl:
        brief["base"] = {"grad": [tl["top"], tl["bot"]]}
    img = facepaint.render(brief, w, h, grid=d.get("grid"), alpha=alpha, seed=h32("face", rel))
    if tl:
        f = np.asarray(tl["frame"], np.float32)
        r = max(2, w // 12)
        lite, dark = np.minimum(255, f * 0.6 + 110), f * 0.55
        img[:r, :, :3] = f
        img[-r:, :, :3] = f
        img[:, :r, :3] = f
        img[:, -r:, :3] = f
        img[:1, :, :3] = lite
        img[:, :1, :3] = lite
        img[-1:, :, :3] = dark
        img[:, -1:, :3] = dark
        img[r - 1:r, r - 1:w - r + 1, :3] = dark
        img[r - 1:h - r + 1, r - 1:r, :3] = dark
        img[..., 3] = 255
    if b.get("_frame"):
        r = max(1, w // 20)
        img[:r, :, :3] = (225, 235, 255)
        img[:, :r, :3] = (225, 235, 255)
        img[-r:, :, :3] = (130, 140, 170)
        img[:, -r:, :3] = (130, 140, 170)
        img[..., 3] = 255
    return img


def render_sprite(frames, b, textures):
    """Paint one brief over a multi-piece sprite: the pieces' kept alpha is
    assembled on a shared canvas (sprite-x/y), painted once, then cut back."""
    out = []
    for pieces in frames:
        pieces = [p for p in pieces if p["rel"] in textures]
        if not pieces:
            continue
        x0 = min(p["x"] for p in pieces)
        y0 = min(p["y"] for p in pieces)
        W = max(p["x"] + p["w"] for p in pieces) - x0
        H = max(p["y"] + p["h"] for p in pieces) - y0
        alpha = np.zeros((H, W), np.float32)
        for p in pieces:
            d = textures[p["rel"]]
            a = unpack_alpha2(d["alpha2"], d["w"], d["h"]) if "alpha2" in d else np.full((d["h"], d["w"]), 255.0)
            sl = alpha[p["y"] - y0:p["y"] - y0 + d["h"], p["x"] - x0:p["x"] - x0 + d["w"]]
            np.maximum(sl, a[:sl.shape[0], :sl.shape[1]], out=sl)
        brief = {k: v for k, v in b.items() if k != "keep_alpha"}
        img = facepaint.render(brief, W, H, alpha=alpha, seed=h32("sprite", pieces[0]["rel"]))
        for p in pieces:
            out.append((p["rel"], img[p["y"] - y0:p["y"] - y0 + p["h"], p["x"] - x0:p["x"] - x0 + p["w"]].copy()))
    return out


def all_overrides(textures, kept=None):
    from games.dkr import eyes, icons
    out = []
    allb = dict(icons.briefs(textures))
    allb.update(eyes.briefs(textures))
    allb.update(load())
    for rel, b in allb.items():
        if rel in textures:
            out.append((rel, render(rel, b, textures[rel]), "face brief"))
    if kept:
        from games.dkr import sprites as spr
        sizes = {k: (v["w"], v["h"]) for k, v in textures.items()}
        sp = spr.sprites(kept, sizes)
        for srel, b in icons.sprite_briefs().items():
            if srel in sp:
                for rel, img in render_sprite(sp[srel], b, textures):
                    out.append((rel, img, "sprite brief"))
    return out
