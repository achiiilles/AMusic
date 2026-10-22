#!/usr/bin/env bash
set -euo pipefail
OUT=.pally
mkdir -p "$OUT"
D=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
M=app/src/main/java/com/music/amusic/MainActivity.kt
V=app/src/main/java/com/music/amusic/ui/MainViewModel.kt

sed -n '1650,1725p' "$M" > "$OUT/e_openbyname.txt"
sed -n '1330,1400p' "$M" > "$OUT/f_playfrom.txt"
sed -n '3030,3080p' "$M" > "$OUT/g_playdetail.txt"
sed -n '2720,2775p' "$D" > "$OUT/h_sectioncard_sig.txt"
sed -n '1135,1165p' "$D" > "$OUT/i_sectioncard_call.txt"
sed -n '2155,2200p' "$V" > "$OUT/j_searchfor.txt"
grep -rn "openByName\|playDetailSongs" app/src/main/java/com/music/amusic --include=*.kt > "$OUT/k_uses.txt" || true
