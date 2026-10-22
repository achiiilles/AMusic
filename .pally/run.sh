#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
echo '=== ShelfItem / HomeShelf models ==='
grep -rn -A 18 "class ShelfItem" shared/src/commonMain/kotlin/com/music/amusic/data/model/Models.kt
grep -rn -A 12 "class HomeShelf" shared/src/commonMain/kotlin/com/music/amusic/data/model/Models.kt
echo '=== files with ShelfItem ==='
grep -rln "ShelfItem" --include='*.kt' sharedUi app tv shared | grep -v '/build/'
echo '=== shelf composables ==='
grep -rn "fun [A-Za-z]*Shelf[A-Za-z]*(" --include='*.kt' sharedUi app | grep -v '/build/' | head -60
echo '=== nav types ==='
grep -rn "sealed class\|sealed interface\|data class [A-Za-z]*Screen\|object [A-Za-z]*Screen" --include='*.kt' app/src/main/java/com/music/amusic/MainActivity.kt app/src/main/java/com/music/amusic/ui/MainViewModel.kt | head -40
