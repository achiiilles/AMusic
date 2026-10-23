package com.music.amusic.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.music.amusic.ui.theme.ArtworkPalette

/**
 * The bottom sheet behind the three dots on an album, single or playlist page.
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
