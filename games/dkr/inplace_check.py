"""Check in-place inflate margins in a built assets.bin (dev/build check).

For every compressed texture: assetSize (bytes in the asset block) vs the
uncompressed size in its header. DKR loads the compressed bytes at
tex + uncompressedSize - assetSize (rounded down to 16) and inflates forward
into tex, so it needs assetSize comfortably below uncompressedSize.

    python -m games.dkr.inplace_check <tree> [--list N]
"""
import json
import os
import struct
import sys


def sections(tree):
    base = os.path.join(tree, "assets")
    lut = open(os.path.join(base, "assets.lut.bin"), "rb").read()
    data = open(os.path.join(base, "assets.bin"), "rb").read()
    offs = struct.unpack(">%dI" % (len(lut) // 4), lut)
    order = json.load(open(os.path.join(base, ".vanilla", "us.v80", "assets.meta.json"), encoding="utf-8"))["assets"]["order"]
    # offs[i] .. offs[i+1] is section i (the LUT may start with a count; detect by size)
    if len(offs) == len(order) + 2:
        offs = offs[1:]
    return {name: data[offs[i]:offs[i + 1]] for i, name in enumerate(order)}


def textures(sec, table, blob):
    t = sec[table]
    offs = [o for o in struct.unpack(">%dI" % (len(t) // 4), t)]
    data = sec[blob]
    out = []
    for i in range(len(offs) - 1):
        a, b = offs[i], offs[i + 1]
        if b <= a or b > len(data) or a == 0xFFFFFFFF:
            continue
        hdr = data[a:a + 32]
        if len(hdr) < 32:
            continue
        compressed = hdr[0x1D] if len(hdr) > 0x1D else 0
        usize = struct.unpack(">I", hdr[0x1C:0x20])[0] if False else None
        out.append((i, b - a, hdr))
    return out


def main(tree, n=15):
    sec = sections(tree)
    rows = []
    for table, blob, tag in (("ASSET_TEXTURES_2D_TABLE", "ASSET_TEXTURES_2D", "2d"), ("ASSET_TEXTURES_3D_TABLE", "ASSET_TEXTURES_3D", "3d")):
        t = sec[table]
        offs = struct.unpack(">%dI" % (len(t) // 4), t)
        data = sec[blob]
        for i in range(len(offs) - 1):
            a, b = offs[i], offs[i + 1]
            if not (0 <= a < b <= len(data)):
                continue
            # TempTexHeader: TextureHeader (0x20, isCompressed at 0x1D), then the
            # uncompressed size (u32, little endian) at 0x20 and the level byte.
            h = data[a:a + 0x28]
            if len(h) < 0x28 or not h[0x1D]:
                continue
            usize = struct.unpack("<I", h[0x20:0x24])[0]
            asset = b - a
            rows.append((asset / max(1, usize), asset, usize, tag, i))
    rows.sort(reverse=True)
    risky = [r for r in rows if r[1] + 16 > r[2]]
    print(f"{len(rows)} compressed textures; {len(risky)} with assetSize > uncompressed (in-place overlap)")
    for r in rows[:n]:
        print(f"  {r[3]} #{r[4]:4d} asset {r[1]:6d} uncompressed {r[2]:6d} ratio {r[0]:.2f}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[3]) if len(sys.argv) > 3 else 15)
