#!/bin/sh
# Publish a built clean site dir to the gh-pages branch (single squashed commit).
# Usage: games/dkr/publish_site.sh <site dir> "<message>"
set -e
S="$1"; MSG="$2"
P=/d/n64work/dkr/pages
rm -rf "$P" && mkdir -p "$P"
cp "$S"/index.html "$S"/devscript.js "$S"/touchpad.js "$S"/dkr.js "$S"/dkr.wasm "$S"/dkr.data "$S"/.nojekyll "$P"/
cd "$P"
git init -q -b gh-pages
git add -A
git -c user.name=andre -c user.email=treesixtyweather@gmail.com commit -qm "$MSG

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
git push -q -f https://github.com/andrewnakas/dkr-cleanroom.git gh-pages
echo "pushed gh-pages: $(ls | tr '\n' ' ')"
