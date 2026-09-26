#!/bin/sh
# Clean room build: spec -> clean tree -> assets.bin -> web build -> site.
# Usage: games/dkr/build_clean.sh <spec> <pristine> <clean> <site> [--only textures|audio]
set -e
S="$1"; P="$2"; C="$3"; W="$4"; shift 4
R="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$R"
python -m games.dkr.generate "$S" "$P" "$C" "$@"
(cd "$C" && rm -f assets/assets.bin assets/assets.lut.bin && "$R/tools/dkrtool/dkrtool" build -o assets/assets.bin -dkrv us.v80 > build_assets.log 2>&1) \
  || { echo "asset build failed"; grep -i "error" "$C/build_assets.log" | head -5; exit 1; }
tail -3 "$C/build_assets.log" | sed 's/\x1b\[[0-9;]*m//g'
rm -rf "$C/build/debug"
sh games/dkr/build_web.sh "$C"
python -m games.dkr.make_site "$C" "$W"
