"""CLEAN ROOM: spec -> DKR asset tree (assets/.vanilla/us.v80) in a clean copy
of the decomp/port source. No ROM, no dirty tree.

    python -m games.dkr.generate <spec dir> <pristine tree> <clean tree> [--only textures|audio]

Textures: every PNG from its digest (colour grid + our detail noise + kept
2-bit alpha), then overrides from our own drawing modules (fonts, labels,
faces, pictures). Audio: games.dkr.audio_gen. Everything else: spec/kept.
"""
import argparse
import json
import os
import shutil
from collections import Counter

import numpy as np
from PIL import Image

from cleanroom.decomp.gen import from_digest
from games.dkr import audio_gen, fonts

VER = "us.v80"
HERE = os.path.dirname(os.path.abspath(__file__))


def copy_tree(pristine, clean):
    if os.path.exists(os.path.join(clean, "Makefile.pc")):
        return
    shutil.copytree(pristine, clean, ignore=shutil.ignore_patterns(".git", "build", "assets", "baseroms"))


def save_png(path, rgba, mode):
    rgba = np.clip(np.round(rgba), 0, 255).astype(np.uint8)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if mode == "LA":
        lum = (rgba[..., 0] * 0.299 + rgba[..., 1] * 0.587 + rgba[..., 2] * 0.114).round().astype(np.uint8)
        Image.fromarray(np.stack([lum, rgba[..., 3]], -1), "LA").save(path)
    elif mode == "L":
        Image.fromarray(rgba[..., 0], "L").save(path)
    else:
        Image.fromarray(rgba, "RGBA").save(path)


def overrides(spec, textures):
    """{relpath: (RGBA float image, source tag)} from our drawing modules."""
    kept = os.path.join(spec, "kept")
    sizes = {k: (v["w"], v["h"]) for k, v in textures.items()}
    out = {}
    for rel, img in fonts.font_textures(kept, sizes).items():
        out[rel] = (img, "font")
    try:
        from games.dkr import drawn
        for rel, img, tag in drawn.all_overrides(kept, textures):
            out[rel] = (img, tag)
    except ImportError:
        pass
    from games.dkr import faces
    for rel, img, tag in faces.all_overrides(textures):
        out[rel] = (img, tag)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("pristine")
    ap.add_argument("clean")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    copy_tree(a.pristine, a.clean)
    dst = os.path.join(a.clean, "assets", ".vanilla", VER)
    counts = Counter()
    if not a.only:
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(os.path.join(a.spec, "kept"), dst)
        counts["kept files"] = sum(len(f) for _, _, f in os.walk(dst))
    if a.only in ("", "textures"):
        textures = json.load(open(os.path.join(a.spec, "textures.json")))
        ov = overrides(a.spec, textures)
        for rel, d in textures.items():
            if rel in ov:
                img, tag = ov[rel]
                counts["texture " + tag] += 1
            else:
                img = from_digest(rel, d).astype(np.float32)
                counts["texture digest"] += 1
            save_png(os.path.join(dst, rel), img, d.get("mode", "RGBA"))
    if a.only in ("", "audio"):
        spec_audio = json.load(open(os.path.join(a.spec, "audio.json")))
        cache = os.path.join(os.path.dirname(os.path.abspath(a.spec)), "gencache", "audio")
        os.makedirs(cache, exist_ok=True)
        for ctl_name, bank in spec_audio.items():
            ctl, tbl = audio_gen.build_bank(ctl_name, bank, cache)
            open(os.path.join(dst, "audio/unknown", ctl_name), "wb").write(ctl)
            open(os.path.join(dst, "audio/unknown", bank["tbl"]), "wb").write(tbl)
            counts["audio bank " + ctl_name] = len(bank["waves"])
    for k, v in sorted(counts.items()):
        print(f"{v:6d} {k}")


if __name__ == "__main__":
    main()
