#!/usr/bin/env bash
set -euo pipefail
OUT=.pally
mkdir -p "$OUT"
D=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
: > "$OUT/u1_ctx.txt"
sed -n '1100,1170p' "$D" >> "$OUT/u1_ctx.txt"
echo '== gridpage calls ==' >> "$OUT/u1_ctx.txt"
grep -n "ArtistShelfGridPage(" "$D" >> "$OUT/u1_ctx.txt" || true
echo '== fun headers ==' >> "$OUT/u1_ctx.txt"
grep -n "^fun DetailScreen\|^private fun \|^internal fun " "$D" | head -40 >> "$OUT/u1_ctx.txt"
: > "$OUT/u2_targets.txt"
sed -n '316,344p' "$D" >> "$OUT/u2_targets.txt"
echo '== sectioncard sig ==' >> "$OUT/u2_targets.txt"
sed -n '2725,2745p' "$D" >> "$OUT/u2_targets.txt"
: > "$OUT/u3_main.txt"
sed -n '3035,3070p' app/src/main/java/com/music/amusic/MainActivity.kt >> "$OUT/u3_main.txt"
