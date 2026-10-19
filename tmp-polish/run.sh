#!/bin/bash
mkdir -p tmp-polish
O=tmp-polish/out-d.txt
S=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui
{
for f in components/Common.kt screens/SearchScreen.kt screens/HomeScreen.kt screens/ExploreScreen.kt; do
echo "== $f"
grep -nE "AsyncImage|CircleShape|RoundedCornerShape\(|^(private |internal )?fun [A-Z]|EntityType|isArtist|rtist" $S/$f | cut -c1-175 | head -70
done
echo "== find screens"
find . -name 'LibraryScreen*.kt' -o -name 'HomeScreen*.kt' -o -name 'DetailScreen*.kt' -o -name 'SeeAll*.kt' | grep -v build/ | head
echo "== other sharedUi artist photo hints"
grep -rlIE --include=*.kt "CircleShape" sharedUi/src app/src | head -30
} > $O
wc -l $O
