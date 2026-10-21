import sys
EDITS = [
('app/src/main/java/com/music/amusic/ui/components/LiquidGlass.kt', r'''@Composable
fun glassIndicatorColor(): Color =
    if (MaterialTheme.colorScheme.surface.luminance() > 0.5f) Color.White else Color.Black
''', r'''@Composable
fun glassIndicatorColor(): Color =
    if (MaterialTheme.colorScheme.surface.luminance() > 0.5f) Color.White else Color.Black

/**
 * Fill alpha of a veiled circle or capsule in light theme. The dark theme's
 * white veil lifts a near-black page; on a white or pastel page the same white
 * veil has nothing to lift, so light theme darkens the page slightly instead,
 * by an amount that shows about as clearly as the white one does in dark theme.
 */
internal const val LIGHT_THEME_VEIL_FILL_ALPHA = 0.08f

/** Hairline alpha of a veiled circle or capsule in light theme. */
internal const val LIGHT_THEME_VEIL_EDGE_ALPHA = 0.14f

/**
 * Fill of a veiled button over the page. Dark theme keeps its white veil at
 * [darkAlpha], unchanged; light theme uses a faint black veil.
 */
@Composable
internal fun veilFillColor(darkAlpha: Float): Color =
    if (MaterialTheme.colorScheme.surface.luminance() > 0.5f) {
        Color.Black.copy(alpha = LIGHT_THEME_VEIL_FILL_ALPHA)
    } else {
        Color.White.copy(alpha = darkAlpha)
    }

/** Hairline of a veiled button. Dark theme keeps its white edge at [darkAlpha]. */
@Composable
internal fun veilEdgeColor(darkAlpha: Float): Color =
    if (MaterialTheme.colorScheme.surface.luminance() > 0.5f) {
        Color.Black.copy(alpha = LIGHT_THEME_VEIL_EDGE_ALPHA)
    } else {
        Color.White.copy(alpha = darkAlpha)
    }
'''),
('app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt', r'''                .background(Color.White.copy(alpha = TOP_BAR_VEIL_FILL_ALPHA * veilAmount), shape)
''', r'''                .background(veilFill.copy(alpha = veilFill.alpha * veilAmount), shape)
'''),
('app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt', r'''    val edgeWidth = GLASS_EDGE_WIDTH + (1.dp - GLASS_EDGE_WIDTH) * veilAmount
''', r'''    val edgeWidth = GLASS_EDGE_WIDTH + (1.dp - GLASS_EDGE_WIDTH) * veilAmount
    // Light theme: a white veil and a white hairline vanish on a light page, so
    // the veil darkens it instead. Dark theme resolves to the same white as before.
    val veilFill = veilFillColor(TOP_BAR_VEIL_FILL_ALPHA)
    val edgeColor by animateColorAsState(
        targetValue = if (veil) veilEdgeColor(GLASS_EDGE_COLOR.alpha) else GLASS_EDGE_COLOR,
        animationSpec = tween(180),
        label = "topBarVeilEdge",
    )
'''),
('app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt', r'''        .border(edgeWidth, GLASS_EDGE_COLOR, shape)
}

/**
 * The account affordance''', r'''        .border(edgeWidth, edgeColor, shape)
}

/**
 * The account affordance'''),
('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt', r'''                    Modifier
                        .background(Color.White.copy(alpha = LIGHT_FILL_ALPHA), CircleShape)
                        .liquidGlassRim(CircleShape)
                        .border(1.dp, Color.White.copy(alpha = TOP_RELEASE_EDGE_ALPHA), CircleShape)''', r'''                    Modifier
                        .background(veilFillColor(LIGHT_FILL_ALPHA), CircleShape)
                        .liquidGlassRim(CircleShape)
                        .border(1.dp, veilEdgeColor(TOP_RELEASE_EDGE_ALPHA), CircleShape)'''),
('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt', r'''            .alpha(if (enabled) 1f else DISABLED_ACTION_ALPHA)
            .clip(CircleShape)
            .background(Color.White.copy(alpha = LIGHT_FILL_ALPHA), CircleShape)''', r'''            // Light theme dims only the glyph of a disabled button: dimming the
            // whole circle as well would take its faint veil below visibility.
            .alpha(if (enabled || lightTheme) 1f else DISABLED_ACTION_ALPHA)
            .clip(CircleShape)
            .background(veilFillColor(LIGHT_FILL_ALPHA), CircleShape)'''),
('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt', r'''            .liquidGlassRim(CircleShape)
            .border(1.dp, Color.White.copy(alpha = TOP_RELEASE_EDGE_ALPHA), CircleShape)
            .clickable(enabled = enabled) {''', r'''            .liquidGlassRim(CircleShape)
            .border(1.dp, veilEdgeColor(TOP_RELEASE_EDGE_ALPHA), CircleShape)
            .clickable(enabled = enabled) {'''),
('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt', r'''            contentDescription = contentDescription,
            tint = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.size(size * 0.44f),''', r'''            contentDescription = contentDescription,
            tint = if (!enabled && lightTheme) {
                MaterialTheme.colorScheme.onSurface.copy(alpha = DISABLED_ACTION_ALPHA)
            } else {
                MaterialTheme.colorScheme.onSurface
            },
            modifier = Modifier.size(size * 0.44f),'''),
('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt', r'''    val haptics = rememberHaptics()
    Box(
        modifier = Modifier
            .size(size)
            // Light theme dims''', r'''    val haptics = rememberHaptics()
    val lightTheme = MaterialTheme.colorScheme.surface.luminance() > 0.5f
    Box(
        modifier = Modifier
            .size(size)
            // Light theme dims'''),
('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt', r'''                    .background(Color.White.copy(alpha = LIGHT_FILL_ALPHA), CircleShape)
                    .border(1.dp, Color.White.copy(alpha = TOP_RELEASE_EDGE_ALPHA), CircleShape)
                    .clickable {
                        haptics.play(if (saved)''', r'''                    .background(veilFillColor(LIGHT_FILL_ALPHA), CircleShape)
                    .border(1.dp, veilEdgeColor(TOP_RELEASE_EDGE_ALPHA), CircleShape)
                    .clickable {
                        haptics.play(if (saved)'''),
('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt', r'''import androidx.compose.ui.graphics.SolidColor
''', r'''import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.luminance
'''),
('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt', r'''import com.music.amusic.ui.components.thumbnailBorder
''', r'''import com.music.amusic.ui.components.thumbnailBorder
import com.music.amusic.ui.components.veilEdgeColor
import com.music.amusic.ui.components.veilFillColor
''')
]
seen = {}
for path, old, new in EDITS:
    text = seen.get(path)
    if text is None:
        text = open(path, encoding="utf-8").read()
    if text.count(old) != 1:
        print("MISMATCH", path, text.count(old), old[:70])
        sys.exit(1)
    seen[path] = text.replace(old, new)
for path, text in seen.items():
    open(path, "w", encoding="utf-8", newline="").write(text)
    print("patched", path)
