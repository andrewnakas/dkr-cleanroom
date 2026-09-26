"""Practice pack for recording DKR character voices (PERSONAL USE: built from
the user's own ROM extraction; written outside the repo, never published).

Per character: a call-and-response track (reference clip at its playback
pitch, 0.3 s, an 80 ms 880 Hz beep, then a gap of 1.5x+1.5 s to repeat it),
the numbered reference clips, and SCRIPT.txt listing every slot in order.

    python -m games.dkr.practice <dirty tree> <spec dir> <out dir>
"""
import json
import os
import re
import struct
import sys
import wave

import numpy as np

from cleanroom.audio import albank
from games.dkr import voices as V
from games.dkr.extract_spec import decode_wave

HZ = 22050
# character: sound-name patterns (the game's own sample names)
CHARACTERS = {
    "diddy": [r"^diddy_", r"^name_diddy$"],
    "pipsy": [r"^pipsy", r"^name_pipsy$"],
    "timber": [r"^tiger", r"^timba\d", r"^name_timba$"],
    "krunch": [r"^new_krem", r"^name_krash$"],
    "conker": [r"^conker\d", r"^name_conker$"],
    "tiptup": [r"^tiptup\d", r"^name_tiptup$"],
    "banjo": [r"^banjo\d", r"^name_banjo$"],
    "drumstick": [r"^chick\d", r"^name_drumstick$"],
    "bumper": [r"^name_bumper$"],
    "tt": [r"^ticktock", r"^stopwatch_(snore|yippee)", r"^more_stopwatch", r"^new_tt_stuff", r"^name_ticktock$"],
    "taj": [r"^dean_(?!.*(DELAY|ECHO|PART))", r"^warden", r"^new_warden", r"^more_warden", r"^bahji"],
    "tricky": [r"^csuth_tricky\d+B?$", r"^tricky\d", r"^tricky_"],
    "bluey": [r"^drag_jc", r"^dragon_jc\d+$"],
    "wally": [r"^wally_(kr\d+|gethit|laugh)"],
    "bubbler": [r"^octopus\d", r"^octo_"],
    "wizpig": [r"^wizpig(?!.*(stamp|ship))", r"^pig_laugh"],
    "announcer": [r"^(get_ready|stopwatch_go|lap2|final_lap|wrong_way\d|press_start|race_record|lap_record|pro_am64)$"],
}


def beep(sr):
    t = np.arange(int(0.08 * sr)) / sr
    return (0.4 * np.sin(2 * np.pi * 880 * t) * np.hanning(len(t))).astype(np.float32)


def write(p, x, sr):
    with wave.open(p, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def main(dirty, spec, out):
    src = os.path.join(dirty, "assets", ".vanilla", "us.v80", "audio", "unknown")
    ctl = open(os.path.join(src, "asset_audio_2.bin"), "rb").read()
    tbl = open(os.path.join(src, "asset_audio_3.bin"), "rb").read()
    sounds = albank.parse_bankfile(ctl)["banks"][0]["insts"][0]["sounds"]
    names = V.sound_names(os.path.join(spec, "kept"))
    tab = open(os.path.join(spec, "kept", "audio/unknown/asset_audio_7_v79.bin"), "rb").read()
    pitch = {}
    for i in range(0, len(tab), 10):
        bite, _, _, p = struct.unpack(">HBBB", tab[i:i + 5])
        pitch.setdefault(bite, p)
    os.makedirs(out, exist_ok=True)
    script = ["DKR voice practice pack (personal use only; do not share).",
              "Each track: reference clip, beep, then your turn (same length plus 1.5 s).",
              "Record each character track straight through; keep the beeps in the recording.", ""]
    manifest = {}
    total = 0
    for who, pats in CHARACTERS.items():
        seen, slots = set(), []
        for i, (n, s) in enumerate(zip(names, sounds)):
            if any(re.search(p, n) for p in pats) and s["wave"]["_id"] not in seen:
                seen.add(s["wave"]["_id"])
                slots.append((i, n, s))
        if not slots:
            continue
        d = os.path.join(out, who)
        os.makedirs(d, exist_ok=True)
        track = []
        script.append(f"== {who} ({len(slots)} clips)")
        for k, (i, n, s) in enumerate(slots):
            x = decode_wave(tbl, s["wave"], None).astype(np.float32) / 32768
            sr = int(HZ * pitch.get(i, 100) / 100)
            if sr != HZ:
                import librosa
                x = librosa.resample(x, orig_sr=sr, target_sr=HZ).astype(np.float32)
            x = x / (np.abs(x).max() + 1e-9) * 0.8
            write(os.path.join(d, f"{k + 1:02d}_{n}.wav"), x, HZ)
            track += [x, np.zeros(int(0.3 * HZ), np.float32), beep(HZ),
                      np.zeros(int((1.5 * len(x) / HZ + 1.5) * HZ), np.float32)]
            script.append(f"  {k + 1:02d}  {n:28s} {len(x) / HZ:4.2f}s")
            manifest.setdefault(who, []).append({"n": k + 1, "sound": n, "wave": s["wave"]["_id"],
                                                 "pitch": pitch.get(i, 100)})
        write(os.path.join(out, f"track_{who}.wav"), np.concatenate(track), HZ)
        total += len(slots)
        script.append("")
    open(os.path.join(out, "SCRIPT.txt"), "w", encoding="utf-8").write("\n".join(script))
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print(f"practice pack: {total} clips, {len(manifest)} characters -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
