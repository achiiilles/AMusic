import sys, os

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
P = "app/src/main/java/com/music/amusic/ui/components/floatingtabbar/FloatingTabBar.kt"


def rd(p):
    with open(os.path.join(ROOT, p), encoding="utf-8", newline="") as f:
        return f.read()


def wr(p, t):
    with open(os.path.join(ROOT, p), "w", encoding="utf-8", newline="") as f:
        f.write(t)


def rep(t, old, new):
    assert t.count(old) == 1, ("anchor", t.count(old), old[:70])
    return t.replace(old, new)


t = rd(P)
nl = "\r\n" if "\r\n" in t else "\n"
t = t.replace("\r\n", "\n")

t = rep(
    t,
    "import androidx.compose.animation.core.snap\n",
    "import androidx.compose.animation.core.snap\nimport androidx.compose.animation.core.tween\n",
)

t = rep(
    t,
    "    val barGlass = rememberLayerBackdrop()\n    val tabRow = rememberLayerBackdrop()\n",
    """    val barGlass = rememberLayerBackdrop()
    val tabRow = rememberLayerBackdrop()

    // The standard bar's selection: same shape the pill always had, but it
    // slides to the tab on a short ease instead of the glass spring. It never
    // lifts past the bar and never squashes, so the bar's clip has nothing to
    // cut off, including on the last tab. Liquid Glass keeps its own motion.
    val plainPill = !(LocalLiquidGlassEnabled.current && isGlassSupported())
    val plainPillPosition by animateFloatAsState(
        targetValue = selectedTabIndex.coerceAtLeast(0).toFloat(),
        animationSpec = if (reduceAnimation) snap() else tween(durationMillis = 220, easing = FastOutSlowInEasing),
        label = "plainTabPill",
    )
""",
)

t = rep(
    t,
    """                if (showPill && (!glassPill || pill.isFlat)) {
                    FlatSelectionPill(""",
    """                if (showPill && plainPill) {
                    FlatSelectionPill(
                        color = colors.indicatorColor,
                        modifier = Modifier
                            .matchParentSize()
                            .pillPlacement(
                                center = { pillCenterInRow(plainPillPosition) },
                                size = { restSize },
                            ),
                    )
                } else if (showPill && (!glassPill || pill.isFlat)) {
                    FlatSelectionPill(""",
)

wr(P, t.replace("\n", nl))
print("ok")
