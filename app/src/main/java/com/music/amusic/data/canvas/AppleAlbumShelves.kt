package com.music.amusic.data.canvas

import com.music.amusic.data.DebugLog as Log
import com.music.amusic.data.YtMusicRepository
import com.music.amusic.data.model.HomeShelf
import com.music.amusic.data.model.SearchFilter
import com.music.amusic.data.model.SearchResult
import com.music.amusic.data.model.ShelfItem
import java.util.concurrent.ConcurrentHashMap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.runBlocking
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
 * appears-on view and "Talvez você goste" from its you-might-also-like view
 * (the view the Apple Music site itself asks for; the documented related-albums
 * view answers "No view found" for albums, so it is only a second attempt).
 * A view Apple leaves empty is simply not drawn. Apple's cards have no YouTube
 * page, so each carries an id starting with "apple:" and is resolved when tapped.
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
    /**
     * Why "Talvez você goste" is not on an album page, in Portuguese, by page id.
     * Set whenever the page's answer was read without that shelf, and removed when
     * the shelf is there. The album page shows it in the shelf's place.
     */
    private val relatedNotes = ConcurrentHashMap<String, String>()
    private val targets = ConcurrentHashMap<String, AppleShelfTarget>()
    private val playlists = ConcurrentHashMap<String, ApplePlaylist>()

    /** The YouTube Music album found for an Apple card; an empty string means there is none. */
    private val youtubeIds = ConcurrentHashMap<String, String>()
    private val opening: MutableSet<String> = ConcurrentHashMap.newKeySet()

    /** False while a tap on the same card is still being resolved, so a second tap opens nothing twice. */
    fun beginOpen(id: String): Boolean {
        if (!opening.add(id)) return false
        // Apple cards may need a YouTube match before opening a page. Warm the
        // artist lookup at the actual tap, alongside that match, not after it.
        targets[id]?.takeIf { it.isAlbum }?.let { AppleReleaseMatcher.prefetch(it.artist) }
        return true
    }

    fun endOpen(id: String) {
        opening.remove(id)
    }

    /** What is known for the page without a request. */
    fun cached(browseId: String): List<HomeShelf> = synchronized(cache) { cache[browseId] }.orEmpty()

    /** The reason "Talvez você goste" is missing for the page; null when it is shown or not known yet. */
    fun relatedNote(browseId: String): String? = relatedNotes[browseId]

    private fun setNote(browseId: String, note: String?) {
        if (note == null) relatedNotes.remove(browseId) else relatedNotes[browseId] = note
    }

    private fun catalogProblem(): String = AppleMusicCanvas.lastCatalogProblem ?: "sem resposta"

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
        onUpdate: ((List<HomeShelf>) -> Unit)? = null,
    ): List<HomeShelf>? {
        if (browseId.isBlank() || album.isBlank() || artist.isBlank()) return null
        synchronized(cache) { cache[browseId] }?.let {
            onUpdate?.invoke(it)
            return it
        }
        val shelves = withContext(Dispatchers.IO) {
            runCatching { load(browseId, album, artist, trackCount, year, trackTitles, onUpdate) }
                .onFailure {
                    Log.d(TAG, "shelves failed for $album: $it")
                    setNote(
                        browseId,
                        "A busca no Apple Music falhou (${it.javaClass.simpleName}: ${it.message.orEmpty().take(60)})",
                    )
                }
                .getOrNull()
        } ?: return null
        synchronized(cache) { cache[browseId] = shelves }
        return shelves
    }

    private fun load(
        browseId: String,
        album: String,
        artist: String,
        trackCount: Int,
        year: String?,
        trackTitles: List<String>,
        onUpdate: ((List<HomeShelf>) -> Unit)?,
    ): List<HomeShelf>? {
        val choice = AppleReleaseMatcher.choose(album, artist, trackCount, year, trackTitles) ?: run {
            setNote(browseId, "Não consegui achar este álbum no Apple Music (artista não encontrado ou sem resposta da busca)")
            return null
        }
        val albumId = choice.collectionId?.toString() ?: run {
            setNote(browseId, "Não achei este álbum entre os lançamentos de ${choice.artistName} no Apple Music")
            return emptyList()
        }
        val body = AppleMusicCanvas.catalogGet(
            "albums/$albumId",
            mapOf("views" to "appears-on,you-might-also-like", "include" to "artists", "l" to "pt-BR"),
        ) ?: run {
            val problem = catalogProblem()
            if (problem.contains("404")) {
                // Apple refused the whole album request with 404: Last.fm still
                // gives the recommendations shelf. Any other failure is retried next time.
                val fallback = lastFmRelated(choice.artistName, albumId)
                if (fallback.isNotEmpty()) {
                    setNote(browseId, null)
                    return listOf(HomeShelf(title = "Talvez você goste", items = fallback))
                }
            }
            setNote(browseId, "A busca no Apple Music falhou ($problem)")
            return null
        }
        val albumTrace = AppleMusicCanvas.catalogTrace()
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: run {
            setNote(browseId, "A Apple respondeu sem dados deste álbum (HTTP 200, lista vazia)")
            return emptyList()
        }
        val albumIdentity = "Escolhido pelo iTunes: $albumId (${choice.collectionName}), ${choice.artistName}; " +
            "Apple respondeu id=${record.text("id")}, tipo=${record.text("type")}, " +
            "nome=${(record["attributes"] as? JsonObject)?.text("name")}; loja=${AppleMusicCanvas.storefront}"
        val views = record["views"] as? JsonObject
        Log.d(
            TAG,
            "debug related: album $albumId storefront ${AppleMusicCanvas.storefront}; " +
                "views in the album answer: ${views?.keys?.joinToString().orEmpty().ifEmpty { "none" }}; " +
                "you-might-also-like view: ${(views?.get("you-might-also-like") as? JsonObject)?.toString()?.take(400) ?: "absent"}",
        )
        val artistRecord = ((record["relationships"] as? JsonObject)?.get("artists") as? JsonObject)
            ?.get("data")?.jsonArray?.firstOrNull() as? JsonObject
        val artistId = artistRecord?.text("id")
        val artistName = (artistRecord?.get("attributes") as? JsonObject)?.text("name") ?: choice.artistName

        // The three shelves are independent once the album answer is in, so they are
        // read at the same time instead of one after the other: the page waits for the
        // slowest of them, not for the sum. Each branch makes the same requests, in the
        // same order, as before; only the branches no longer wait for each other.
        // Publish each page before following continuations, with ordered snapshots.
        // The complete result alone enters the existing cache.
        val previewLock = Any()
        val previews = arrayOf(emptyList<ShelfItem>(), emptyList<ShelfItem>(), emptyList<ShelfItem>())
        fun publish(slot: Int, items: List<ShelfItem>) {
            synchronized(previewLock) {
                previews[slot] = items
                val snapshot = buildList<HomeShelf> {
                    if (previews[0].isNotEmpty()) add(HomeShelf(title = "Mais de $artistName", items = previews[0]))
                    if (previews[1].isNotEmpty()) add(HomeShelf(title = "Com participação em", items = previews[1]))
                    if (previews[2].isNotEmpty()) add(HomeShelf(title = "Talvez você goste", items = previews[2]))
                }
                onUpdate?.invoke(snapshot)
            }
        }
        val askNotes = mutableListOf<String>()
        val branches = runBlocking {
            coroutineScope {
                val moreJob = async(Dispatchers.IO) {
                    if (artistId != null) moreFromArtist(artistId, albumId) { publish(0, it) } else emptyList()
                }
                // Apple answers a view with its first page only (10 cards) and a "next"
                // path for the rest, so the remaining pages are read here.
                val appearsOnJob = async(Dispatchers.IO) {
                    pagedView(views, "appears-on", "albums/$albumId/view/appears-on", onPage = { records ->
                        publish(1, records.take(MAX_PAGED_CARDS).mapNotNull { card(it, isAlbum = false) })
                    })
                }
                // "Talvez você goste" is the album's you-might-also-like view, the one the
                // Apple Music site asks for (checked on the catalog: it answers 200 with
                // the same albums the site shows, while the documented related-albums
                // view answers HTTP 400 "No view found"). It is paged like the two
                // shelves above, and asked for on its own when the album answer carries
                // the view without any card. related-albums stays as a second attempt.
                // Last.fm is asked only when Apple has no cards (404 or empty view), and
                // that wait now happens beside the other two shelves, not after them.
                val relatedJob = async(Dispatchers.IO) {
                    var records = pagedView(
                        views,
                        "you-might-also-like",
                        "albums/$albumId/view/you-might-also-like",
                        askWhenEmpty = true,
                        notes = askNotes,
                        onPage = { records ->
                            publish(2, records.filter { it.text("id") != albumId }
                                .take(MAX_PAGED_CARDS).mapNotNull { card(it, isAlbum = true) })
                        },
                    )
                    if (records.isEmpty()) {
                        records = pagedView(
                            views,
                            "related-albums",
                            "albums/$albumId/view/related-albums",
                            askWhenEmpty = true,
                            notes = askNotes,
                            onPage = { records ->
                                publish(2, records.filter { it.text("id") != albumId }
                                    .take(MAX_PAGED_CARDS).mapNotNull { card(it, isAlbum = true) })
                            },
                        )
                    }
                    Log.d(TAG, "debug related: ${records.size} records before filtering, ids ${records.take(5).joinToString { it.text("id").orEmpty() }}")
                    var cards = records
                        .filter { it.text("id") != albumId }
                        .take(MAX_PAGED_CARDS)
                        .mapNotNull { card(it, isAlbum = true) }
                    if (cards.isEmpty()) {
                        // Apple has no recommendations for this album (404 or an empty view):
                        // the shelf is built from Last.fm's similar artists instead.
                        cards = lastFmRelated(artistName, albumId)
                        if (cards.isNotEmpty()) Log.d(TAG, "related for $albumId: ${cards.size} cards from Last.fm")
                    }
                    publish(2, cards)
                    Pair(records, cards)
                }
                Triple(moreJob.await(), appearsOnJob.await(), relatedJob.await())
            }
        }
        val more = branches.first
        val appearsOnRecords = branches.second
        val relatedRecords = branches.third.first
        val related = branches.third.second

        val shelves = mutableListOf<HomeShelf>()
        if (more.isNotEmpty()) shelves += HomeShelf(title = "Mais de $artistName", items = more)
        val appearsOn = appearsOnRecords.take(MAX_PAGED_CARDS).mapNotNull { card(it, isAlbum = false) }
        if (appearsOn.isNotEmpty()) shelves += HomeShelf(title = "Com participação em", items = appearsOn)
        if (related.isNotEmpty()) {
            shelves += HomeShelf(title = "Talvez você goste", items = related)
            setNote(browseId, null)
        } else {
            Log.d(
                TAG,
                "related for $albumId: no cards (view in the album answer: ${views?.containsKey("you-might-also-like") == true})",
            )
            // The reason shown on the album page where the shelf would be.
            val ownAlbum = relatedRecords.count { it.text("id") == albumId }
            val sawInAnswer = when {
                views == null -> "sem seções na resposta do álbum"
                views.containsKey("you-might-also-like") -> "you-might-also-like veio vazio"
                else -> "sem you-might-also-like (seções: ${views.keys.joinToString().ifEmpty { "nenhuma" }})"
            }
            val reason = when {
                relatedRecords.isNotEmpty() -> {
                    val kept = (relatedRecords.size - ownAlbum).coerceAtMost(MAX_PAGED_CARDS)
                    "Todos os cards foram descartados (${relatedRecords.size} recebidos: " +
                        "$ownAlbum eram o próprio álbum, ${(kept - related.size).coerceAtLeast(0)} sem nome ou endereço)"
                }
                askNotes.isNotEmpty() -> "Consultas de recomendações: ${askNotes.joinToString("\n")}"
                else -> "A Apple não devolveu recomendações para este álbum ($sawInAnswer; consulta própria: 0 cards)"
            }
            setNote(browseId, "$reason\n$albumIdentity\nPedido do álbum: $albumTrace")
        }
        Log.d(TAG, "apple shelves for '$album': ${shelves.joinToString { "${it.title} (${it.items.size})" }}")
        return shelves
    }

    /**
     * "Talvez você goste" built from Last.fm: about ten artists similar to
     * [artistName], the top album of each, found on Apple Music by name so the
     * card has Apple's cover and opens like any other Apple card. Empty when
     * the build has no Last.fm key, so the shelf is simply not drawn.
     */
    private fun lastFmRelated(artistName: String, currentAlbumId: String): List<ShelfItem> {
        if (!LastFmSimilarAlbums.available) return emptyList()
        val similar = runCatching { LastFmSimilarAlbums.similarTo(artistName) }
            .onFailure { Log.d(TAG, "last.fm similar failed: ${it.javaClass.simpleName}") }
            .getOrDefault(emptyList())
        if (similar.isEmpty()) return emptyList()
        val records = runBlocking {
            coroutineScope {
                similar.map { artist ->
                    async(Dispatchers.IO) {
                        runCatching { findOnApple(artist.name, artist.albums) }.getOrNull()
                    }
                }.awaitAll()
            }
        }
        return records.filterNotNull()
            .filter { it.text("id") != currentAlbumId }
            .distinctBy { it.text("id") }
            .mapNotNull { card(it, isAlbum = true) }
    }

    /**
     * The Apple Music album for a Last.fm (artist, albums) pair, by catalog
     * search with the same token and storefront as the rest of this file. The
     * artist has to agree. The title is matched first exactly and then loosely
     * (edition suffixes ignored); with no title match the first album of the
     * right artist for Last.fm's first album is taken.
     */
    private fun findOnApple(similarArtist: String, albums: List<String>): JsonObject? {
        val wantArtist = AppleReleaseMatcher.cleanTitle(similarArtist)
        var artistOnly: JsonObject? = null
        for ((index, album) in albums.withIndex()) {
            val body = AppleMusicCanvas.catalogGet(
                "search",
                mapOf("term" to "$similarArtist $album", "types" to "albums", "limit" to "8", "l" to "pt-BR"),
            ) ?: continue
            val hits = runCatching {
                Json.parseToJsonElement(body).jsonObject["results"]?.jsonObject
                    ?.get("albums")?.jsonObject?.get("data")?.jsonArray
            }.getOrNull().orEmpty().mapNotNull { it as? JsonObject }
            val sameArtist = hits.filter { hit ->
                val credited = AppleReleaseMatcher.cleanTitle(
                    (hit["attributes"] as? JsonObject)?.text("artistName").orEmpty(),
                )
                credited.isNotEmpty() && (credited == wantArtist || credited.contains(wantArtist) || wantArtist.contains(credited))
            }
            val wantAlbum = AppleReleaseMatcher.cleanTitle(album)
            fun titleOf(hit: JsonObject): String =
                AppleReleaseMatcher.cleanTitle((hit["attributes"] as? JsonObject)?.text("name").orEmpty())
            sameArtist.firstOrNull { titleOf(it) == wantAlbum }?.let { return it }
            sameArtist.firstOrNull { titleOf(it).contains(wantAlbum) || wantAlbum.contains(titleOf(it)) }
                ?.let { return it }
            if (index == 0 && artistOnly == null) artistOnly = sameArtist.firstOrNull()
        }
        return artistOnly
    }

    /** The artist's own albums, singles and EPs, newest first, without the page's own album. */
    private fun moreFromArtist(
        artistId: String,
        currentAlbumId: String,
        onPage: ((List<ShelfItem>) -> Unit)? = null,
    ): List<ShelfItem> {
        val body = AppleMusicCanvas.catalogGet(
            "artists/$artistId",
            mapOf("views" to "full-albums,singles,appears-on-albums", "l" to "pt-BR"),
        ) ?: return emptyList()
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: return emptyList()
        val views = record["views"] as? JsonObject
        val pageLock = Any()
        val pageRecords = mutableMapOf<String, List<JsonObject>>()
        fun artistCards(records: List<JsonObject>): List<ShelfItem> = records
            .filter { it.text("id") != currentAlbumId }
            .distinctBy { it.text("id") }
            .sortedByDescending { (it["attributes"] as? JsonObject)?.text("releaseDate").orEmpty() }
            .take(MAX_PAGED_CARDS)
            .mapNotNull { card(it, isAlbum = true) }
        // The three artist views are read at the same time; the order of the result is kept.
        val records = runBlocking {
            coroutineScope {
                listOf("full-albums", "singles", "appears-on-albums").map { name ->
                    async(Dispatchers.IO) {
                        pagedView(views, name, "artists/$artistId/view/$name", onPage = { records ->
                            synchronized(pageLock) {
                                pageRecords[name] = records
                                val merged = listOf("full-albums", "singles", "appears-on-albums")
                                    .flatMap { pageRecords[it].orEmpty() }
                                onPage?.invoke(artistCards(merged))
                            }
                        })
                    }
                }.awaitAll()
            }
        }
        return records.flatten()
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
    private fun pagedView(
        views: JsonObject?,
        name: String,
        viewPath: String,
        askWhenEmpty: Boolean = false,
        notes: MutableList<String>? = null,
        onPage: ((List<JsonObject>) -> Unit)? = null,
    ): List<JsonObject> {
        val records = dataOf(views, name).toMutableList()
        var next = ((views?.get(name) as? JsonObject)?.get("next") as? JsonPrimitive)?.contentOrNull
        var pages = 0
        if (askWhenEmpty && records.isEmpty() && next == null) {
            // The parent answer had nothing for this view: ask for the view on
            // its own (/view/<name>), which Apple documents as a request of its own.
            pages++
            fun ask(path: String, params: Map<String, String>): String? {
                val answer = AppleMusicCanvas.catalogGet(path, params)
                notes?.add("$name: ${AppleMusicCanvas.catalogTrace()}")
                return answer
            }
            val body = ask(
                viewPath,
                mapOf("offset" to "0", "limit" to PAGE_SIZE, "l" to "pt-BR"),
            ) ?: ask(viewPath, mapOf("l" to "pt-BR"))
            val page = body?.let { runCatching { Json.parseToJsonElement(it).jsonObject }.getOrNull() }
            if (body == null) {
                val ownProblem = AppleMusicCanvas.catalogTrace()
                // The view's own path was refused (HTTP 400 seen on an album): ask the
                // album record for just this view instead, with the language and then
                // without it, and keep what each answer said for the note on the page.
                val parentPath = viewPath.substringBefore("/view/")
                val viaParent = ask(
                    parentPath,
                    mapOf("views" to name, "l" to "pt-BR"),
                ) ?: ask(parentPath, mapOf("views" to name))
                val parentViews = viaParent
                    ?.let { runCatching { Json.parseToJsonElement(it).jsonObject }.getOrNull() }
                    ?.get("data")?.let { it as? kotlinx.serialization.json.JsonArray }
                    ?.firstOrNull()?.let { it as? JsonObject }
                    ?.get("views") as? JsonObject
                if (parentViews != null) {
                    records += dataOf(parentViews, name)
                    next = ((parentViews[name] as? JsonObject)?.get("next") as? JsonPrimitive)?.contentOrNull
                }
                Log.d(
                    TAG,
                    "debug view $name via $parentPath: ${if (viaParent == null) "failed (${AppleMusicCanvas.catalogTrace()})" else "${records.size} cards"}",
                )
                if (records.isEmpty()) {
                    notes?.add(
                        "$name, rota própria da vista: $ownProblem; pelo álbum: " +
                            (if (viaParent == null) AppleMusicCanvas.catalogTrace() else "respondeu sem cards"),
                    )
                }
            } else if (page == null) {
                notes?.add("resposta ilegível")
            }
            if (page != null) {
                records += (page["data"] as? kotlinx.serialization.json.JsonArray).orEmpty()
                    .mapNotNull { it as? JsonObject }
                next = (page["next"] as? JsonPrimitive)?.contentOrNull
            }
            Log.d(TAG, "view $name asked on its own: ${records.size} cards, answer ${if (page == null) "missing" else "read"}")
            Log.d(TAG, "debug view $name on its own: $viewPath answer ${body?.take(400) ?: "null (no token, http error or no answer)"}")
        }
        // Inline pages can be smaller than 25. Requests and retries are unchanged.
        onPage?.invoke(records.distinctBy { it.text("id") })
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
            onPage?.invoke(records.distinctBy { it.text("id") })
        }
        Log.d(TAG, "view $name: ${records.size} cards in ${pages + 1} page(s)")
        return records.distinctBy { it.text("id") }
    }

    private fun dataOf(views: JsonObject?, name: String): List<JsonObject> =
        ((views?.get(name) as? JsonObject)?.get("data")?.jsonArray).orEmpty().mapNotNull { it as? JsonObject }

    private fun card(record: JsonObject, isAlbum: Boolean): ShelfItem? {
        val id = record.text("id") ?: run {
            Log.d(TAG, "debug card dropped: record without id ${record.toString().take(200)}")
            return null
        }
        val attributes = record["attributes"] as? JsonObject ?: run {
            Log.d(TAG, "debug card dropped: $id has no attributes")
            return null
        }
        val name = attributes.text("name") ?: run {
            Log.d(TAG, "debug card dropped: $id has no name")
            return null
        }
        val url = attributes.text("url") ?: run {
            Log.d(TAG, "debug card dropped: $id ($name) has no url")
            return null
        }
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
