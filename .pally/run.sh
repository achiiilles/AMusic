#!/usr/bin/env bash
set -euo pipefail
cd "$GITHUB_WORKSPACE"
echo '=== ApplePreRelease.kt ==='
cat shared/src/jvmSharedMain/kotlin/com/music/amusic/data/ApplePreRelease.kt
echo '=== refs ApplePreRelease ==='
grep -rn "ApplePreRelease" --include='*.kt' . | grep -v '/build/'
echo '=== refs prelanc ==='
grep -rniE "prelanc|pré-lan|pre-lan|upcomingRelease|preRelease" --include='*.kt' . | grep -v '/build/' | head -80
echo '=== model files ==='
ls shared/src/jvmSharedMain/kotlin/com/music/amusic/data/model
