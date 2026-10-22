#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
S=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
{
echo '### DetailScreen shelf/card usages'
grep -n 'HomeShelf\|NewShelfCard\|ShelfCard\|ShelfRow' $S | head -40
echo '### DetailScreen artist funs'
grep -n 'fun .*Artist' $S | head -30
echo '### MainActivity DetailScreen call'
grep -n 'DetailScreen(' app/src/main/java/com/music/amusic/MainActivity.kt | head -20
echo '### HomeScreen maxLines'
grep -n 'maxLines' sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt | head -25
} > .pally/1.txt 2>&1
