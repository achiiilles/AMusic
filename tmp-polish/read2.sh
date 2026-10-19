#!/bin/bash
D=app/src/main/java/com/music/amusic
mkdir -p tmp-polish
O=tmp-polish/out-read2.txt
{
echo "== A ui files mentioning artist"
grep -rlIE "rtist" $D/ui | sed "s#$D/##" | head -80
echo "== B recent search and history"
grep -rnIE "Pesquisas recentes|SearchHistory|recentSearch" $D app/src/main/res | sed "s#app/src/main/##" | cut -c1-170 | head -40
echo "== C circle shapes in ui"
grep -rnIE "CircleShape" $D/ui | sed "s#$D/##" | cut -c1-170 | head -50
echo "== D artist image args"
grep -rnIE "artistThumb|artistImage|ArtistArt|artistPhoto|artistArt" $D | sed "s#$D/##" | cut -c1-170 | head -60
} > $O
wc -l $O
