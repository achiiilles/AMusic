#!/bin/bash
set -u
OUT=tmp-polish/out-size2.txt
F=app/src/main/java/com/music/amusic/MainActivity.kt
{
echo '== actions 3770-3870'
sed -n '3770,3870p' "$F"
echo '== download button definition and calls'
grep -rn -B5 -A65 'fun TopBarDownloadButton' app/src/main/java/com/music/amusic/ui/components | head -80
} > "$OUT"
