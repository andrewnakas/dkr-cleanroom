"""Compose sample strings with our font atlases through the kept font metrics
(uv, tex-size, char-width), like the game's text renderer, for a readability
check. python -m games.dkr.font_check <spec> <atlas root (prev or clean assets)> <out.png>"""
import json
import os
import sys

import numpy as np
from PIL import Image

from games.dkr.fonts import STYLES

SAMPLES = ["DIDDY KONG RACING", "Press START to play!", "Lap 2/3  Time 0'42\"18", "Whale Bay: 1st place?"]


def main(spec, root, out):
    kept = os.path.join(spec, "kept")
    sec = json.load(open(os.path.join(kept, "asset_textures_2d.meta.json"), encoding="utf-8"))["files"]["sections"]
    rows = []
    for font in STYLES:
        meta = json.load(open(os.path.join(kept, "fonts/game_fonts/%s.meta.json" % font), encoding="utf-8"))
        cache = {}
        for s in SAMPLES:
            h = max(c["tex-size"]["height"] for c in meta["characters"].values() if c["tex-index"] >= 0)
            line = np.zeros((h + 2, 900, 4), np.uint8)
            x = 0
            for ch in s:
                c = meta["characters"].get(ch)
                if c is None:
                    x += meta.get("special-character-width", 4)
                    continue
                ti = c["tex-index"]
                if ti >= 0 and meta["textures"][ti]:
                    rel = "textures/2d/" + sec[meta["textures"][ti]]["filename"][:-5] + ".png"
                    if rel not in cache:
                        cache[rel] = np.asarray(Image.open(os.path.join(root, rel)).convert("RGBA"))
                    atlas = cache[rel]
                    u, v = c["uv"]["u"] & 0xFF, c["uv"]["v"] & 0xFF
                    w, hh = c["tex-size"].get("width", 0), c["tex-size"]["height"]
                    g = atlas[v:v + hh, u:u + w]
                    gh, gw = g.shape[:2]
                    if x + gw < line.shape[1]:
                        a = g[..., 3:4] / 255.0
                        dst = line[0:gh, x:x + gw]
                        dst[..., :3] = (dst[..., :3] * (1 - a) + g[..., :3] * a).astype(np.uint8)
                        dst[..., 3] = np.maximum(dst[..., 3], g[..., 3])
                x += c["char-width"]
            rows.append(line)
    H = sum(r.shape[0] for r in rows)
    sheet = np.zeros((H, 900, 4), np.uint8)
    sheet[..., :3] = (40, 60, 110)
    sheet[..., 3] = 255
    y = 0
    for r in rows:
        a = r[..., 3:4] / 255.0
        sheet[y:y + r.shape[0], :, :3] = (sheet[y:y + r.shape[0], :, :3] * (1 - a) + r[..., :3] * a).astype(np.uint8)
        y += r.shape[0]
    im = Image.fromarray(sheet).resize((1800, H * 2), Image.NEAREST)
    im.convert("RGB").save(out)
    print(out, im.size)


if __name__ == "__main__":
    main(*sys.argv[1:4])
