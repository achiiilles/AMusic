#!/bin/bash
mkdir -p tmp-polish
O=tmp-polish/out-e.txt
S=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens
A=app/src/main/java/com/music/amusic
{
echo "== Search 877-990"
sed -n '877,990p' $S/SearchScreen.kt | cut -c1-165
echo "== Home 1020-1090"
sed -n '1020,1090p' $S/HomeScreen.kt | cut -c1-165
echo "== Library grep"
grep -nE "AsyncImage|CircleShape|ARTIST|rtist.*(Card|Grid|Item|Row)" $S/LibraryScreen.kt | cut -c1-170 | head -40
echo "== Detail AsyncImage"
grep -nE -B4 -A6 "AsyncImage\(" $A/ui/screens/DetailScreen.kt | cut -c1-150 | head -230
echo "== MainActivity"
grep -nE "AsyncImage|CanvasCache.init|SearchHistory.init" $A/MainActivity.kt $A/*.kt | cut -c1-170 | head
echo "== EntityType"
grep -rn -A8 "enum class EntityType" shared/src | cut -c1-150 | head -14
} > $O
wc -l $O
