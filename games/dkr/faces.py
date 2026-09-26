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


def all_overrides(textures):
    from games.dkr import icons
    out = []
    from games.dkr import eyes
    allb = dict(icons.briefs(textures))
    allb.update(eyes.briefs(textures))
    allb.update(load())
    for rel, b in allb.items():
        if rel in textures:
            out.append((rel, render(rel, b, textures[rel]), "face brief"))
    return out
