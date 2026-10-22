import hashlib, subprocess, sys

PAGE_DARK_FADE = "private const val PAGE_DARK_FADE_MS = 220"


def gh(b):
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


AP = "sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/theme/ArtworkPalette.kt"
TH = "app/src/main/java/com/music/amusic/ui/theme/Theme.kt"
MA = "app/src/main/java/com/music/amusic/MainActivity.kt"

TOWARD = """/** This scheme, [amount] (0..1) of the way to [DarkColors]. */
private fun ColorScheme.towardDark(amount: Float): ColorScheme {
    val dark = DarkColors
    fun mix(from: Color, to: Color) = lerp(from, to, amount)
    return copy(
""" + "".join(
    "        %s = mix(%s, dark.%s),\n" % (n, n, n)
    for n in [
        "primary", "onPrimary", "primaryContainer", "onPrimaryContainer", "secondary", "onSecondary",
        "secondaryContainer", "onSecondaryContainer", "tertiary", "onTertiary", "background", "onBackground",
        "surface", "onSurface", "surfaceVariant", "onSurfaceVariant", "surfaceTint", "inverseSurface",
        "inverseOnSurface", "outline", "outlineVariant", "scrim", "surfaceContainer", "surfaceContainerHigh",
        "surfaceContainerHighest", "surfaceContainerLow", "surfaceContainerLowest",
    ]
) + """    )
}

"""

PAGE_DARK = """/** How long a page takes to settle into (or out of) the dark colours. */
private const val PAGE_DARK_FADE_MS = 220

/**
 * Paints [content] in the dark colours while the app itself is on the Light
 * theme. Used for an album or single page whose Apple colour is dark: the page
 * keeps that colour and every button, veil, text colour and hairline that asks
 * the theme gets the dark answer. The look follows the page colour, not the
 * theme. [enabled] crossfades over [PAGE_DARK_FADE_MS]; with it off the current
 * scheme is passed through untouched.
 *
 * It also provides [LocalBaseDarkTheme], so a palette read inside still sees
 * the theme the app is really on.
 */
@Composable
fun PageDarkTheme(
    enabled: Boolean,
    content: @Composable () -> Unit,
) {
    val amount by animateFloatAsState(
        targetValue = if (enabled) 1f else 0f,
        animationSpec = tween(PAGE_DARK_FADE_MS),
        label = "pageDarkTheme",
    )
    val base = MaterialTheme.colorScheme
    val baseDark = LocalBaseDarkTheme.current ?: (base.background.luminance() < 0.5f)
    val scheme = when {
        amount <= 0f -> base
        amount >= 1f -> DarkColors
        else -> base.towardDark(amount)
    }
    val contentColor = lerp(LocalContentColor.current, Color.White, amount)
    MaterialTheme(
        colorScheme = scheme,
        typography = MaterialTheme.typography,
        shapes = MaterialTheme.shapes,
    ) {
        CompositionLocalProvider(
            LocalContentColor provides contentColor,
            LocalBaseDarkTheme provides baseDark,
        ) {
            content()
        }
    }
}

""" + TOWARD

DARK_FN = """/**
 * Light theme, album and single, when Apple's colour for the release is too dark
 * for black text: the page keeps that colour, with white text, icons and
 * hairlines, as Apple's own page does. The look follows the page colour, not
 * the theme. Black reads when its contrast on the colour is at least
 * [BODY_TEXT_CONTRAST] (4.5:1), about 0.175 relative luminance; a darker colour
 * is handled here, a paler one by [toExactLightPalette].
 */
private fun Seed.toExactDarkOnLightPalette(): ArtworkPalette {
    val page = dominant.darkenedForWhiteText()
    val accentBase = vibrant.withHsl(
        saturation = { adaptedArtworkSaturation(it, minimum = 0.55f, maximum = 1f) },
        lightness = { it.coerceIn(0.62f, 0.78f) },
    )
    return ArtworkPalette(
        background = page,
        wash = page,
        elevated = page.mixToward(Color.White, EXACT_ELEVATED_WHITE),
        accent = accentBase.liftedToContrastOn(page),
        onBackground = Color.White,
        onBackgroundVariant = page.mixToward(Color.White, EXACT_VARIANT_WHITE),
        divider = Color.White.copy(alpha = 0.14f),
        pageTop = dominant,
        darkPageOnLight = true,
    )
}

"""

EDITS = [
    (AP, "c080618d810fd0877a6c6df8e0a8bc4118064eb4", [
        ("import androidx.compose.runtime.Immutable\n",
         "import androidx.compose.runtime.Immutable\nimport androidx.compose.runtime.compositionLocalOf\n"),
        ("    val pageTop: Color? = null,\n)\n",
         "    val pageTop: Color? = null,\n"
         "    /**\n"
         "     * Album and single pages only: true when this is the dark page Apple's own\n"
         "     * colour gives a release on the Light theme, drawn with white text and\n"
         "     * icons. The look follows the page colour, not the theme.\n"
         "     */\n"
         "    val darkPageOnLight: Boolean = false,\n)\n\n"
         "/**\n"
         " * The darkness of the theme the app is really on, while a page is composed\n"
         " * under the dark colours on top of the Light theme (see PageDarkTheme). Null\n"
         " * everywhere else, which then reads the theme's own colours.\n"
         " */\n"
         "val LocalBaseDarkTheme = compositionLocalOf<Boolean?> { null }\n"),
        ("fun rememberArtworkPalette(\n    imageUrl: String?,\n    dark: Boolean = MaterialTheme.colorScheme.background.luminance() < 0.5f,\n",
         "fun rememberArtworkPalette(\n    imageUrl: String?,\n    dark: Boolean = LocalBaseDarkTheme.current ?: (MaterialTheme.colorScheme.background.luminance() < 0.5f),\n"),
        ('        pageTop = target.pageTop?.let { animateColorAsState(it, spec, label = "tintPageTop").value },\n    )\n',
         '        pageTop = target.pageTop?.let { animateColorAsState(it, spec, label = "tintPageTop").value },\n'
         '        darkPageOnLight = target.darkPageOnLight,\n    )\n'),
        ("} else if (!dark && exact && dominant.readsWithBlackText()) {\n    toExactLightPalette()\n} else if (dark) {\n",
         "} else if (!dark && exact && dominant.readsWithBlackText()) {\n    toExactLightPalette()\n"
         "} else if (!dark && exact) {\n    toExactDarkOnLightPalette()\n} else if (dark) {\n"),
        ("/**\n * Light theme, album and single: Apple's colour for the release at the top of\n",
         DARK_FN + "/**\n * Light theme, album and single: Apple's colour for the release at the top of\n"),
    ]),
    (TH, "803fce7ad24050d57d292b657d51febb2ca0d8b6", [
        ("import android.app.Activity\n",
         "import android.app.Activity\nimport androidx.compose.animation.core.animateFloatAsState\nimport androidx.compose.animation.core.tween\n"),
        ("import androidx.compose.foundation.isSystemInDarkTheme\n",
         "import androidx.compose.foundation.isSystemInDarkTheme\nimport androidx.compose.material3.ColorScheme\nimport androidx.compose.material3.LocalContentColor\n"),
        ("import androidx.compose.runtime.Composable\n",
         "import androidx.compose.runtime.Composable\nimport androidx.compose.runtime.CompositionLocalProvider\nimport androidx.compose.runtime.getValue\n"),
        ("import androidx.compose.ui.graphics.Color\n",
         "import androidx.compose.ui.graphics.Color\nimport androidx.compose.ui.graphics.lerp\nimport androidx.compose.ui.graphics.luminance\n"),
        ("/**\n * Draws the status and navigation bar glyphs dark or light.\n",
         PAGE_DARK + "/**\n * Draws the status and navigation bar glyphs dark or light.\n"),
    ]),
    (MA, "5e5ebffe5357bb6e520731f52c27abd0a3467d25", [
        ("import com.music.amusic.ui.theme.SystemBarIcons\n",
         "import com.music.amusic.ui.theme.PageDarkTheme\nimport com.music.amusic.ui.theme.SystemBarIcons\n"),
        ("    SystemBarIcons(\n        dark = !darkTheme && !showNowPlaying && !showReplay && replayStory == null && !onboardingVisible,\n    )\n",
         "    // The bar glyphs are set further down, once the page on screen is known.\n"),
        ('        accentWhenNeutral = detail?.type == BrowseType.ALBUM && !detailIsLibraryArtist &&\n            !detail?.browseId.orEmpty().startsWith("local:"),\n    )\n',
         '        accentWhenNeutral = detail?.type == BrowseType.ALBUM && !detailIsLibraryArtist &&\n            !detail?.browseId.orEmpty().startsWith("local:"),\n    )\n\n'
         "    // Album and single pages whose Apple colour is dark keep it on the Light\n"
         "    // theme with white text and icons: the look follows the page colour, not\n"
         "    // the theme. The bar glyphs follow it too.\n"
         "    val detailDarkPageOnLight = !darkTheme && detail?.type == BrowseType.ALBUM &&\n"
         "        !detailIsLibraryArtist && !detail?.browseId.orEmpty().startsWith(\"local:\") &&\n"
         "        detailPalette.darkPageOnLight\n"
         "    val lightThemeDarkPage = detailDarkPageOnLight && !showDiscord && !showHistory &&\n"
         "        !showSettings && !showAccountScrobbling && !showSources && !showListenTogether &&\n"
         "        !showWearOs && !showEqualizer && !showReplay\n"
         "    SystemBarIcons(\n"
         "        dark = !darkTheme && !showNowPlaying && !showReplay && replayStory == null &&\n"
         "            !onboardingVisible && !lightThemeDarkPage,\n"
         "    )\n"),
        ("                        DetailScreen(\n                            page = shownPage,\n",
         "                        val pageDarkOnLight = !darkTheme && page.type == BrowseType.ALBUM &&\n"
         "                            !isLibraryArtistPage && !page.browseId.orEmpty().startsWith(\"local:\") &&\n"
         "                            detail?.browseId == page.browseId && detailPalette.darkPageOnLight\n"
         "                        PageDarkTheme(enabled = pageDarkOnLight) {\n"
         "                        DetailScreen(\n                            page = shownPage,\n"),
        ("                            pullState = if (isLibraryArtistPage) detailPull else null,\n                        )\n                    } else when (key.removePrefix(TAB_KEY).toIntOrNull() ?: selectedTab) {\n",
         "                            pullState = if (isLibraryArtistPage) detailPull else null,\n                        )\n                        }\n                    } else when (key.removePrefix(TAB_KEY).toIntOrNull() ?: selectedTab) {\n"),
        ("                FrostedTopBar(\n                    title = when {\n",
         "                PageDarkTheme(enabled = lightThemeDarkPage) {\n                FrostedTopBar(\n                    title = when {\n"),
        ("                    },\n                )\n\n                // Drawn before the bars so their own glass reads on top of it.\n",
         "                    },\n                )\n                }\n\n                // Drawn before the bars so their own glass reads on top of it.\n"),
    ]),
]


def apply(root):
    for path, sha, edits in EDITS:
        raw = open(root + "/" + path, "rb").read()
        assert gh(raw) == sha, "blob sha mismatch for " + path
        s = raw.decode()
        for old, new in edits:
            assert s.count(old) == 1, "anchor count %d for %r" % (s.count(old), old[:70])
            s = s.replace(old, new)
        open(root + "/" + path, "w").write(s)


if __name__ == "__main__":
    apply(".")
    run = lambda *a: subprocess.run(a, check=True)
    run("git", "config", "user.name", "pally-bot")
    run("git", "config", "user.email", "pally-bot@users.noreply.github.com")
    run("git", "add", "-A")
    run("git", "commit", "-m", "Album e single: texto, icones e botoes seguem a cor da pagina [skip ci]")
    run("git", "pull", "--rebase", "origin", "polish-refresh-transitions")
    run("git", "push", "origin", "HEAD:polish-refresh-transitions")
