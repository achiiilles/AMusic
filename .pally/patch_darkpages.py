import sys
P_THEME = 'app/src/main/java/com/music/amusic/ui/theme/Theme.kt'
P_PAL = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/theme/ArtworkPalette.kt'
P_MAIN = 'app/src/main/java/com/music/amusic/MainActivity.kt'
EDITS = [
(P_THEME, r'''import androidx.compose.foundation.isSystemInDarkTheme
''', r'''import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.isSystemInDarkTheme
'''),
(P_THEME, r'''import androidx.compose.material3.MaterialTheme
''', r'''import androidx.compose.material3.ColorScheme
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
'''),
(P_THEME, r'''import androidx.compose.runtime.Composable
''', r'''import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
'''),
(P_THEME, r'''import androidx.compose.ui.graphics.Color
''', r'''import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
'''),
(P_THEME, r'''/**
 * Draws the status and navigation bar glyphs dark or light.
''', r'''/** How long a page takes to settle into (or out of) the dark colours. */
private const val PAGE_DARK_FADE_MS = 220

/**
 * Paints [content] in the dark colours while the app itself is on the Light
 * theme.
 *
 * The coloured pages (album, single, playlist and artist) take their look from
 * the sleeve, and it reads far better on the dark tint than on the pale one. So
 * on Light those pages, and the top bar over them, are composed under the Dark
 * colour scheme: every button, veil, text colour and hairline that asks the
 * theme what it is gets the dark answer, with no change to the components
 * themselves. The bottom bar, the mini player and every other screen are
 * outside this and stay Light.
 *
 * [enabled] crossfades over [PAGE_DARK_FADE_MS] on a plain ease. With nothing
 * enabled the current scheme is passed through untouched, so on the Dark theme
 * (where this is never enabled) it changes nothing.
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
        CompositionLocalProvider(LocalContentColor provides contentColor) {
            content()
        }
    }
}

/** This scheme, [amount] (0..1) of the way to [DarkColors]. */
private fun ColorScheme.towardDark(amount: Float): ColorScheme {
    val dark = DarkColors
    fun mix(from: Color, to: Color) = lerp(from, to, amount)
    return copy(
        primary = mix(primary, dark.primary),
        onPrimary = mix(onPrimary, dark.onPrimary),
        primaryContainer = mix(primaryContainer, dark.primaryContainer),
        onPrimaryContainer = mix(onPrimaryContainer, dark.onPrimaryContainer),
        secondary = mix(secondary, dark.secondary),
        onSecondary = mix(onSecondary, dark.onSecondary),
        secondaryContainer = mix(secondaryContainer, dark.secondaryContainer),
        onSecondaryContainer = mix(onSecondaryContainer, dark.onSecondaryContainer),
        tertiary = mix(tertiary, dark.tertiary),
        onTertiary = mix(onTertiary, dark.onTertiary),
        background = mix(background, dark.background),
        onBackground = mix(onBackground, dark.onBackground),
        surface = mix(surface, dark.surface),
        onSurface = mix(onSurface, dark.onSurface),
        surfaceVariant = mix(surfaceVariant, dark.surfaceVariant),
        onSurfaceVariant = mix(onSurfaceVariant, dark.onSurfaceVariant),
        surfaceTint = mix(surfaceTint, dark.surfaceTint),
        inverseSurface = mix(inverseSurface, dark.inverseSurface),
        inverseOnSurface = mix(inverseOnSurface, dark.inverseOnSurface),
        outline = mix(outline, dark.outline),
        outlineVariant = mix(outlineVariant, dark.outlineVariant),
        scrim = mix(scrim, dark.scrim),
        surfaceContainer = mix(surfaceContainer, dark.surfaceContainer),
        surfaceContainerHigh = mix(surfaceContainerHigh, dark.surfaceContainerHigh),
        surfaceContainerHighest = mix(surfaceContainerHighest, dark.surfaceContainerHighest),
        surfaceContainerLow = mix(surfaceContainerLow, dark.surfaceContainerLow),
        surfaceContainerLowest = mix(surfaceContainerLowest, dark.surfaceContainerLowest),
    )
}

/**
 * Draws the status and navigation bar glyphs dark or light.
'''),
(P_PAL, r'''    val target = shaped?.toPalette(dark) ?: ArtworkPalette(
        background = scheme.background,
        wash = scheme.background,
        elevated = scheme.surfaceVariant,
        accent = scheme.primary,
        onBackground = scheme.onBackground,
        onBackgroundVariant = scheme.onSurfaceVariant,
        divider = scheme.outline,
    )
''', r'''    // A dark page asked for from outside the dark scheme (the bars around a
    // coloured page on the Light theme) has no sleeve colours yet on a first
    // visit; its stand-in is the dark theme's own, not the white page.
    val darkOnLight = dark && scheme.background.luminance() >= 0.5f
    val target = shaped?.toPalette(dark) ?: if (darkOnLight) {
        ArtworkPalette(
            background = Color.Black,
            wash = Color.Black,
            elevated = Color(0xFF1C1C1E),
            accent = Color.White,
            onBackground = Color.White,
            onBackgroundVariant = Color(0xFF8E8E93),
            divider = Color(0xFF2C2C2E),
        )
    } else {
        ArtworkPalette(
            background = scheme.background,
            wash = scheme.background,
            elevated = scheme.surfaceVariant,
            accent = scheme.primary,
            onBackground = scheme.onBackground,
            onBackgroundVariant = scheme.onSurfaceVariant,
            divider = scheme.outline,
        )
    }
'''),
(P_MAIN, r'''import com.music.amusic.ui.theme.SystemBarIcons
''', r'''import com.music.amusic.ui.theme.PageDarkTheme
import com.music.amusic.ui.theme.SystemBarIcons
'''),
(P_MAIN, r'''private const val TOP_FADE_RAMP = 0.3f
''', r'''private const val TOP_FADE_RAMP = 0.3f

/** How long the fades at the screen's ends take to settle onto a coloured page's tint. */
private const val PAGE_SCRIM_FADE_MS = 220
'''),
(P_MAIN, r'''    SystemBarIcons(
        dark = !darkTheme && !showNowPlaying && !showReplay && replayStory == null && !onboardingVisible,
    )
''', r'''    // The glyphs themselves are set further down, once the page on screen is known.
'''),
(P_MAIN, r'''    val detailPalette = rememberArtworkPalette(
        imageUrl = detailApple?.heroUrl ?: detail?.thumbnailUrl,
        keyColors = detailApple?.keyColors(),
''', r'''    // On the Light theme the coloured pages (album, single, playlist, artist and
    // the library's own artist page) are drawn in the dark colours, which suit
    // the sleeve's tint far better. Device folders stay Light. Never true on
    // the Dark theme, which is exactly as it was.
    val detailDarkPage = !darkTheme && detail != null && !detail.browseId.isDeviceFolder() &&
        (detail.type == BrowseType.ALBUM ||
            detail.type == BrowseType.PLAYLIST ||
            detail.type == BrowseType.ARTIST ||
            detailIsLibraryArtist ||
            LocalGroups.isArtist(detail.browseId))
    val lightThemeDarkPage = detailDarkPage &&
        !showDiscord && !showHistory && !showSettings &&
        !showAccountScrobbling && !showSources && !showListenTogether && !showWearOs && !showEqualizer && !showReplay
    // One call, so its glyph colours cannot be left behind by a second one that
    // composition skips: dark glyphs on Light, except where the page beneath
    // them is dark.
    SystemBarIcons(
        dark = !darkTheme && !showNowPlaying && !showReplay && replayStory == null && !onboardingVisible &&
            !lightThemeDarkPage,
    )
    val detailPalette = rememberArtworkPalette(
        imageUrl = detailApple?.heroUrl ?: detail?.thumbnailUrl,
        keyColors = detailApple?.keyColors(),
        dark = darkTheme || detailDarkPage,
'''),
(P_MAIN, r'''                        DetailScreen(
                            page = shownPage,
''', r'''                        // Coloured pages are drawn in the dark colours on the Light theme.
                        val pageDark = !darkTheme && !page.browseId.isDeviceFolder() &&
                            (page.type == BrowseType.ALBUM ||
                                page.type == BrowseType.PLAYLIST ||
                                page.type == BrowseType.ARTIST ||
                                isLibraryArtistPage ||
                                LocalGroups.isArtist(page.browseId))
                        PageDarkTheme(enabled = pageDark) {
                        DetailScreen(
                            page = shownPage,
'''),
(P_MAIN, r'''                            contentPadding = listPadding,
                        )
                    } else when (key.removePrefix(TAB_KEY).toIntOrNull() ?: selectedTab) {
''', r'''                            contentPadding = listPadding,
                        )
                        }
                    } else when (key.removePrefix(TAB_KEY).toIntOrNull() ?: selectedTab) {
'''),
(P_MAIN, r'''                val chromePageColor = if (isDetailVisible) {
                    detailPalette.background
''', r'''                val chromePageColor = if (isDetailVisible || lightThemeDarkPage) {
                    detailPalette.background
'''),
(P_MAIN, r'''                // This is the bottom floor itself turned upside down, not a
''', r'''                // What the fades at the top and foot of the screen paint. On the Light
                // theme a coloured page is dark, so it settles in over a short fade
                // rather than flashing white behind the bars as the page comes or goes.
                val scrimPageColor by androidx.compose.animation.animateColorAsState(
                    targetValue = chromePageColor,
                    animationSpec = if (darkTheme) {
                        androidx.compose.animation.core.snap<Color>()
                    } else {
                        androidx.compose.animation.core.tween<Color>(PAGE_SCRIM_FADE_MS)
                    },
                    label = "pageScrimColor",
                )
                // This is the bottom floor itself turned upside down, not a
'''),
(P_MAIN, r'''                BottomFadeScrim(
                    pageColor = chromePageColor,
                    modifier = Modifier
                        .align(Alignment.TopCenter)
''', r'''                BottomFadeScrim(
                    pageColor = scrimPageColor,
                    modifier = Modifier
                        .align(Alignment.TopCenter)
'''),
(P_MAIN, r'''                FrostedTopBar(
                    title = when {
                        showSpotify && detail == null -> stringResource(R.string.spotify)
''', r'''                // Over a coloured page on the Light theme the bar's circles, pill and
                // veil are the dark ones; everywhere else this passes the theme through.
                PageDarkTheme(enabled = lightThemeDarkPage) {
                FrostedTopBar(
                    title = when {
                        showSpotify && detail == null -> stringResource(R.string.spotify)
'''),
(P_MAIN, r'''                )

                // Drawn before the bars so their own glass reads on top of it.
                BottomFadeScrim(
''', r'''                )
                }

                // Drawn before the bars so their own glass reads on top of it.
                BottomFadeScrim(
'''),
(P_MAIN, r'''                    pageColor = chromePageColor,
                    modifier = Modifier.align(Alignment.BottomCenter),
''', r'''                    pageColor = scrimPageColor,
                    modifier = Modifier.align(Alignment.BottomCenter),
'''),
]
files = {}
for path, old, new in EDITS:
    if path not in files:
        files[path] = open(path, encoding='utf-8').read()
    n = files[path].count(old)
    if n != 1:
        sys.exit('edit not unique/found (%d) in %s: %r' % (n, path, old[:80]))
    files[path] = files[path].replace(old, new, 1)
for path, text in files.items():
    open(path, 'w', encoding='utf-8').write(text)
print('patched', ', '.join(files))
