#!/bin/bash
mkdir -p tmp-polish
O=tmp-polish/out-f.txt
A=app/src/main/java/com/music/amusic
{
echo "== Detail 2370-2440"
sed -n '2370,2440p' $A/ui/screens/DetailScreen.kt | cut -c1-165
echo "== Detail artistAwareShape and ARTIST"
grep -nE "artistAwareShape|BrowseType.ARTIST|startsWith\(\"UC\"" $A/ui/screens/DetailScreen.kt | cut -c1-170 | head -30
echo "== Detail imports coil/components"
grep -nE "^import (coil3|com.music.amusic.ui.components)" $A/ui/screens/DetailScreen.kt | head -30
echo "== Application 88-132"
sed -n '88,132p' $A/AMusicApplication.kt | cut -c1-150
echo "== Library artists cards"
grep -rnE "ArtistCard|ArtistsGrid|artistGrid|ShelfCard\(|BrowseCard\(" sharedUi/src app/src/main --include=*.kt | cut -c1-170 | head -20
} > $O
wc -l $O
