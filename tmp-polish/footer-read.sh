#!/bin/bash
cd "$(git rev-parse --show-toplevel)"
F=app/src/main/java/com/music/amusic/ui/screens/SettingsSheet.kt
echo '=== SettingsSheet link lines ==='
grep -nE 'withLink|LinkAnnotation|Uri.parse|github|Backend|\.discord\.|http' $F | head -40
echo '=== xml pt ==='
grep -nE 'developer|website|backend|github|about|version' -i app/src/main/res/values/strings.xml | head -40
grep -nE 'developer|website|backend|github' -i app/src/main/res/values-pt/strings.xml | head -20
echo '=== context ==='
N=$(grep -nE 'withLink' $F | head -1 | cut -d: -f1)
if [ -n "$N" ]; then S=$((N-40)); E=$((N+60)); sed -n "${S},${E}p" $F | cat -A | sed 's/\$$//' | head -120; fi
