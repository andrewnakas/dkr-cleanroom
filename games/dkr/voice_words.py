"""DIRTY ROOM (dev only): transcribe candidate speech samples with Whisper to
learn their words (text facts only; no audio is written).

    python -m games.dkr.voice_words <dirty tree> <spec dir> [name substrings...]
"""
import json
import os
import struct
import sys

import numpy as np

from cleanroom.audio import albank
from games.dkr import voices as V
from games.dkr.extract_spec import decode_wave


def main(dirty, spec, subs):
    src = os.path.join(dirty, "assets", ".vanilla", "us.v80", "audio", "unknown")
    ctl = open(os.path.join(src, "asset_audio_2.bin"), "rb").read()
    tbl = open(os.path.join(src, "asset_audio_3.bin"), "rb").read()
    bf = albank.parse_bankfile(ctl)
    sounds = bf["banks"][0]["insts"][0]["sounds"]
    names = V.sound_names(os.path.join(spec, "kept"))
    tab = open(os.path.join(spec, "kept", "audio/unknown/asset_audio_7_v79.bin"), "rb").read()
    pitch = {}
    for i in range(0, len(tab), 10):
        bite, _, _, p = struct.unpack(">HBBB", tab[i:i + 5])
        pitch.setdefault(bite, p)
    import librosa
    from faster_whisper import WhisperModel
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    seen = set()
    for i, (n, s) in enumerate(zip(names, sounds)):
        if subs and not any(k in n for k in subs):
            continue
        if any(t in n for t in ("DELAY", "ECHO", "LINK", "PART")) or s["wave"]["_id"] in seen:
            continue
        seen.add(s["wave"]["_id"])
        x = decode_wave(tbl, s["wave"], None).astype(np.float32) / 32768
        sr = 22050 * pitch.get(i, 100) / 100.0
        x16 = librosa.resample(x, orig_sr=sr, target_sr=16000)
        segs, _ = model.transcribe(np.concatenate([np.zeros(1600, np.float32), x16, np.zeros(8000, np.float32)]),
                                   language="en", beam_size=5)
        text = " ".join(t.text.strip() for t in segs)
        print(f"{n:24s} {len(x) / sr:4.2f}s p{pitch.get(i, 100):3d} | {text}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
