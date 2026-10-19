package com.music.amusic.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.layout.ContentScale
import coil3.compose.AsyncImage
import coil3.compose.AsyncImagePainter

/**
 * Where an artist's photo from Apple Music comes from. The app registers one
 * implementation at start-up; without it every artist keeps the YouTube photo.
 */
interface ArtistPhotoProvider {
    /**
     * What is already known for [artistName], without any request: null when
     * the name was never looked up, an empty string when it was and there is
     * no photo, otherwise the photo URL. Cheap enough to call while composing.
     */
    fun peek(artistName: String): String?

    /** Looks the photo up off the main thread. Null or empty when there is none. */
    suspend fun fetch(artistName: String): String?
}

object ArtistPhotos {
    @Volatile
    var provider: ArtistPhotoProvider? = null
}

/**
 * An image that is the artist's Apple Music photo when one is known, and the
 * [model] it was given (the YouTube thumbnail) until then and whenever Apple has
 * none.
 *
 * The YouTube picture is drawn at once; the Apple photo is requested only while
 * this item is composed, so a row that has scrolled away cancels its own wait,
 * and fades in over the first picture in 220 ms once it has loaded. Pass a null
 * [artistName] for anything that is not an artist and this is a plain image.
 */
@Composable
fun ArtistAwareImage(
    model: Any?,
    artistName: String?,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    contentScale: ContentScale = ContentScale.Fit,
) {
    val provider = ArtistPhotos.provider
    val name = artistName?.trim()?.takeIf { it.isNotEmpty() }
    if (provider == null || name == null) {
        AsyncImage(
            model = model,
            contentDescription = contentDescription,
            contentScale = contentScale,
            modifier = modifier,
        )
        return
    }

    var photo by remember(name) { mutableStateOf(provider.peek(name)?.takeIf { it.isNotEmpty() }) }
    LaunchedEffect(name) {
        if (provider.peek(name) == null) {
            photo = provider.fetch(name)?.takeIf { it.isNotEmpty() }
        }
    }

    Box(modifier) {
        AsyncImage(
            model = model,
            contentDescription = contentDescription,
            contentScale = contentScale,
            modifier = Modifier.fillMaxSize(),
        )
        val url = photo
        if (url != null) {
            var loaded by remember(url) { mutableStateOf(false) }
            val fade by animateFloatAsState(
                targetValue = if (loaded) 1f else 0f,
                animationSpec = tween(durationMillis = 220),
                label = "artistPhotoFade",
            )
            AsyncImage(
                model = url,
                contentDescription = null,
                contentScale = ContentScale.Crop,
                onState = { if (it is AsyncImagePainter.State.Success) loaded = true },
                modifier = Modifier.fillMaxSize().alpha(fade),
            )
        }
    }
}
