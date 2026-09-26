"""Taint report (dev only; reads the dirty tree): every generated texture (RGBA
pixels), both sample tables (raw bytes) and every wave (decoded PCM) of the
clean tree vs every retail one. Shared runs >= 32 bytes fail.

    python -m games.dkr.taint_report <dirty tree> <clean tree> <spec dir>
"""
import json
import os
import sys

import numpy as np
from PIL import Image

from cleanroom import taint
from cleanroom.audio import albank
from games.dkr.extract_spec import BANKS, VER, decode_wave


def png_streams(root, rels):
    for r in rels:
        p = os.path.join(root, r)
        if os.path.exists(p):
            yield r, np.asarray(Image.open(p).convert("RGBA")).tobytes()


def audio_streams(root):
    for ctl_name, tbl_name in BANKS.items():
        ctl = open(os.path.join(root, "audio/unknown", ctl_name), "rb").read()
        tbl = open(os.path.join(root, "audio/unknown", tbl_name), "rb").read()
        yield tbl_name + " raw", tbl
        bf = albank.parse_bankfile(ctl)
        seen = set()
        for bank in bf["banks"]:
            for ins in list(bank["insts"]) + [bank["percussion"]]:
                if not ins:
                    continue
                for s in ins["sounds"]:
                    w = s["wave"]
                    if w["_id"] in seen:
                        continue
                    seen.add(w["_id"])
                    yield f"{ctl_name} {w['_id']}", decode_wave(tbl, w, None).astype(">i2").tobytes()


def main(dirty, clean, spec):
    rels = list(json.load(open(os.path.join(spec, "textures.json"))))
    d = os.path.join(dirty, "assets", ".vanilla", VER)
    c = os.path.join(clean, "assets", ".vanilla", VER)
    index = taint.build_index(s for _, s in list(png_streams(d, rels)) + list(audio_streams(d)))
    hits = taint.scan(index, list(png_streams(c, rels)) + list(audio_streams(c)))
    bad = sorted((h for h in hits if h[3] >= taint.FAIL_RUN), key=lambda h: -h[3])
    print(f"taint: {len(rels)} textures + 2 sample tables + all waves scanned; {len(hits)} with short "
          f"coincidental matches; {len(bad)} failing (run >= {taint.FAIL_RUN} B)")
    for label, off, n, run in bad[:10]:
        print(f"  FAIL {label} run {run} B")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
