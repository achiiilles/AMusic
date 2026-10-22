#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
DS=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
HS=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt
MA=app/src/main/java/com/music/amusic/MainActivity.kt
MD=shared/src/commonMain/kotlin/com/music/amusic/data/model/Models.kt
AP=shared/src/jvmSharedMain/kotlin/com/music/amusic/data/ApplePreRelease.kt
rm -f .pally/*.txt
{
echo '## DS preRelease/HomeShelf/Shelf'
grep -n 'preRelease\|PreRelease\|HomeShelf\|NewShelfCard\|ShelfCard\|Shelf(' "$DS" | head -70
echo '## DS Artist lines'
grep -n 'Artist' "$DS" | head -60
} > .pally/1.txt 2>&1
grep -n 'maxLines\|item.title\|fun ShelfCard\|fun NewShelfCard\|fun Shelf\|fun HomeShelf' "$HS" | head -60 > .pally/2.txt 2>&1
grep -n 'DetailScreen(' "$MA" | head -20 > .pally/3.txt 2>&1
sed -n '380,415p' "$MD" > .pally/4.txt 2>&1
sed -n '1,70p' "$AP" > .pally/5.txt 2>&1
sed -n '71,200p' "$AP" > .pally/6.txt 2>&1
L=$(grep -n 'HomeShelf(' "$DS" | head -1 | cut -d: -f1)
if [ -n "${L:-}" ]; then sed -n "$((L-40)),$((L+70))p" "$DS" > .pally/7.txt; fi
exit 0
