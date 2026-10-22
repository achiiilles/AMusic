#!/usr/bin/env bash
set -euo pipefail
OUT=.pally
mkdir -p "$OUT"
D=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
M=app/src/main/java/com/music/amusic/MainActivity.kt

grep -rn "enum class PlaybackSourceType" -A 14 app/src/main/java/com/music/amusic --include=*.kt > "$OUT/p1_source_type.txt" || true
grep -rn "sealed class SearchResult\|sealed interface SearchResult" -A 45 app/src/main/java/com/music/amusic --include=*.kt > "$OUT/p2_searchresult.txt" || true
grep -n "SearchResult.Song\|SearchFilter" "$M" | head -30 > "$OUT/p3_uses.txt" || true
grep -n "fun playRadio" -A 8 "$M" > "$OUT/p4_playradio.txt" || true
grep -rln "object YtMusicRepository" app/src/main/java/com/music/amusic > "$OUT/p5_repo_file.txt" || true
sed -n '318,360p' "$D" > "$OUT/p6_detailsig.txt"
sed -n '2786,2833p' "$D" > "$OUT/p7_gridpage.txt"
