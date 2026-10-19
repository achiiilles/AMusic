OUT=tmp-polish/blur-out.txt
: > "$OUT"
F=app/src/main/java/com/music/amusic/data/settings/AppSettings.kt
echo "== total lines $(wc -l < $F)" >> "$OUT"
echo '== imports' >> "$OUT"
grep -n '^import android' "$F" | cut -c1-160 >> "$OUT"
for spec in "398:408" "855:900" "1270:1300"; do
  IFS=: read -r start end <<< "$spec"
  echo "== $F:$start-$end" >> "$OUT"
  sed -n "${start},${end}p" "$F" | cut -c1-170 >> "$OUT"
done
echo '== KEY_REDUCE_BLUR and SDK_INT uses' >> "$OUT"
grep -n 'KEY_REDUCE_BLUR\|SDK_INT\|VERSION_CODES' "$F" | cut -c1-170 | head -30 >> "$OUT"
echo '== other readers of the raw key outside AppSettings' >> "$OUT"
grep -rn 'reduce_blur\|reduceBlur\|KEY_REDUCE_BLUR' app/src --include='*.kt' | grep -v 'AppSettings.kt' | cut -c1-170 | head -10 >> "$OUT"
