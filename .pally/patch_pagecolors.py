import hashlib, os, subprocess, sys

BASE = 'app/src/main/java/com/music/amusic'
MP = BASE + '/MainActivity.kt'
TP = BASE + '/ui/theme/Theme.kt'
AP = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/theme/ArtworkPalette.kt'
EXPECT = {
    MP: '0054712dffdd69fd4916eb022d1f071d010abe1b',
    TP: '5cfe33a44376b18501988bb99c933800fd05534b',
    AP: 'a2e38cb78176a76781b90df72a54cff1f1cdf901',
}

def gh(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

def bal(s):
    return (s.count('{') - s.count('}'), s.count('(') - s.count(')'))

def rep(s, old, new, cnt=1):
    assert s.count(old) == cnt, ('anchor count', s.count(old), old[:80])
    return s.replace(old, new)

def cut(s, start, end):
    a = s.find(start)
    b = s.find(end)
    assert a >= 0 and b > a, ('cut markers', start[:60], end[:60])
    assert s.count(start) == 1 and s.count(end) == 1, ('cut markers not unique', start[:60])
    return s[:a] + s[b:]

orig = {}
for p, sha in EXPECT.items():
    b = open(p, 'rb').read()
    assert gh(b) == sha, ('sha changed', p, gh(b))
    orig[p] = b.decode('utf-8')

# ---------------- MainActivity.kt: undo 5ba9470 ----------------
s = orig[MP]
s = rep(s, "import com.music.amusic.ui.theme.PageDarkTheme\n", "")
s = rep(s, "/** How long the fades at the screen's ends take to settle onto a coloured page's tint. */\nprivate const val PAGE_SCRIM_FADE_MS = 220\n\n", "")
s = rep(s, "    // The glyphs themselves are set further down, once the page on screen is known.\n",
        "    SystemBarIcons(\n        dark = !darkTheme && !showNowPlaying && !showReplay && replayStory == null && !onboardingVisible,\n    )\n")
s = cut(s, "    // On the Light theme the coloured pages (album, single, playlist, artist and\n", "    val detailPalette = rememberArtworkPalette(")
s = rep(s, "        dark = darkTheme || detailDarkPage,\n", "")
a = s.find("                        // Coloured pages are drawn in the dark colours on the Light theme.\n")
mark = "                        PageDarkTheme(enabled = pageDark) {\n"
b = s.find(mark)
assert a >= 0 and b > a and s.count(mark) == 1
s = s[:a] + s[b + len(mark):]
s = rep(s, "pullState = if (isLibraryArtistPage) detailPull else null,\n                        )\n                        }\n",
        "pullState = if (isLibraryArtistPage) detailPull else null,\n                        )\n")
s = rep(s, "val chromePageColor = if (isDetailVisible || lightThemeDarkPage) {", "val chromePageColor = if (isDetailVisible) {")
s = cut(s, "                // What the fades at the top and foot of the screen paint. On the Light\n", "                // This is the bottom floor itself turned upside down")
s = rep(s, "pageColor = scrimPageColor,", "pageColor = chromePageColor,", 2)
s = rep(s, "                // Over a coloured page on the Light theme the bar's circles, pill and\n                // veil are the dark ones; everywhere else this passes the theme through.\n                PageDarkTheme(enabled = lightThemeDarkPage) {\n", "")
s = rep(s, "                    },\n                )\n                }\n\n                // Drawn before the bars so their own glass reads on top of it.",
        "                    },\n                )\n\n                // Drawn before the bars so their own glass reads on top of it.")
for k in ['PageDarkTheme', 'detailDarkPage', 'lightThemeDarkPage', 'pageDark', 'scrimPageColor', 'PAGE_SCRIM_FADE_MS']:
    assert s.count(k) == 0, k
new = {MP: s}

# ---------------- Theme.kt: undo 5ba9470 ----------------
t = orig[TP]
t = cut(t, "/** How long a page takes to settle", "/**\n * Draws the status and navigation bar glyphs")
for imp in ["androidx.compose.animation.core.animateFloatAsState", "androidx.compose.animation.core.tween",
            "androidx.compose.material3.ColorScheme", "androidx.compose.material3.LocalContentColor",
            "androidx.compose.runtime.CompositionLocalProvider", "androidx.compose.runtime.getValue",
            "androidx.compose.ui.graphics.lerp"]:
    t = rep(t, "import " + imp + "\n", "")
new[TP] = t

# ---------------- ArtworkPalette.kt ----------------
p = orig[AP]
a = p.find("    // A dark page asked for from outside the dark scheme (the bars around a\n")
b = p.find("    val spec: AnimationSpec<Color> = if (reduceAnimation")
assert a > 0 and b > a
p = p[:a] + """    val target = shaped?.toPalette(dark) ?: ArtworkPalette(
        background = scheme.background,
        wash = scheme.background,
        elevated = scheme.surfaceVariant,
        accent = scheme.primary,
        onBackground = scheme.onBackground,
        onBackgroundVariant = scheme.onSurfaceVariant,
        divider = scheme.outline,
    )

""" + p[b:]

p = rep(p, """private fun Seed.toPalette(dark: Boolean): ArtworkPalette = if (dark && exact) {
    toExactPalette()
} else if (dark) {""", """private fun Seed.toPalette(dark: Boolean): ArtworkPalette = if (dark && exact) {
    toExactPalette()
} else if (!dark && exact && dominant.readsWithBlackText()) {
    toExactLightPalette()
} else if (dark) {""")

p = rep(p, """private fun Seed.toExactPalette(): ArtworkPalette {
    val page = dominant.darkenedForWhiteText()
""", """private fun Seed.toExactPalette(): ArtworkPalette {
    val page = dominant.cappedForDarkPage().darkenedForWhiteText()
""")

p = rep(p, """/** Share of white mixed into the page colour for cards and glass buttons. */
private const val EXACT_ELEVATED_WHITE = 0.14f
""", """/**
 * Apple's dark pages sit at about this lightness whatever the release colour:
 * the dark colours Apple publishes for releases (Short n' Sweet, Guts, Man's
 * Best Friend) are all at or under it, and a pale sleeve colour such as a
 * yellow becomes a dark brown of the same hue. A colour already at or under it
 * is left alone; only a lighter one is taken down to it, keeping hue and
 * saturation.
 */
private const val DARK_PAGE_MAX_LIGHTNESS = 0.15f

private fun Color.cappedForDarkPage(): Color =
    withHsl(lightness = { it.coerceAtMost(DARK_PAGE_MAX_LIGHTNESS) })

/** Share of white mixed into the page colour for cards and glass buttons. */
private const val EXACT_ELEVATED_WHITE = 0.14f
""")

p = rep(p, """/** Mixes towards white in small steps until this colour reads at 4.5:1 on [page]. */""", """/** True when black text on this colour reads at 4.5:1. */
private fun Color.readsWithBlackText(): Boolean = exactContrast(Color.Black, this) >= BODY_TEXT_CONTRAST

/**
 * The page for an album or single on the Light theme, when Apple's colour for
 * the release is pale enough for dark text: that colour, flat, as it is, with
 * black text. Cards and glass buttons are the page taken a little darker, the
 * secondary text is the page taken well down, and the accent is Apple's own
 * text colour for the release, darkened only if it would not read. A colour too
 * dark for dark text is not handled here; it keeps the pale tint of its hue.
 */
private fun Seed.toExactLightPalette(): ArtworkPalette {
    val page = dominant
    return ArtworkPalette(
        background = page,
        wash = page,
        elevated = page.mixToward(Color.Black, EXACT_LIGHT_ELEVATED_BLACK),
        accent = vibrant.darkenedToContrastOn(page),
        onBackground = Color.Black,
        onBackgroundVariant = page.mixToward(Color.Black, EXACT_LIGHT_VARIANT_BLACK),
        divider = Color.Black.copy(alpha = 0.12f),
    )
}

/** Share of black mixed into the page colour for cards and glass buttons on a light page. */
private const val EXACT_LIGHT_ELEVATED_BLACK = 0.08f

/** Share of black mixed into the page colour for secondary text on a light page. */
private const val EXACT_LIGHT_VARIANT_BLACK = 0.60f

/** Mixes towards black in small steps until this colour reads at 4.5:1 on [page]. */
private fun Color.darkenedToContrastOn(page: Color): Color {
    var result = this
    var steps = 0
    while (exactContrast(result, page) < BODY_TEXT_CONTRAST && steps < 20) {
        result = result.mixToward(Color.Black, 0.1f)
        steps++
    }
    return result
}

/** Mixes towards white in small steps until this colour reads at 4.5:1 on [page]. */""")
new[AP] = p

for q in EXPECT:
    assert bal(new[q]) == bal(orig[q]), ('balance', q, bal(orig[q]), bal(new[q]))

for q, txt in new.items():
    open(q, 'w', encoding='utf-8', newline='').write(txt)
if os.environ.get('DRY') == '1':
    print('dry ok')
    sys.exit(0)
subprocess.run(['git', 'config', 'user.name', 'pally-bot'], check=True)
subprocess.run(['git', 'config', 'user.email', 'pally-bot@users.noreply.github.com'], check=True)
subprocess.run(['git', 'add'] + list(EXPECT), check=True)
subprocess.run(['git', 'commit', '-m', 'Paginas coloridas: segue o tema (sem visual escuro forcado no Claro); album e single no Claro usam a cor clara da Apple com texto escuro, no Escuro a versao escura [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
