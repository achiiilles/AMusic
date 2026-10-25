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

/** One track of a release that is not out yet, as Apple's catalogue describes it. */
data class PreReleaseTrack(
    /** The sleeve's own number, kept so the row reads 1, 2, 3 as the album does. */
    val number: Int,
    /** The catalogue's name: the real one once it is out, "Track 2" until then. */
    val name: String,
    /** True once the catalogue gives the track a name and a preview of its own. */
    val released: Boolean,
    val previewUrl: String?,
)

/** A pre-order release read straight from Apple's public catalogue. */
data class PreReleaseAlbum(
    val collectionId: String,
    val name: String,
    val artistName: String?,
    /** The day the whole thing lands, as the album result reported it. */
    val releaseDate: String?,
    val artworkUrl: String?,
    val tracks: List<PreReleaseTrack>,
)

/**
 * Apple Music's pre-releases, read as a shelf for an artist page and as a page
 * of their own once a card is tapped.
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

    /** The longer read a tapped card is allowed: a whole track list, not a shelf. */
    private const val ALBUM_TIMEOUT_MS = 12_000L

    /** Apple names a track it has not announced yet exactly this way. */
    private val PLACEHOLDER = Regex("^Track\\s*\\d+$", RegexOption.IGNORE_CASE)

    private val TYPE_SUFFIX = Regex("""\s+-\s+(?:single|ep)\s*\z""", RegexOption.IGNORE_CASE)

    /**
     * An Apple release name as it is shown: only a trailing " - Single" or " - EP"
     * is dropped, since the type is drawn on its own line. Anything else in the
     * name ("The 1st Mini Album", an "EP" in the middle) stays as Apple wrote it.
     */
    fun displayTitle(raw: String): String {
        val trimmed = raw.trim()
        return TYPE_SUFFIX.replace(trimmed, "").trim().ifEmpty { trimmed }
    }

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }
    private val cache = ConcurrentHashMap<String, Pair<Long, HomeShelf?>>()
    private val albums = ConcurrentHashMap<String, Pair<Long, PreReleaseAlbum?>>()

    /**
     * The Apple id behind each card, by name, so a tapped card can ask for the
     * track list without a second search. Filled by [load] as the shelf is
     * built; the card itself carries no id because the YouTube fields it has
     * are the wrong kind of id.
     */
    private val collectionIds = ConcurrentHashMap<String, String>()

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

    /**
     * The Apple collection id behind a card this object built, or null when the
     * card did not come from here (an album that is already out, say).
     */
    fun collectionIdOf(title: String?): String? {
        val key = title?.trim().orEmpty()
        if (key.isEmpty()) return null
        return collectionIds[key]
    }

    /**
     * The release itself: its name, credit, day and every track the catalogue
     * already lists. Null when Apple does not answer.
     *
     * A track counts as out only when the catalogue says so — a real name and
     * a preview of its own, or a release day that has passed. A track still
     * named "Track 2" is not out, and it is shown that way rather than given a
     * name of our own.
     */
    suspend fun album(collectionId: String?, today: LocalDate = LocalDate.now()): PreReleaseAlbum? {
        val id = collectionId?.trim().orEmpty()
        if (id.isEmpty()) return null
        return withContext(Dispatchers.IO) {
            val cached = albums[id]
            if (cached != null && System.currentTimeMillis() - cached.first < CACHE_TTL_MS) {
                return@withContext cached.second
            }
            val album = withTimeoutOrNull(ALBUM_TIMEOUT_MS) {
                runCatching { loadAlbum(id, today) }.getOrNull()
            }
            if (album != null) {
                albums[id] = System.currentTimeMillis() to album
            }
            album
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
                album.text("collectionId")?.let { collectionIds[title.trim()] = it }
                ShelfItem(
                    title = title,
                    // The card's only line under the cover: this is where the
                    // badge lives, with the day it lands.
                    subtitle = "Pré-Lançamento · ${date.format(dateFormat)}",
                    thumbnailUrl = album.text("artworkUrl100")?.replace("100x100bb", "600x600bb"),
                    videoId = null,
                    // No YouTube page exists for it yet; the card opens this
                    // object's own page instead, found by name.
                    browseId = null,
                ) to date
            }
            .sortedBy { it.second }
            .map { it.first }
            .take(MAX_ITEMS)
        if (items.isEmpty()) return null
        return HomeShelf(title = SHELF_TITLE, items = items)
    }

    private fun loadAlbum(collectionId: String, today: LocalDate): PreReleaseAlbum? {
        val answer = get("$LOOKUP?id=$collectionId&entity=song&limit=200") ?: return null
        val results = answer["results"]?.jsonArray.orEmpty()
            .mapNotNull { result -> runCatching { result.jsonObject }.getOrNull() }
        val collection = results.firstOrNull { it.text("wrapperType") == "collection" }
        val songs = results.filter { it.text("wrapperType") == "track" }
        if (collection == null && songs.isEmpty()) return null

        val tracks = songs.mapIndexedNotNull { index, song ->
            val rawName = song.text("trackName")?.trim()
            val number = song.text("trackNumber")?.toIntOrNull() ?: (index + 1)
            val placeholder = rawName.isNullOrEmpty() || PLACEHOLDER.matches(rawName)
            val preview = song.text("previewUrl")
            val trackDate = song.text("releaseDate")?.take(10)
                ?.let { raw -> runCatching { LocalDate.parse(raw) }.getOrNull() }
            val dayPassed = trackDate != null && !trackDate.isAfter(today)
            val released = !placeholder && (!preview.isNullOrBlank() || dayPassed)
            PreReleaseTrack(
                number = number,
                // A placeholder keeps the catalogue's own wording — "Track 2" —
                // and a track with no name at all falls back to the same shape.
                name = if (placeholder) "Faixa $number" else rawName.orEmpty(),
                released = released,
                previewUrl = preview,
            )
        }.sortedBy { it.number }

        val cover = (collection ?: songs.firstOrNull())
            ?.text("artworkUrl100")
            ?.replace("100x100bb", "600x600bb")

        return PreReleaseAlbum(
            collectionId = collectionId,
            name = displayTitle(
                collection?.text("collectionName")
                    ?: songs.firstOrNull()?.text("collectionName")
                    ?: "",
            ),
            artistName = collection?.text("artistName")
                ?: songs.firstOrNull()?.text("artistName"),
            releaseDate = collection?.text("releaseDate")?.take(10),
            artworkUrl = cover,
            tracks = tracks,
        )
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
