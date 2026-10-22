#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
rm -f .pally/*.txt
DS=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
sed -n '1,90p' "$DS" > .pally/a_imports.txt
sed -n '2715,2815p' "$DS" > .pally/b_sectioncard.txt
sed -n '395,450p' "$DS" > .pally/c_header.txt
sed -n '1128,1168p' "$DS" > .pally/d_carousel.txt
grep -n 'fun ' "$DS" | tail -80 > .pally/e_funs.txt
cat shared/src/jvmSharedMain/kotlin/com/music/amusic/data/ApplePreRelease.kt > .pally/f_apple.txt
sed -n '385,410p' shared/src/commonMain/kotlin/com/music/amusic/data/model/Models.kt > .pally/g_models.txt
sed -n '2155,2195p' app/src/main/java/com/music/amusic/ui/MainViewModel.kt > .pally/h_searchfor.txt
grep -n 'ArtistAwareImage\|artworkAt\|AsyncImage' "$DS" | head -30 > .pally/i_img.txt
ls app/src/main/java/com/music/amusic/ui/screens/ > .pally/j_screens.txt
grep -rn 'coil' app/build.gradle.kts gradle/libs.versions.toml 2>/dev/null | head -10 > .pally/k_coil.txt
grep -n 'window.Dialog\|Dialog(' "$DS" | head -10 > .pally/l_dialog.txt
for f in .github/workflows/*.yml; do echo "== $f"; sed -n '1,14p' "$f"; done > .pally/m_workflows.txt
wc -c "$DS" app/src/main/java/com/music/amusic/ui/MainViewModel.kt shared/src/jvmSharedMain/kotlin/com/music/amusic/data/ApplePreRelease.kt > .pally/n_sizes.txt
exit 0
