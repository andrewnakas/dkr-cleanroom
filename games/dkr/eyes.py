"""CLEAN ROOM: eye and mouth textures as facepaint briefs generated from a
small table of our own descriptions (skin colour, eye layout, iris colour).
Blink frames: suffix _0 open ... _N closed (the lid comes down in steps).

briefs(textures) -> {relpath: brief}
"""
import re

import numpy as np

# name: skin, eyes [(cx, cy, rx, ry)], iris, extras
CHAR = {
    "banjo_eyes": dict(skin=[190, 110, 50], eyes=[(0.3, 0.55, 0.17, 0.36), (0.7, 0.55, 0.17, 0.36)], iris=[25, 25, 70], irisr=0.5),
    "bumper_eyes": dict(skin=[130, 130, 140], eyes=[(0.3, 0.52, 0.15, 0.3), (0.7, 0.52, 0.15, 0.3)], iris=[170, 50, 40], irisr=0.5),
    "conker_eyes": dict(skin=[215, 95, 40], eyes=[(0.5, 0.52, 0.36, 0.44)], iris=[40, 110, 220], irisr=0.5, look=[0.15, 0.05]),
    "diddy_eye": dict(skin=[175, 95, 45], eyes=[(0.5, 0.55, 0.4, 0.42)], iris=[50, 90, 200], irisr=0.5, look=[0.1, 0.1]),
    "diddy_eye_noblink": dict(skin=[175, 95, 45], eyes=[(0.5, 0.55, 0.4, 0.42)], iris=[50, 90, 200], irisr=0.5, look=[0.1, 0.1]),
    "drumstick_eyes": dict(skin=[220, 30, 30], eyes=[(0.28, 0.5, 0.22, 0.38), (0.72, 0.5, 0.22, 0.38)], iris=[150, 40, 30], irisr=0.45),
    "krunch_eye": dict(skin=[120, 180, 30], eyes=[(0.5, 0.58, 0.38, 0.36)], iris=[40, 140, 40], irisr=0.5, lid0=0.3, lidc=[130, 80, 30]),
    "krunch_eye_lowpoly": dict(skin=[120, 180, 30], eyes=[(0.5, 0.58, 0.38, 0.36)], iris=[40, 140, 40], irisr=0.5, lid0=0.3, lidc=[130, 80, 30]),
    "pipsy_eyes": dict(skin=[250, 220, 40], eyes=[(0.5, 0.55, 0.38, 0.4)], iris=[40, 110, 220], irisr=0.5),
    "timber_eye": dict(skin=[250, 120, 20], eyes=[(0.5, 0.5, 0.36, 0.4)], iris=[200, 130, 20], irisr=0.5),
    "tiptup_eye": dict(skin=[40, 220, 40], eyes=[(0.5, 0.5, 0.4, 0.36)], iris=[40, 70, 200], irisr=0.45),
    "taj_eye": dict(skin=[80, 80, 240], eyes=[(0.5, 0.55, 0.4, 0.4)], iris=[40, 90, 220], irisr=0.45),
    "tt_eye": dict(skin=[255, 235, 10], eyes=[(0.5, 0.62, 0.38, 0.26)], iris=[170, 50, 40], irisr=0.5, brow=True),
    "tt_eye_still": dict(skin=[255, 235, 10], eyes=[(0.5, 0.62, 0.38, 0.26)], iris=[170, 50, 40], irisr=0.5, brow=True),
    "stopwatch_eye": dict(skin=[255, 235, 10], eyes=[(0.5, 0.62, 0.38, 0.26)], iris=[170, 50, 40], irisr=0.5, brow=True),
    "whale_eye": dict(skin=[130, 70, 200], eyes=[(0.5, 0.52, 0.4, 0.4)], iris=[220, 60, 200], irisr=0.5, lash=True),
    "wizpig_eye": dict(skin=[200, 110, 20], eyes=[(0.5, 0.55, 0.38, 0.36)], sclera=[250, 220, 40], iris=[200, 40, 20], irisr=0.45),
    "bubbler_eye": dict(skin=[220, 20, 20], eyes=[(0.5, 0.5, 0.4, 0.4)], sclera=[250, 225, 40], iris=[190, 30, 20], irisr=0.5),
    "bluey_eye": dict(skin=[250, 235, 170], eyes=[(0.5, 0.55, 0.4, 0.4)], iris=[40, 60, 200], irisr=0.45, lid0=0.2, lidc=[40, 60, 200]),
    "smokey_eye": dict(skin=[150, 200, 30], eyes=[(0.5, 0.5, 0.4, 0.36)], sclera=[225, 235, 70], iris=[90, 110, 20], irisr=0.5),
}

LIDS = {1: [0.0], 2: [0.0, 1.0], 3: [0.0, 0.55, 1.0], 4: [0.0, 0.45, 0.8, 1.0]}

MOUTHS = {
    "tt_mouth_smile": ("smile", [255, 235, 10]),
    "stopwatch_mouth_happy": ("grin", [255, 235, 10]),
    "stopwatch_mouth_open_mouth": ("open", [255, 235, 10]),
    "stopwatch_mouth_worried": ("wavy", [255, 235, 10]),
    "bronze_trophy_smile": ("smile", [205, 130, 60]),
    "gold_silver_trophy_mouth": ("smile", [230, 200, 80]),
    "conkey_mouth": ("teeth", [245, 220, 170]),
    "timber_mouth": ("smile", [250, 245, 235]),
    "timber_mouth_lowpoly": ("smile", [250, 245, 235]),
    "smokey_mouth": ("teeth", [250, 240, 20]),
    "krunch_mouth": ("teeth", [180, 210, 60]),
}


def _eye_ops(d, lid, rel):
    ops = []
    for (cx, cy, rx, ry) in d["eyes"]:
        look = list(d.get("look", [0, 0]))
        if len(d["eyes"]) == 2:
            look = [0.15 if cx < 0.5 else -0.15, 0.05]
        e = {"c": [cx, cy], "r": [rx, ry], "sclera": d.get("sclera", [250, 250, 250]), "iris": d["iris"],
             "irisr": d.get("irisr", 0.5), "look": look, "border": 0.08, "borderc": [30, 20, 20],
             "lid": max(lid, d.get("lid0", 0.0) if lid < 0.999 else lid), "lidc": d.get("lidc", d["skin"])}
        if d.get("lash"):
            e["lash"] = [30, 10, 40]
            e["lashw"] = 0.04
        ops.append({"eye": e})
        if lid >= 0.999:
            ops.append({"arc": [cx, cy + ry * 0.2, rx * 0.9, ry * 0.25, 20, 160], "w": 0.05, "c": [40, 20, 20]})
    if d.get("brow"):
        ops.append({"arc": [0.5, 0.36, 0.3, 0.12, 200, 340], "w": 0.07, "c": [20, 20, 20]})
    return ops


def _mouth(kind, skin):
    ops = []
    if kind == "smile":
        ops = [{"arc": [0.5, 0.35, 0.36, 0.35, 20, 160], "w": 0.1, "c": [30, 10, 10]}]
    elif kind == "grin":
        ops = [{"poly": [[0.12, 0.35], [0.88, 0.35], [0.7, 0.75], [0.3, 0.75]], "c": [40, 5, 10]},
               {"e": [0.5, 0.66, 0.16, 0.08], "c": [210, 40, 50]}]
    elif kind == "open":
        ops = [{"e": [0.5, 0.5, 0.14, 0.2], "c": [40, 5, 10]}, {"e": [0.5, 0.6, 0.08, 0.08], "c": [200, 40, 50]}]
    elif kind == "wavy":
        ops = [{"line": [[0.1, 0.55], [0.25, 0.45], [0.4, 0.55], [0.55, 0.45], [0.7, 0.55], [0.9, 0.45]], "w": 0.08, "c": [30, 10, 10]}]
    elif kind == "teeth":
        ops = [{"e": [0.5, 0.5, 0.4, 0.22], "c": [80, 20, 20]},
               {"rect": [0.2, 0.3, 0.8, 0.45], "c": [255, 255, 250]},
               {"line": [[0.35, 0.3], [0.35, 0.45]], "w": 0.03, "c": [150, 150, 150]},
               {"line": [[0.5, 0.3], [0.5, 0.45]], "w": 0.03, "c": [150, 150, 150]},
               {"line": [[0.65, 0.3], [0.65, 0.45]], "w": 0.03, "c": [150, 150, 150]}]
    return {"base": skin, "ops": ops}


def _generic_eye(d):
    """Unlisted creature eye: the kept colour grid as the skin, our own round eye."""
    return {"base": "grid", "keep_alpha": True, "detail": 0.03,
            "ops": [{"eye": {"c": [0.5, 0.5], "r": [0.36, 0.36], "iris": [40, 30, 20], "irisr": 0.5, "border": 0.08,
                             "borderc": [30, 20, 20]}}]}


def briefs(textures):
    out = {}
    groups = {}
    for rel in textures:
        if not rel.startswith("textures/3d/"):
            continue
        name = rel.rsplit("/", 1)[1][:-4]
        m = re.match(r"(.+?)_(\d)$", name)
        base, idx = (m.group(1), int(m.group(2))) if m else (name, 0)
        if base in CHAR or name in CHAR:
            key = name if name in CHAR else base
            groups.setdefault(key, []).append((idx if key == base else 0, rel))
        elif name in MOUTHS:
            kind, skin = MOUTHS[name]
            out[rel] = _mouth(kind, skin)
        elif re.search(r"(^|_)eye($|_)", name) and "socket" not in name and "brow" not in name:
            out[rel] = _generic_eye(textures[rel])
    for key, frames in groups.items():
        d = CHAR[key]
        n = max(i for i, _ in frames) + 1
        lids = LIDS.get(n, list(np.linspace(0, 1, n)))
        for i, rel in frames:
            out[rel] = {"base": d["skin"], "ops": _eye_ops(d, lids[min(i, len(lids) - 1)], rel)}
            if "alpha2" in textures[rel]:
                out[rel]["keep_alpha"] = True
    return out
