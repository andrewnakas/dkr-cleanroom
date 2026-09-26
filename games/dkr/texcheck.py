"""In-place inflate safety for generated textures.

DKR loads a compressed texture at the END of its output block and inflates it
forward (src/textures_sprites.c), so a texture that barely compresses makes the
inflater overwrite its own input (corruption, hangs). Retail art compresses
well; noise-detailed art may not. This packs a generated image the way its
N64 format stores it, deflates it, and reports the ratio.

    ratio(img, fmt) -> compressed / raw (deflate level 6, plus gzip header)
    python -m games.dkr.texcheck <clean tree>      # report the worst textures
"""
import json
import os
import sys
import zlib

import numpy as np
from PIL import Image

LIMIT = 0.72   # keep compressed size well below the raw size


def pack(img, fmt):
    a = np.clip(np.round(img), 0, 255).astype(np.uint16)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    lum = ((r * 299 + g * 587 + b * 114) // 1000).astype(np.uint16)
    if fmt == "RGBA32":
        return a.astype(np.uint8).tobytes()
    if fmt == "RGBA16":
        v = ((r >> 3) << 11) | ((g >> 3) << 6) | ((b >> 3) << 1) | (al >> 7)
        return v.astype(">u2").tobytes()
    if fmt == "IA16":
        return np.stack([lum, al], -1).astype(np.uint8).tobytes()
    if fmt == "IA8":
        return (((lum >> 4) << 4) | (al >> 4)).astype(np.uint8).tobytes()
    if fmt == "I8":
        return lum.astype(np.uint8).tobytes()
    v = (((lum >> 5) << 1) | (al >> 7)) if fmt == "IA4" else (lum >> 4)
    v = v.ravel().astype(np.uint8)
    if len(v) % 2:
        v = np.append(v, 0)
    return ((v[0::2] << 4) | v[1::2]).astype(np.uint8).tobytes()


def ratio(img, fmt):
    raw = pack(img, fmt)
    return (len(zlib.compress(raw, 6)) + 18) / max(1, len(raw))


def target(img, fmt):
    raw = len(pack(img, fmt))
    return 0.9 if raw < 256 else (0.75 if raw < 1024 else 0.6)


def make_safe(img, fmt):
    """Reduce fine detail until the texture deflates below its target ratio:
    posterize, then repeat pixels in 2x2 / 4x4 blocks. Alpha is left alone.
    Returns (image, steps taken)."""
    t = target(img, fmt)
    if ratio(img, fmt) <= t:
        return img, 0
    h, w = img.shape[:2]
    for step, (q, blk) in enumerate(((12, 1), (24, 1), (24, 2), (32, 2), (32, 4), (48, 4)), 1):
        out = img.copy()
        rgb = out[..., :3]
        if blk > 1:
            hh, ww = h // blk * blk, w // blk * blk
            if hh and ww:
                v = rgb[:hh, :ww].reshape(hh // blk, blk, ww // blk, blk, 3).mean((1, 3))
                rgb[:hh, :ww] = np.repeat(np.repeat(v, blk, 0), blk, 1)
        out[..., :3] = np.round(rgb / q) * q
        if ratio(out, fmt) <= t:
            return out, step
    return out, 6


def formats(kept):
    """{texture png relpath: (format, compressed)} from the kept JSON sidecars."""
    out = {}
    for root, _, files in os.walk(os.path.join(kept, "textures")):
        for f in files:
            if not f.endswith(".json"):
                continue
            j = json.load(open(os.path.join(root, f), encoding="utf-8"))
            d = os.path.relpath(root, kept).replace(os.sep, "/")
            for im in j.get("images", []):
                out[d + "/" + im] = (j.get("format", "RGBA16").upper(), bool(j.get("compressed")))
    return out


def main(tree):
    base = os.path.join(tree, "assets", ".vanilla", "us.v80")
    fm = formats(base)
    rows = []
    for rel, (fmt, comp) in fm.items():
        if not comp:
            continue
        img = np.asarray(Image.open(os.path.join(base, rel)).convert("RGBA")).astype(np.float32)
        rows.append((ratio(img, fmt), rel, fmt))
    rows.sort(reverse=True)
    bad = [r for r in rows if r[0] > LIMIT]
    print(f"{len(rows)} compressed textures; {len(bad)} above {LIMIT:.2f}")
    for r in bad[:15]:
        print(f"  {r[0]:.2f} {r[2]:6s} {r[1]}")


if __name__ == "__main__":
    main(sys.argv[1])
