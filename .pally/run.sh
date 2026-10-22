#!/usr/bin/env bash
set -euo pipefail
python3 .pally/patch.py
git config user.name "pally probe"
git config user.email "probe@users.noreply.github.com"
git add app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt app/src/main/java/com/music/amusic/ui/screens/PreReleaseScreen.kt shared/src/jvmSharedMain/kotlin/com/music/amusic/data/ApplePreRelease.kt
git commit -m "fix: faixas de pré-lançamento não lançadas viram Faixa N, apagadas, sem subtexto [skip ci]"
git push origin HEAD:polish-refresh-transitions
