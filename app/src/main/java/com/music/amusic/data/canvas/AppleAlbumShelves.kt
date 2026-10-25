package com.music.amusic.data.canvas

import com.music.amusic.data.ApplePreRelease
import com.music.amusic.data.DebugLog as Log
import com.music.amusic.data.YtMusicRepository
import com.music.amusic.data.model.HomeShelf
import com.music.amusic.data.model.SearchFilter
import com.music.amusic.data.model.SearchResult
import com.music.amusic.data.model.ShelfItem
import java.util.concurrent.ConcurrentHashMap
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
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

    /** Limits only the Last.fm fallback; Apple's own shelves keep their existing limits. */
    private const val MAX_LASTFM_CARDS = 30
    private const val APPLE_ALBUMS_PER_SIMILAR_ARTIST = 2
    private const val MAX_LASTFM_APPLE_LOOKUPS = 6
    private val lastFmAppleGate = Semaphore(MAX_LASTFM_APPLE_LOOKUPS)

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
    private val boundAlbums = ConcurrentHashMap<String, AppleReleaseChoice>()

    /** Preserve the catalog id already established by an Apple card, including homonyms. */
    fun bindAlbum(browseId: String, target: AppleShelfTarget) {
        target.appleId.toLongOrNull()?.let { boundAlbums[browseId] = AppleReleaseChoice(target.title, target.artist, it) }
    }
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
                    if (it is CancellationException) throw it
                    Log.d(TAG, "shelves failed for $album: $it")
                    setNote(
                        browseId,
                        "A busca no Apple Music falhou (${it.javaClass.simpleName}: ${it.message.orEmpty().take(60)})",
                    )
                }
                .getOrNull()
        } ?: return null
        // A result without "Talvez você goste" is not kept: opening the page again asks again.
        if (shelves.any { it.title == "Talvez você goste" }) synchronized(cache) { cache[browseId] = shelves }
        return shelves
    }

    private suspend fun load(
        browseId: String,
        album: String,
        artist: String,
        trackCount: Int,
        year: String?,
        trackTitles: List<String>,
        onUpdate: ((List<HomeShelf>) -> Unit)?,
    ): List<HomeShelf>? = coroutineScope {
        val known = boundAlbums[browseId] ?: browseId.removePrefix("prerelease:").takeIf {
            browseId.startsWith("prerelease:") && it.isNotBlank() && it.all(Char::isDigit)
        }?.let { AppleReleaseChoice(album, artist, it.toLongOrNull()) }
        val choice = known ?: AppleReleaseMatcher.choose(album, artist, trackCount, year, trackTitles) ?: run {
            val fallback = lastFmRelated(artist, "") { cards ->
                if (cards.isNotEmpty()) onUpdate?.invoke(listOf(HomeShelf(title = "Talvez você goste", items = cards)))
            }
            if (fallback.isNotEmpty()) {
                setNote(browseId, null)
                return@coroutineScope listOf(HomeShelf(title = "Talvez você goste", items = fallback))
            }
            setNote(
                browseId,
                "Não consegui achar este álbum no Apple Music (artista não encontrado ou sem resposta da busca)\n" +
                    lastFmNotes[""].orEmpty(),
            )
            return@coroutineScope null
        }
        val albumId = choice.collectionId?.toString() ?: run {
            val fallback = lastFmRelated(choice.artistName, "") { cards ->
                if (cards.isNotEmpty()) onUpdate?.invoke(listOf(HomeShelf(title = "Talvez você goste", items = cards)))
            }
            if (fallback.isNotEmpty()) {
                setNote(browseId, null)
                return@coroutineScope listOf(HomeShelf(title = "Talvez você goste", items = fallback))
            }
            setNote(
                browseId,
                "Não achei este álbum entre os lançamentos de ${choice.artistName} no Apple Music\n" +
                    lastFmNotes[""].orEmpty(),
            )
            return@coroutineScope emptyList()
        }
        var artistName = choice.artistName
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
        lastFmNotes.remove(albumId)
        var useFallback = false
        var appleWins = false
        var fallbackPreview = emptyList<ShelfItem>()
        // Speculate beside the album request, not after Apple's empty-view retries.
        val lastFmJob = async(Dispatchers.IO) {
            try {
                lastFmRelated(choice.artistName, albumId) { cards ->
                    synchronized(previewLock) {
                        fallbackPreview = cards
                        if (useFallback && !appleWins) publish(2, cards)
                    }
                }
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { Log.d(TAG, "last.fm shelf failed: ${e.javaClass.simpleName}"); emptyList<ShelfItem>() }
        }
        fun enableFallback() {
            synchronized(previewLock) {
                useFallback = true
                if (!appleWins && fallbackPreview.isNotEmpty()) publish(2, fallbackPreview)
            }
        }
        suspend fun fallbackCards(): List<ShelfItem> {
            enableFallback()
            return lastFmJob.await()
        }
        fun publishApple(records: List<JsonObject>) {
            val cards = records.filter { it.text("id") != albumId }
                .take(MAX_PAGED_CARDS).mapNotNull { card(it, isAlbum = true) }
            if (cards.isEmpty()) return
            // One lock owns both sources. Any late fallback update is ignored after Apple wins.
            synchronized(previewLock) {
                appleWins = true
                useFallback = false
                publish(2, cards)
            }
            lastFmJob.cancel()
        }
        val body = AppleMusicCanvas.catalogGet(
            "albums/$albumId",
            mapOf("views" to "appears-on,you-might-also-like", "include" to "artists", "l" to "pt-BR"),
        ) ?: run {
            // The status comes from this thread's trace of the album request: the global
            // problem text is rewritten by the parallel Last.fm searches.
            val failedTrace = AppleMusicCanvas.catalogTrace()
            val failedCode = Regex("""; HTTP (\d{3})""").find(failedTrace)?.groupValues?.get(1)
            val problem = if (failedCode != null) "erro HTTP $failedCode" else catalogProblem()
            if (failedCode == "404") {
                // Apple refused the whole album request with 404: Last.fm still
                // gives the recommendations shelf. Any other failure is retried next time.
                val fallback = fallbackCards()
                if (fallback.isNotEmpty()) {
                    setNote(browseId, null)
                    return@coroutineScope listOf(HomeShelf(title = "Talvez você goste", items = fallback))
                }
            }
            lastFmJob.cancel()
            setNote(browseId, "A busca no Apple Music falhou ($problem)")
            return@coroutineScope null
        }
        val albumTrace = AppleMusicCanvas.catalogTrace()
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: run {
            val fallback = fallbackCards()
            if (fallback.isNotEmpty()) {
                setNote(browseId, null)
                return@coroutineScope listOf(HomeShelf(title = "Talvez você goste", items = fallback))
            }
            setNote(browseId, "A Apple respondeu sem dados deste álbum (HTTP 200, lista vazia)")
            return@coroutineScope emptyList()
        }
        val albumIdentity = "Escolhido pelo iTunes: $albumId (${choice.collectionName}), ${choice.artistName}; " +
            "Apple respondeu id=${record.text("id")}, tipo=${record.text("type")}, " +
            "nome=${(record["attributes"] as? JsonObject)?.text("name")}; loja=${AppleMusicCanvas.storefront}"
        val views = record["views"] as? JsonObject
        if (dataOf(views, "you-might-also-like").isEmpty()) enableFallback()
        Log.d(
            TAG,
            "debug related: album $albumId storefront ${AppleMusicCanvas.storefront}; " +
                "views in the album answer: ${views?.keys?.joinToString().orEmpty().ifEmpty { "none" }}; " +
                "you-might-also-like view: ${(views?.get("you-might-also-like") as? JsonObject)?.toString()?.take(400) ?: "absent"}",
        )
        val artistRecord = ((record["relationships"] as? JsonObject)?.get("artists") as? JsonObject)
            ?.get("data")?.jsonArray?.firstOrNull() as? JsonObject
        val artistId = artistRecord?.text("id")
        synchronized(previewLock) { artistName = (artistRecord?.get("attributes") as? JsonObject)?.text("name") ?: choice.artistName }

        // The three shelves are independent once the album answer is in, so they are
        // read at the same time instead of one after the other: the page waits for the
        // slowest of them, not for the sum. Each branch makes the same requests, in the
        // same order, as before; only the branches no longer wait for each other.
        // Publish each page before following continuations, with ordered snapshots.
        // The complete result alone enters the existing cache.
        val askNotes = mutableListOf<String>()
        val branches = coroutineScope {
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
                // Last.fm already runs beside the album request; Apple remains the preferred source.
                val relatedJob = async(Dispatchers.IO) {
                    var records = pagedView(
                        views,
                        "you-might-also-like",
                        "albums/$albumId/view/you-might-also-like",
                        askWhenEmpty = true,
                        notes = askNotes,
                        onPage = { records ->
                            publishApple(records)
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
                                publishApple(records)
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
                        cards = fallbackCards()
                        if (cards.isNotEmpty()) Log.d(TAG, "related for $albumId: ${cards.size} cards from Last.fm")
                    }
                    publish(2, cards)
                    Pair(records, cards)
                }
                Triple(moreJob.await(), appearsOnJob.await(), relatedJob.await())
        }
        // The speculative Last.fm request is over once the three branches are in.
        lastFmJob.cancel()
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
            setNote(browseId, "$reason\n$albumIdentity\nPedido do álbum: $albumTrace\n${lastFmNotes[albumId].orEmpty()}")
        }
        Log.d(TAG, "apple shelves for '$album': ${shelves.joinToString { "${it.title} (${it.items.size})" }}")
        return@coroutineScope shelves
    }

    /**
     * "Talvez você goste" built from the Last.fm similar artists with a match of at
     * least [LastFmSimilarAlbums.MIN_MATCH], most similar first. Each album must be
     * found on Apple Music with the same artist (name compared whole, never as a
     * substring) and the same title, and must be an original release: no
     * compilation, live, remix, soundtrack or tribute by name or by Apple genre.
     * The search runs in two phases. The first finds one album per artist, all at
     * the same time under [lastFmAppleGate]; the second looks for a different second
     * album per artist, and only while the shelf is short of [MAX_LASTFM_CARDS].
     * Only the fallback is capped. Empty without a Last.fm key; Apple's own
     * recommendations are unchanged.
     */
    private val lastFmNotes = ConcurrentHashMap<String, String>()

    private suspend fun lastFmRelated(
        artistName: String,
        currentAlbumId: String,
        onCards: (List<ShelfItem>) -> Unit = {},
    ): List<ShelfItem> = coroutineScope {
        if (!LastFmSimilarAlbums.available) {
            lastFmNotes[currentAlbumId] = "Last.fm: este build não tem a chave"
            return@coroutineScope emptyList<ShelfItem>()
        }
        val started = System.nanoTime()
        val ranked = LastFmSimilarAlbums.rankedFor(artistName)
        val similar = ranked.artists
        if (similar.isEmpty()) {
            lastFmNotes[currentAlbumId] =
                "Last.fm: nenhum artista parecido para ${ranked.tried.joinToString(" / ")} (${LastFmSimilarAlbums.diagnosis()})"
            return@coroutineScope emptyList<ShelfItem>()
        }
        val searches = ConcurrentHashMap<String, List<JsonObject>>()
        val candidates = similar.map { artist ->
            async<Pair<LastFmSimilarAlbums.SimilarArtist, AppleFind?>>(Dispatchers.IO) {
                try {
                    currentCoroutineContext().ensureActive()
                    val withAlbums = LastFmSimilarAlbums.albumsFor(artist)
                    val found = if (withAlbums.albums.isEmpty()) {
                        null
                    } else {
                        lastFmAppleGate.withPermit {
                            currentCoroutineContext().ensureActive()
                            findNextOnApple(withAlbums.name, withAlbums.albums, 0, emptySet(), searches)
                        }
                    }
                    Pair(withAlbums, found)
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    Log.d(TAG, "last.fm candidate failed: ${e.javaClass.simpleName}")
                    Pair<LastFmSimilarAlbums.SimilarArtist, AppleFind?>(artist, null)
                }
            }
        }
        val seen = mutableSetOf(currentAlbumId)
        val cards = mutableListOf<ShelfItem>()
        fun accept(find: AppleFind?) {
            if (find == null || cards.size >= MAX_LASTFM_CARDS) return
            val id = find.record.text("id") ?: return
            val key = releaseKey(find.record)
            if (id in seen || key in seen) return
            val item = card(find.record, isAlbum = true) ?: return
            seen += id
            seen += key
            cards += item
            if (cards.size == 1) Log.d(TAG, "last.fm first card after ${(System.nanoTime() - started) / 1_000_000} ms")
            onCards(cards.toList())
        }
        // Cards enter in score order as each artist's first album resolves, so the
        // shelf grows from the most similar artist without waiting for all of them.
        // Second albums come after, also in score order, so visible cards never reorder.
        try {
            val firsts = ArrayList<Pair<LastFmSimilarAlbums.SimilarArtist, AppleFind?>>()
            for (candidate in candidates) {
                currentCoroutineContext().ensureActive()
                val resolved = candidate.await()
                firsts += resolved
                accept(resolved.second)
                if (cards.size >= MAX_LASTFM_CARDS) break
            }
            if (cards.size < MAX_LASTFM_CARDS) {
                val seconds = firsts.map { (artist, first) ->
                    if (first == null) {
                        null
                    } else {
                        async<AppleFind?>(Dispatchers.IO) {
                            try {
                                lastFmAppleGate.withPermit {
                                    currentCoroutineContext().ensureActive()
                                    findNextOnApple(
                                        artist.name,
                                        artist.albums,
                                        first.next,
                                        setOf(first.record.text("id").orEmpty(), releaseKey(first.record)),
                                        searches,
                                    )
                                }
                            } catch (e: CancellationException) {
                                throw e
                            } catch (e: Exception) {
                                Log.d(TAG, "last.fm second album failed: ${e.javaClass.simpleName}")
                                null
                            }
                        }
                    }
                }
                try {
                    for (second in seconds) {
                        if (second == null) continue
                        accept(second.await())
                        if (cards.size >= MAX_LASTFM_CARDS) break
                    }
                } finally {
                    seconds.forEach { it?.cancel() }
                }
            }
        } finally {
            candidates.forEach { it.cancel() }
        }
        val elapsed = (System.nanoTime() - started) / 1_000_000
        lastFmNotes[currentAlbumId] =
            "Last.fm: ${similar.size} artistas parecidos (via ${ranked.used}), ${cards.size} cards em $elapsed ms " +
                "(${LastFmSimilarAlbums.diagnosis()})"
        Log.d(TAG, "last.fm shelf: ${similar.size} similar artists, ${cards.size} cards, $elapsed ms")
        cards.toList()
    }

    /** An Apple album found for a Last.fm artist, and where in its candidate list the search stopped. */
    private class AppleFind(val record: JsonObject, val next: Int)

    /** Artist and title of an Apple album, folded for comparison: the key that tells two editions apart from two albums. */
    private fun releaseKey(record: JsonObject): String {
        val attributes = record["attributes"] as? JsonObject
        return AppleReleaseMatcher.cleanTitle(attributes?.text("artistName").orEmpty()) + "|" +
            AppleReleaseMatcher.cleanTitle(attributes?.text("name").orEmpty())
    }

    /** True when the artist Apple credits is the artist Last.fm named: the whole name, not a part of it. */
    private fun sameArtist(credited: String, wanted: String): Boolean {
        val a = AppleReleaseMatcher.cleanTitle(credited)
        val b = AppleReleaseMatcher.cleanTitle(wanted)
        return if (a.isNotEmpty() && b.isNotEmpty()) {
            a == b
        } else {
            credited.isNotBlank() && credited.trim().equals(wanted.trim(), ignoreCase = true)
        }
    }

    /**
     * False for a compilation, live record, remix, soundtrack or tribute, judged by the
     * name and by Apple's genres. Apple's isCompilation flag is not used: the catalog
     * flags real releases with it (checked on Dangerous Woman's anniversary edition
     * and on a Holly Humberstone single).
     */
    private fun isOriginalRelease(attributes: JsonObject): Boolean {
        if (!LastFmSimilarAlbums.isOriginalReleaseName(attributes.text("name").orEmpty())) return false
        val genres = (attributes["genreNames"] as? JsonArray)
            ?.mapNotNull { (it as? JsonPrimitive)?.contentOrNull }
            .orEmpty()
        return genres.none { NOT_ORIGINAL_GENRE.containsMatchIn(it) }
    }

    private val NOT_ORIGINAL_GENRE = Regex("""soundtrack|trilha|karaok|tribut|cast recording|score""", RegexOption.IGNORE_CASE)
    private val EDITION_MARK = Regex(
        """\b(?:deluxe|expanded|edition|remaster(?:ed)?|anniversary|version|bonus|special|complete)\b""",
        RegexOption.IGNORE_CASE,
    )

    /** One catalog search for an album by artist and name, or null when the request failed. */
    private class SearchEntry(val hits: List<JsonObject>, val at: Long)
    private const val SEARCH_TTL_MS = 24L * 60 * 60 * 1000
    private val resolvedSearches = object : LinkedHashMap<String, SearchEntry>(256, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, SearchEntry>) = size > 256
    }

    private fun searchAlbums(artist: String, album: String): List<JsonObject>? {
        val key = "lastfm-apple-v1:${AppleMusicCanvas.storefront}:" +
            AppleReleaseMatcher.cleanTitle(artist) + "|" + AppleReleaseMatcher.cleanTitle(album)
        val now = System.currentTimeMillis()
        synchronized(resolvedSearches) { resolvedSearches[key] }?.takeIf { now - it.at < SEARCH_TTL_MS }?.let { return it.hits }
        val saved = AppleLookupStore.read(key, SEARCH_TTL_MS)?.let {
            runCatching { Json.parseToJsonElement(it).jsonArray.mapNotNull { row -> row as? JsonObject } }.getOrNull()
        }
        if (!saved.isNullOrEmpty()) {
            synchronized(resolvedSearches) { resolvedSearches[key] = SearchEntry(saved, now) }
            return saved
        }
        val body = AppleMusicCanvas.catalogGet(
            "search",
            mapOf("term" to "$artist $album", "types" to "albums", "limit" to "8", "l" to "pt-BR"),
        ) ?: return null
        val hits = runCatching {
            Json.parseToJsonElement(body).jsonObject["results"]?.jsonObject
                ?.get("albums")?.jsonObject?.get("data")?.jsonArray
        }.getOrNull().orEmpty().mapNotNull { it as? JsonObject }
        if (hits.isNotEmpty()) {
            synchronized(resolvedSearches) { resolvedSearches[key] = SearchEntry(hits, now) }
            AppleLookupStore.write(key, JsonArray(hits).toString())
        }
        return hits
    }

    /**
     * The next Apple Music album for a Last.fm (artist, candidate albums) pair, trying
     * the candidates from index [from]. A hit needs the same artist, the same title
     * (edition suffixes ignored) and an original release, and must not be in [taken]
     * (ids and artist|title keys). The edition without "deluxe" or "edition" in its
     * name is preferred. A candidate with no such hit is skipped: no other album of
     * the artist takes its place. Searches are shared through [searches].
     */
    private fun findNextOnApple(
        similarArtist: String,
        albums: List<String>,
        from: Int,
        taken: Set<String>,
        searches: ConcurrentHashMap<String, List<JsonObject>>,
    ): AppleFind? {
        val wantArtist = AppleReleaseMatcher.cleanTitle(similarArtist)
        if (wantArtist.isEmpty()) return null
        for (index in from until albums.size) {
            val album = albums[index]
            val wantAlbum = AppleReleaseMatcher.cleanTitle(album)
            val searchKey = "$wantArtist|$wantAlbum"
            val hits = searches[searchKey]
                ?: (searchAlbums(similarArtist, album) ?: continue).also { searches[searchKey] = it }
            val matches = hits.filter { hit ->
                val attributes = hit["attributes"] as? JsonObject ?: return@filter false
                val id = hit.text("id") ?: return@filter false
                sameArtist(attributes.text("artistName").orEmpty(), similarArtist) &&
                    AppleReleaseMatcher.cleanTitle(attributes.text("name").orEmpty()) == wantAlbum &&
                    isOriginalRelease(attributes) &&
                    id !in taken &&
                    releaseKey(hit) !in taken
            }
            val best = matches.sortedBy { hit ->
                if (EDITION_MARK.containsMatchIn((hit["attributes"] as? JsonObject)?.text("name").orEmpty())) 1 else 0
            }.firstOrNull() ?: continue
            return AppleFind(best, index + 1)
        }
        return null
    }

    /**
     * Up to two distinct Apple Music albums for a Last.fm (artist, albums) pair,
     * found one after the other with [findNextOnApple]. Kept for callers that want
     * both albums of one artist at once; the shelf itself searches in two phases.
     */
    private fun findOnApple(similarArtist: String, albums: List<String>): List<JsonObject> {
        val searches = ConcurrentHashMap<String, List<JsonObject>>()
        val found = mutableListOf<JsonObject>()
        val taken = mutableSetOf<String>()
        var from = 0
        while (found.size < APPLE_ALBUMS_PER_SIMILAR_ARTIST) {
            val next = findNextOnApple(similarArtist, albums, from, taken, searches) ?: break
            found += next.record
            taken += next.record.text("id").orEmpty()
            taken += releaseKey(next.record)
            from = next.next
        }
        return found
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
        val ownName = (record["attributes"] as? JsonObject)?.text("name")
        val pageLock = Any()
        val pageRecords = mutableMapOf<String, List<JsonObject>>()
        fun artistCards(records: List<JsonObject>): List<ShelfItem> = records
            .filter { it.text("id") != currentAlbumId }
            .distinctBy { it.text("id") }
            .sortedByDescending { (it["attributes"] as? JsonObject)?.text("releaseDate").orEmpty() }
            .take(MAX_PAGED_CARDS)
            .mapNotNull { card(it, isAlbum = true, ownArtist = ownName) }
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
            .mapNotNull { card(it, isAlbum = true, ownArtist = ownName) }
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
            ) ?: AppleMusicCanvas.catalogGet(viewPath, mapOf("offset" to offset, "l" to "pt-BR"))
                ?: break
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

    /**
     * One Apple card. For an album, single or EP the title is Apple's name without
     * its trailing " - Single" or " - EP" (the type moves to the line under it, as
     * YouTube Music draws it), and the line under it is "Single • 2025" on the
     * artist's own shelf ([ownArtist] is that artist) or "Single • Artista" on a
     * shelf of other artists. The card is built from the record alone, so no
     * request is added; the YouTube Music album is only searched when it is tapped.
     */
    private fun card(record: JsonObject, isAlbum: Boolean, ownArtist: String? = null): ShelfItem? {
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
        val shownTitle = if (isAlbum) ApplePreRelease.displayTitle(name) else name
        val onOwnShelf = isAlbum && !ownArtist.isNullOrBlank() &&
            subtitle.normalizeForMatch().contains(ownArtist.normalizeForMatch())
        val shownSubtitle = when {
            !isAlbum -> subtitle
            onOwnShelf -> releaseLine
            else -> listOf(kind, subtitle).filter { it.isNotBlank() }.joinToString(" • ")
        }
        targets[key] = AppleShelfTarget(key, shownTitle, subtitle, url, isAlbum, releaseLine)
        return ShelfItem(
            title = shownTitle,
            subtitle = shownSubtitle,
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
        val artistKey = target.artist.substringBefore(",").substringBefore("&").normalizeForMatch()
        val found = hits.firstNotNullOfOrNull { hit ->
            val item = (hit as? SearchResult.Browse)?.item ?: return@firstNotNullOfOrNull null
            when {
                !item.browseId.startsWith("MPRE") -> null
                AppleReleaseMatcher.cleanTitle(item.title) != want -> null
                artistKey.isNotEmpty() && !item.subtitle.normalizeForMatch().contains(artistKey) -> null
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
