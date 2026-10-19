OUT=tmp-polish/replay-out.txt
: > "$OUT"
echo '== credit card definition locations' >> "$OUT"
grep -R -n 'fun ReplayCreditCard\|class ReplayCreditCard' app/src/main/java/com/music/amusic sharedUi/src/jvmSharedMain/kotlin/com/music/amusic --include='*.kt' | cut -c1-170 | head -12 >> "$OUT"
R=app/src/main/java/com/music/amusic/ui/replay/ReplayModel.kt
for span in 355,415 420,480; do echo "== ReplayModel:$span" >> "$OUT"; sed -n "${span}p" "$R" | cut -c1-170 >> "$OUT"; done
