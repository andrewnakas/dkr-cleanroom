"""Labelled contact sheet of textures (dev: dirty or clean tree), each tile
scaled by an integer factor, packed in rows.

    python tools/texsheet.py <asset root> <out.png> <glob> [<glob>...] [--scale 2] [--width 1600] [--first]
--first keeps only the first frame of names ending in _<n>."""
import argparse
import glob
import os
import re

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("out")
    ap.add_argument("globs", nargs="+")
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--first", action="store_true")
    ap.add_argument("--maxdim", type=int, default=128)
    a = ap.parse_args()
    paths = []
    for g in a.globs:
        paths += sorted(glob.glob(os.path.join(a.root, g), recursive=True))
    if a.first:
        seen, keep = set(), []
        for p in paths:
            k = re.sub(r"_\d+\.png$", "", p)
            if k not in seen:
                seen.add(k)
                keep.append(p)
        paths = keep
    tiles = []
    for p in paths:
        im = Image.open(p).convert("RGBA")
        s = a.scale
        while s > 1 and max(im.size) * s > a.maxdim * a.scale:
            s -= 1
        im = im.resize((im.width * s, im.height * s), Image.NEAREST)
        tiles.append((os.path.basename(p)[:-4], im))
    x = y = rowh = 0
    pos = []
    for n, im in tiles:
        w = max(im.width, len(n) * 6) + 6
        if x + w > a.width:
            x, y, rowh = 0, y + rowh, 0
        pos.append((x, y))
        x += w
        rowh = max(rowh, im.height + 14)
    sheet = Image.new("RGBA", (a.width, y + rowh), (60, 60, 70, 255))
    chk = Image.new("RGBA", (8, 8), (80, 80, 92, 255))
    d = ImageDraw.Draw(sheet)
    for (n, im), (x, y) in zip(tiles, pos):
        sheet.alpha_composite(im, (x, y))
        d.text((x, y + im.height), n, fill=(255, 255, 255, 255))
    sheet.convert("RGB").save(a.out)
    print(a.out, sheet.size, len(tiles), "tiles")


if __name__ == "__main__":
    main()
