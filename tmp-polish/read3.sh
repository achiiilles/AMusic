OUT=tmp-polish/out-g.txt
: > $OUT
echo '== AsyncImage files' >> $OUT
grep -rl 'AsyncImage' --include=*.kt . | grep -v '/build/' | head -60 >> $OUT
echo '== ArtistAwareImage signature' >> $OUT
F=$(find . -name ArtistAwareImage.kt | grep -v '/build/' | head -1)
echo "file $F" >> $OUT
grep -n 'fun ' "$F" | cut -c1-170 | head -12 >> $OUT
echo '== target files' >> $OUT
for f in $(find . \( -name SearchScreen.kt -o -name HomeScreen.kt \) | grep -v '/build/'); do
  echo "== FILE $f" >> $OUT
  grep -n -E 'AsyncImage|ArtistAware|TopResultCard|HeroCard|isArtist|ARTIST|Artist' "$f" | cut -c1-170 | head -70 >> $OUT
done
echo '== function bodies' >> $OUT
for f in $(find . \( -name SearchScreen.kt -o -name HomeScreen.kt \) | grep -v '/build/'); do
  for fn in TopResultCard HeroCard; do
    n=$(grep -n "fun $fn" "$f" | head -1 | cut -d: -f1)
    if [ -n "$n" ]; then echo "== $fn in $f at $n" >> $OUT; sed -n "${n},$((n+45))p" "$f" | cut -c1-170 >> $OUT; fi
  done
done
