#!/bin/bash
OUT=tmp-polish/out-find3.txt
: > $OUT
sec() { echo "=== $1" >> $OUT; }
P=shared/src/jvmSharedMain/kotlin/com/music/amusic/data/innertube/InnertubeParser.kt
sec "parser 40-130"
sed -n '40,130p' $P >> $OUT
sec "parser 695-790"
sed -n '695,790p' $P >> $OUT
sec "parser: function names"
grep -n -E "^\s*(private |internal )?fun " $P | head -60 >> $OUT
sec "composeResources dirs"
git ls-files sharedUi | grep -E "strings.xml" | head -40 >> $OUT
C=$(git ls-files sharedUi | grep -E "composeResources/values/strings.xml" | head -1)
sec "keys en: $C"
grep -n -E "name=\"(play|playlist_action|recent_searches|search_hint|search_empty|clear)\"" $C >> $OUT
grep -c "<string " $C >> $OUT
sec "pt files"
git ls-files sharedUi | grep -E "values-pt" | head >> $OUT
sec "tests on locale"
git ls-files | grep -i -E "LocaleStrings" | head >> $OUT
T=$(git ls-files | grep -i -E "LocaleStringsTest" | head -1)
[ -n "$T" ] && sed -n '1,70p' "$T" >> $OUT
sec "repository search fn"
grep -n -E "suspend fun search|fun search" shared/src/jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt | head >> $OUT
sec "MainViewModel results ordering 2419-2445"
sed -n '2419,2445p' app/src/main/java/com/music/amusic/ui/MainViewModel.kt >> $OUT
