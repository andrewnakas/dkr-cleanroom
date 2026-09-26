# Diddy Kong Racing — clean room web build

Play: **https://andrewnakas.github.io/dkr-cleanroom/**

Diddy Kong Racing built from the community decompilation
([DavidSM64/Diddy-Kong-Racing](https://github.com/DavidSM64/Diddy-Kong-Racing)) and its PC port
([Bruceleeto/Diddy-Kong-Racing](https://github.com/Bruceleeto/Diddy-Kong-Racing), SDL2 + GL) for the
browser (Emscripten + WebGL 2), with **every asset the decomp normally extracts from a ROM regenerated**:
textures, fonts, HUD art, sprites, instrument and sound-effect samples. No ROM is needed to build or play it.

Controls: `Arrows`/`WASD` steer · `X` A (accelerate) · `C` B (brake) · `Z` Z (item) · `Space`/`Shift` R (hop,
powerslide) · `Q` L · `Enter` Start · `I J K L` C buttons · gamepads work too (standard mapping). Saves are kept in
the browser.

## What is kept, what is generated

The decomp's `dkr_assets_tool extract` turns the ROM's asset block into PNGs, JSON and binaries. This project reads
that output **once, in a "dirty room" step** (`games/dkr/extract_spec.py`), keeps only facts, and builds every
asset from those facts:

| Asset | Kept fact | Generated |
|---|---|---|
| Textures (2,718 PNGs) | format, size, a 4×4 colour grid (16×16 for ≥128 px), a 2-bit alpha outline | colour from the grid plus our own noise detail |
| Fonts (4 game fonts, 42 atlases) | glyph cell positions and advance widths (font metadata) | every glyph drawn with our own stroke font in our own styles (`fonts.py`) |
| HUD / menu text (FINAL LAP, GET READY, GO!, WRONG WAY, TIME, digits, place suffixes, option labels, title logo), track-name signs, START banners | the words; where each strip of a multi-strip sprite sits | re-typeset (`drawn.py`, `hud_text.json`) |
| Faces and pictures: HUD portraits, eyes and mouths (with blink frames), weapon/menu icons, pickups | kept alpha outline where the texture has one | painted from our own descriptions (`face_briefs.json`, `eyes.py`, `icons.py`) |
| World surfaces (grass, sand, rock, wood, brick, roof tiles, snow, water, metal) | colour grid, alpha | tileable procedural detail chosen by texture name (`materials.py`) |
| Character voices (≈300 clips: mumbles, laughs, grunts) | as samples below | resynthesised like every sample; the retail clips are gibberish vocalisations, not words, so there are no TTS lines. `games/dkr/practice.py` builds a personal practice pack for recording your own takes |
| Samples (677 waves in two banks) | length, rate, loop points, a coarse spectral outline, a median pitch | resynthesised; our own VADPCM codebooks of the same shape; banks keep their exact sizes and offsets |
| Music | note sequences (user scope: melodies kept) | played by the resynthesised instruments |
| Geometry, level/object models, animations, text, game tables, time-trial ghosts | kept as facts (user scope) | — |

`games/dkr/taint_report.py` scans every generated texture (RGBA) and every sample (raw table bytes and decoded PCM)
against the retail extraction for shared byte runs of 32 bytes or more.

## Build (Windows, Git Bash)

Needs Python 3 (numpy, Pillow), Node, GNU make and emsdk.

```sh
# the decomp's asset tool, built for Node (see tools/dkrtool)
sh tools/dkrtool/build_node.sh
# dirty room, once: needs your own ROM (US 1.1), never published
git clone -c core.autocrlf=false https://github.com/Bruceleeto/Diddy-Kong-Racing dirty
cp baserom.us.v80.z64 dirty/baseroms/ && (cd dirty && tools/dkrtool/dkrtool extract -dkrv us.v80)
python -m games.dkr.extract_spec dirty spec
# clean room: from the spec only
git clone -c core.autocrlf=false https://github.com/Bruceleeto/Diddy-Kong-Racing pristine
python -m games.dkr.generate spec pristine clean
(cd clean && tools/dkrtool/dkrtool build -o assets/assets.bin -dkrv us.v80)
games/dkr/build_web.sh clean
python -m games.dkr.make_site clean site
```

`games/dkr/port_patches.py` lists every source change to the port: WebGL 2 renderer (`web/gfx_web.c`), Gamepad API
input (`web/input_web.c`), Asyncify frame pacing, localStorage EEPROM saves, two signature fixes wasm needs.

## Notes

- The asset tool is built for Node with two packer changes: level-6 search effort, and no stored deflate
  blocks (the game's inflater, `src/gzip.c`, mishandles them; retail data never had any). Generated textures
  are kept compressible because the game inflates them in place (`games/dkr/texcheck.py`).
- Headless checks: `?script=` in the page URL drives the menus (see `games/dkr/web/devscript.js`); use the
  hardware GPU for long runs (SwiftShader stalls under load).
