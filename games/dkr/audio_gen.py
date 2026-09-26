"""CLEAN ROOM: DKR sound banks from spec/audio.json.

The ctl skeleton (instrument/keymap/envelope layout, books and loop states
zeroed) is filled in place, so every offset and the bank sizes stay exactly as
the game's fixed audio pools expect. Each wave is resynthesised from its
outline (cleanroom.audio.descriptor), encoded with our own VADPCM codebook of
the same shape (order 2, same predictor count), and its loop state is taken
from our own decoded stream.
"""
import hashlib
import json
import os
import struct

import numpy as np

from cleanroom.audio import descriptor, vadpcm

MUSIC_CTL = "asset_audio_0.bin"


def _seed(*parts):
    return int.from_bytes(hashlib.sha1("/".join(map(str, parts)).encode()).digest()[:4], "little")


def fit_predictors(x, n):
    """n order-2 predictors (a1, a2) fitted to our own signal by k-means over
    per-frame least-squares fits."""
    x = np.asarray(x, np.float64)
    fits = []
    for s in range(2, len(x) - 16, 16):
        y, p1, p2 = x[s:s + 16], x[s - 1:s + 15], x[s - 2:s + 14]
        if (y ** 2).sum() < 1e3:
            continue
        a, *_ = np.linalg.lstsq(np.stack([p1, p2], 1), y, rcond=None)
        fits.append(a)
    defaults = [(1.8, -0.82), (1.0, 0.0), (1.95, -0.96), (0.0, 0.0)]
    if len(fits) < n * 2:
        return defaults[:n]
    f = np.clip(np.asarray(fits), [-1.95, -0.98], [1.95, 0.98])
    order = np.argsort(f[:, 0])
    c = f[order[np.linspace(0, len(f) - 1, n).astype(int)]].copy()
    for _ in range(12):
        lab = np.argmin(((f[:, None, :] - c[None]) ** 2).sum(-1), 1)
        for k in range(n):
            if (lab == k).any():
                c[k] = f[lab == k].mean(0)
    out = []
    for a1, a2 in c:
        a2 = float(np.clip(a2, -0.98, 0.98))
        out.append((float(np.clip(a1, -(1 - a2) + 0.02, (1 - a2) - 0.02)), a2))
    return out


def wave_pcm(bank, w, rate, music):
    desc = json.loads(json.dumps(w["desc"]))
    if music and w.get("f0", 0) > 20:
        for f in desc["frames"]:
            if f["h"] > 0.3:
                f["f0"] = w["f0"]
    n = w["n"]
    x = descriptor.synthesize(desc, n, rate, seed=_seed(bank, w["wave"]))
    if music and w.get("f0", 0) > 20:
        # reinforce the fundamental: the outline's bands start at 40 Hz and a weak
        # fundamental makes low instruments read an octave high
        t = np.arange(n) / rate
        env = np.sqrt(np.convolve(np.asarray(x, np.float64) ** 2, np.ones(256) / 256, "same"))
        x = np.asarray(x, np.float64) + 0.6 * np.sqrt(2) * env * np.sin(2 * np.pi * w["f0"] * t)
    lp = w.get("loop")
    if lp and lp["count"] and lp["end"] <= n and lp["end"] - lp["start"] > 32:
        x = descriptor.make_loop_seamless(x, lp["start"], lp["end"])
    peak = np.abs(x).max()
    if peak > 0 and w.get("peak"):
        x = x * min(0.99, w["peak"] / 32768.0) / peak
    return np.clip(np.round(np.asarray(x, np.float64) * 32767), -32768, 32767).astype(np.int64)


def voice_pcm(v, w):
    """A cached placeholder voice line, scaled to the slot's peak level."""
    x = np.zeros(w["n"], np.float64)
    x[:min(len(v), w["n"])] = v[:w["n"]]
    peak = np.abs(x).max()
    if peak > 0:
        x = x * min(0.99, max(w.get("peak", 20000), 8000) / 32768.0) / peak
    return np.clip(np.round(x * 32767), -32768, 32767).astype(np.int64)


def build_bank(ctl_name, spec_bank, cache_dir=None, spec=None):
    from games.dkr import voices
    ctl = bytearray(bytes.fromhex(spec_bank["ctl_skeleton"]))
    tbl = bytearray(spec_bank["tbl_size"])
    rate = spec_bank["rate"]
    music = ctl_name == MUSIC_CTL
    for w in spec_bank["waves"]:
        v = voices.for_wave(spec, ctl_name, w["wave"]) if spec else None
        vkey = hashlib.sha1(v.tobytes()).hexdigest() if v is not None else ""
        key = hashlib.sha1(json.dumps([ctl_name, MUSIC_CTL, w, vkey, "fund1" if ctl_name == MUSIC_CTL else ""], sort_keys=True).encode()).hexdigest()[:16]
        cp = os.path.join(cache_dir, key + ".npz") if cache_dir else None
        if cp and os.path.exists(cp):
            z = np.load(cp)
            data, book, dec = z["data"].tobytes(), z["book"].tolist(), z["dec"]
        else:
            pcm = voice_pcm(v, w) if v is not None else wave_pcm(ctl_name, w, rate, music)
            book, dec = [], np.zeros(0, np.int64)
            if w["type"] == 1:        # RAW16
                data = pcm[:w["len"] // 2].astype(">i2").tobytes()
            else:
                bk = vadpcm.make_book(fit_predictors(pcm, w["npred"]))
                data, _, dec = vadpcm.encode(pcm, bk)
                book = bk["book"]
            if cp:
                np.savez(cp, data=np.frombuffer(data, np.uint8), book=np.asarray(book, np.int64), dec=dec)
        base = w["base"]
        data = data[:w["len"]]
        tbl[base:base + len(data)] = data
        if w["type"] == 0:
            off = int(w["book"].split("@")[1], 16)
            ctl[off + 8:off + 8 + 2 * len(book)] = struct.pack(">%dh" % len(book), *book)
            lp = w.get("loop")
            if lp:
                loff = int(lp["id"].split("@")[1], 16)
                st = vadpcm.loop_state(np.asarray(dec), lp["start"] & ~15)
                ctl[loff + 12:loff + 44] = struct.pack(">16h", *[max(-32768, min(32767, v)) for v in st])
    return bytes(ctl), bytes(tbl)
