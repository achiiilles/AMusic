#!/usr/bin/env bash
set -euo pipefail
cd "$GITHUB_WORKSPACE"
grep -rn --include=*.kt -E "ApplePreRelease|PreRelease|preRelease|preLanc|Pre-release" app/src/main/java | head -150
