#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
rm -f .pally/*.txt
DS=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
sed -n '318,405p' "$DS" > .pally/q1_sig.txt
sed -n '1040,1185p' "$DS" > .pally/q2_artistbody.txt
grep -n 'onSectionItemClick' "$DS" > .pally/q3a_click.txt
grep -n 'ApplePreRelease\|activeShelf\|ArtistShelfGridPage' "$DS" > .pally/q3b_shelf.txt
grep -n 'onOpenSong\|onPlaySong\|onPlay\|onBack\|onSearch\|Dialog(' "$DS" > .pally/q3c_calls.txt
grep -rn 'ApplePreRelease' shared/src/jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt > .pally/q4_yt.txt
sed -n '2986,3020p' "$DS" > .pally/q5_pull.txt
wc -l "$DS" > .pally/q6_wc.txt
exit 0
