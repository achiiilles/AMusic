#!/bin/bash
O=tmp-polish
P=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/player
git show 2f12e3c 166b48d fee5b92 -U4 --format='== %h %s' | cut -c1-190 > $O/out-land-c.txt
grep -nE 'hideSongStatus|dismissHandle|height\(5\.dp\)|width\(38\.dp\)|spotifyChromeAlpha|DISMISS_STRIP|LandscapePlayer\(|landscapePlayerAvailable\(' $P/NowPlayingScreen.kt $P/LandscapePlayer.kt $P/PlayerSidePanels.kt $P/PlayerControls.kt $P/PlayerHost.kt | cut -c1-230 > $O/out-land-d.txt
grep -rnEi 'ORIENTATION_LANDSCAPE|isLandscape|landscape|NavigationRail|screenWidthDp|windowWidth' app/src/main/java --include=*.kt | cut -c1-230 | head -80 > $O/out-land-e.txt
git show c0543882 d93e8d24 -U2 --format='== %h %s' | cut -c1-190 | head -230 > $O/out-land-f.txt
