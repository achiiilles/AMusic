import sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def rd(p):
    with open(os.path.join(ROOT, p), encoding="utf-8", newline="") as f:
        return f.read()


def wr(p, t):
    with open(os.path.join(ROOT, p), "w", encoding="utf-8", newline="") as f:
        f.write(t)


def rep(t, old, new):
    assert t.count(old) == 1, ("anchor", t.count(old), old[:80])
    return t.replace(old, new)


def edit(path, fn):
    t = rd(path)
    nl = "\r\n" if "\r\n" in t else "\n"
    t = t.replace("\r\n", "\n")
    t = fn(t)
    wr(path, t.replace("\n", nl))


AP = "sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/theme/ArtworkPalette.kt"
NP = "sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/player/NowPlayingScreen.kt"
GN = "app/src/main/java/com/music/amusic/ui/components/GlassNavBar.kt"
MP = "app/src/main/java/com/music/amusic/ui/components/MiniPlayer.kt"

PALETTE_ADD = """
/**
 * The colour a bar takes from the sleeve while its text and symbols stay as
 * they are. Read off the same per-artwork cache the pages' palettes use, so a
 * sleeve that has been seen once costs nothing the second time, and only a
 * sleeve seen for the first time is decoded, once, off the main thread.
 *
 * The tone is taken down (or, on a light theme, up) until the unchanged text
 * still reads on it: a pale cover gives a dark shade of its hue, not a pale
 * one that white text would disappear into. [deep] goes further down, for a
 * scrim that sits over a picture.
 *
 * Changes fade over [BAR_FADE_MS] on a plain ease, no spring. Until a colour
 * is known, and while the next sleeve is still being read, the last one is
 * held — or [fallback] if there never was one — so a skip never flashes.
 * The result is read at draw time by whoever paints it, so the fade does not
 * recompose anything. "Reduce animation" turns it into a cut.
 */
@Composable
fun rememberArtworkBarColor(
    imageUrl: String?,
    artPx: Int = CARD_ART_PX,
    dark: Boolean = MaterialTheme.colorScheme.background.luminance() < 0.5f,
    deep: Boolean = false,
    fallback: Color = Color.Transparent,
): State<Color> {
    val reduceAnimation by PlayerPlatform.host.settings.reduceAnimation.collectAsStateWithLifecycle()
    val seed = rememberArtworkSeed(imageUrl, artPx)
    val computed = remember(seed, dark, deep) { seed?.barColor(dark, deep) }
    val held = remember { mutableStateOf(computed) }
    LaunchedEffect(computed) {
        if (computed != null) held.value = computed
    }
    val spec: AnimationSpec<Color> = if (reduceAnimation) {
        snap()
    } else {
        tween(BAR_FADE_MS, easing = FastOutSlowInEasing)
    }
    return animateColorAsState(
        targetValue = held.value ?: fallback,
        animationSpec = spec,
        label = "artworkBarColor",
    )
}

private fun Seed.barColor(dark: Boolean, deep: Boolean): Color = if (dark) {
    dominant.withHsl(
        saturation = { adaptedArtworkSaturation(it, minimum = 0.30f, maximum = 0.65f) },
        lightness = { if (deep) 0.14f else 0.26f },
    )
} else {
    dominant.withHsl(
        saturation = { adaptedArtworkSaturation(it, minimum = 0.25f, maximum = 0.60f) },
        lightness = { 0.86f },
    )
}

private const val BAR_FADE_MS = 220
"""


def f_ap(t):
    t = rep(t, "import androidx.compose.animation.core.tween\n",
            "import androidx.compose.animation.core.tween\nimport androidx.compose.animation.core.FastOutSlowInEasing\n")
    t = rep(t, "import androidx.compose.runtime.Immutable\n",
            "import androidx.compose.runtime.Immutable\nimport androidx.compose.runtime.State\n")
    return t.rstrip("\n") + "\n" + PALETTE_ADD


edit(AP, f_ap)


def f_np(t):
    t = rep(t, "import com.music.amusic.ui.theme.StatusBarIcons\n",
            "import com.music.amusic.ui.theme.StatusBarIcons\nimport com.music.amusic.ui.theme.rememberArtworkBarColor\n")
    t = rep(t, "    val artworkTint = rememberPlayerTint(remoteArt, ART_PX) ?: Color.White\n",
            """    val artworkTint = rememberPlayerTint(remoteArt, ART_PX) ?: Color.White
    // The status bar's scrim takes a deep shade of the sleeve's colour instead
    // of plain black, black until the colour is known. Icons stay as they are.
    val scrimTint = rememberArtworkBarColor(remoteArt, ART_PX, dark = true, deep = true, fallback = Color.Black)
""")
    t = rep(t, "brush = topScrimBrush,",
            """brush = Brush.verticalGradient(
                                            List(steps) { index ->
                                                val progress = index / (steps - 1).toFloat()
                                                val factor = (1f - progress).toDouble().pow(1.5).toFloat()
                                                scrimTint.value.copy(alpha = topGradientAlpha * factor)
                                            },
                                        ),""")
    return t


edit(NP, f_np)


def f_gn(t):
    t = rep(t, "import com.music.amusic.ui.player.PlayerDock\n",
            "import com.music.amusic.ui.player.PlayerDock\nimport com.music.amusic.ui.theme.rememberArtworkBarColor\n")
    t = rep(t, "    val artistColor = if (plainSurface) scheme.onSurfaceVariant else contentColor.copy(alpha = 0.7f)\n",
            """    val artistColor = if (plainSurface) scheme.onSurfaceVariant else contentColor.copy(alpha = 0.7f)
    // The sleeve's colour under the now playing bar of the standard surface.
    // Text and symbols keep their colours; liquid glass is left as it is.
    val sleeveTint = if (plainSurface) {
        rememberArtworkBarColor(song?.let { rememberRemoteArtworkUrl(it) }, ROW_ART_PX)
    } else {
        null
    }
""")
    t = rep(t, "            plainBarSurface(hazeState = hazeState, shape = pillShape, thin = true)\n",
            "            plainBarSurface(hazeState = hazeState, shape = pillShape, thin = true, tint = sleeveTint)\n")
    t = rep(t, "    thin: Boolean,\n): Modifier {\n    val reduceDynamicBlur",
            "    thin: Boolean,\n    tint: androidx.compose.runtime.State<Color>? = null,\n): Modifier {\n    val reduceDynamicBlur")
    t = rep(t, "    return fill.border(GLASS_EDGE_WIDTH, GLASS_EDGE_COLOR, shape)",
            "    return fill\n        .then(if (tint != null) Modifier.artworkBarTint(tint) else Modifier)\n        .border(GLASS_EDGE_WIDTH, GLASS_EDGE_COLOR, shape)")
    return t


edit(GN, f_gn)

MINI_ADD = """
/**
 * Paints the sleeve's colour over a pill-shaped bar's surface, under its
 * hairline edge and its content. Read at draw time, so a fade between two
 * sleeves redraws the bar without recomposing it. Nothing is drawn until a
 * colour exists, which leaves the bar's own surface as it was.
 */
internal fun Modifier.artworkBarTint(tint: androidx.compose.runtime.State<Color>): Modifier =
    drawBehind {
        val color = tint.value
        if (color.alpha > 0f) {
            drawRoundRect(
                color = color.copy(alpha = color.alpha * ARTWORK_BAR_TINT_ALPHA),
                cornerRadius = CornerRadius(size.height / 2f),
            )
        }
    }

/** Enough of the surface under it still shows for the bar to read as frosted. */
private const val ARTWORK_BAR_TINT_ALPHA = 0.88f
"""


def f_mp(t):
    t = rep(t, "import androidx.compose.ui.draw.clip\n",
            "import androidx.compose.ui.draw.clip\nimport androidx.compose.ui.draw.drawBehind\nimport androidx.compose.ui.geometry.CornerRadius\n")
    t = rep(t, "import com.music.amusic.ui.player.PlayerDock\n",
            "import com.music.amusic.ui.player.PlayerDock\nimport com.music.amusic.ui.theme.rememberArtworkBarColor\n")
    t = rep(t, "    val reduceDynamicBlur by AppSettings.reduceDynamicBlur.collectAsStateWithLifecycle()\n    val haptics = rememberHaptics()\n",
            "    val reduceDynamicBlur by AppSettings.reduceDynamicBlur.collectAsStateWithLifecycle()\n    val haptics = rememberHaptics()\n    val sleeveTint = rememberArtworkBarColor(rememberRemoteArtworkUrl(song), ROW_ART_PX)\n")
    t = rep(t, ".border(0.5.dp, Color.White.copy(alpha = 0.10f), shape)",
            ".artworkBarTint(sleeveTint)\n            .border(0.5.dp, Color.White.copy(alpha = 0.10f), shape)")
    return t.rstrip("\n") + "\n" + MINI_ADD


edit(MP, f_mp)
print("ok")
