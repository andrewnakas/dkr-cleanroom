# Diddy Kong Racing clean room: status

## Decisions (log)
- **Web route = PC port + Emscripten** (playbook §4 route 1/2). Bruceleeto/Diddy-Kong-Racing has a small
  single-threaded SDL2 + GL 1.x port (`linux/`, ~3k lines). Replaced its GL layer with a WebGL2 shader
  (`games/dkr/web/gfx_web.c`), added Gamepad API input (`web/input_web.c`), Asyncify for the frame sleep,
  EEPROM saves in localStorage. Decided at ~30 min: dev build boots to the attract mode with no crashes.
- **ROM = US v80** (Rev 1, sha1 6d96743d…). The port defaulted to v77; the web build defines VERSION_US_V80.
- **Asset tool** (`dkr_assets_tool`, C++17) does not build natively on Windows (wide `fs::path`). Built it
  with Emscripten for Node (`NODERAWFS`, `-fexceptions`, PCRE2 compiled from source; `std::regex` rejects
  its patterns). Node preload fakes a POSIX cwd. Dirty extract 70 s; asset build 2 min.
- **Round trip**: dirty `assets.bin` rebuilt by the tool is byte-identical to the ROM's asset block (0xED1B0).
- Dev server port: **8731** (8071/8093 belong to other sessions).

## Works
- Dev web build (retail assets, local only) boots: title, N64 logo, Rare logo, attract flyby.

## Next
- Census + dirty spec (textures/sprites/fonts/audio), clean generator, clean build, taint, publish.

## For the morning
- (nothing yet)
