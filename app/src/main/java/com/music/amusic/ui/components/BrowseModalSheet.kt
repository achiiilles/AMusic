package com.music.amusic.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.music.amusic.data.settings.AppSettings
import com.music.amusic.ui.theme.ArtworkPalette

/**
 * The bottom sheet behind the three dots on an album, single, playlist or
 * artist page.
 *
 * With liquid glass on (Android 12 or newer, and "reduce dynamic blur" off) the
 * sheet is the same glass the navigation bar and the mini player wear, so it
 * reads as one material with them; see [GlassBrowseSheet]. In every other case
 * it is what it has always been:
 *
 * [pagePalette] is the palette the page itself already resolved, so the sheet
 * opens in the page's colour from its first frame instead of black, and text,
 * icons and dividers keep the contrast that palette was corrected for. Without
 * it the sheet is the app background, as before. The drag handle sits close to
 * the top edge rather than in Material's 22dp of padding above and below.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BrowseModalSheet(
    pagePalette: ArtworkPalette?,
    onDismissRequest: () -> Unit,
    content: @Composable () -> Unit,
) {
    val reduceDynamicBlur by AppSettings.reduceDynamicBlur.collectAsStateWithLifecycle()
    // The same test the navigation bar and the top buttons use, plus "reduce
    // dynamic blur", which asks for solid surfaces rather than glass.
    val useGlass = LocalLiquidGlassEnabled.current && isGlassSupported() && !reduceDynamicBlur
    if (useGlass) {
        GlassBrowseSheet(onDismissRequest = onDismissRequest, content = content)
        return
    }
    if (pagePalette == null) {
        ModalBottomSheet(
            onDismissRequest = onDismissRequest,
            containerColor = MaterialTheme.colorScheme.background,
        ) {
            content()
        }
        return
    }
    val p = pagePalette
    val pageScheme = MaterialTheme.colorScheme.copy(
        background = p.background,
        surface = p.background,
        onBackground = p.onBackground,
        onSurface = p.onBackground,
        onSurfaceVariant = p.onBackgroundVariant,
        outline = p.divider,
        primary = p.accent,
    )
    ModalBottomSheet(
        onDismissRequest = onDismissRequest,
        containerColor = p.background,
        contentColor = p.onBackground,
        dragHandle = {
            Box(
                Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp, bottom = 4.dp),
                contentAlignment = Alignment.Center,
            ) {
                Box(
                    Modifier
                        .size(width = 34.dp, height = 4.dp)
                        .clip(CircleShape)
                        .background(p.onBackground.copy(alpha = 0.35f)),
                )
            }
        },
    ) {
        MaterialTheme(
            colorScheme = pageScheme,
            shapes = MaterialTheme.shapes,
            typography = MaterialTheme.typography,
        ) {
            content()
        }
    }
}

/** Material's own expanded-sheet corners: 28dp on top, square at the bottom edge. */
private val GlassSheetShape = RoundedCornerShape(
    topStart = 28.dp,
    topEnd = 28.dp,
    bottomStart = 0.dp,
    bottomEnd = 0.dp,
)

/**
 * The sheet in liquid glass: the same [liquidGlass] surface the navigation bar
 * and the mini player use, over the app's recorded backdrop.
 *
 * The glass is drawn by a column inside the sheet, not by the sheet's own
 * modifier, because Material offsets the sheet itself while it slides. A surface
 * drawn inside that offset travels with the sheet and fades in with it, with no
 * extra animation and no frame where it is missing. The sheet's own container is
 * transparent so the glass is the only fill, and the handle is drawn here for the
 * same reason the page-coloured sheet draws its own: the container has nothing
 * left to hang Material's on.
 *
 * Text and icons take the theme's colours rather than the page's, since glass
 * shows whatever is behind it and its tint follows the theme, like the bar.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun GlassBrowseSheet(
    onDismissRequest: () -> Unit,
    content: @Composable () -> Unit,
) {
    ModalBottomSheet(
        onDismissRequest = onDismissRequest,
        containerColor = Color.Transparent,
        contentColor = MaterialTheme.colorScheme.onSurface,
        shape = GlassSheetShape,
        tonalElevation = 0.dp,
        dragHandle = null,
    ) {
        Column(
            Modifier
                .fillMaxWidth()
                .liquidGlass(GlassSheetShape),
        ) {
            Box(
                Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp, bottom = 4.dp),
                contentAlignment = Alignment.Center,
            ) {
                Box(
                    Modifier
                        .size(width = 34.dp, height = 4.dp)
                        .clip(CircleShape)
                        .background(glassContentColor().copy(alpha = 0.35f)),
                )
            }
            content()
        }
    }
}
