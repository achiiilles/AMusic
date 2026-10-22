package com.music.amusic.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Close
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil3.compose.AsyncImage
import com.music.amusic.data.ApplePreRelease
import com.music.amusic.data.PreReleaseAlbum
import com.music.amusic.data.PreReleaseTrack
import com.music.amusic.data.model.artworkAt

/** Big enough that Apple's 600x600 artwork is never upscaled past its source. */
private const val PRE_RELEASE_COVER_PX = 600

/**
 * The page a pre-release card opens.
 *
 * YouTube Music has no page for a release that is not out yet, so this one is
 * built entirely from Apple's public catalogue: the cover, the name, the
 * credit, the day it lands and the track list the catalogue already returns.
 *
 * Each track is drawn by its own state. A track the catalogue already names
 * is out, so it opens the way any other track in the app does; a track Apple
 * still lists as a placeholder ("Track 2") is not out, so it stays grey and
 * does nothing when tapped. When the catalogue returns nothing — no track list
 * yet — the page shows the cover and the date and says so, rather than
 * inventing a set of names.
 *
 * Drawn in a full-screen dialog so closing it hands the artist page back
 * exactly as it was: same scroll position, same shelves, no reload.
 */
@Composable
fun PreReleasePage(
    title: String,
    artistName: String?,
    badge: String,
    coverUrl: String?,
    collectionId: String?,
    onDismiss: () -> Unit,
    onOpenTrack: ((name: String, artist: String?) -> Unit)? = null,
) {
    var album by remember(collectionId) { mutableStateOf<PreReleaseAlbum?>(null) }
    var loaded by remember(collectionId) { mutableStateOf(false) }

    LaunchedEffect(collectionId) {
        if (collectionId == null) {
            loaded = true
            return@LaunchedEffect
        }
        album = ApplePreRelease.album(collectionId)
        loaded = true
    }

    val colors = MaterialTheme.colorScheme
    Dialog(onDismissRequest = onDismiss, properties = DialogProperties(usePlatformDefaultWidth = false)) {
        Surface(modifier = Modifier.fillMaxSize(), color = colors.background) {
            Box(modifier = Modifier.fillMaxSize()) {
                val shownTitle = album?.name ?: title
                val shownArtist = album?.artistName ?: artistName
                val shownCover = album?.artworkUrl ?: coverUrl
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(top = 64.dp, bottom = 32.dp),
                    verticalArrangement = Arrangement.spacedBy(2.dp),
                ) {
                    item {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            AsyncImage(
                                model = shownCover.artworkAt(PRE_RELEASE_COVER_PX),
                                contentDescription = null,
                                contentScale = ContentScale.Crop,
                                modifier = Modifier
                                    .width(220.dp)
                                    .aspectRatio(1f)
                                    .clip(RoundedCornerShape(14.dp))
                                    .background(colors.surfaceVariant),
                            )
                            Spacer(Modifier.height(18.dp))
                            Text(
                                text = shownTitle,
                                style = MaterialTheme.typography.titleLarge,
                                fontWeight = FontWeight.Bold,
                                color = colors.onBackground,
                                textAlign = TextAlign.Center,
                                maxLines = 3,
                                overflow = TextOverflow.Ellipsis,
                                modifier = Modifier.padding(horizontal = 24.dp),
                            )
                            shownArtist?.let { artist ->
                                Spacer(Modifier.height(4.dp))
                                Text(
                                    text = artist,
                                    style = MaterialTheme.typography.titleMedium,
                                    color = colors.onBackgroundVariant(),
                                    textAlign = TextAlign.Center,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                    modifier = Modifier.padding(horizontal = 24.dp),
                                )
                            }
                            Spacer(Modifier.height(6.dp))
                            Text(
                                text = badge,
                                style = MaterialTheme.typography.bodyMedium,
                                color = colors.onBackgroundVariant(),
                                textAlign = TextAlign.Center,
                                modifier = Modifier.padding(horizontal = 24.dp),
                            )
                            Spacer(Modifier.height(20.dp))
                        }
                    }

                    val tracks = album?.tracks.orEmpty()
                    if (!loaded) {
                        item {
                            Box(modifier = Modifier.fillMaxWidth().padding(vertical = 28.dp), contentAlignment = Alignment.Center) {
                                CircularProgressIndicator(modifier = Modifier.size(22.dp), strokeWidth = 2.dp)
                            }
                        }
                    } else if (tracks.isEmpty()) {
                        item {
                            Text(
                                text = "As faixas ainda não foram divulgadas.",
                                style = MaterialTheme.typography.bodyMedium,
                                color = colors.onBackgroundVariant(),
                                textAlign = TextAlign.Center,
                                modifier = Modifier.fillMaxWidth().padding(horizontal = 32.dp, vertical = 12.dp),
                            )
                        }
                    } else {
                        itemsIndexed(tracks, key = { _, track -> track.number }) { index, track ->
                            PreReleaseTrackRow(
                                track = track,
                                onOpen = if (track.released && onOpenTrack != null) {
                                    { onOpenTrack(track.name, shownArtist) }
                                } else {
                                    null
                                },
                            )
                            if (index == tracks.lastIndex) {
                                Spacer(Modifier.height(8.dp))
                            }
                        }
                    }
                }

                IconButton(
                    onClick = onDismiss,
                    modifier = Modifier.align(Alignment.TopStart).padding(8.dp),
                ) {
                    Icon(
                        imageVector = Icons.Rounded.Close,
                        contentDescription = "Fechar",
                        tint = colors.onBackground,
                    )
                }
            }
        }
    }
}

/** One numbered row: a released track is a link, an unreleased one is grey. */
@Composable
private fun PreReleaseTrackRow(track: PreReleaseTrack, onOpen: (() -> Unit)?) {
    val colors = MaterialTheme.colorScheme
    val textColor = if (track.released) colors.onBackground else colors.onBackgroundVariant().copy(alpha = 0.6f)
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onOpen != null) Modifier.clickable(onClick = onOpen) else Modifier)
            .padding(horizontal = 20.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = track.number.toString(),
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold,
            color = textColor,
            textAlign = TextAlign.End,
            modifier = Modifier.width(26.dp),
        )
        Spacer(Modifier.width(14.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = track.name,
                style = MaterialTheme.typography.bodyLarge,
                color = textColor,
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
            if (!track.released) {
                Text(
                    text = "Ainda não lançada",
                    style = MaterialTheme.typography.bodySmall,
                    color = colors.onBackgroundVariant().copy(alpha = 0.6f),
                    maxLines = 1,
                )
            }
        }
    }
    HorizontalDivider(
        modifier = Modifier.padding(start = 60.dp, end = 20.dp),
        color = colors.onBackgroundVariant().copy(alpha = 0.12f),
    )
}

/** The app's own secondary text colour, which Material's scheme has no slot for. */
@Composable
private fun Color.onBackgroundVariant(): Color = this
