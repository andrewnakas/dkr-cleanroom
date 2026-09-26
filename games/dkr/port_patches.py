"""Idempotent patches that turn the DKR PC port (Bruceleeto fork, SDL2 + GL)
into a web build. Each entry is (file, old, new). Only platform glue changes;
no game logic.

Also writes Makefile.web (from Makefile.pc) and copies web/*.c into the tree.

Usage: python -m games.dkr.port_patches <tree>
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PATCHES = [
    # Pace with the browser: emscripten_sleep yields (Asyncify) so the page can
    # present and run audio/input callbacks.
    ("linux/main.c", "#include <time.h>\n", "#include <time.h>\n#include <emscripten.h>\n"),
    ("linux/main.c",
     "        nanosleep(&req, NULL);\n",
     "        (void) req;\n        emscripten_sleep((unsigned) ((targetNs - nowNs) / 1000000ll));\n"),
    # Web: the canvas is 2x; CSS scales it to the page.
    ("linux/main.c", "#define WINDOW_SCALE 3\n", "#define WINDOW_SCALE 2\n"),
    # EEPROM saves persist in localStorage.
    ("linux/reimpl.c",
     "    memset(gEeprom, 0xFF, PC_EEPROM_BYTES); // erased\n#endif\n",
     "    memset(gEeprom, 0xFF, PC_EEPROM_BYTES); // erased\n#endif\n"
     "    EM_ASM({\n"
     "        try { var s = localStorage.getItem('dkr_eeprom'); if (s && s.length == $1 * 2)\n"
     "            for (var i = 0; i < $1; i++) HEAPU8[$0 + i] = parseInt(s.substr(i * 2, 2), 16); } catch (e) {}\n"
     "    }, gEeprom, PC_EEPROM_BYTES);\n"),
    ("linux/reimpl.c",
     "        memcpy(&gEeprom[address * 8], buffer, 8);\n    }\n",
     "        memcpy(&gEeprom[address * 8], buffer, 8);\n"
     "        EM_ASM({\n"
     "            try { var s = ''; for (var i = 0; i < $1; i++) s += (HEAPU8[$0 + i] + 256).toString(16).substr(1);\n"
     "                localStorage.setItem('dkr_eeprom', s); } catch (e) {}\n"
     "        }, gEeprom, PC_EEPROM_BYTES);\n"
     "    }\n"),
    ("linux/reimpl.c", "#define PC_EEPROM_BLOCKS 64\n", "#include <emscripten.h>\n#define PC_EEPROM_BLOCKS 64\n"),
    # wasm checks call signatures: the game's own f32 log() must not replace
    # libm's double log() that SDL links against; the AI shim returns s32.
    ("src/audio_vehicle.c", "f32 log(f32 x);\n", "#define log dkr_log\nf32 log(f32 x);\n"),
    ("linux/audio.c", "void osAiSetNextBuffer(void *buf, u32 size) {", "s32 osAiSetNextBuffer(void *buf, u32 size) {"),
    ("linux/audio.c",
     "    if (!sAudioReady || buf == NULL || size == 0) {\n        return;\n    }\n\n    SDL_LockAudioDevice",
     "    if (!sAudioReady || buf == NULL || size == 0) {\n        return 0;\n    }\n\n    SDL_LockAudioDevice"),
    ("linux/audio.c",
     "        SDL_UnlockAudioDevice(sAudioDev);\n        return;\n    }\n    for (i = 0; i < size; i++) {",
     "        SDL_UnlockAudioDevice(sAudioDev);\n        return 0;\n    }\n    for (i = 0; i < size; i++) {"),
    ("linux/audio.c",
     "    sRingUsed += size;\n    SDL_UnlockAudioDevice(sAudioDev);\n}\n",
     "    sRingUsed += size;\n    SDL_UnlockAudioDevice(sAudioDev);\n    return 0;\n}\n"),
    # The inflater's Huffman tables come from a 0x2800-byte bump buffer (1280 entries of 8 bytes).
    # gzip's worst case needs more; retail streams never got there, regenerated assets can.
    ("src/gzip.c", "gHuftTable = (huft *) mempool_alloc_safe(0x2800, COLOUR_TAG_BLACK);",
     "gHuftTable = (huft *) mempool_alloc_safe(0x10000, COLOUR_TAG_BLACK);"),
    # Deeper audio buffer: browser timers jitter more than a native sleep.
    ("linux/audio.c", "#define PC_AUDIO_TARGET_FRAMES 3 ", "#define PC_AUDIO_TARGET_FRAMES 5 "),
]


def make_web_makefile(tree):
    src = open(os.path.join(tree, "Makefile.pc"), encoding="utf-8").read()
    src = src.replace("CC      := gcc", "CC      := emcc")
    src = src.replace("BUILD   := build/pc\n", "BUILD   := build/web\n")
    src = src.replace("-DVERSION_US_V77", "-DVERSION_US_V80")
    src = src.replace("EEPROM_PRESET_100 ?= 1", "EEPROM_PRESET_100 ?= 0")
    src = src.replace("BASE_CFLAGS := -m$(BITS) $(OPT)", "BASE_CFLAGS := $(OPT)")
    src = src.replace("OPT      ?= -Os", "OPT      ?= -O2")
    src = src.replace("\tlinux/gfx.c \\\n", "\tweb/gfx_web.c \\\n")
    src = src.replace("\tlinux/input.c \\\n", "\tweb/input_web.c \\\n\tweb/dev_web.c \\\n")
    src = src.replace("LIBS := -lm -lSDL2 -lGL $(SAN_FLAGS)",
                      "LIBS := -lm -sUSE_SDL=2 -sMIN_WEBGL_VERSION=2 -sMAX_WEBGL_VERSION=2 -sASYNCIFY=1 "
                      "-sASYNCIFY_STACK_SIZE=65536 -sINITIAL_MEMORY=128MB -sALLOW_MEMORY_GROWTH=1 "
                      "-sSTACK_SIZE=1MB -sENVIRONMENT=web --profiling-funcs "
                      "-sEXPORTED_RUNTIME_METHODS=['FS'] --preload-file assets/assets.bin@assets/assets.bin "
                      "--preload-file assets/assets.lut.bin@assets/assets.lut.bin")
    src = src.replace("TARGET := dkracing\n", "TARGET := $(BUILD)/dkr.js\n")
    src = src.replace("\t$(CC) -m$(BITS) $(O_FILES) -o $(TARGET) $(LIBS)\n",
                      "\t$(file >$(BUILD)/link.rsp,$(O_FILES))\n\t$(CC) @$(BUILD)/link.rsp -o $(TARGET) $(LIBS)\n")
    src = src.replace("$(BUILD)/linux/%.o: linux/%.c\n",
                      "$(BUILD)/web/%.o: web/%.c\n\t@mkdir -p $(dir $@)\n\t$(CC) $(CFLAGS_REIMPL) -sUSE_SDL=2 -c -o $@ $<\n\n"
                      "$(BUILD)/linux/%.o: linux/%.c\n")
    src = src.replace("\t$(CC) $(CFLAGS_REIMPL) -c -o $@ $<\n\n$(BUILD)/%.o",
                      "\t$(CC) $(CFLAGS_REIMPL) -sUSE_SDL=2 -c -o $@ $<\n\n$(BUILD)/%.o")
    for must in ("emcc", "web/gfx_web.c", "ASYNCIFY", "link.rsp", "VERSION_US_V80"):
        assert must in src, must
    open(os.path.join(tree, "Makefile.web"), "w", encoding="utf-8", newline="\n").write(src)


def main(tree):
    applied = skipped = 0
    for path, old, new in PATCHES:
        p = os.path.join(tree, path)
        s = open(p, encoding="utf-8").read()
        if new in s:
            skipped += 1
            continue
        if old not in s:
            print("PATCH FAILED:", path, repr(old[:60]))
            sys.exit(1)
        s = s.replace(old, new, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(s)
        applied += 1
    os.makedirs(os.path.join(tree, "web"), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "web")):
        if f.endswith(".c") or f.endswith(".h"):
            shutil.copy(os.path.join(HERE, "web", f), os.path.join(tree, "web", f))
    make_web_makefile(tree)
    print(f"patches: {applied} applied, {skipped} already in")


if __name__ == "__main__":
    main(sys.argv[1])
