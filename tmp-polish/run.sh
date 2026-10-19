#!/bin/bash
D=app/src/main/java/com/music/amusic
mkdir -p tmp-polish
O=tmp-polish/out-b.txt
K="--include=*.kt"
{
echo "== 1 recent_searches usage"
grep -rnI $K "recent_searches" app/src | cut -c1-200 | head -10
echo "== 2 files with SearchHistoryEntity"
grep -rlI $K "SearchHistoryEntity" app/src | head -10
echo "== 3 entity def"
grep -rnI $K -B3 -A14 "class SearchHistoryEntity" app/src | cut -c1-170 | head -30
echo "== 4 coil / image libs count per file"
grep -rcIE $K "AsyncImage|SubcomposeAsyncImage|rememberAsyncImagePainter" $D | grep -v ":0$" | sed "s#$D/##" | head -50
echo "== 5 coil imports"
grep -rhI $K "^import coil" $D | sort | uniq -c | head -15
echo "== 6 artist item types"
grep -rnI $K -E "(data|sealed|enum) class [A-Za-z]*(Artist|Item)[A-Za-z]*" app/src | cut -c1-190 | head -20
} > $O
wc -l $O
