package com.music.amusic.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

/**
 * The one drag handle every context-menu bottom sheet uses, with the same height and
 * spacing as the header of the song context menu.
 *
 * The default handle of `ModalBottomSheet` carries 22dp of padding above and below, which
 * leaves a wide gap between the top edge and the first line of the sheet. This one keeps
 * 8dp above and 4dp below, so a new sheet only has to pass it as its `dragHandle` to match
 * the others. The title that follows it should not add more than a few dp of its own on top.
 */
@Composable
fun CompactSheetDragHandle(
    color: Color = MaterialTheme.colorScheme.onBackground.copy(alpha = 0.35f),
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 8.dp, bottom = 4.dp),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            Modifier
                .size(width = 34.dp, height = 4.dp)
                .clip(CircleShape)
                .background(color),
        )
    }
}
