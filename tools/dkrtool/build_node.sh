#!/bin/sh
# Build dkr_assets_tool as a Node program (POSIX std::filesystem via NODERAWFS).
set -e
export PATH="/e/n64web/emsdk/upstream/emscripten:/e/n64web/emsdk/upstream/bin:$PATH" EM_CACHE=E:/n64web/emcache
SRC=/d/n64work/dkr/pristine/tools
OUT=/d/n64work/dkr/tooljs/obj
mkdir -p $OUT
cd $SRC
# Faster gzip search for level 9 (level-6 settings): clean textures carry noise
# detail, and a 4096-long chain search on them takes the build from 2 to 30+ min.
mkdir -p /d/n64work/dkr/tooljs/override
# ...and never emit stored (type 0) blocks: the game's inflater (src/gzip.c) assumes an empty bit
# buffer after byte-aligning a stored block, which retail data never exercised.
sed -e 's#/\* 9 \*/ {32, 258, 258, 4096}#/* 9 */ {8,   16, 128, 128}#' -e 's#} else if (stored_len+4 <= opt_lenb \&\& buf != (char\*)0) {#} else if (0 \&\& stored_len+4 <= opt_lenb \&\& buf != (char*)0) {#' dkr_assets_tool_src/libs/gzip/DKRGzip.c > /d/n64work/dkr/tooljs/override/DKRGzip.c
grep -q '/\* 9 \*/ {8,   16, 128, 128}' /d/n64work/dkr/tooljs/override/DKRGzip.c || { echo "gzip patch failed"; exit 1; }
grep -q 'else if (0 && stored_len+4' /d/n64work/dkr/tooljs/override/DKRGzip.c || { echo "stored patch failed"; exit 1; }
emcc $FL -I dkr_assets_tool_src/libs/gzip -c /d/n64work/dkr/tooljs/override/DKRGzip.c -o $OUT/zz_DKRGzip_fast.o
FL="-O2 -fexceptions -DPCRE2_CODE_UNIT_WIDTH=8 -DPCRE2_STATIC -I/d/n64work/dkr/tooljs/pcre2-10.44/src -pthread -I . -I dkr_assets_tool_src/ -D__linux__=1"
find dkr_assets_tool_src \( -name '*.cpp' -o -name '*.c' \) ! -name DKRGzip.c | xargs -P 12 -I{} sh -c '
  f={}; o='$OUT'/$(echo $f | tr / _).o
  [ -s $o ] && [ $o -nt $f ] && exit 0
  case $f in *.cpp) em++ -std=c++17 '"$FL"' -c $f -o $o ;; *) emcc '"$FL"' -c $f -o $o ;; esac || echo FAIL $f'
em++ -O2 -fexceptions --profiling-funcs -sASSERTIONS=1 -pthread $OUT/*.o /d/n64work/dkr/tooljs/pcre2-10.44/libpcre2-8.a -o /d/n64work/dkr/tooljs/dkr_assets_tool.js -sNODERAWFS=1 -sALLOW_MEMORY_GROWTH=1 \
  -sPROXY_TO_PTHREAD=1 -sPTHREAD_POOL_SIZE=16 -sEXIT_RUNTIME=1 -sSTACK_SIZE=8MB -sINITIAL_MEMORY=512MB -sMAXIMUM_MEMORY=4GB -sDEFAULT_PTHREAD_STACK_SIZE=4MB
echo built
