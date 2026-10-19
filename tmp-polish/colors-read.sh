#!/bin/bash
F=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
wc -l $F > tmp-polish/out-colors-b.txt
{
echo "=== palette/wash/pageColor/chip refs"
grep -nE "palette|wash|pageColor|chipColor|buttonColor|FrostedTopBar|backButtonHazeState|artworkPageChrome|actionsScrollPx|isArtist|inLibraryArtistPage|isPlaylist|isAlbum|Border|border" $F | cut -c1-200 | head -220
} >> tmp-polish/out-colors-b.txt 2>&1
{
echo "=== 365-420"; sed -n '365,420p' $F | cut -c1-200
echo "=== 545-600"; sed -n '545,600p' $F | cut -c1-200
} > tmp-polish/out-colors-c.txt 2>&1
