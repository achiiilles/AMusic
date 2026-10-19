#!/bin/bash
# temporary read-only script: writes limited grep excerpts to tmp-polish/out-find.txt
OUT=tmp-polish/out-find.txt
: > $OUT
sec() { echo "=== $1" >> $OUT; }
sec "files"
git ls-files app | grep -i -E "search|innertube|youtubemusic|ytmusic|Chip|Filter" | head -60 >> $OUT
sec "grep Top result"
grep -rIn --include=*.kt --include=*.xml -i "top result" app | head -20 >> $OUT
sec "grep musicCardShelf / topResult"
grep -rIn --include=*.kt -E "musicCardShelf|TopResult|topResult" app | head -40 >> $OUT
sec "grep chip"
grep -rIn --include=*.kt -E "chipCloud|ChipCloud|FilterChip|SearchFilter|searchFilter" app | head -40 >> $OUT
sec "values strings files"
git ls-files app | grep -E "res/values[^/]*/strings.xml" | head -40 >> $OUT
sec "grep section literals"
grep -rIn --include=*.kt -E "\"(Songs|Videos|Albums|Artists|Playlists|Featured playlists|Podcasts|Profiles|Episodes|Community playlists|All)\"" app | head -50 >> $OUT
