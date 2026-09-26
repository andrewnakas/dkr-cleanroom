"""Sprite / texture indexing from the kept asset metadata (no pixels).

tex_index(kept) -> {"ASSET_TEX2D_...": "textures/2d/<...>.png" (first image)}
sprites(kept)   -> {sprite relpath: [frame: [piece: {rel, x, y, w, h}]]}
"""
import glob
import json
import os


def _load(p):
    return json.load(open(p, encoding="utf-8"))


def tex_json_index(kept, which="2d"):
    m = _load(os.path.join(kept, "asset_textures_%s.meta.json" % which))
    out = {}
    for name, sec in m["files"]["sections"].items():
        out[name] = "textures/%s/%s" % (which, sec["filename"])
    return out


def tex_images(kept, js_rel):
    j = _load(os.path.join(kept, js_rel))
    d = os.path.dirname(js_rel)
    return j, [d + "/" + im for im in j.get("images", [])]


def sprites(kept, sizes):
    order = _load(os.path.join(kept, "asset_textures_2d.meta.json"))["files"]["order"]
    idx = tex_json_index(kept, "2d")
    out = {}
    for p in glob.glob(os.path.join(kept, "sprites", "**", "*.json"), recursive=True):
        j = _load(p)
        if j.get("type") != "Sprite" or j.get("start-texture") not in idx:
            continue
        start = order.index(j["start-texture"])
        frames, k = [], start
        for n in j.get("frame-tex-count", []):
            pieces = []
            for t in order[k:k + n]:
                tj, ims = tex_images(kept, idx[t])
                for im in ims[:1]:
                    w, h = sizes.get(im, (0, 0))
                    pieces.append({"rel": im, "x": tj.get("sprite-x", 0), "y": tj.get("sprite-y", 0), "w": w, "h": h})
            frames.append(pieces)
            k += n
        rel = os.path.relpath(p, kept).replace(os.sep, "/")
        out[rel] = frames
    return out


if __name__ == "__main__":
    import sys
    kept = sys.argv[1]
    t = json.load(open(os.path.join(os.path.dirname(kept.rstrip("/")), "textures.json")))
    sizes = {k: (v["w"], v["h"]) for k, v in t.items()}
    for rel, frames in sorted(sprites(kept, sizes).items()):
        if any(len(f) > 1 for f in frames) or len(frames) > 1:
            print(rel, len(frames), "frames", [len(f) for f in frames][:6],
                  [(q["rel"].split("/")[-1], q["x"], q["y"], q["w"], q["h"]) for q in frames[0]][:4])
