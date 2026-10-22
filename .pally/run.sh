#!/usr/bin/env bash
set -euo pipefail
OUT=.pally
mkdir -p "$OUT"
M=app/src/main/java/com/music/amusic/MainActivity.kt

sed -n '1800,1900p' "$M" > "$OUT/q1_searchsongs.txt"
sed -n '1900,1960p' "$M" > "$OUT/q2_searchsongs2.txt"
grep -n "playRadio\|QueueSource(" "$M" | head -40 > "$OUT/q3_queue.txt" || true
