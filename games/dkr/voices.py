"""Placeholder voice lines for DKR speech samples: Piper TTS in character
voices (not the original performers), fitted to each wave's length, best of
several takes by Whisper. Cached in games/dkr/voices/<sound name>.wav.

    python -m games.dkr.voices <spec dir> build [name ...]
    python -m games.dkr.voices <spec dir> map          # sound name -> wave, one line each

audio_gen uses voices.for_wave(ctl_name, wave_id) when a cached line exists.
"""
import json
import os
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("CLEANROOM_GAME", HERE)
CACHE = os.path.join(HERE, "voices")
SFX_CTL = "asset_audio_2.bin"


def lines():
    d = json.load(open(os.path.join(HERE, "voice_lines.json"), encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}


def sound_names(kept):
    b = open(os.path.join(kept, "audio/unknown/asset_audio_4.bin"), "rb").read()
    return [n.decode("latin1").replace("_snd", "") for n in b[4:].split(b"\n\x00")]


def name_to_wave(spec):
    """{sound name: wave _id} for the SFX bank's single instrument."""
    from cleanroom.audio import albank
    a = json.load(open(os.path.join(spec, "audio.json")))
    bf = albank.parse_bankfile(bytes.fromhex(a[SFX_CTL]["ctl_skeleton"]))
    sounds = bf["banks"][0]["insts"][0]["sounds"]
    names = sound_names(os.path.join(spec, "kept"))
    return {n: s["wave"]["_id"] for n, s in zip(names, sounds)}


_WAVE_INDEX = None


def for_wave(spec, ctl_name, wave_id):
    """Float samples of a cached voice line for this wave, or None."""
    global _WAVE_INDEX
    if ctl_name != SFX_CTL:
        return None
    if _WAVE_INDEX is None:
        n2w = name_to_wave(spec)
        _WAVE_INDEX = {}
        for name in lines():
            p = os.path.join(CACHE, name + ".wav")
            if name in n2w and os.path.exists(p):
                _WAVE_INDEX.setdefault(n2w[name], p)
    p = _WAVE_INDEX.get(wave_id)
    if not p:
        return None
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768


def build(spec, only=None):
    from cleanroom.voice import voices as V
    a = json.load(open(os.path.join(spec, "audio.json")))
    waves = {w["wave"]: w for w in a[SFX_CTL]["waves"]}
    rate = a[SFX_CTL]["rate"]
    n2w = name_to_wave(spec)
    os.makedirs(CACHE, exist_ok=True)
    summary = []
    L = lines()
    for name, v in L.items():
        if only and name not in only:
            continue
        if name not in n2w:
            summary.append(f"{name}: no such sound")
            continue
        n, hz = waves[n2w[name]]["n"], rate
        who = v["who"]
        base = V.CHARACTERS[who]["length"]
        f = 2 ** (V.CHARACTERS[who]["semitones"] / 12)
        for k in range(8):
            length = base * (0.88 ** k)
            raw, sr = V._piper(who, v["text"], length * f)
            x = V._trim(V._character(who, raw, sr, hz))
            if len(x) <= n:
                break
        takes = [x]
        for _ in range(3):
            raw, sr = V._piper(who, v["text"], length * f)
            y = V._trim(V._character(who, raw, sr, hz))
            if len(y) <= n:
                takes.append(y)
        scores = [V._hear_score(t, hz, v["text"]) for t in takes]
        x = takes[int(np.argmax(scores))]
        if max(scores) < 0.5:
            summary.append(f"{name} heard {max(scores):.0%}")
        if len(x) > n:
            summary.append(f"{name} squeezed {len(x) / n:.2f}")
            x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
        x = x / (np.abs(x).max() + 1e-9) * 0.9
        out = np.zeros(n, np.float32)
        out[:len(x)] = x[:n]
        with wave.open(os.path.join(CACHE, name + ".wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(hz)
            w.writeframes((out * 32767).astype("<i2").tobytes())
    print(f"voices: {len(L)} lines -> {CACHE}")
    print("notes:", "; ".join(summary) or "none")


if __name__ == "__main__":
    spec, cmd = sys.argv[1], sys.argv[2]
    if cmd == "build":
        build(spec, sys.argv[3:] or None)
    elif cmd == "map":
        m = name_to_wave(spec)
        for k in lines():
            print(k, m.get(k))
