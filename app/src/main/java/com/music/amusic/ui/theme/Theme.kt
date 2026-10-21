package com.music.amusic.ui.theme

import android.app.Activity
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.Typography
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.music.amusic.R

// Apple Music's signature red. No longer the primary accent, but kept for the
// spots (Replay's rank badge) that want that specific red regardless of theme.
val AccentRed = Color(0xFFFA2D48)

private val DarkColors = darkColorScheme(
    primary = Color.White,
    onPrimary = Color.Black,
    background = Color.Black,
    onBackground = Color.White,
    surface = Color(0xFF0D0D0F),
    onSurface = Color.White,
    surfaceVariant = Color(0xFF1C1C1E),
    onSurfaceVariant = Color(0xFF8E8E93),
    outline = Color(0xFF2C2C2E),
)

private val LightColors = lightColorScheme(
    primary = Color.Black,
    onPrimary = Color.White,
    background = Color.White,
    onBackground = Color.Black,
    surface = Color(0xFFF7F7F9),
    onSurface = Color.Black,
    surfaceVariant = Color(0xFFF2F2F7),
    onSurfaceVariant = Color(0xFF6E6E73),
    outline = Color(0xFFE5E5EA),
)

/**
 * SF Pro Display, the face Apple Music itself is set in. Only the weights the
 * type scale actually asks for are bundled; Compose synthesises nothing, so a
 * missing weight would silently fall back to the nearest one shipped.
 */
val SFProDisplay = FontFamily(
    Font(R.font.sf_pro_display_regular, FontWeight.W400),
    Font(R.font.sf_pro_display_medium, FontWeight.W500),
    Font(R.font.sf_pro_display_semibold, FontWeight.W600),
    Font(R.font.sf_pro_display_bold, FontWeight.W700),
    Font(R.font.sf_pro_display_heavy, FontWeight.W800),
)

// Heavy, tight typography — the backbone of the Apple Music look.
private val AMusicTypography = Typography(
    displayLarge = TextStyle(fontWeight = FontWeight.W800, fontSize = 34.sp, letterSpacing = (-0.8).sp),
    headlineLarge = TextStyle(fontWeight = FontWeight.W800, fontSize = 30.sp, letterSpacing = (-0.7).sp),
    headlineMedium = TextStyle(fontWeight = FontWeight.W700, fontSize = 22.sp, letterSpacing = (-0.4).sp),
    titleLarge = TextStyle(fontWeight = FontWeight.W700, fontSize = 20.sp, letterSpacing = (-0.3).sp),
    titleMedium = TextStyle(fontWeight = FontWeight.W600, fontSize = 16.sp, letterSpacing = (-0.2).sp),
    bodyLarge = TextStyle(fontWeight = FontWeight.W400, fontSize = 16.sp),
    bodyMedium = TextStyle(fontWeight = FontWeight.W400, fontSize = 14.sp),
    labelMedium = TextStyle(fontWeight = FontWeight.W600, fontSize = 12.sp),
    labelSmall = TextStyle(fontWeight = FontWeight.W600, fontSize = 11.sp),
).withFamily(SFProDisplay)

/** Applies [family] to every style in the scale, so nothing is left on Roboto. */
private fun Typography.withFamily(family: FontFamily) = Typography(
    displayLarge = displayLarge.copy(fontFamily = family),
    displayMedium = displayMedium.copy(fontFamily = family),
    displaySmall = displaySmall.copy(fontFamily = family),
    headlineLarge = headlineLarge.copy(fontFamily = family),
    headlineMedium = headlineMedium.copy(fontFamily = family),
    headlineSmall = headlineSmall.copy(fontFamily = family),
    titleLarge = titleLarge.copy(fontFamily = family),
    titleMedium = titleMedium.copy(fontFamily = family),
    titleSmall = titleSmall.copy(fontFamily = family),
    bodyLarge = bodyLarge.copy(fontFamily = family),
    bodyMedium = bodyMedium.copy(fontFamily = family),
    bodySmall = bodySmall.copy(fontFamily = family),
    labelLarge = labelLarge.copy(fontFamily = family),
    labelMedium = labelMedium.copy(fontFamily = family),
    labelSmall = labelSmall.copy(fontFamily = family),
)

@Composable
fun AMusicTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = AMusicTypography,
        content = content,
    )
}

/** How long a page takes to settle into (or out of) the dark colours. */
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
 *
 * `enableEdgeToEdge()` decides this from the *system* dark-mode setting, which
 * is the wrong input the moment the in-app theme disagrees with it: Light theme
 * on a phone in dark mode left white icons on a white bar, invisible. The bars
 * have to follow the content the app is actually painting. The player supplies
 * its own stable light-icon value and paints contrast behind it; every other
 * surface follows the theme. Hence a parameter rather than reading it here.
 */
@Composable
fun SystemBarIcons(dark: Boolean) {
    val view = LocalView.current
    if (view.isInEditMode) return
    val window = findWindow(view) ?: return
    SideEffect {
        WindowCompat.getInsetsController(window, view).apply {
            isAppearanceLightStatusBars = dark
            isAppearanceLightNavigationBars = dark
        }
    }
}

