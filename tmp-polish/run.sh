#!/bin/bash
mkdir -p tmp-polish
O=tmp-polish/out-c.txt
K="--include=*.kt"
R="sharedUi shared"
{
echo "== 1 recent_searches usage"
grep -rnI $K "recent_searches\|Pesquisas recentes" $R | cut -c1-200 | head -10
echo "== 2 entity def"
grep -rnI $K -B3 -A14 "class SearchHistoryEntity" $R | cut -c1-170 | head -30
echo "== 3 AsyncImage count per file"
grep -rcIE $K "AsyncImage" $R | grep -v ":0$" | head -50
echo "== 4 kt files in sharedUi count"
find sharedUi shared -name '*.kt' | wc -l
echo "== 5 sharedUi dirs"
find sharedUi -type d -path '*src*' -not -path '*/build/*' | head -30
} > $O
wc -l $O
