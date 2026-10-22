#!/usr/bin/env bash
set -euo pipefail
python3 .pally/patch.py
git config user.name "pally probe"
git config user.email "probe@users.noreply.github.com"
git add app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt app/src/main/java/com/music/amusic/MainActivity.kt app/src/main/java/com/music/amusic/ui/MainViewModel.kt
git commit -m "feat: card de pré-lançamento abre a página de álbum normal [skip ci]"
git push origin HEAD:polish-refresh-transitions
