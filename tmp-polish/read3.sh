OUT=tmp-polish/out-g.txt
: > "$OUT"
H=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt
D=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
S=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/SearchScreen.kt
for spec in "$H:295:365" "$H:735:810" "$H:1030:1075" "$D:1042:1104" "$D:1525:1568" "$D:2275:2330" "$S:300:325" "$S:940:988"; do
  IFS=: read -r file start end <<< "$spec"
  echo "== $file:$start-$end" >> "$OUT"
  sed -n "${start},${end}p" "$file" | cut -c1-160 >> "$OUT"
done
echo '== ShelfItem declaration locations' >> "$OUT"
grep -rn 'data class ShelfItem\|class ShelfItem' shared/src sharedUi/src app/src/main/java/com/music/amusic/data --include='*.kt' | cut -c1-160 | head -12 >> "$OUT"
