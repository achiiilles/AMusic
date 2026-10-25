package com.music.amusic.ui.components

import com.music.amusic.data.innertube.Innertube
import com.music.amusic.data.innertube.InnertubeParser
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.ConcurrentHashMap

/**
 * The YouTube Music photo of an artist, found by the artist's channel id.
 *
 * The rows of [ArtistChoiceSheet] only know a name and a channel id, so each row asks
 * here for its photo, read off the header of the artist's own page: one request, without
 * the song and release paging a full artist page does. It is asked for by channel id and
 * never by name, so a namesake's face cannot turn up. The answer is kept for the process,
 * so a sheet opened again for the same credit paints the photo on its first frame; the
 * picture itself comes through the app's shared image loader and its caches.
 */
object ArtistPhotoLookup {
    // An empty string means the page was read and has no photo. A failed request is not
    // stored, so the next time the sheet opens it asks again.
    private val photos = ConcurrentHashMap<String, String>()

    /** What [fetch] already found for [browseId], without a request. Empty when the page has no photo. */
    fun cached(browseId: String): String? = photos[browseId]

    /** The photo URL for [browseId], read off the main thread. Null when there is none or the request failed. */
    suspend fun fetch(browseId: String): String? {
        photos[browseId]?.let { return it.takeIf(String::isNotEmpty) }
        return withContext(Dispatchers.IO) {
            try {
                val url = InnertubeParser.parseArtistPage(Innertube.browse(browseId)).thumbnailUrl
                photos[browseId] = url.orEmpty()
                url?.takeIf(String::isNotEmpty)
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                null
            }
        }
    }
}
