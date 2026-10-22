#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
DS=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
rm -f .pally/*.txt
sed -n '1100,1165p' "$DS" > .pally/17.txt
sed -n '300,352p' "$DS" > .pally/18.txt
sed -n '780,830p' "$DS" > .pally/19.txt
grep -rn 'ShelfSection\|fun Shelf' app/src sharedUi/src | head -20 > .pally/20.txt
grep -n 'SectionCard(\|ShelfCard(\|ShelfRow(\|LazyRow\|onSectionItemClick' "$DS" | head -40 > .pally/21.txt
grep -n 'onSongClick\|onPlaySong\|onTrackClick\|SongRow(' "$DS" | head -25 > .pally/22.txt
exit 0
