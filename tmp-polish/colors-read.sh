#!/bin/bash
D=app/src/main/java/com/music/amusic
F=$D/ui/screens/DetailScreen.kt
M=$D/MainActivity.kt
{ echo "=== MainActivity 3600-3760"; sed -n '3600,3760p' $M | cut -c1-200; } > tmp-polish/out-colors-f.txt 2>&1
{ echo "=== consts"; grep -rnE "LIGHT_FILL_ALPHA|TOP_RELEASE_EDGE_ALPHA|GLASS_EDGE_WIDTH|GLASS_EDGE_COLOR" $D | grep -E "val |const" | cut -c1-220
echo "=== CircleIconButton"; grep -rn "fun CircleIconButton" $D | cut -c1-200
C=$(grep -rl "fun CircleIconButton" $D | head -1); echo "FILE $C"; N=$(grep -n "fun CircleIconButton" $C | head -1 | cut -d: -f1); sed -n "$((N-8)),$((N+60))p" $C | cut -c1-190
echo "=== ArtworkPalette"; grep -rn "ArtworkPalette(\|class ArtworkPalette\|rememberArtworkPalette" $D --include=*.kt | grep -v DetailScreen | cut -c1-200 | head
} > tmp-polish/out-colors-g.txt 2>&1
