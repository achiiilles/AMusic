#!/bin/bash
set -e
F=app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt
grep -q 'TOP_BAR_VEIL_BACKING_ALPHA = 0.72f' "$F"
sed -i 's/TOP_BAR_VEIL_BACKING_ALPHA = 0.72f/TOP_BAR_VEIL_BACKING_ALPHA = 0.90f/' "$F"
git diff --stat
