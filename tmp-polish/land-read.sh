#!/bin/bash
O=tmp-polish
S=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui
P=$S/player
{ echo '== LandscapePlayer 225-290'; sed -n '225,290p' $P/LandscapePlayer.kt; echo '== funcs'; grep -nE '^(internal |private |public )?(@Composable )?fun |^@Composable' $P/LandscapePlayer.kt; echo '== landscape in NowPlaying'; grep -n -i 'landscape' $P/NowPlayingScreen.kt | sed -n '1,70p'; } | cut -c1-200 > $O/out-land-g.txt
{ echo '== caption'; grep -rnE 'playbackOriginText|hideSongStatus' $S ../../../../app/src/main/java 2>/dev/null; grep -rnE 'playbackOriginText|hideSongStatus' app/src/main/java sharedUi/src | cut -c1-220; echo '== manifest'; grep -nE 'screenOrientation|configChanges|android:name=".MainActivity|resizeable' app/src/main/AndroidManifest.xml; echo '== 1885-1895'; sed -n '1885,1896p' $P/NowPlayingScreen.kt; echo '== 2370-2410'; sed -n '2368,2410p' $P/NowPlayingScreen.kt; } | cut -c1-200 > $O/out-land-h.txt
