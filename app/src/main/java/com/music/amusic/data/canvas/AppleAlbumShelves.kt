package com.music.amusic.data.canvas

import com.music.amusic.data.DebugLog as Log
import com.music.amusic.data.YtMusicRepository
import com.music.amusic.data.model.HomeShelf
import com.music.amusic.data.model.SearchFilter
import com.music.amusic.data.model.SearchResult
import com.music.amusic.data.model.ShelfItem
import java.util.concurrent.ConcurrentHashMap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject

/** An Apple Music card of the album page: what a tap on it has to open. */
class AppleShelfTarget(
    val id: String,
    val title: String,
    val artist: String,
    val url: String,
    val isAlbum: Boolean,
    /** "Álbum • 2026", "Single • 2026" or "EP • 2026": the line an in-app page draws under the credit. */
    val releaseLine: String = "",
) {
    /** The id Apple's catalog uses for the card: what follows the last colon of [id]. */
    val appleId: String
        get() = id.substringAfterLast(':')
}

/** One song of an Apple Music playlist, in the playlist's own order. */
class ApplePlaylistTrack(
    val number: Int,
    val name: String,
    val artist: String,
    val artworkUrl: String?,
)

/** An Apple Music playlist read from the catalog, with the songs it returns. */
class ApplePlaylist(
    val id: String,
    val name: String,
    val curator: String,
    val artworkUrl: String?,
    val tracks: List<ApplePlaylistTrack>,
)

/**
 * The shelves Apple Music draws under an album, read from Apple's catalog with
 * the same anonymous token and storefront the album colours use.
 *
 * Only what the catalog really returns is shown: "Mais de <artista>" from the
 * artist's own albums and singles, "Com participação em" from the album's
 * appears-on view and "Talvez você goste" from its related-albums view. A view
 * Apple leaves empty is simply not drawn. Apple's cards have no YouTube page,
 * so each carries an id starting with "apple:" and is resolved when tapped.
 */
object AppleAlbumShelves {
    private const val TAG = "AppleAlbumShelves"
    private const val MAX_CARDS = 20

    /** The most cards a paged shelf ("Mais de <artista>", "Com participação em") collects across pages. */
    private const val MAX_PAGED_CARDS = 100

    /** Pages followed per view, so a catalog that keeps answering "next" cannot loop for ever. */
    private const val MAX_PAGES = 8

    /** Page size asked of the catalog; its own default for a view is 10. */
    private const val PAGE_SIZE = "25"
    private const val CACHE_SIZE = 64

    private val cache = object : LinkedHashMap<String, List<HomeShelf>>(CACHE_SIZE, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, List<HomeShelf>>) =
            size > CACHE_SIZE
    }
    private val targets = ConcurrentHashMap<String, AppleShelfTarget>()
    private val playlists = ConcurrentHashMap<String, ApplePlaylist>()

    /** The YouTube Music album found for an Apple card; an empty string means there is none. */
    private val youtubeIds = ConcurrentHashMap<String, String>()
    private val opening: MutableSet<String> = ConcurrentHashMap.newKeySet()

    /** False while a tap on the same card is still being resolved, so a second tap opens nothing twice. */
    fun beginOpen(id: String): Boolean = opening.add(id)

    fun endOpen(id: String) {
        opening.remove(id)
    }

    /** What is known for the page without a request. */
    fun cached(browseId: String): List<HomeShelf> = synchronized(cache) { cache[browseId] }.orEmpty()

    /** What an Apple card id stands for; null for anything that is not one. */
    fun target(id: String): AppleShelfTarget? = targets[id]

    /**
     * The shelves for an album page. Null means nothing could be settled (no
     * token, no network) and is tried again next time; an empty list means
     * Apple answered and has nothing to show.
     */
    suspend fun shelvesFor(
        browseId: String,
        album: String,
        artist: String,
        trackCount: Int,
        year: String?,
        trackTitles: List<String>,
    ): List<HomeShelf>? {
        if (browseId.isBlank() || album.isBlank() || artist.isBlank()) return null
        synchronized(cache) { cache[browseId] }?.let { return it }
        val shelves = withContext(Dispatchers.IO) {
            runCatching { load(album, artist, trackCount, year, trackTitles) }
                .onFailure { Log.d(TAG, "shelves failed for $album: $it") }
                .getOrNull()
        } ?: return null
        synchronized(cache) { cache[browseId] = shelves }
        return shelves
    }

    private fun load(
        album: String,
        artist: String,
        trackCount: Int,
        year: String?,
        trackTitles: List<String>,
    ): List<HomeShelf>? {
        val choice = AppleReleaseMatcher.choose(album, artist, trackCount, year, trackTitles) ?: return null
        val albumId = choice.collectionId?.toString() ?: return emptyList()
        val body = AppleMusicCanvas.catalogGet(
            "albums/$albumId",
            mapOf("views" to "appears-on,related-albums", "include" to "artists", "l" to "pt-BR"),
        ) ?: return null
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: return emptyList()
        val views = record["views"] as? JsonObject
        val artistRecord = ((record["relationships"] as? JsonObject)?.get("artists") as? JsonObject)
            ?.get("data")?.jsonArray?.firstOrNull() as? JsonObject
        val artistId = artistRecord?.text("id")
        val artistName = (artistRecord?.get("attributes") as? JsonObject)?.text("name") ?: choice.artistName

        val shelves = mutableListOf<HomeShelf>()
        if (artistId != null) {
            val more = moreFromArtist(artistId, albumId)
            if (more.isNotEmpty()) shelves += HomeShelf(title = "Mais de $artistName", items = more)
        }
        // Apple answers a view with its first page only (10 cards) and a "next"
        // path for the rest, so the remaining pages are read here.
        val appearsOnRecords = pagedView(views, "appears-on", "albums/$albumId/view/appears-on")
        val appearsOn = appearsOnRecords.take(MAX_PAGED_CARDS).mapNotNull { card(it, isAlbum = false) }
        if (appearsOn.isNotEmpty()) shelves += HomeShelf(title = "Com participação em", items = appearsOn)
        val related = viewCards(views, "related-albums", isAlbum = true)
        if (related.isNotEmpty()) shelves += HomeShelf(title = "Talvez você goste", items = related)
        Log.d(TAG, "apple shelves for '$album': ${shelves.joinToString { "${it.title} (${it.items.size})" }}")
        return shelves
    }

    /** The artist's own albums, singles and EPs, newest first, without the page's own album. */
    private fun moreFromArtist(artistId: String, currentAlbumId: String): List<ShelfItem> {
        val body = AppleMusicCanvas.catalogGet(
            "artists/$artistId",
            mapOf("views" to "full-albums,singles,appears-on-albums", "l" to "pt-BR"),
        ) ?: return emptyList()
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: return emptyList()
        val views = record["views"] as? JsonObject
        return listOf("full-albums", "singles", "appears-on-albums")
            .flatMap { pagedView(views, it, "artists/$artistId/view/$it") }
            .filter { it.text("id") != currentAlbumId }
            .distinctBy { it.text("id") }
            .sortedByDescending { (it["attributes"] as? JsonObject)?.text("releaseDate").orEmpty() }
            .take(MAX_PAGED_CARDS)
            .mapNotNull { card(it, isAlbum = true) }
    }

    private fun viewCards(views: JsonObject?, name: String, isAlbum: Boolean): List<ShelfItem> =
        dataOf(views, name).take(MAX_CARDS).mapNotNull { card(it, isAlbum) }

    /**
     * Every record of a catalog view: the first page the parent request
     * already carried, then the pages its "next" path points to, up to
     * [MAX_PAGED_CARDS] records. A page that fails ends the list there, so
     * what was read so far is still shown.
     */
    private fun pagedView(views: JsonObject?, name: String, viewPath: String): List<JsonObject> {
        val records = dataOf(views, name).toMutableList()
        var next = ((views?.get(name) as? JsonObject)?.get("next") as? JsonPrimitive)?.contentOrNull
        var pages = 0
        while (next != null && records.size < MAX_PAGED_CARDS && pages < MAX_PAGES) {
            pages++
            val offset = Regex("""[?&]offset=(\d+)""").find(next)?.groupValues?.get(1) ?: records.size.toString()
            val body = AppleMusicCanvas.catalogGet(
                viewPath,
                mapOf("offset" to offset, "limit" to PAGE_SIZE, "l" to "pt-BR"),
            ) ?: AppleMusicCanvas.catalogGet(viewPath, mapOf("offset" to offset, "l" to "pt-BR")) ?: break
            val page = runCatching { Json.parseToJsonElement(body).jsonObject }.getOrNull() ?: break
            val batch = (page["data"] as? kotlinx.serialization.json.JsonArray).orEmpty()
                .mapNotNull { it as? JsonObject }
            if (batch.isEmpty()) break
            records += batch
            next = (page["next"] as? JsonPrimitive)?.contentOrNull
        }
        Log.d(TAG, "view $name: ${records.size} cards in ${pages + 1} page(s)")
        return records.distinctBy { it.text("id") }
    }

    private fun dataOf(views: JsonObject?, name: String): List<JsonObject> =
        ((views?.get(name) as? JsonObject)?.get("data")?.jsonArray).orEmpty().mapNotNull { it as? JsonObject }

    private fun card(record: JsonObject, isAlbum: Boolean): ShelfItem? {
        val id = record.text("id") ?: return null
        val attributes = record["attributes"] as? JsonObject ?: return null
        val name = attributes.text("name") ?: return null
        val url = attributes.text("url") ?: return null
        val template = (attributes["artwork"] as? JsonObject)?.text("url")
        val thumbnail = template
            ?.replace("{w}", "480")?.replace("{h}", "480")?.replace("{c}", "bb")?.replace("{f}", "jpg")
        val subtitle = (if (isAlbum) attributes.text("artistName") else attributes.text("curatorName")).orEmpty()
        val key = (if (isAlbum) "apple:album:" else "apple:playlist:") + id
        val year = attributes.text("releaseDate")?.take(4)?.takeIf { it.length == 4 && it.all(Char::isDigit) }
        val kind = when {
            name.trimEnd().endsWith("- EP", ignoreCase = true) -> "EP"
            attributes.text("isSingle") == "true" || name.trimEnd().endsWith("- Single", ignoreCase = true) -> "Single"
            else -> "Álbum"
        }
        val releaseLine = if (isAlbum) listOfNotNull(kind, year).joinToString(" • ") else ""
        targets[key] = AppleShelfTarget(key, name, subtitle, url, isAlbum, releaseLine)
        return ShelfItem(
            title = name,
            subtitle = subtitle,
            thumbnailUrl = thumbnail,
            videoId = null,
            browseId = key,
            explicit = attributes.text("contentRating") == "explicit",
        )
    }

    /**
     * The YouTube Music album that is the same release as an Apple card, found
     * by search and accepted only when the cleaned title and the artist agree.
     * Null when there is none, and the caller then opens the app's own album
     * page built from Apple's track list. The answer is remembered, so a
     * second tap on the same card opens at once.
     */
    suspend fun youtubeAlbumFor(target: AppleShelfTarget): String? {
        youtubeIds[target.id]?.let { return it.takeIf { id -> id.isNotEmpty() } }
        val want = AppleReleaseMatcher.cleanTitle(target.title)
        if (want.isBlank()) return null
        val hits = runCatching {
            YtMusicRepository.search("${target.artist} ${target.title}".trim(), SearchFilter.ALBUMS)
                .getOrNull()
        }.getOrNull() ?: return null
        val artistKey = target.artist.substringBefore(",").substringBefore("&").trim().lowercase()
        val found = hits.firstNotNullOfOrNull { hit ->
            val item = (hit as? SearchResult.Browse)?.item ?: return@firstNotNullOfOrNull null
            when {
                !item.browseId.startsWith("MPRE") -> null
                AppleReleaseMatcher.cleanTitle(item.title) != want -> null
                artistKey.isNotEmpty() && !item.subtitle.lowercase().contains(artistKey) -> null
                else -> item.browseId
            }
        }
        youtubeIds[target.id] = found.orEmpty()
        return found
    }

    /**
     * An Apple Music playlist with the songs the catalog returns for it (its
     * first page, up to 100), for the app's own playlist page. Null when
     * Apple does not answer; remembered once it has.
     */
    suspend fun playlistFor(playlistId: String): ApplePlaylist? {
        if (playlistId.isBlank()) return null
        playlists[playlistId]?.let { return it }
        val playlist = withContext(Dispatchers.IO) {
            runCatching { loadPlaylist(playlistId) }
                .onFailure { Log.d(TAG, "playlist failed for $playlistId: $it") }
                .getOrNull()
        } ?: return null
        playlists[playlistId] = playlist
        return playlist
    }

    private fun loadPlaylist(playlistId: String): ApplePlaylist? {
        val body = AppleMusicCanvas.catalogGet(
            "playlists/$playlistId",
            mapOf("include" to "tracks", "l" to "pt-BR"),
        ) ?: return null
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: return null
        val attributes = record["attributes"] as? JsonObject
        val songs = (((record["relationships"] as? JsonObject)?.get("tracks") as? JsonObject)
            ?.get("data")?.jsonArray).orEmpty()
            .mapNotNull { it as? JsonObject }
            .filter { it.text("type") == "songs" }
        val tracks = songs.mapIndexedNotNull { index, song ->
            val songAttributes = song["attributes"] as? JsonObject ?: return@mapIndexedNotNull null
            val name = songAttributes.text("name") ?: return@mapIndexedNotNull null
            ApplePlaylistTrack(
                number = index + 1,
                name = name,
                artist = songAttributes.text("artistName").orEmpty(),
                artworkUrl = artworkOf(songAttributes),
            )
        }
        return ApplePlaylist(
            id = playlistId,
            name = attributes?.text("name").orEmpty(),
            curator = attributes?.text("curatorName").orEmpty(),
            artworkUrl = attributes?.let { artworkOf(it) },
            tracks = tracks,
        )
    }

    private fun artworkOf(attributes: JsonObject): String? =
        (attributes["artwork"] as? JsonObject)?.text("url")
            ?.replace("{w}", "480")?.replace("{h}", "480")?.replace("{c}", "bb")?.replace("{f}", "jpg")

    private fun JsonObject.text(key: String): String? =
        (this[key] as? JsonPrimitive)?.contentOrNull?.trim()?.takeIf { it.isNotBlank() }
}
