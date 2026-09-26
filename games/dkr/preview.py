"""Write our drawn overrides (and fonts) as PNGs into a folder for a contact
sheet: python -m games.dkr.preview <spec> <out dir> [substring filter]"""
import json
import os
import sys

from games.dkr import drawn, faces, fonts
from games.dkr.generate import save_png


def main(spec, out, filt=""):
    textures = json.load(open(os.path.join(spec, "textures.json")))
    kept = os.path.join(spec, "kept")
    sizes = {k: (v["w"], v["h"]) for k, v in textures.items()}
    items = [(r, i) for r, i in fonts.font_textures(kept, sizes).items()]
    items += [(r, i) for r, i, _ in drawn.all_overrides(kept, textures)]
    items += [(r, i) for r, i, _ in faces.all_overrides(textures, kept)]
    n = 0
    for rel, img in items:
        if filt and filt not in rel:
            continue
        p = os.path.join(out, rel)
        save_png(p, img, "RGBA")
        n += 1
    print(n, "written under", out)


if __name__ == "__main__":
    main(*sys.argv[1:])
