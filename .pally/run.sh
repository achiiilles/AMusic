#!/usr/bin/env bash
set -euo pipefail
OUT=.pally
mkdir -p "$OUT"
D=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
M=app/src/main/java/com/music/amusic/MainActivity.kt
: > "$OUT/t1_uses.txt"
grep -rn "SearchResult.Song" --include=*.kt . | head -20 >> "$OUT/t1_uses.txt" || true
grep -rn "SearchResult" shared/src --include=*.kt | head -40 >> "$OUT/t1_uses.txt" || true
: > "$OUT/t2_def.txt"
grep -rn -A 14 "sealed class SearchResult" --include=*.kt . >> "$OUT/t2_def.txt" || true
: > "$OUT/t3_playdetail.txt"
grep -n -A 16 "fun playDetailSongs" "$M" >> "$OUT/t3_playdetail.txt" || true
grep -n "onSongSwipe: (Song) -> Unit" "$D" >> "$OUT/t3_playdetail.txt" || true
grep -n "onSectionItemLongPress: ((ShelfItem) -> Unit)? = null" "$D" >> "$OUT/t3_playdetail.txt" || true
grep -n "PreReleasePage(" -A 10 "$D" > "$OUT/t4_page.txt" || true
