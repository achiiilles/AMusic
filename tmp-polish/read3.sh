OUT=tmp-polish/out-g.txt
: > "$OUT"
for f in sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/{HomeScreen,SearchScreen,ExploreScreen}.kt sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components/Common.kt app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt; do
  echo "== FILE $f" >> "$OUT"
  grep -n -E 'AsyncImage\(|ArtistAwareImage\(|HeroCard\(|TopResultCard\(|BrowseType.ARTIST|ShelfItem.Type.ARTIST|item.type|item.category|item.browse|artistName|ArtistCard|artistCard' "$f" | cut -c1-160 | head -85 >> "$OUT"
  if [[ "$f" == *HomeScreen.kt ]]; then
    for span in 330,365 455,485 755,810 1025,1065; do sed -n "${span}p" "$f" | cut -c1-160 >> "$OUT"; done
  fi
  if [[ "$f" == *SearchScreen.kt ]]; then
    sed -n '307,336p;475,505p;704,735p' "$f" | cut -c1-160 >> "$OUT"
  fi
  if [[ "$f" == *ExploreScreen.kt ]]; then
    grep -n -C 9 'AsyncImage(' "$f" | cut -c1-160 | head -120 >> "$OUT"
  fi
  if [[ "$f" == *Common.kt ]]; then
    grep -n -C 9 'AsyncImage(' "$f" | cut -c1-160 | head -120 >> "$OUT"
  fi
  if [[ "$f" == *DetailScreen.kt ]]; then
    grep -n -C 6 'AsyncImage(' "$f" | cut -c1-160 | head -120 >> "$OUT"
  fi
done
