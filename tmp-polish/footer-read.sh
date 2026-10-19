#!/bin/bash
cd "$(git rev-parse --show-toplevel)"
F=app/src/main/java/com/music/amusic/ui/screens/SettingsSheet.kt
sed -n '1545,1600p' $F | cat -n
