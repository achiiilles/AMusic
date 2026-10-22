#!/usr/bin/env bash
set -euo pipefail
OUT=.pally
mkdir -p "$OUT"
D=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
M=app/src/main/java/com/music/amusic/MainActivity.kt

grep -n "^private fun \|^internal fun \|^fun \|^@Composable" "$D" > "$OUT/l_map.txt" || true
grep -n "^private fun \|^internal fun \|^fun " "$D" | head -80 > "$OUT/l_map2.txt" || true
sed -n '3100,3190p' "$M" > "$OUT/m_detailscreen_call.txt"
sed -n '2820,2860p' "$M" > "$OUT/n_chart_rows.txt"
grep -rn "fun search(\|object YtMusicRepository\|SearchResult.Song" app/src/main/java/com/music/amusic/data/ytmusic --include=*.kt | head -40 > "$OUT/o_repo.txt" || true
ls app/src/main/java/com/music/amusic/data/ | head -40 >> "$OUT/o_repo.txt"
