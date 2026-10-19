#!/bin/bash
OUT=tmp-polish/out-rec.txt
: > $OUT
sec() { echo "=== $1" >> $OUT; }
sec "RECENTS_TITLE uses"
grep -rIn --include=*.kt RECENTS_TITLE sharedUi app | head -12 | cut -c1-200 >> $OUT
sec "Recents word in kt"
grep -rIn --include=*.kt Recents sharedUi app | head -12 | cut -c1-200 >> $OUT
sec "Recents word in xml"
grep -rIn Recents --include=*.xml sharedUi app | head -12 | cut -c1-200 >> $OUT
sec "RecentSectionHeader def"
grep -rIn --include=*.kt -A14 'fun RecentSectionHeader' sharedUi app | head -30 | cut -c1-200 >> $OUT
sec "localizeShelfTitle callers"
grep -rIn --include=*.kt 'localizeShelfTitle(' sharedUi app | head -20 | cut -c1-200 >> $OUT
sec "shelf_charts xml"
grep -rIn shelf_charts --include=*.xml sharedUi app | head -12 | cut -c1-200 >> $OUT
sec "top result xml"
grep -rIn -i top_result --include=*.xml sharedUi app | head -12 | cut -c1-200 >> $OUT
sec "shelf_top_tunes xml"
grep -rIn shelf_top_tunes --include=*.xml sharedUi app | head -12 | cut -c1-200 >> $OUT
sec "screen files"
find sharedUi app/src -name '*.kt' -path '*screens*' | grep -i -E 'explor|library|home|browse|search' >> $OUT
for f in $(find sharedUi app/src -name '*.kt' -path '*screens*' | grep -i -E 'explor|library|browse|home'); do echo "--- $f" >> $OUT; grep -n -E 'Text[(]|title = |label = |text = ' $f | grep -E '"[A-Z][a-z]' | cut -c1-170 | head -30 >> $OUT; done
echo done >> $OUT
