#!/bin/bash
D=app/src/main/java/com/music/amusic
F=$D/ui/screens/DetailScreen.kt
{ echo "=== 440-470"; sed -n '440,470p' $F | cut -c1-190
echo "=== 1670-1712"; sed -n '1670,1712p' $F | cut -c1-190
echo "=== 1714-1760"; sed -n '1714,1760p' $F | cut -c1-190
echo "=== 2285-2325"; sed -n '2285,2325p' $F | cut -c1-190
} > tmp-polish/out-colors-d.txt 2>&1
{ echo "=== ArtworkPalette def"; grep -rn "class ArtworkPalette\|fun rememberArtworkPalette" $D | cut -c1-200
P=$(grep -rl "class ArtworkPalette" $D | head -1)
echo "FILE $P"; grep -n "val \|fun " $P | cut -c1-200 | head -80
echo "=== FrostedTopBar users"; grep -rn "FrostedTopBar(\|backButtonHazeState\|TopBarShare\|ShareButton\|artworkPageChrome" $D --include=*.kt | grep -v "ui/components/FrostedTopBar.kt" | cut -c1-200 | head -60
} > tmp-polish/out-colors-e.txt 2>&1
