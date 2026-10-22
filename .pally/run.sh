#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
MA=app/src/main/java/com/music/amusic/MainActivity.kt
rm -f .pally/*.txt
sed -n '3125,3185p' "$MA" > .pally/23.txt
ls app/src/main/java/com/music/amusic/ui/*.kt > .pally/24.txt 2>&1
grep -rn 'fun play\|fun search\|suspend fun search' app/src/main/java/com/music/amusic/ui/MainViewModel.kt shared/src/jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt 2>/dev/null | head -30 > .pally/25.txt
grep -rn 'onSectionItemClick\|onSongClick' "$MA" | head -20 > .pally/26.txt
exit 0
