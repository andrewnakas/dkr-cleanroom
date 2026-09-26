"""CLEAN ROOM: tileable procedural surface detail for world textures.

The kept 4x4 (16x16) colour grid gives each texture its colours; the texture
name picks one of our own material patterns (grass, sand, rock, wood, brick,
roof tiles, snow, water, metal, fur) that modulates it. All noise is built
periodic (FFT-filtered white noise), so textures tile without seams.

apply(rel, d) -> RGBA float image, or None when no material fits.
"""
import re

import numpy as np

from cleanroom.decomp.gen import h32, unpack_alpha2, upsample_grid

SKIP = re.compile(r"eye|mouth|face|sign|logo|number|digit|envmap|shadow|sky|gradient|light|flag|icon|font|"
                  r"letter|smile|nose|cheek|teeth|tongue|window|arrow|neon|balloon|trophy|portrait|screen|"
                  r"head|lowpoly|charselect|goggles|cap_|_cap|hat|billboard")

CLASSES = [
    ("brick", r"brick"),
    ("tiles", r"roof|tile"),
    ("bark", r"bark|trunk"),
    ("wood", r"wood|log|plank|fence|crate|barrel|board|bridge|jetty|pier|hut"),
    ("grass", r"grass|bush|leaf|leaves|hedge|jungle|moss|mossy|fern|plant|vine|weed"),
    ("snow", r"snow|ice|icy|frost|frozen|igloo"),
    ("water", r"water|sea|wave|lagoon|lake|river|stream|waterfall|pool"),
    ("grain", r"sand|sandy|beach|dirt|path|ground|mud|road|track|floor|earth|soil"),
    ("rock", r"stone|rock|cliff|boulder|cave|wall|castle|volcano|lava|mountain|canyon|crystal|column|pillar|arch"),
    ("metal", r"metal|steel|iron|spaceship|ship|pipe|panel|rail|guardrail|tower|rocket|machine|space"),
    ("fur", r"fur|skin|feather|hair|wool"),
]


MENU = {"track_select_bg_dino_domain": "grain", "track_select_bg_dragon_forest": "grass",
        "track_select_bg_sherbet_island": "grain", "track_select_bg_snowflake_mountain": "snow",
        "track_select_bg_future_fun_land": "metal", "cobble_panel": "rock", "portal_panel": "water",
        "wood_panel": "wood", "track_select_locked": "rock", "track_select_unlocked": "grass"}


def classify(rel):
    name = rel.rsplit("/", 1)[-1][:-4].lower()
    if rel.startswith("textures/2d/objects/") and not SKIP.search(name):
        if re.search(r"tree|bush|plant|palm|reed|leaves|fern", name):
            return "grass"
        if re.search(r"snowman", name):
            return "snow"
        return None
    if rel.startswith("textures/2d/menu/"):
        return MENU.get(re.sub(r"_\d+$", "", name))
    if not rel.startswith("textures/3d/") or SKIP.search(name):
        return None
    for cls, pat in CLASSES:
        if re.search(pat, name):
            return cls
    return None


def pnoise(h, w, seed, lo=0.0, hi=0.5, ax=1.0, ay=1.0):
    """Periodic band-limited noise, zero mean, unit std. lo/hi: radial band in
    cycles/pixel; ax/ay > 1 smooth the noise along x/y (streaks run along that axis)."""
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * ay
    fx = np.fft.fftfreq(w)[None, :] * ax
    r = np.sqrt(fx * fx + fy * fy)
    band = ((r >= lo) & (r <= hi)).astype(np.float64)
    band[0, 0] = 0
    out = np.real(np.fft.ifft2(np.fft.fft2(n) * band))
    s = out.std()
    return (out / s) if s > 1e-9 else out


def pattern(cls, h, w, seed):
    """(luminance modulation p (zero-mean-ish), amplitude, mortar mask or None)"""
    if cls == "grain":
        return pnoise(h, w, seed, 0.18, 0.5) * 0.7 + pnoise(h, w, seed + 1, 0.04, 0.12) * 0.5, 0.10, None
    if cls == "grass":
        blades = pnoise(h, w, seed, 0.12, 0.5, ax=1.0, ay=5.0)
        return blades + 0.4 * pnoise(h, w, seed + 1, 0.03, 0.1), 0.14, None
    if cls == "rock":
        base = pnoise(h, w, seed, 0.02, 0.12) + 0.5 * pnoise(h, w, seed + 1, 0.12, 0.35)
        ridge = 1.0 - np.abs(pnoise(h, w, seed + 2, 0.03, 0.09))
        cracks = np.clip((ridge - 0.9) * 10, 0, 1)
        return base - 2.0 * cracks, 0.14, None
    if cls == "wood":
        streaks = pnoise(h, w, seed, 0.05, 0.5, ax=7.0, ay=1.0)
        warp = pnoise(h, w, seed + 1, 0.01, 0.05) * 0.12
        y = np.arange(h)[:, None] / h
        rings = np.sin(2 * np.pi * (y * max(1, h // 16) + warp))
        return streaks + 0.35 * rings, 0.12, None
    if cls in ("brick", "tiles"):
        rows = max(2, (h // 8) // 2 * 2) if cls == "brick" else max(2, h // 8)
        cols = max(1, w // 16) if cls == "brick" else max(2, w // 8)
        y = np.arange(h)[:, None] / h * rows
        x = np.arange(w)[None, :] / w * cols
        row = np.floor(y)
        xo = x + (0.5 * (row % 2) if cls == "brick" else 0)
        mort = ((y - row) < 1.2 * rows / h) | ((xo - np.floor(xo)) < 1.2 * cols / w)
        cell = np.floor(xo) * 7 + row * 13
        shade = np.sin(cell * 12.9898) * 0.5
        return shade + 0.5 * pnoise(h, w, seed, 0.15, 0.5), 0.12, mort.astype(np.float64)
    if cls == "snow":
        sp = pnoise(h, w, seed, 0.3, 0.5)
        return 0.5 * pnoise(h, w, seed + 1, 0.03, 0.12) + np.clip(sp - 2.2, 0, 2), 0.06, None
    if cls == "water":
        rip = np.sin(pnoise(h, w, seed, 0.02, 0.08) * 3.0)
        return rip + 0.3 * pnoise(h, w, seed + 1, 0.1, 0.3, ax=2.5, ay=1.0), 0.09, None
    if cls == "metal":
        return pnoise(h, w, seed, 0.1, 0.5, ax=8.0, ay=1.0) + 0.3 * pnoise(h, w, seed + 1, 0.02, 0.06), 0.06, None
    if cls == "bark":
        return pnoise(h, w, seed, 0.05, 0.5, ax=1.0, ay=7.0) + 0.3 * pnoise(h, w, seed + 1, 0.02, 0.08), 0.14, None
    if cls == "fur":
        return pnoise(h, w, seed, 0.2, 0.5, ax=1.0, ay=3.0), 0.10, None
    return None


def apply(rel, d):
    cls = classify(rel)
    if cls is None:
        return None
    w, h = d["w"], d["h"]
    n = int(round(len(d["grid"]) ** 0.5))
    rgba = upsample_grid(d["grid"], n, w, h)
    p, amp, mortar = pattern(cls, h, w, h32("mat", rel))
    p = np.clip(p, -2.5, 2.5)
    rgba[..., :3] *= (1.0 + amp * p)[..., None]
    if mortar is not None:
        m = mortar[..., None]
        mc = rgba[..., :3] * 0.55 + 60
        rgba[..., :3] = rgba[..., :3] * (1 - m * 0.8) + mc * m * 0.8
    rgba[..., 3] = unpack_alpha2(d["alpha2"], w, h) if "alpha2" in d else 255
    return np.clip(rgba, 0, 255).astype(np.float32)
