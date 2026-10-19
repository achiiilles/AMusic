#!/bin/bash
cd "$1"
O=tmp-polish/out-color-recon.txt
: > $O
S='app/src/main sharedUi/src'
{
echo '=== palette / dominant / status bar ==='
grep -rnE 'ArtworkPalette|dominantColor|DominantColor|rememberArtworkColor|Palette\.|PaletteQuantizer|artworkColor|accentFrom|StatusBarIcons|isAppearanceLightStatusBars|statusBarColor|enableEdgeToEdge|SystemBarStyle' $S --include=*.kt | cut -c1-220 | head -120
echo '=== MiniPlayer usage ==='
grep -rnE 'MiniPlayer\(|MiniPlayerNextGlyph|DockedMiniPlayer|miniPlayerGestures|playerDockArt' $S --include=*.kt | cut -c1-220 | head -60
echo '=== files ==='
find sharedUi/src -name '*.kt' | grep -iE 'palette|theme|player|color|statusbar' | head -60
} >> $O
wc -l $O
