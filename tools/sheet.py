"""Contact sheet: python tools/sheet.py out.png img1 img2 ... [--cols 2] [--w 480] [--label]
Images are scaled to width --w and tiled; file names are drawn under each tile with --label."""
import argparse
import os

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("imgs", nargs="+")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--w", type=int, default=480)
    ap.add_argument("--label", action="store_true")
    ap.add_argument("--nearest", action="store_true")
    a = ap.parse_args()
    ims = []
    for p in a.imgs:
        im = Image.open(p).convert("RGBA")
        h = max(1, round(im.height * a.w / im.width))
        im = im.resize((a.w, h), Image.NEAREST if a.nearest else Image.LANCZOS)
        ims.append((os.path.basename(p), im))
    lh = 14 if a.label else 0
    rows = (len(ims) + a.cols - 1) // a.cols
    th = max(im.height for _, im in ims) + lh
    sheet = Image.new("RGBA", (a.cols * (a.w + 4), rows * (th + 4)), (40, 40, 48, 255))
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(ims):
        x, y = (i % a.cols) * (a.w + 4), (i // a.cols) * (th + 4)
        sheet.alpha_composite(im, (x, y))
        if a.label:
            d.text((x + 2, y + im.height), n[:a.w // 6], fill=(255, 255, 255, 255))
    sheet.convert("RGB").save(a.out)
    print(a.out, sheet.size)


if __name__ == "__main__":
    main()
