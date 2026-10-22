#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
DS=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
HS=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt
rm -f .pally/*.txt
sed -n '2680,2755p' "$DS" > .pally/10.txt
sed -n '2756,2830p' "$DS" > .pally/11.txt
sed -n '2831,2905p' "$DS" > .pally/12.txt
sed -n '2555,2600p' "$DS" > .pally/13.txt
sed -n '1060,1105p' "$HS" > .pally/14.txt
sed -n '854,905p' "$HS" > .pally/15.txt
grep -n 'preRelease\|SHELF_TITLE\|activeShelf\|onActiveShelfChange\|topRelease' "$DS" | head -30 > .pally/16.txt
exit 0
