# Diddy Kong Racing clean room: status

Play: https://andrewnakas.github.io/dkr-cleanroom/ (published once the first clean site passed taint)

## Works
- **Clean web build boots and plays**: N64/Rare logos, attract flyby, title (our logo), PLAYER SELECT,
  CAUTION text, GAME SELECT, initials entry, Adventure intro and driving in the hub. Audio plays through
  (no underruns in a 90 s headless run).
- **Taint: 0 failing** (2,718 textures as RGBA, both sample tables raw, all 677 waves as PCM).
- Every texture regenerated: digest (4x4 grid + noise + kept 2-bit alpha) by default, plus drawn overrides:
  - 4 game fonts re-typeset (glyph cells placed by the kept font metrics) - `fonts.py`, checked with `font_check.py`
  - HUD words/numbers (FINAL, FINISH, GET READY, GO!, LAP, WRONG WAY, TIME, place numbers + ST/ND/RD/TH,
    timers, speedometer labels, rocket counters), menu option panels, title logo - `drawn.py` + `hud_text.json`
  - 25 track-name signs, EXIT signs, trophy numbers, door digits, "Nintendo" wordmark re-typeset
  - 10 HUD character portraits (`face_briefs.json`), 15 weapon icons (`icons.py`)
  - ~100 eye/mouth textures incl. blink frames (`eyes.py`)
- All samples resynthesised from outlines; banks keep exact sizes/offsets; our own VADPCM books and loop states.

## Decisions (log)
- **Web route = PC port + Emscripten** (playbook §4 route 1/2). Bruceleeto/Diddy-Kong-Racing has a small
  single-threaded SDL2 + GL 1.x port (`linux/`, ~3k lines). Replaced its GL layer with a WebGL2 shader
  (`games/dkr/web/gfx_web.c`), added Gamepad API input (`web/input_web.c`), Asyncify for the frame sleep,
  EEPROM saves in localStorage. Decided at ~30 min: dev build booted to the attract mode.
- **ROM = US v80** (Rev 1, sha1 6d96743d...). The port defaulted to v77; the web build defines VERSION_US_V80.
- **Asset tool** (`dkr_assets_tool`, C++17) does not build natively on Windows (wide `fs::path`). Built it
  with Emscripten for Node (`NODERAWFS`, `-fexceptions`, PCRE2 from source; `std::regex` rejects its
  patterns). Node preload fakes a POSIX cwd. Its gzip level-9 table is swapped for level-6 search settings
  in our build (noise-detailed textures made the 4096-chain search take 30+ min; now ~5 min).
- **Round trip**: dirty `assets.bin` rebuilt by the tool is byte-identical to the ROM's asset block (0xED1B0).
- **Kept facts** (user scope): geometry (level/object models, animations), object placement maps (gltf,
  checked image-free), text, sequences, game tables, TT ghosts. Spec lives in D:/n64work/dkr/spec (not committed).
- The tool's `debug/` extraction (raw retail texture dumps) is never copied to spec or clean.
- Signature fixes wasm needs: `osAiSetNextBuffer` returns s32; the game's own `f32 log()` renamed so SDL's
  `double log()` is not hijacked.
- Dev server port: **8731** dev (dirty, local only), **8732** clean.

## Next
- More icons: turn indicators, reticles, speedometer needle/dial, balloons, banana/egg, checkered flag,
  menu icons (trophies, keys, amulets, vehicle icons), track-select backgrounds.
- Character body textures that carry detail (Diddy's cap star, shirts), trophy art, Wizpig.
- Voices: placeholder TTS + practice pack (DKR has few voice clips; check the sfx bank for speech).
- In-race check (Tracks mode) and gamepad check.

## For the morning
- Play it with a controller; tell me what looks wrong first.
