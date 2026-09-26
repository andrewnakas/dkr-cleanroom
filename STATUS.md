# Diddy Kong Racing clean room: status

Play: **https://andrewnakas.github.io/dkr-cleanroom/** (repo: andrewnakas/dkr-cleanroom, site on gh-pages)

## Works (verified in headless Chrome on the clean build)
- Boots: N64/Rare logos, attract flyby, attract demo races, title with our logo, OPTIONS menu.
- **Plays**: PLAYER SELECT -> CAUTION -> GAME SELECT (Adventure/Tracks) -> Tracks race with full HUD
  (place + suffix, LAP 1/3, banana count, TIME, WRONG WAY, weapon icon, minimap); Adventure intro + hub drive.
- Audio plays through (no underruns in 90 s runs). Keyboard + Gamepad API (standard mapping) input.
- **Taint: 0 failing** (2,718 textures as RGBA, both sample tables raw, all 677 waves as PCM).

## What is generated (all from spec facts + our own code)
- Textures: digest (4x4/16x16 grid + noise + kept 2-bit alpha) by default; **tileable procedural materials**
  by name for world textures (grass, sand/dirt, rock, wood, bark, brick, roof tiles, snow, water, metal, fur)
  and tree/bush billboards (`materials.py`).
- Readable: 4 game fonts re-typeset through the kept metrics (`fonts.py`, `font_check.py`); HUD words and
  numbers, menu option panels, title logo (`drawn.py`, `hud_text.json`); 25 track-name signs, EXIT signs,
  trophy numbers, door digits, wordmarks.
- Faces/sprites/pictures: 10 HUD portraits (`face_briefs.json`), ~100 eye/mouth textures with blink frames
  (`eyes.py`), weapon icons x3 levels, turn indicators, reticles, speedometer, checkered flag, balloon icons,
  pickups (weapon balloons, bananas, silver coins, eggs, bombs) painted across their multi-strip sprites,
  menu icons (vehicle pictures, option icons, TT on/off, keys, trophies, amulet progress) (`icons.py`, `faces.py`).
- Audio: every wave resynthesised from its outline; music instruments held at the kept median pitch; our own
  VADPCM books/loop states; banks keep exact sizes and offsets.

## Decisions (log)
- **Web route = PC port + Emscripten** (Bruceleeto/Diddy-Kong-Racing SDL2+GL port; WebGL2 shader renderer,
  Gamepad API, Asyncify pacing, localStorage EEPROM). Decided in the first 30 min.
- **ROM = US v80** (Rev 1); the web build defines VERSION_US_V80.
- **Asset tool** built with Emscripten for Node (NODERAWFS, -fexceptions, PCRE2 from source, POSIX-cwd preload);
  gzip level-9 search swapped for level-6 settings (noise textures: 30+ min -> ~4 min). Round trip of the dirty
  tree is byte-identical to the ROM's asset block.
- **Kept facts**: geometry (level/object models, animations), object placement maps (gltf, verified image-free),
  text, sequences, game tables, TT ghosts. The tool's `debug/` raw texture dumps are never used.
- **Bank roles**: asset_audio_0/1 = music ctl/tbl, 2/3 = SFX ctl/tbl, 7 = SFX table (bank sound + pitch),
  4 = SFX sound names. (First generation had music/SFX swapped for the pitch rule; fixed and regenerated.)
- **Voices: no TTS placeholders.** DKR's character "speech" samples are gibberish vocalisations (Whisper on the
  retail clips finds no consistent words - e.g. every `dean_*` "track name" is a mumble), so English TTS would
  be wrong. They stay resynthesised until the user records takes. Practice pack built (see morning list).
- **In-race hang fixed (important)**: noise-detailed textures made deflate emit *stored* blocks, which retail
  data never has; the game's inflater (src/gzip.c) assumes an empty bit buffer after aligning a stored block
  and derails (hang / corruption). Our build of the asset tool never emits stored blocks now, and the
  generator keeps every texture well compressible (`texcheck.py`; textures are inflated in place).
  Builds published before 01:50 could hang in races.
- **Headless testing**: long runs with SwiftShader (`--webgl`) stall in the GPU process when the machine is
  loaded (retail dev build too); run race tests on the hardware GPU (omit `--webgl`): 0 underruns.
  `ports/wasm/cdp_shot.py` takes CDP screenshots without the console transport.
- Port hardening: the inflater's Huffman table buffer is 0x10000 instead of 0x2800 (gzip worst case).
- Dev hook: `?script=` page sequencer (menu-aware via exported `dev_menu_id`), used for headless race tests.
- Ports: 8731 dev (dirty, local only), 8732 clean.

## Next
- Character body textures with detail (Diddy's cap star, shirts), Wizpig/boss faces on 3D models, trophies.
- Adventure hub: Taj, doors, balloon counters; results/trophy screens check.
- Music instrument quality (listen report from the user); SFX that sound wrong.

## For the morning
- Play it (keyboard or controller): https://andrewnakas.github.io/dkr-cleanroom/ - tell me what looks or
  sounds wrong first.
- **Voice practice pack** (personal use, not published): `D:/n64work/dkr/practice_pack/`
  - `SCRIPT.txt`, one `track_<character>.wav` per character (17 characters, 317 clips):
    reference clip, beep, your turn. Record each track straight through (keep the beeps).
  - These are mumbles/grunts/laughs, not words - imitate the feel, not the syllables.
