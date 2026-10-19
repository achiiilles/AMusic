OUT=tmp-polish/replay-out.txt
: > "$OUT"
echo '== ReplayCreditCard locations' >> "$OUT"
grep -R -n 'fun ReplayCreditCard\|data class ReplayHeroCard\|fun artistRows\|fun artistCard' app/src/main/java/com/music/amusic/ui/replay --include='*.kt' | cut -c1-170 | head -20 >> "$OUT"
echo '== replay components with artwork' >> "$OUT"
grep -R -n -C 6 'ReplayCreditCard\|artworkUrl = card.artworkUrl\|private fun ReplayChartRow\|fun Cover(' app/src/main/java/com/music/amusic/ui/replay --include='*.kt' | cut -c1-170 | head -180 >> "$OUT"
