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
    private const val CACHE_SIZE = 64

    private val cache = object : LinkedHashMap<String, List<HomeShelf>>(CACHE_SIZE, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, List<HomeShelf>>) =
            size > CACHE_SIZE
    }
    private val targets = ConcurrentHashMap<String, AppleShelfTarget>()

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
        val appearsOn = viewCards(views, "appears-on", isAlbum = false)
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
            .flatMap { dataOf(views, it) }
            .filter { it.text("id") != currentAlbumId }
            .distinctBy { it.text("id") }
            .sortedByDescending { (it["attributes"] as? JsonObject)?.text("releaseDate").orEmpty() }
            .take(MAX_CARDS)
            .mapNotNull { card(it, isAlbum = true) }
    }

    private fun viewCards(views: JsonObject?, name: String, isAlbum: Boolean): List<ShelfItem> =
        dataOf(views, name).take(MAX_CARDS).mapNotNull { card(it, isAlbum) }

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
        targets[key] = AppleShelfTarget(key, name, subtitle, url, isAlbum)
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
     * Null when there is none, and the caller opens Apple's own page instead.
     */
    suspend fun youtubeAlbumFor(target: AppleShelfTarget): String? {
        val want = AppleReleaseMatcher.cleanTitle(target.title)
        if (want.isBlank()) return null
        val hits = runCatching {
            YtMusicRepository.search("${target.artist} ${target.title}".trim(), SearchFilter.ALBUMS)
                .getOrNull().orEmpty()
        }.getOrDefault(emptyList())
        val artistKey = target.artist.substringBefore(",").substringBefore("&").trim().lowercase()
        return hits.firstNotNullOfOrNull { hit ->
            val item = (hit as? SearchResult.Browse)?.item ?: return@firstNotNullOfOrNull null
            when {
                !item.browseId.startsWith("MPRE") -> null
                AppleReleaseMatcher.cleanTitle(item.title) != want -> null
                artistKey.isNotEmpty() && !item.subtitle.lowercase().contains(artistKey) -> null
                else -> item.browseId
            }
        }
    }

    private fun JsonObject.text(key: String): String? =
        (this[key] as? JsonPrimitive)?.contentOrNull?.trim()?.takeIf { it.isNotBlank() }
}
