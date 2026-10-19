#!/bin/bash
set -u
OUT=tmp-polish/out-size2.txt
F=app/src/main/java/com/music/amusic/MainActivity.kt
{
echo '== top bar caller setup 3600-3750'
sed -n '3600,3750p' "$F"
echo '== top bar actions 3850-4020'
sed -n '3850,4020p' "$F"
echo '== library and history references nearby'
sed -n '3600,4020p' "$F" | grep -inE -B2 -A2 'library|history|action|pill|isRoot|selectedTab|currentTab' | head -160
echo '== avatar constant references'
grep -rn 'AVATAR_SIZE' app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt
} > "$OUT"
