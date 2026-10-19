#!/bin/bash
D=app/src/main/java/com/music/amusic
mkdir -p tmp-polish
O=tmp-polish/out-a.txt
{
echo "== A recent search"
grep -rnIE "Pesquisas recentes|recent_searches|SearchHistory\.recent|searchHistory" $D app/src/main/res/values* | sed "s#app/src/main/##;s#java/com/music/amusic/##" | cut -c1-170 | head -30
echo "== B SearchHistoryEntity"
grep -rn -A14 "class SearchHistoryEntity" $D | sed "s#$D/##" | cut -c1-150 | head -30
echo "== C image composables"
grep -rnIE "^(internal |private )?fun [A-Za-z]*(Artwork|Cover|Thumb|Image|Avatar|Photo)[A-Za-z]*\(" $D/ui | sed "s#$D/##" | cut -c1-170 | head -40
echo "== D files with Artist and AsyncImage or Artwork"
grep -rlIE "AsyncImage|Artwork|Thumbnail" $D/ui | xargs grep -lIE "rtist" | sed "s#$D/##" | head -40
} > $O
wc -l $O
