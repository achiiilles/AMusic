package com.music.amusic.ui.components

import android.widget.Toast
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Person
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.music.amusic.R
import coil3.compose.AsyncImage
import coil3.compose.AsyncImagePainter
import com.music.amusic.data.YtMusicRepository
import com.music.amusic.data.model.artworkAt
import kotlinx.coroutines.launch

/** The row's photo is drawn at 44 dp; 160 px covers it on dense screens without fetching a big picture. */
private const val ARTIST_PHOTO_PX = 160

/**
 * One artist of a shared credit. [browseId] is the artist's own channel when the page
 * said which one it is, and null when only the name is known.
 */
data class CreditArtist(
    val name: String,
    val browseId: String?,
)

/**
 * The small list that opens when the credit of a page names more than one artist
 * ("Olivia Rodrigo e Chappell Roan"): one row per artist, and the chosen artist's own
 * page opens through [onPick] with the channel id and the name.
 *
 * An artist without a channel id is looked up by name, and a page only opens when the
 * name matches exactly, so a stranger's page never opens by mistake. While that look-up
 * runs the row shows a small spinner that fades in, and the other rows ignore taps, so
 * a second tap cannot open a second page. When nothing is found the sheet stays open
 * and a short notice says so.
 *
 * Each row shows the artist's own YouTube Music photo in a circle. A [CreditArtist] only
 * carries a name and a channel id, so every row asks for its photo by channel id, on its
 * own and all at once, after the sheet is already on screen; the user-icon circle stays
 * until the photo has loaded (or when there is none) and the photo fades in over it. An
 * artist without a channel id gets the same exact-name look-up a tap uses, and the id it
 * finds is kept so the tap does not search a second time.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ArtistChoiceSheet(
    artists: List<CreditArtist>,
    onPick: (String, String) -> Unit,
    onDismiss: () -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var resolving by remember { mutableStateOf<String?>(null) }
    // Channel ids found by name for artists the credit gave none for, by artist name.
    val foundIds = remember { mutableStateMapOf<String, String>() }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = MaterialTheme.colorScheme.background,
    ) {
        Column(Modifier.fillMaxWidth()) {
            Text(
                text = stringResource(R.string.artists),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onBackground,
                modifier = Modifier.padding(horizontal = 22.dp, vertical = 8.dp),
            )
            HorizontalDivider(
                modifier = Modifier.padding(bottom = 4.dp),
                thickness = 0.5.dp,
                color = MaterialTheme.colorScheme.outline,
            )
            artists.forEach { artist ->
                ArtistChoiceRow(
                    name = artist.name,
                    browseId = artist.browseId,
                    busy = resolving == artist.name,
                    enabled = resolving == null,
                    onIdFound = { found -> foundIds[artist.name] = found },
                    onClick = {
                        val id = artist.browseId ?: foundIds[artist.name]
                        if (id != null) {
                            onPick(id, artist.name)
                            onDismiss()
                        } else {
                            resolving = artist.name
                            scope.launch {
                                val found = YtMusicRepository.findArtistPageId(artist.name).getOrNull()
                                if (found != null) {
                                    onPick(found, artist.name)
                                    onDismiss()
                                } else {
                                    resolving = null
                                    Toast.makeText(
                                        context,
                                        context.getString(R.string.couldnt_find, artist.name),
                                        Toast.LENGTH_SHORT,
                                    ).show()
                                }
                            }
                        }
                    },
                )
            }
            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun ArtistChoiceRow(
    name: String,
    browseId: String?,
    busy: Boolean,
    enabled: Boolean,
    onIdFound: (String) -> Unit,
    onClick: () -> Unit,
) {
    // What is already known paints on the first frame; the rest is asked for once the row
    // is composed, so opening the sheet never waits on a photo.
    var photo by remember(browseId, name) {
        mutableStateOf(browseId?.let { ArtistPhotoLookup.cached(it) }?.takeIf { it.isNotEmpty() })
    }
    LaunchedEffect(browseId, name) {
        if (photo != null) return@LaunchedEffect
        val id = browseId ?: YtMusicRepository.findArtistPageId(name).getOrNull()?.also(onIdFound)
        if (id != null) {
            photo = ArtistPhotoLookup.fetch(id)
        }
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = 22.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        var loaded by remember(photo) { mutableStateOf(false) }
        val fade by animateFloatAsState(
            targetValue = if (loaded) 1f else 0f,
            animationSpec = tween(durationMillis = 220),
            label = "artistChoicePhotoFade",
        )
        Box(
            modifier = Modifier
                .size(44.dp)
                .clip(CircleShape)
                .background(MaterialTheme.colorScheme.surfaceVariant),
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                imageVector = Icons.Rounded.Person,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier
                    .size(24.dp)
                    .alpha(1f - fade),
            )
            val url = photo
            if (url != null) {
                AsyncImage(
                    model = url.artworkAt(ARTIST_PHOTO_PX),
                    contentDescription = null,
                    contentScale = ContentScale.Crop,
                    onState = { if (it is AsyncImagePainter.State.Success) loaded = true },
                    modifier = Modifier
                        .matchParentSize()
                        .alpha(fade),
                )
            }
        }
        Spacer(Modifier.width(14.dp))
        Text(
            text = name,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onBackground,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
            modifier = Modifier.weight(1f),
        )
        AnimatedVisibility(visible = busy, enter = fadeIn(), exit = fadeOut()) {
            CircularProgressIndicator(
                strokeWidth = 2.dp,
                modifier = Modifier
                    .padding(start = 12.dp)
                    .size(20.dp),
            )
        }
    }
}
