#!/usr/bin/env bash
set -euo pipefail
cd "$GITHUB_WORKSPACE"
echo '--- top level ---'
ls
for d in */; do echo "[$d]"; ls "$d" | head -20; done
echo '--- grep prelanc ---'
grep -rniE "prelanc|pré-lan|pre-lan|prerelease|pre_release" --include='*.kt' --include='*.kts' --include='*.xml' . 2>/dev/null | grep -v '/build/' | head -200
echo '--- grep apple ---'
grep -rliE "itunes|apple ?music|music.apple" --include='*.kt' . 2>/dev/null | grep -v '/build/' | head -60
