"""DIRTY ROOM: extracted DKR assets -> clean-room spec (facts only).

    python -m games.dkr.extract_spec <dirty tree> <spec dir>

Reads <dirty>/assets/.vanilla/us.v80 (dkr_assets_tool extract output) and writes:
  kept/...           verbatim: JSON sidecars, geometry/text/sequence/table bins
                     (user scope: geometry, text, note sequences, demo inputs,
                     game tables). Never PNG pixels, gltf, sample data, books.
  textures.json      per PNG: size, 4x4 colour grid (16x16 for >=128 px),
                     2-bit alpha outline (cleanroom.decomp.spec.texture_fact)
  audio.json         per bank (ctl 0/2): ctl skeleton (books and loop states
                     zeroed), bank rate, per wave: base, len, type, loop,
                     npred/order, a coarse outline (descriptor) and median f0
Prints a one-screen summary.
"""
import json
import os
import shutil
import struct
import sys
from collections import Counter

import numpy as np
from PIL import Image

from cleanroom.audio import albank, descriptor, vadpcm
from cleanroom.audio.pitch import median_f0
from cleanroom.decomp.spec import texture_fact

VER = "us.v80"
# ctl -> tbl pairs inside audio/unknown
BANKS = {"asset_audio_0.bin": "asset_audio_1.bin", "asset_audio_2.bin": "asset_audio_3.bin"}
SKIP_DIRS = ("debug/",)
SRC_ROOT = [""]


def kept_file(rel):
    if rel.startswith(SKIP_DIRS):
        return False
    if rel.endswith(".png"):
        return False
    if rel.endswith(".gltf"):          # object placement maps; kept only if image-free
        j = json.load(open(os.path.join(SRC_ROOT[0], rel), encoding="utf-8"))
        return not (j.get("images") or j.get("textures"))
    base = os.path.basename(rel)
    if rel.startswith("audio/") and (base in BANKS or base in BANKS.values()):
        return False
    return True


def u16be(b):
    return np.frombuffer(b, ">i2").astype(np.int64)


def decode_wave(tbl, w, npred_order):
    data = tbl[w["base"]:w["base"] + w["len"]]
    if w["type"] == albank.RAW16:
        return u16be(data[:len(data) // 2 * 2])
    bk = w["book"]
    book = {"order": bk["order"], "npred": bk["npred"], "book": bk["book"]}
    return vadpcm.decode(data, book, len(data) // 9 * 16)


def audio_facts(src):
    out = {}
    for ctl_name, tbl_name in BANKS.items():
        ctl = bytearray(open(os.path.join(src, "audio/unknown", ctl_name), "rb").read())
        tbl = open(os.path.join(src, "audio/unknown", tbl_name), "rb").read()
        bf = albank.parse_bankfile(bytes(ctl))
        rate = bf["banks"][0]["rate"]
        waves = {}
        for bank in bf["banks"]:
            insts = list(bank["insts"]) + [bank["percussion"]]
            for ins in insts:
                if not ins:
                    continue
                for s in ins["sounds"]:
                    waves.setdefault(s["wave"]["_id"], s["wave"])
        facts = []
        for wid, w in sorted(waves.items(), key=lambda kv: kv[1]["base"]):
            pcm = decode_wave(tbl, w, None)
            d = {"wave": wid, "base": w["base"], "len": w["len"], "type": w["type"], "n": int(len(pcm))}
            if w["book"]:
                bid = w["book"]["_id"]
                d["book"] = bid
                d["npred"] = w["book"]["npred"]
                d["order"] = w["book"]["order"]
                off = int(bid.split("@")[1], 16)
                n = w["book"]["npred"] * w["book"]["order"] * 8
                ctl[off + 8:off + 8 + 2 * n] = bytes(2 * n)          # zero the retail book
            if w["loop"]:
                lp = w["loop"]
                d["loop"] = {"id": lp["_id"], "start": lp["start"], "end": lp["end"], "count": lp["count"]}
                if w["type"] == albank.ADPCM:
                    off = int(lp["_id"].split("@")[1], 16)
                    ctl[off + 12:off + 44] = bytes(32)               # zero the retail loop state
            d["desc"] = descriptor.describe(pcm, rate)
            f0 = median_f0(pcm.astype(np.float32) / 32768.0, rate)
            d["f0"] = round(float(f0), 1) if f0 else 0.0
            d["peak"] = int(np.abs(pcm).max()) if len(pcm) else 0
            facts.append(d)
        out[ctl_name] = {"tbl": tbl_name, "tbl_size": len(tbl), "rate": rate,
                         "ctl_skeleton": bytes(ctl).hex(), "waves": facts}
    return out


def main(dirty, spec):
    src = os.path.join(dirty, "assets", ".vanilla", VER)
    SRC_ROOT[0] = src
    kept_dir = os.path.join(spec, "kept")
    shutil.rmtree(kept_dir, ignore_errors=True)
    counts = Counter()
    textures = {}
    for root, _, files in os.walk(src):
        for f in files:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, src).replace(os.sep, "/")
            if rel.startswith(SKIP_DIRS):
                counts["skipped debug"] += 1
                continue
            if rel.endswith(".png"):
                im = np.asarray(Image.open(p).convert("RGBA"))
                textures[rel] = texture_fact(rel, im)
                textures[rel]["mode"] = Image.open(p).mode
                counts["texture png"] += 1
            elif kept_file(rel):
                dst = os.path.join(kept_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(p, dst)
                counts["kept " + rel.split("/")[0]] += 1
            else:
                counts["regenerated/dropped " + os.path.splitext(rel)[1]] += 1
    json.dump(textures, open(os.path.join(spec, "textures.json"), "w"), separators=(",", ":"))
    audio = audio_facts(src)
    json.dump(audio, open(os.path.join(spec, "audio.json"), "w"), separators=(",", ":"))
    for k, v in sorted(counts.items()):
        print(f"{v:6d} {k}")
    for k, v in audio.items():
        print(f"audio {k}: {len(v['waves'])} waves, rate {v['rate']}, tbl {v['tbl_size']} bytes")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
