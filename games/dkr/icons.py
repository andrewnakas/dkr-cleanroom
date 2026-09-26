"""CLEAN ROOM: HUD / menu icons as facepaint briefs generated in code (our own
designs): weapon icons per level, turn indicators, reticles, balloon icons,
banana, egg, speedometer needle and dial, checkered flag frames.

briefs(textures) -> {relpath: brief}; rendered by games.dkr.faces.render.
"""
import math

H = "textures/2d/hud/"

FLAME = [[255, 140, 30], [60, 220, 255], [230, 60, 230]]


def tile(frame, top, bot, ops):
    return {"_tile": {"frame": frame, "top": top, "bot": bot}, "ops": ops}


def weapon(kind, lvl):
    if kind == "boost":
        f = FLAME[lvl]
        ops = [
            {"poly": [[0.2, 0.3], [0.55, 0.18], [0.62, 0.34], [0.27, 0.46]], "c": [200, 205, 215]},
            {"poly": [[0.3, 0.5], [0.65, 0.38], [0.72, 0.54], [0.37, 0.66]], "c": [200, 205, 215]},
            {"line": [[0.2, 0.3], [0.55, 0.18]], "w": 0.03, "c": [250, 250, 255]},
            {"line": [[0.3, 0.5], [0.65, 0.38]], "w": 0.03, "c": [250, 250, 255]},
            {"poly": [[0.2, 0.32], [0.27, 0.46], [0.08, 0.62], [0.12, 0.42]], "c": f},
            {"poly": [[0.3, 0.52], [0.37, 0.66], [0.18, 0.88], [0.2, 0.62]], "c": f},
            {"poly": [[0.2, 0.35], [0.25, 0.44], [0.15, 0.52]], "c": [255, 250, 200]},
            {"poly": [[0.3, 0.55], [0.35, 0.64], [0.25, 0.74]], "c": [255, 250, 200]},
        ]
        return tile([40, 80, 230], [150, 200, 255], [70, 120, 220], ops)
    if kind == "magnet":
        tint = [[120, 170, 255], [120, 230, 255], [220, 150, 255]][lvl]
        ops = [
            {"arc": [0.5, 0.5, 0.24, 0.24, 0, 180], "w": 0.16, "c": [220, 30, 30]},
            {"rect": [0.18, 0.2, 0.34, 0.5], "c": [220, 30, 30]},
            {"rect": [0.66, 0.2, 0.82, 0.5], "c": [220, 30, 30]},
            {"rect": [0.18, 0.14, 0.34, 0.26], "c": [225, 230, 240]},
            {"rect": [0.66, 0.14, 0.82, 0.26], "c": [225, 230, 240]},
            {"line": [[0.12, 0.1], [0.06, 0.02]], "w": 0.03, "c": [255, 255, 255]},
            {"line": [[0.88, 0.1], [0.94, 0.02]], "w": 0.03, "c": [255, 255, 255]},
        ]
        return tile([140, 40, 200], tint, [60, 60, 170], ops)
    if kind == "rocket":
        body = [[240, 240, 245], [255, 230, 90], [120, 255, 140]][lvl]
        ops = [
            {"poly": [[0.25, 0.75], [0.62, 0.38], [0.72, 0.48], [0.35, 0.85]], "c": body},
            {"poly": [[0.62, 0.38], [0.84, 0.16], [0.72, 0.48]], "c": [220, 30, 30]},
            {"poly": [[0.25, 0.75], [0.14, 0.7], [0.3, 0.6]], "c": [220, 30, 30]},
            {"poly": [[0.35, 0.85], [0.4, 0.96], [0.5, 0.7]], "c": [220, 30, 30]},
            {"poly": [[0.25, 0.75], [0.35, 0.85], [0.12, 0.96], [0.14, 0.88]], "c": [255, 170, 30]},
            {"e": [0.55, 0.55, 0.05, 0.05], "c": [60, 150, 230]},
        ]
        return tile([200, 30, 30], [255, 150, 90], [200, 60, 30], ops)
    if kind == "shield":
        c = [[240, 40, 40], [40, 120, 240], [200, 60, 220]][lvl]
        ops = [{"glow": [0.5, 0.5, 0.5, 0.5], "c": [255, 255, 180]},
               {"e": [0.5, 0.5, 0.09, 0.09], "c": c}]
        for k in range(3):
            a = math.radians(-90 + 120 * k)
            ops.append({"poly": [[0.5 + 0.12 * math.cos(a - 0.5), 0.5 + 0.12 * math.sin(a - 0.5)],
                                 [0.5 + 0.34 * math.cos(a - 0.5), 0.5 + 0.34 * math.sin(a - 0.5)],
                                 [0.5 + 0.34 * math.cos(a + 0.5), 0.5 + 0.34 * math.sin(a + 0.5)],
                                 [0.5 + 0.12 * math.cos(a + 0.5), 0.5 + 0.12 * math.sin(a + 0.5)]], "c": c})
        return tile([230, 190, 30], [255, 240, 120], [250, 150, 30], ops)
    if kind == "trap":
        if lvl == 0:
            ops = [{"poly": [[0.5, 0.14], [0.68, 0.5], [0.32, 0.5]], "c": [30, 25, 30]},
                   {"e": [0.5, 0.6, 0.2, 0.22], "c": [30, 25, 30]},
                   {"e": [0.43, 0.56, 0.05, 0.08], "c": [150, 150, 170]}]
        elif lvl == 1:
            ops = [{"e": [0.5, 0.52, 0.3, 0.3], "c": [150, 220, 255]},
                   {"ring": [0.5, 0.52, 0.3, 0.3], "w": 0.04, "c": [240, 250, 255]},
                   {"e": [0.4, 0.42, 0.07, 0.06], "c": [255, 255, 255]}]
        else:
            ops = [{"e": [0.5, 0.55, 0.25, 0.25], "c": [40, 40, 50]}]
            for k in range(8):
                a = math.radians(45 * k)
                ops.append({"line": [[0.5 + 0.2 * math.cos(a), 0.55 + 0.2 * math.sin(a)],
                                     [0.5 + 0.36 * math.cos(a), 0.55 + 0.36 * math.sin(a)]], "w": 0.05, "c": [40, 40, 50]})
            ops.append({"e": [0.42, 0.46, 0.06, 0.05], "c": [160, 160, 180]})
        return tile([30, 170, 40], [170, 250, 150], [40, 150, 60], ops)
    return None


def arrow(kind):
    """Turn indicators: magenta->yellow arrows with a dark rim, kept alpha shape
    replaced by our own arrow (transparent background)."""
    c = [240, 60, 200]
    rim = [90, 0, 70]
    if kind == "down":
        shape = [[0.35, 0.05], [0.65, 0.05], [0.65, 0.5], [0.9, 0.5], [0.5, 0.95], [0.1, 0.5], [0.35, 0.5]]
        return {"base": "clear", "ops": [{"poly": shape, "c": rim, "grow": 0.05}, {"poly": shape, "c": c}]}
    if kind == "caution":
        return {"base": "clear", "ops": [{"rect": [0.3, 0.04, 0.7, 0.66], "c": [250, 220, 40]},
                                          {"e": [0.5, 0.85, 0.2, 0.1], "c": [250, 220, 40]},
                                          {"rect": [0.42, 0.1, 0.58, 0.6], "c": [220, 30, 30]},
                                          {"e": [0.5, 0.85, 0.1, 0.06], "c": [220, 30, 30]}]}
    return None


def silhouette(top, bot, edge, ops=None, ow=1):
    """Kept alpha outline as the shape; our own gradient fill and dark rim."""
    return {"base": {"grad": [top, bot]}, "keep_alpha": True, "ops": (ops or []) + [{"outline": ow, "c": edge}]}


def checker_flag(phase):
    ops = []
    n, m = 6, 4
    for i in range(n):
        for j in range(m):
            if (i + j) % 2:
                continue
            x0, x1 = i / n, (i + 1) / n
            wob = 0.06 * math.sin(phase + i * 1.1)
            y0, y1 = j / m + wob, (j + 1) / m + wob
            ops.append({"poly": [[x0, y0], [x1, y0 + 0.03], [x1, y1 + 0.03], [x0, y1]], "c": [25, 25, 30]})
    return {"base": [245, 245, 245], "keep_alpha": True, "ops": ops + [{"outline": 1, "c": [60, 60, 70]}]}


SIMPLE = {
    "indicatoricon_down": ([255, 240, 70], [240, 40, 200], [110, 0, 90]),
    "indicatoricon_slight_turn": ([255, 240, 70], [240, 40, 200], [110, 0, 90]),
    "indicatoricon_turn": ([255, 240, 70], [240, 40, 200], [110, 0, 90]),
    "indicatoricon_uturn": ([255, 240, 70], [240, 40, 200], [110, 0, 90]),
    "indicatoricon_caution": ([255, 240, 70], [240, 40, 200], [110, 0, 90]),
    "reticle_circle": ([255, 255, 255], [220, 225, 240], [40, 40, 60]),
    "reticle_square": ([255, 255, 255], [220, 225, 240], [40, 40, 60]),
    "reticle_x": ([255, 255, 255], [220, 225, 240], [40, 40, 60]),
    "retical_homing_0": ([255, 240, 90], [240, 170, 20], [80, 40, 0]),
    "retical_homing_1": ([255, 240, 90], [240, 170, 20], [80, 40, 0]),
    "speedometer_arrow": ([255, 250, 120], [250, 170, 20], [30, 50, 200]),
    "speedometer_ticks": ([255, 255, 255], [230, 230, 240], [60, 60, 80]),
    "banana_icon_0": ([255, 245, 110], [235, 190, 20], [110, 70, 0]),
    "banana_icon_1": ([255, 245, 110], [235, 190, 20], [110, 70, 0]),
    "egg_icon": ([255, 250, 235], [225, 205, 170], [120, 90, 60]),
}


def balloon(top, bot):
    return {"base": {"grad": [top, bot]}, "keep_alpha": True,
            "ops": [{"sphere": [0.5, 0.42, 0.38, 0.4], "c": top}, {"hl": [0.38, 0.26, 0.08]},
                    {"outline": 1, "c": [70, 50, 20]}]}


def briefs(textures):
    out = {}
    for name, (a, b, e) in SIMPLE.items():
        rel = H + name + ".png"
        if rel in textures:
            out[rel] = silhouette(a, b, e)
    for i in range(5):
        rel = H + "final_lap_%d.png" % i
        if rel in textures:
            out[rel] = checker_flag(i * 1.25)
    if H + "golden_balloon_icon.png" in textures:
        out[H + "golden_balloon_icon.png"] = balloon([255, 220, 60], [200, 140, 10])
    if H + "silver_balloon_icon.png" in textures:
        out[H + "silver_balloon_icon.png"] = balloon([235, 240, 250], [150, 160, 180])
    for kind in ("boost", "magnet", "rocket", "shield", "trap"):
        for lvl in range(3):
            rel = H + "weapon_icon_%s_%d.png" % (kind, lvl)
            if rel in textures:
                out[rel] = weapon(kind, lvl)
    return out
