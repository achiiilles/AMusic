#!/bin/bash
O=tmp-polish
P=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/player
{ echo '== LP 125-182'; sed -n '125,182p' $P/LandscapePlayer.kt; echo '== NP 1795-1812'; sed -n '1795,1812p' $P/NowPlayingScreen.kt; echo '== other callers'; grep -rn 'LandscapePlayerLayout(' sharedUi app desktopUi tv --include=*.kt; } | cut -c1-200 > $O/out-land-i.txt
