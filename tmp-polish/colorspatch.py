import re, sys, subprocess
D = "app/src/main/java/com/music/amusic/"
def edit(path, subs):
    s = open(path, encoding="utf-8").read()
    for pat, rep, n, flags in subs:
        s, c = re.subn(pat, lambda m, rep=rep: m.expand(rep), s, flags=flags)
        if c != n:
            print("FAIL", path, pat[:60], c, "expected", n); sys.exit(1)
    open(path, "w", encoding="utf-8").write(s)

FT = D + "ui/components/FrostedTopBar.kt"
edit(FT, [
 # 1 constant
 (r"(private val ACCESSORY_GAP = 8\.dp\n)",
  "\\1\n/** Fill of the top circles on pages that colour themselves from artwork: the same light veil as the Shuffle and Subscribe circles. */\nprivate const val TOP_BAR_VEIL_FILL_ALPHA = 0.07f\n", 1, 0),
 # 2 FrostedTopBar param
 (r"(\n[ \t]*)(backButtonHazeState: HazeState\? = null,\n)",
  "\\1\\2\\1/** Artwork-coloured pages (album, playlist, artist): circles wear the page's light veil and 1dp hairline instead of the glass. */\\1pageVeil: Boolean = false,\n", 1, 0),
 # 3 back button call
 (r"(\n[ \t]*)hazeState = backButtonHazeState,\n",
  "\\1hazeState = backButtonHazeState,\\1veil = pageVeil,\n", 1, 0),
 # 4 actions call
 (r"ArtworkPageActions\(hazeState = backButtonHazeState, content = actions\)",
  "ArtworkPageActions(hazeState = backButtonHazeState, veil = pageVeil, content = actions)", 1, 0),
 # 5 back button def
 (r"(private fun ArtworkPageBackButton\(\s*onClick: \(\) -> Unit,\s*hazeState: HazeState\?,)(\s*)",
  "\\1\\2veil: Boolean = false,\\2", 1, 0),
 (r"val contentColor = if \(useLiquidGlass && !reduceDynamicBlur\) \{",
  "val contentColor = if (useLiquidGlass && !reduceDynamicBlur && !veil) {", 1, 0),
 (r"artworkPageSurface\(shape = shape, hazeState = hazeState\)",
  "artworkPageSurface(shape = shape, hazeState = hazeState, veil = veil)", 1, 0),
 # 6 actions def
 (r"(private fun ArtworkPageActions\(\s*hazeState: HazeState\?,)(\s*)",
  "\\1\\2veil: Boolean = false,\\2", 1, 0),
 (r"artworkPageSurface\(shape = CircleShape, hazeState = hazeState\)",
  "artworkPageSurface(shape = CircleShape, hazeState = hazeState, veil = veil)", 1, 0),
 # 7 surface def
 (r"(private fun artworkPageSurface\(\s*shape: CornerBasedShape,\s*hazeState: HazeState\?,)(\s*)(\): Modifier \{)",
  "\\1\\2    veil: Boolean = false,\\2\\3", 1, 0),
])
s = open(FT, encoding="utf-8").read()
m = re.search(r"(return Modifier\s*\.clip\(shape\)\s*\.then\(\s*when \{\s*)(useLiquidGlass -> Modifier\.liquidGlass\(shape\))", s)
if not m: print("FAIL surface body"); sys.exit(1)
s = s[:m.start()] + (
 "val veilAmount by animateFloatAsState(\n"
 "        targetValue = if (veil) 1f else 0f,\n"
 "        animationSpec = tween(180),\n"
 "        label = \"topBarVeil\",\n"
 "    )\n"
 "    val edgeWidth = GLASS_EDGE_WIDTH + (1.dp - GLASS_EDGE_WIDTH) * veilAmount\n"
 "    ") + m.group(1) + (
 "veil -> Modifier\n"
 "                .background(Color.White.copy(alpha = TOP_BAR_VEIL_FILL_ALPHA * veilAmount), shape)\n"
 "                .liquidGlassRim(shape)\n"
 "            ") + m.group(2) + s[m.end():]
s, c = re.subn(r"\.border\(GLASS_EDGE_WIDTH, GLASS_EDGE_COLOR, shape\)", ".border(edgeWidth, GLASS_EDGE_COLOR, shape)", s)
if c != 1: print("FAIL border", c); sys.exit(1)
open(FT, "w", encoding="utf-8").write(s)

MA = D + "MainActivity.kt"
edit(MA, [
 (r"(\n[ \t]*)backButtonHazeState = hazeState,\n",
  "\\1backButtonHazeState = hazeState,\\1pageVeil = isDetailVisible,\n", 1, 0),
])
print("OK")
