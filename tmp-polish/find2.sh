#!/bin/bash
OUT=tmp-polish/out-find2.txt
: > $OUT
sec() { echo "=== $1" >> $OUT; }
sec "top-level dirs"
git ls-files | cut -d/ -f1 | sort -u | head -30 >> $OUT
sec "musicCardShelf in any kt (repo)"
grep -rIn --include=*.kt -E "musicCardShelf|MusicCardShelf" . | grep -v "/test/" | head -20 >> $OUT
sec "enum SearchFilter"
grep -rIn --include=*.kt -E "enum class SearchFilter" . | head -5 >> $OUT
F=$(grep -rIl --include=*.kt -E "enum class SearchFilter" . | head -1)
[ -n "$F" ] && grep -n -B2 -A25 "enum class SearchFilter" "$F" >> $OUT
sec "TopTrack / TopArtist etc"
grep -rIn --include=*.kt -E "TopTrack|TopArtist|TopAlbum|TopPlaylist|TopVideo|class TopResult" . | grep -v "/test/" | head -50 >> $OUT
sec "UI uses of SearchFilter entries"
grep -rIn --include=*.kt -E "SearchFilter\.entries|SearchFilter\.values|FilterChip|ChipRow|SearchChip" app/src/main | head -30 >> $OUT
sec "strings.xml search keys"
grep -n -i -E "search|filter|top_result|chip" app/src/main/res/values/strings.xml | head -60 >> $OUT
sec "strings pt search keys"
grep -n -i -E "search|filter|top_result|chip" app/src/main/res/values-pt/strings.xml | head -60 >> $OUT
