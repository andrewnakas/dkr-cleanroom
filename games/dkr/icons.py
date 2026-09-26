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


def _balloon(c, dark):
    return {"base": {"grad": [c, dark]},
            "ops": [{"sphere": [0.5, 0.36, 0.46, 0.36], "c": c}, {"hl": [0.36, 0.2, 0.08]},
                    {"hl": [0.3, 0.3, 0.035]}, {"outline": 1, "c": [40, 30, 30]}]}


def _amulet(pieces, piece_c):
    """Amulet progress icon: a grey medallion with `pieces` of 4 quarters in colour."""
    grey = [175, 178, 185]
    ops = [{"sphere": [0.5, 0.52, 0.46, 0.44], "c": grey}]
    quads = [[[0.5, 0.52], [0.5, 0.0], [0.0, 0.0], [0.0, 0.52]], [[0.5, 0.52], [0.5, 0.0], [1.0, 0.0], [1.0, 0.52]],
             [[0.5, 0.52], [1.0, 0.52], [1.0, 1.0], [0.5, 1.0]], [[0.5, 0.52], [0.0, 0.52], [0.0, 1.0], [0.5, 1.0]]]
    for q in quads[:pieces]:
        ops.append({"poly": q, "c": piece_c})
    ops += [{"line": [[0.5, 0.1], [0.5, 0.94]], "w": 0.03, "c": [90, 90, 100]},
            {"line": [[0.06, 0.52], [0.94, 0.52]], "w": 0.03, "c": [90, 90, 100]},
            {"ring": [0.5, 0.52, 0.42, 0.4], "w": 0.05, "c": [110, 100, 80]}, {"hl": [0.36, 0.32, 0.06]},
            {"outline": 1, "c": [50, 40, 20]}]
    return {"base": [175, 178, 185], "ops": ops}


M = "textures/2d/menu/"
SKY = {"grad": [[150, 210, 255], [230, 245, 255]]}


def vehicle(kind, sel):
    ops = [{"rect": [0, 0.78, 1, 1], "c": [110, 190, 80]}]
    body = [230, 40, 40] if sel == 0 else [250, 200, 40]
    if kind == "car":
        ops += [{"poly": [[0.22, 0.7], [0.3, 0.45], [0.62, 0.42], [0.8, 0.55], [0.82, 0.7]], "c": body},
                {"e": [0.46, 0.4, 0.07, 0.1], "c": [120, 70, 40]},
                {"e": [0.46, 0.3, 0.06, 0.06], "c": [220, 40, 40]},
                {"e": [0.32, 0.74, 0.08, 0.16], "c": [30, 30, 35]}, {"e": [0.72, 0.74, 0.08, 0.16], "c": [30, 30, 35]},
                {"e": [0.32, 0.74, 0.03, 0.06], "c": [200, 200, 210]}, {"e": [0.72, 0.74, 0.03, 0.06], "c": [200, 200, 210]}]
    elif kind == "hover":
        ops += [{"e": [0.52, 0.66, 0.34, 0.14], "c": [40, 40, 50]},
                {"poly": [[0.2, 0.62], [0.3, 0.45], [0.7, 0.45], [0.84, 0.62]], "c": body},
                {"e": [0.5, 0.38, 0.07, 0.1], "c": [120, 70, 40]},
                {"e": [0.5, 0.28, 0.06, 0.06], "c": [220, 40, 40]},
                {"e": [0.85, 0.45, 0.06, 0.18], "c": [200, 200, 210]}]
    else:
        ops += [{"poly": [[0.18, 0.5], [0.3, 0.4], [0.78, 0.42], [0.86, 0.5], [0.3, 0.6]], "c": body},
                {"poly": [[0.38, 0.5], [0.62, 0.5], [0.56, 0.72], [0.42, 0.72]], "c": [255, 255, 255]},
                {"poly": [[0.2, 0.44], [0.24, 0.22], [0.3, 0.42]], "c": body},
                {"e": [0.9, 0.46, 0.03, 0.2], "c": [200, 200, 210]},
                {"e": [0.5, 0.33, 0.06, 0.09], "c": [120, 70, 40]}]
    return {"base": SKY, "ops": ops}


def tt_face(awake):
    ops = [{"e": [0.3, 0.52, 0.22, 0.38], "c": [230, 40, 40]}, {"e": [0.3, 0.52, 0.18, 0.32], "c": [255, 230, 40]}]
    if awake:
        ops += [{"eye": {"c": [0.24, 0.45], "r": [0.05, 0.1], "iris": [30, 30, 30], "irisr": 0.6}},
                {"eye": {"c": [0.36, 0.45], "r": [0.05, 0.1], "iris": [30, 30, 30], "irisr": 0.6}},
                {"arc": [0.3, 0.6, 0.08, 0.1, 15, 165], "w": 0.04, "c": [120, 30, 20]}]
    else:
        ops += [{"arc": [0.24, 0.45, 0.05, 0.05, 20, 160], "w": 0.03, "c": [30, 30, 30]},
                {"arc": [0.36, 0.45, 0.05, 0.05, 20, 160], "w": 0.03, "c": [30, 30, 30]},
                {"line": [[0.6, 0.25], [0.7, 0.25], [0.6, 0.4], [0.7, 0.4]], "w": 0.04, "c": [40, 60, 200]},
                {"line": [[0.74, 0.12], [0.84, 0.12], [0.74, 0.27], [0.84, 0.27]], "w": 0.04, "c": [40, 60, 200]}]
    return {"base": SKY, "ops": ops}


OPTION_BG = {"controller_pak": ([180, 90, 230], [90, 30, 150]), "external_data": ([200, 220, 240], [120, 140, 170]),
             "ghosts": ([240, 80, 80], [60, 80, 220]), "n64": ([255, 230, 90], [200, 160, 20]),
             "rubbishbin": ([90, 200, 255], [30, 90, 200]), "times": ([150, 240, 110], [40, 150, 50])}


def option_icon(kind):
    top, bot = OPTION_BG[kind]
    if kind in ("controller_pak", "external_data"):
        ops = [{"rect": [0.25, 0.2, 0.75, 0.8], "c": [70, 70, 80]}, {"rect": [0.3, 0.26, 0.7, 0.5], "c": [220, 220, 230]},
               {"line": [[0.35, 0.8], [0.35, 0.88], [0.65, 0.88], [0.65, 0.8]], "w": 0.04, "c": [200, 180, 60]}]
        if kind == "external_data":
            ops.append({"poly": [[0.45, 0.55], [0.55, 0.55], [0.55, 0.65], [0.62, 0.65], [0.5, 0.76],
                                 [0.38, 0.65], [0.45, 0.65]], "c": [230, 40, 40]})
    elif kind == "ghosts":
        ops = []
        for cx, c in ((0.36, [245, 245, 255]), (0.64, [220, 230, 255])):
            ops += [{"e": [cx, 0.42, 0.17, 0.2], "c": c}, {"rect": [cx - 0.17, 0.42, cx + 0.17, 0.72], "c": c},
                    {"poly": [[cx - 0.17, 0.72], [cx - 0.1, 0.8], [cx - 0.04, 0.72], [cx + 0.04, 0.8],
                              [cx + 0.1, 0.72], [cx + 0.17, 0.8], [cx + 0.17, 0.72]], "c": c},
                    {"e": [cx - 0.06, 0.42, 0.03, 0.05], "c": [30, 30, 40]},
                    {"e": [cx + 0.06, 0.42, 0.03, 0.05], "c": [30, 30, 40]}]
    elif kind == "n64":
        ops = [{"poly": [[0.12, 0.6], [0.3, 0.4], [0.7, 0.4], [0.88, 0.6], [0.8, 0.78], [0.2, 0.78]], "c": [70, 70, 80]},
               {"rect": [0.35, 0.44, 0.65, 0.54], "c": [40, 40, 45]}, {"e": [0.72, 0.66, 0.04, 0.04], "c": [230, 40, 40]}]
    elif kind == "rubbishbin":
        ops = [{"poly": [[0.3, 0.3], [0.7, 0.3], [0.65, 0.85], [0.35, 0.85]], "c": [200, 205, 215]},
               {"rect": [0.26, 0.24, 0.74, 0.3], "c": [150, 155, 165]}, {"rect": [0.45, 0.18, 0.55, 0.24], "c": [150, 155, 165]},
               {"line": [[0.42, 0.38], [0.44, 0.78]], "w": 0.03, "c": [130, 135, 145]},
               {"line": [[0.58, 0.38], [0.56, 0.78]], "w": 0.03, "c": [130, 135, 145]}]
    else:
        ops = [{"e": [0.5, 0.52, 0.32, 0.32], "c": [230, 40, 40]}, {"e": [0.5, 0.52, 0.27, 0.27], "c": [255, 245, 220]},
               {"line": [[0.5, 0.52], [0.5, 0.32]], "w": 0.04, "c": [30, 30, 30]},
               {"line": [[0.5, 0.52], [0.64, 0.6]], "w": 0.04, "c": [30, 30, 30]},
               {"rect": [0.46, 0.14, 0.54, 0.22], "c": [230, 40, 40]}]
    return {"base": {"grad": [top, bot]}, "ops": ops}


def menu_briefs(textures):
    out = {}
    for kind in ("car", "hover", "plane"):
        for sel in (0, 1):
            rel = M + "%s_icon_%d.png" % (kind, sel)
            if rel in textures:
                out[rel] = vehicle(kind, sel)
    for on in ("on", "off"):
        for f in (0, 1):
            rel = M + "time_trial_%s_icon_%d.png" % (on, f)
            if rel in textures:
                out[rel] = tt_face(on == "on")
    for kind in OPTION_BG:
        rel = M + "icon_%s.png" % kind
        if rel in textures:
            out[rel] = option_icon(kind)
    gold = ([255, 235, 90], [200, 140, 20], [90, 50, 0])
    dark = ([90, 90, 100], [40, 40, 50], [10, 10, 15])
    for rel, (a, b, e) in ((M + "icon_key_collected.png", gold), (M + "icon_key_not_collected.png", dark),
                           (M + "icon_trophy_collected.png", gold), (M + "icon_trophy_not_collected.png", dark),
                           (M + "tt_beaten_icon.png", gold)):
        if rel in textures:
            out[rel] = silhouette(a, b, e)
    return out


def sprite_briefs():
    """Multi-piece world sprites (pickups) painted over their kept silhouettes."""
    O = "sprites/objects/"
    return {
        "sprites/menu/icon_tt_amulet.json": [_amulet(k, [255, 215, 60]) for k in range(5)],
        "sprites/menu/icon_wizpig_amulet_v79.json": [_amulet(k, [255, 215, 60]) for k in range(5)],
        O + "balloon_boost_v79.json": _balloon([80, 140, 255], [20, 50, 170]),
        O + "balloon_missle_v79.json": _balloon([255, 70, 60], [160, 10, 10]),
        O + "balloon_magnet_v79.json": _balloon([200, 110, 255], [90, 30, 160]),
        O + "balloon_shield_v79.json": _balloon([255, 230, 70], [200, 140, 10]),
        O + "balloon_trap_v79.json": _balloon([90, 230, 90], [20, 130, 40]),
        O + "balloon_gold_v79.json": _balloon([255, 215, 60], [190, 120, 10]),
        O + "balloon_silver_v79.json": _balloon([235, 240, 250], [140, 150, 170]),
        O + "banana_v79.json": {"base": {"grad": [[255, 245, 110], [230, 180, 20]]},
                                "ops": [{"outline": 1, "c": [110, 70, 0]}]},
        O + "silver_coin_v79.json": {"base": {"grad": [[250, 250, 255], [150, 160, 180]]},
                                     "ops": [{"ring": [0.5, 0.5, 0.3, 0.3], "w": 0.06, "c": [120, 130, 150]},
                                             {"hl": [0.38, 0.32, 0.07]}, {"outline": 1, "c": [70, 75, 90]}]},
        O + "egg.json": {"base": {"grad": [[255, 252, 240], [220, 200, 160]]},
                         "ops": [{"hl": [0.38, 0.3, 0.08]}, {"outline": 1, "c": [120, 90, 60]}]},
        O + "bomb.json": {"base": {"grad": [[90, 90, 110], [20, 20, 30]]},
                          "ops": [{"hl": [0.36, 0.34, 0.07]}, {"outline": 1, "c": [0, 0, 0]}]},
    }
