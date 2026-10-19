#!/bin/bash
set -u
OUT=tmp-polish/out-size2.txt
F=app/src/main/java/com/music/amusic/MainActivity.kt
L=$(grep -n 'if (!isReleaseDetail) TopBarAccountButton(' "$F" | head -1 | cut -d: -f1)
{
echo "== MainActivity around account button, line $L"
sed -n "$((L-70)),$((L+12))p" "$F"
echo '== FrostedTopBar( call sites'
grep -rn 'FrostedTopBar(' app/src/main/java | head -20
} > $OUT
