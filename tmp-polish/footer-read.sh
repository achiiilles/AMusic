#!/bin/bash
cd "$(git rev-parse --show-toplevel)"
echo '=== grep kt ==='
grep -rnE 'LinkAnnotation|withLink|discord|Discord|github\.com|Website|Developer|Listen Together Backend|app_footer|about_' app/src/main/java --include=*.kt | grep -v '^app/src/main/java/com/music/amusic/data/listentogether' | head -80
echo '=== grep xml ==='
grep -rnE 'Developer|Discord|Website|Backend|GitHub' app/src/main/res --include=strings.xml | head -40
