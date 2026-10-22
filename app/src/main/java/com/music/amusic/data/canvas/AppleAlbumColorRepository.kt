package com.music.amusic.data.canvas

import androidx.compose.ui.graphics.Color
import com.music.amusic.data.DebugLog as Log
import com.music.amusic.data.YtMusicRepository
import com.music.amusic.ui.theme.ArtworkKeyColors
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.withContext

/**
 * Apple Music's own colours for an album or single: the background colour the
 * release is shown on and the text colour that goes with it (both ARGB).
 * They come from the catalog API: the preview frame of the release's motion
 * artwork when it has one (that is the colour Apple's own album page uses), else
 * `attributes.artwork`. Nothing has to be decoded from the sleeve to find them.
 */
data class AppleAlbumColors(
    val background: Int,
    val accent: Int,
)

/**
 * What a lookup settled on. [colors] is null when Apple answered but has no
 * confident match for the release; a lookup that could not be answered at all
 * (no token, no network) is not a result and is returned as null instead.
 */
class AppleAlbumColorsResult(
    val colors: AppleAlbumColors?,
    val genre: String? = null,
    val releaseYear: String? = null,
    /** Apple's `releaseDate`, as sent (yyyy-MM-dd, or just the year on some releases). */
    val releaseDate: String? = null,
    /** Apple's `copyright` line for the release. */
    val copyright: String? = null,
    /** Apple's `recordLabel` for the release. */
    val recordLabel: String? = null,
)

/** Apple's colours for this release, in the form the palette takes. */
fun AppleAlbumColors.keyColors() = ArtworkKeyColors(Color(background), Color(accent), exact = true)

/**
 * Finds [AppleAlbumColors] for an album or single page from its title and
 * artist, through the same catalog search the animated sleeves use.
 *
 * The answer is kept by the page's browse id, so the page and the bars around
 * it read the same thing. Only a settled answer (including "Apple has none") is
 * remembered; a network hiccup is tried again the next time the page opens.
 * Every miss leaves the page on the colours taken from the sleeve.
 */
object AppleAlbumColorRepository {

    private const val TAG = "AppleAlbumColors"
    private const val CACHE_SIZE = 128

    private class Entry(val result: AppleAlbumColorsResult)

    private val cache = object : LinkedHashMap<String, Entry>(CACHE_SIZE, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, Entry>) =
            size > CACHE_SIZE
    }

    private val _updates = MutableStateFlow(0)

    /** Ticks whenever a lookup settles, so the bars drawn outside the page re-read [cached]. */
    val updates: StateFlow<Int> = _updates

    /** What is known for [browseId] without a request; null for never looked up and for no colours. */
    fun cached(browseId: String): AppleAlbumColors? = cachedResult(browseId)?.colors

    /** The already settled catalog match, including a match without page colours. */
    fun cachedResult(browseId: String): AppleAlbumColorsResult? =
        synchronized(cache) { cache[browseId] }?.result

    /**
     * Genre and release year travel with the existing colour lookup; no second search.
     *
     * The match is made through the artist's own releases and scored on the cleaned
     * title, the track count, the year and the song names. A caller that does not
     * pass the page's songs gets them read here from the page's own browse id, so
     * the count and the song names are still part of the score.
     */
    suspend fun resultFor(
        browseId: String,
        album: String,
        artist: String,
        trackCount: Int = 0,
        year: String? = null,
        trackTitles: List<String> = emptyList(),
    ): AppleAlbumColorsResult? {
        if (browseId.isBlank() || album.isBlank() || artist.isBlank()) return null
        synchronized(cache) { cache[browseId] }?.let { return it.result }

        var count = trackCount
        var titles = trackTitles
        if (titles.isEmpty()) {
            val songs = YtMusicRepository.browseSongs(browseId).getOrNull()?.songs.orEmpty()
            if (songs.isNotEmpty()) {
                titles = songs.map { it.title }
                if (count <= 0) count = songs.size
            }
        }

        val result = withContext(Dispatchers.IO) {
            runCatching { AppleMusicCanvas.albumColors(album, artist, count, year, titles) }
                .onFailure { Log.d(TAG, "lookup failed for $album: $it") }
                .getOrNull()
        } ?: return null
        synchronized(cache) { cache[browseId] = Entry(result) }
        _updates.value++
        return result
    }

    /** Existing callers that only need the background still get the same nullable colours. */
    suspend fun colorsFor(browseId: String, album: String, artist: String): AppleAlbumColors? =
        resultFor(browseId, album, artist)?.colors
}
