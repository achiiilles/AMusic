#!/bin/bash
OUT=tmp-polish/out-rec.txt
: > $OUT
sec() { echo "=== $1" >> $OUT; }
sec "files screens"
git ls-files sharedUi | grep -E "HomeScreen|ExploreScreen|LibraryScreen" | head -20 >> $OUT
sec "grep recent (kt)"
grep -rIn --include=*.kt -i "recent" sharedUi | cut -c1-220 | head -60 >> $OUT
sec "grep recent (strings xml)"
grep -rIn --include=strings.xml -i "recent" sharedUi | cut -c1-200 | head -30 >> $OUT
sec "files mentioning Recents"
grep -rIln --include=*.kt -i "recents" . | head -30 >> $OUT
