import sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
C = "app/src/main/java/com/music/amusic/"


def rd(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def wr(p, s):
    with open(os.path.join(ROOT, p), "w", encoding="utf-8", newline="") as f:
        f.write(s)


def rep(s, old, new, count=1, label=""):
    n = s.count(old)
    if n != count:
        raise SystemExit("ANCHOR %s: esperado %d, achou %d" % (label or old[:60], count, n))
    return s.replace(old, new)


# ---------------- GlassNavBar.kt ----------------
gp = C + "ui/components/GlassNavBar.kt"
g = rd(gp)

g = rep(g, "import androidx.compose.animation.SharedTransitionScope\n",
        "import androidx.compose.animation.SharedTransitionScope\nimport androidx.compose.animation.animateColorAsState\n", label="imp1")
g = rep(g, "import androidx.compose.animation.core.animateFloatAsState\n",
        "import androidx.compose.animation.core.animateFloatAsState\nimport androidx.compose.animation.core.snap\nimport androidx.compose.animation.core.tween\n", label="imp2")
g = rep(g, "import androidx.compose.foundation.background\n",
        "import androidx.compose.foundation.background\nimport androidx.compose.foundation.border\n", label="imp3")
g = rep(g, "import coil3.compose.AsyncImage\n",
        "import androidx.lifecycle.compose.collectAsStateWithLifecycle\nimport coil3.compose.AsyncImage\n", label="imp4")
g = rep(g, "import com.music.amusic.data.model.artworkAt\n",
        "import com.music.amusic.data.model.artworkAt\nimport com.music.amusic.data.settings.AppSettings\n", label="imp5")
g = rep(g, "import com.music.amusic.ui.player.PlayerDock\n",
        "import com.music.amusic.ui.player.PlayerDock\nimport dev.chrisbanes.haze.HazeState\nimport dev.chrisbanes.haze.materials.ExperimentalHazeMaterialsApi\nimport dev.chrisbanes.haze.materials.HazeMaterials\n", label="imp6")

# signature
g = rep(g, "@Composable\nfun GlassNavBar(", "@OptIn(ExperimentalHazeMaterialsApi::class)\n@Composable\nfun GlassNavBar(", label="sig-optin")
g = rep(g,
"""    /** Dragging the bar's player up into the full player. */
    pull: MiniPlayerPull? = null,
    modifier: Modifier = Modifier,
) {
    // Held for the same reason [tabs] is.""",
"""    /** Dragging the bar's player up into the full player. */
    pull: MiniPlayerPull? = null,
    /**
     * Where the plain surfaces sample their frost from. Read only when
     * [plainSurface] is on; null falls back to the solid theme surface.
     */
    hazeState: HazeState? = null,
    /**
     * The standard bar's material on this same layout and motion: the tab pill,
     * the Search circle and the now playing pill keep the plain bar's Haze
     * surface, hairline, theme colours and indicator instead of liquid glass.
     * Off (the default) is the liquid glass bar exactly as it was.
     */
    plainSurface: Boolean = false,
    modifier: Modifier = Modifier,
) {
    // Held for the same reason [tabs] is.""", label="sig-params")

# colours
g = rep(g,
"""    val contentColor = glassContentColor()
    val selectedColor = contentColor
    val unselectedColor = contentColor.copy(alpha = 0.65f)
""",
"""    val scheme = MaterialTheme.colorScheme
    // The plain bar's own tints: primary on the selected tab, onSurfaceVariant
    // on the rest, onBackground on the now playing title. Glass keeps the
    // black or white it reads off the theme.
    val contentColor = if (plainSurface) scheme.onBackground else glassContentColor()
    val selectedColor = if (plainSurface) scheme.primary else contentColor
    val unselectedColor = if (plainSurface) scheme.onSurfaceVariant else contentColor.copy(alpha = 0.65f)
    val artistColor = if (plainSurface) scheme.onSurfaceVariant else contentColor.copy(alpha = 0.7f)
""", label="colors")

# surfaces
g = rep(g,
"""    val glassSurface: @Composable () -> Modifier = { Modifier.liquidGlass(shape = pillShape) }
""",
"""    val glassSurface: @Composable () -> Modifier = {
        if (plainSurface) {
            plainBarSurface(hazeState = hazeState, shape = pillShape, thin = false)
        } else {
            Modifier.liquidGlass(shape = pillShape)
        }
    }
    // The now playing pill: the plain mini player's thin frost over the tab
    // pill's regular one, as in the standard bars.
    val accessorySurface: @Composable () -> Modifier = {
        if (plainSurface) {
            plainBarSurface(hazeState = hazeState, shape = pillShape, thin = true)
        } else {
            glassSurface()
        }
    }
""", label="surface")
g = rep(g, ".then(glassSurface())", ".then(accessorySurface())", count=2, label="acc-surface")

# artist colour into both docked players
g = rep(g, "                    pull = pull,\n                    modifier = accessoryModifier",
        "                    pull = pull,\n                    artistColor = artistColor,\n                    modifier = accessoryModifier", count=2, label="acc-artist")

# indicator
g = rep(g, "            indicatorColor = glassIndicatorColor().copy(alpha = 0.5f),\n",
        "            indicatorColor = if (plainSurface) {\n                scheme.primary.copy(alpha = 0.14f)\n            } else {\n                glassIndicatorColor().copy(alpha = 0.5f)\n            },\n", label="indicator")

# tab tint eased in the plain bar (the standard bar's 200 ms), snapped in glass as before
g = rep(g,
"""            val tint = if (isSelected) selectedColor else unselectedColor
            val onClick = {""",
"""            val targetTint = if (isSelected) selectedColor else unselectedColor
            val onClick = {""", label="tint1")
g = rep(g,
"""                    icon = {
                        Icon(
                            imageVector = tab.icon,
                            contentDescription = tab.label,
                            tint = tint,""",
"""                    icon = {
                        val tint by animateColorAsState(
                            targetValue = targetTint,
                            animationSpec = if (plainSurface) tween(200) else snap(),
                            label = "tabTint",
                        )
                        Icon(
                            imageVector = tab.icon,
                            contentDescription = tab.label,
                            tint = tint,""", count=2, label="tint2")
g = rep(g,
"""                    title = {
                        Text(
                            text = tab.label,
                            style = MaterialTheme.typography.labelSmall,
                            color = tint,""",
"""                    title = {
                        val tint by animateColorAsState(
                            targetValue = targetTint,
                            animationSpec = if (plainSurface) tween(200) else snap(),
                            label = "tabTitleTint",
                        )
                        Text(
                            text = tab.label,
                            style = MaterialTheme.typography.labelSmall,
                            color = tint,""", label="tint3")

# GlassNowPlaying param + artist line
g = rep(g,
"""    pull: MiniPlayerPull?,
    modifier: Modifier = Modifier,
) {
    val haptics = rememberHaptics()
    val pressSource""",
"""    pull: MiniPlayerPull?,
    artistColor: Color = contentColor.copy(alpha = 0.7f),
    modifier: Modifier = Modifier,
) {
    val haptics = rememberHaptics()
    val pressSource""", label="np-param")
g = rep(g, "                        color = contentColor.copy(alpha = 0.7f),\n",
        "                        color = artistColor,\n", label="np-artist")

# helper at the end
g = g.rstrip("\n") + '''

/**
 * The standard bar's surface, for [GlassNavBar]'s plain mode: the same Haze
 * material, theme surface colour, "reduce dynamic blur" solid fill and hairline
 * that [FloatingBottomBar] (regular) and [MiniPlayer] (thin) draw, so the
 * opacity and background are the ones the bar has always had. No lens, no
 * rim highlight, no shadow pass.
 *
 * The shape is already clipped by the tab bar before this is applied.
 */
@OptIn(ExperimentalHazeMaterialsApi::class)
@Composable
private fun plainBarSurface(
    hazeState: HazeState?,
    shape: RoundedCornerShape,
    thin: Boolean,
): Modifier {
    val reduceDynamicBlur by AppSettings.reduceDynamicBlur.collectAsStateWithLifecycle()
    val container = MaterialTheme.colorScheme.surface
    val fill = if (reduceDynamicBlur || hazeState == null) {
        Modifier.background(container)
    } else {
        Modifier.optimizedHazeEffect(
            state = hazeState,
            style = if (thin) HazeMaterials.thin(container) else HazeMaterials.regular(container),
        )
    }
    return fill.border(GLASS_EDGE_WIDTH, GLASS_EDGE_COLOR, shape)
}
'''
wr(gp, g)

# ---------------- FloatingTabBar.kt ----------------
fp = C + "ui/components/floatingtabbar/FloatingTabBar.kt"
f = rd(fp)
f = rep(f, "import com.music.amusic.ui.components.LocalGlassExport\n",
        "import com.music.amusic.ui.components.LocalGlassExport\nimport com.music.amusic.ui.components.LocalLiquidGlassEnabled\n", label="ft-imp")
f = rep(f, "    val glassPill = isGlassSupported() && !reduceDynamicBlur\n",
        "    // Also off when Liquid Glass is: the plain bar runs this same layout and\n    // motion, and its selection is the flat pill, not a lens over the page.\n    val glassPill = LocalLiquidGlassEnabled.current && isGlassSupported() && !reduceDynamicBlur\n", label="ft-glassPill")
wr(fp, f)

# ---------------- MainActivity.kt ----------------
mp = C + "MainActivity.kt"
m = rd(mp)
m = rep(m,
"""                            if (glassActive) {
                                Modifier
                                    // Not under "reduce dynamic blur\"""",
"""                            if (glassActive || UNIFIED_NAV_BAR) {
                                Modifier
                                    // Not under "reduce dynamic blur\"""", label="main-scroll")
m = rep(m, "                if (glassActive) Column(\n", "                if (glassActive || UNIFIED_NAV_BAR) Column(\n", label="main-col")
m = rep(m,
"""                        pull = playerSheetMotion.takeIf { !reducePlayerMotion },
                        modifier = Modifier.fillMaxWidth(),
                    )
                } else Column(""",
"""                        pull = playerSheetMotion.takeIf { !reducePlayerMotion },
                        hazeState = hazeState,
                        // Liquid glass off: the same layout and fold, on the
                        // standard bar's own surface.
                        plainSurface = !glassActive,
                        modifier = Modifier.fillMaxWidth(),
                    )
                } else Column(""", label="main-call")
m = m.rstrip("\n") + '''

/**
 * The standard bar uses [GlassNavBar]'s layout (tab pill + separate Search
 * circle, the now playing pill docked in it, the fold on scroll) with its own
 * surface. The older MiniPlayer + FloatingBottomBar branch stays in
 * MainActivity behind this switch rather than being removed.
 */
private val UNIFIED_NAV_BAR: Boolean get() = true
'''
wr(mp, m)
print("OK")
