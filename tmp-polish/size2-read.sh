#!/bin/bash
set -u
OUT=tmp-polish/out-size2.txt
F=app/src/main/java/com/music/amusic/MainActivity.kt
{
echo '== download session imports and references in MainActivity'
grep -nE 'DownloadSession|DownloadManagerSheet|downloadSession|session.visible|updateNotice|TAB_LIBRARY|isReleaseDetail' "$F" | head -95
echo '== download session object declaration'
grep -rn -B3 -A35 '^object DownloadSession' app/src/main/java/com/music/amusic | head -50
echo '== actions near 3760'
sed -n '3755,3780p' "$F"
} > "$OUT"
