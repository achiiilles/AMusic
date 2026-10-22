package com.music.amusic.data

import com.music.amusic.data.model.HomeShelf
import com.music.amusic.data.model.ShelfItem
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.Request
import java.net.URLEncoder
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.concurrent.ConcurrentHashMap

/**
 * Apple Music's pre-releases, read as a shelf for an artist page.
 *
 * YouTube Music has no notion of a release that is not out yet, so the artist
 * page it serves can only ever list what has already shipped. Apple's own
 * artist page does show what is up for pre-order, and its public catalogue
 * feed carries the same thing: this asks for the artist by name, then for
 * their albums, and keeps only the ones whose release date is still ahead of
 * today. Nothing is invented — with no future release the shelf is null and
 * the page is exactly what it was.
 *
 * Kept in this module because the artist page is assembled here, in
 * [YtMusicRepository.artistPage]: that call adds one request, bounded by
 * [TIMEOUT_MS], so a slow or silent Apple never holds the page up.
 */
object ApplePreRelease {

    /** Heading the artist page draws above these cards. */
    const val SHELF_TITLE = "Pré-Lançamentos"

    private const val SEARCH = "https://itunes.apple.com/search"
    private const val LOOKUP = "https://itunes.apple.com/lookup"
    private const val UA = "AMusic/1.0 (Android)"

    /** A pre-order window is short; more than a handful is never real. */
    private const val MAX_ITEMS = 8

    /** Spent inside the artist page call, so it stays small on purpose. */
    private const val TIMEOUT_MS = 4_000L
    private const val CACHE_TTL_MS = 6 * 60 * 60 * 1000L

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }
    private val cache = ConcurrentHashMap<String, Pair<Long, HomeShelf?>>()
    private val dateFormat: DateTimeFormatter = DateTimeFormatter.ofPattern("dd/MM")

    /**
     * The pre-release shelf for [artistName], or null when nothing of theirs is
     * on pre-order, when the name is unknown, or when Apple does not answer in
     * time. Cached for [CACHE_TTL_MS], nulls included, so flipping between
     * artist pages does not re-ask.
     */
    suspend fun shelf(artistName: String?, today: LocalDate = LocalDate.now()): HomeShelf? {
        val name = artistName?.trim().orEmpty()
        if (name.isEmpty()) return null
        return withContext(Dispatchers.IO) {
            val cached = cache[name]
            if (cached != null && System.currentTimeMillis() - cached.first < CACHE_TTL_MS) {
                return@withContext cached.second
            }
            val shelf = withTimeoutOrNull(TIMEOUT_MS) {
                runCatching { load(name, today) }.getOrNull()
            }
            if (shelf != null || cached != null) {
                cache[name] = System.currentTimeMillis() to shelf
            }
            shelf
        }
    }

    private fun load(name: String, today: LocalDate): HomeShelf? {
        val artistId = artistIdOf(name) ?: return null
        val answer = get("$LOOKUP?id=$artistId&entity=album&limit=200") ?: return null
        val items = answer["results"]?.jsonArray.orEmpty()
            .mapNotNull { result ->
                val album = runCatching { result.jsonObject }.getOrNull() ?: return@mapNotNull null
                if (album.text("wrapperType") != "collection") return@mapNotNull null
                val released = album.text("releaseDate")?.take(10) ?: return@mapNotNull null
                val date = runCatching { LocalDate.parse(released) }.getOrNull()
                    ?: return@mapNotNull null
                if (!date.isAfter(today)) return@mapNotNull null
                val title = album.text("collectionName") ?: return@mapNotNull null
                ShelfItem(
                    title = title,
                    // The card's only line under the cover: this is where the
                    // badge lives, with the day it lands.
                    subtitle = "Pré-Lançamento · ${date.format(dateFormat)}",
                    thumbnailUrl = album.text("artworkUrl100")?.replace("100x100bb", "600x600bb"),
                    videoId = null,
                    // No YouTube page exists for it yet, so the card is not a
                    // link; tapping it opens nothing rather than the wrong page.
                    browseId = null,
                ) to date
            }
            .sortedBy { it.second }
            .map { it.first }
            .take(MAX_ITEMS)
        if (items.isEmpty()) return null
        return HomeShelf(title = SHELF_TITLE, items = items)
    }

    /** The Apple Music artist id for [name], preferring an exact name match. */
    private fun artistIdOf(name: String): String? {
        val query = URLEncoder.encode(name, "UTF-8")
        val answer = get("$SEARCH?term=$query&entity=musicArtist&limit=5") ?: return null
        val artists = answer["results"]?.jsonArray.orEmpty()
            .mapNotNull { result -> runCatching { result.jsonObject }.getOrNull() }
            .filter { it.text("wrapperType") == "artist" }
        val match = artists.firstOrNull { it.text("artistName").equals(name, ignoreCase = true) }
            ?: artists.firstOrNull()
        return match?.text("artistId")
    }

    private fun get(url: String): JsonObject? = runCatching {
        val request = Request.Builder().url(url).header("User-Agent", UA).build()
        Http.client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) return null
            val body = response.body?.string() ?: return null
            json.parseToJsonElement(body).jsonObject
        }
    }.getOrNull()

    private fun JsonObject.text(key: String): String? {
        val element = this[key] ?: return null
        return runCatching { element.jsonPrimitive.contentOrNull }.getOrNull()
    }
}
