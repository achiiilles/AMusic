OUT=tmp-polish/blur-out.txt
: > "$OUT"
echo '== files mentioning the preference (names only)' >> "$OUT"
grep -rliE 'desfoque|reduceBlur|reduce_blur|ReduceDynamicBlur|reduceDynamicBlur|dynamicBlur' --include='*.kt' --include='*.xml' --include='*.java' . 2>/dev/null | head -40 >> "$OUT"
echo '== matching lines' >> "$OUT"
grep -rnE 'desfoque|reduceBlur|reduce_blur|ReduceDynamicBlur|reduceDynamicBlur|dynamicBlur' --include='*.kt' --include='*.xml' --include='*.java' . 2>/dev/null | cut -c1-200 | head -80 >> "$OUT"
