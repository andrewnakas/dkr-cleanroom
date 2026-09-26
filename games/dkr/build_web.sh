#!/bin/sh
# Build a DKR tree (with assets/assets.bin built) for the web.
# Usage: games/dkr/build_web.sh <tree> [make args]. Summary only; log at <tree>/build_web.log
T="$1"; shift
R="$(cd "$(dirname "$0")/../.." && pwd)"
(cd "$R" && python -m games.dkr.port_patches "$T") || exit 1
export PATH="$HOME/bin:/e/n64web/emsdk/upstream/emscripten:/e/n64web/emsdk/upstream/bin:$PATH"
export EM_CACHE=E:/n64web/emcache EMSDK=E:/n64web/emsdk
cd "$T" && make -f Makefile.web -j12 "$@" > build_web.log 2>&1
rc=$?
echo "make rc=$rc"
grep -E "error" build_web.log | sed -E 's/^[^ ]*:[0-9]+:[0-9]+: //' | sort | uniq -c | sort -rn | head -12
ls -la build/web/dkr.* 2>/dev/null | awk '{print $5, $9}'
