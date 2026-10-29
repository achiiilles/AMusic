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
 *
 * A settled answer is also saved on disk ([AppleLookupStore]), so a page opened
 * before, even in an earlier session, gets its colours and details at once and
 * without any request.
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

        // Answered before, maybe in an earlier session: no request at all.
        val saved = withContext(Dispatchers.IO) { AppleLookupStore.readAlbum(browseId) }
        if (saved != null) {
            synchronized(cache) { cache[browseId] = Entry(saved) }
            _updates.value++
            return saved
        }

        // The artist and the artist's releases are looked up while the page's own songs load.
        AppleReleaseMatcher.prefetch(artist)

        var count = trackCount
        var titles = trackTitles
        if (titles.isEmpty()) {
            val songs = YtMusicRepository.browseSongs(browseId).getOrNull()?.songs.orEmpty()
            if (songs.isNotEmpty()) {
                titles = songs.map { it.title }
                if (count <= 0) count = songs.size
            }
        }

        val wantCount = count
        val wantTitles = titles
        val result = withContext(Dispatchers.IO) {
            runCatching {
                // The artist's own releases decide which Apple release this page is. When that
                // cannot be settled (artist not found, no network) the old title search still runs.
                val choice = AppleReleaseMatcher.choose(album, artist, wantCount, year, wantTitles)
                val chosen = choice?.collectionName
                when {
                    choice == null -> AppleMusicCanvas.albumColors(album, artist)
                    chosen == null -> AppleAlbumColorsResult(null)
                    else -> AppleMusicCanvas.albumColors(chosen, choice.artistName)
                }
            }
                .onFailure { Log.d(TAG, "lookup failed for $album: $it") }
                .getOrNull()
        } ?: return null

        // Apple has no details for this release (a single it does not carry, for example):
        // the genre, date and label come from Deezer instead, only when its entry has the
        // same artist, title, track count and songs. A Deezer that could not be asked leaves
        // the answer unsaved on disk so the next visit asks again.
        var settled = true
        val finalResult = if (result.genre == null && result.recordLabel == null && result.releaseDate == null) {
            val extra = withContext(Dispatchers.IO) {
                runCatching { DeezerAlbumLookup.lookup(album, artist, wantCount, wantTitles) }
                    .onFailure { Log.d(TAG, "deezer lookup failed for $album: $it") }
                    .getOrNull()
            }
            if (extra == null) {
                settled = false
                result
            } else {
                AppleAlbumColorsResult(
                    colors = result.colors,
                    genre = extra.genre,
                    releaseYear = result.releaseYear,
                    releaseDate = extra.releaseDate,
                    copyright = result.copyright,
                    recordLabel = extra.label,
                )
            }
        } else {
            result
        }

        if (settled) withContext(Dispatchers.IO) { AppleLookupStore.writeAlbum(browseId, finalResult) }
        synchronized(cache) { cache[browseId] = Entry(finalResult) }
        _updates.value++
        return finalResult
    }

    /** Existing callers that only need the background still get the same nullable colours. */
    suspend fun colorsFor(browseId: String, album: String, artist: String): AppleAlbumColors? =
        resultFor(browseId, album, artist)?.colors
}
