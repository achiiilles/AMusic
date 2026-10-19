#!/bin/bash
cd "$1"
O=tmp-polish/out-color-recon.txt
: > $O
M=app/src/main/java/com/music/amusic
U=sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui
x() { echo "=== $1 [$2,$3] ==="; sed -n "$2,$3p" "$1" | cut -c1-200; }
{
x $U/theme/ArtworkPalette.kt 40 135
x $U/player/MeshGradient.kt 225 330
x $U/player/NowPlayingScreen.kt 755 775
echo '=== grep NowPlayingScreen ==='
grep -nE 'statusBars|WindowInsets|ArtworkMeshBackdrop|rememberArtworkColors|MeshPalette|fun NowPlaying|fun PlayerSheet|Brush|background\(' $U/player/NowPlayingScreen.kt | cut -c1-200 | head -80
x $M/ui/components/GlassNavBar.kt 330 520
x $M/MainActivity.kt 4150 4260
} >> $O
wc -l $O
