#!/bin/bash
D=app/src/main/java/com/music/amusic
{ grep -n "liquidGlassRim\|fun Modifier.liquidGlass\|^import" $D/ui/components/LiquidGlass.kt | grep -v import | cut -c1-200
grep -n -B2 -A12 "fun Modifier.liquidGlassRim" $D/ui/components/LiquidGlass.kt | cut -c1-200
echo "=== counts"; grep -c "backButtonHazeState = hazeState," $D/MainActivity.kt; grep -c "hazeState = backButtonHazeState" $D/ui/components/FrostedTopBar.kt; grep -c "backButtonHazeState: HazeState? = null," $D/ui/components/FrostedTopBar.kt
grep -n "hazeState = backButtonHazeState" $D/ui/components/FrostedTopBar.kt | cat -A | cut -c1-160
grep -n "artworkPageSurface\|ACCESSORY_GAP = " $D/ui/components/FrostedTopBar.kt
} > tmp-polish/out-colors-h.txt 2>&1
