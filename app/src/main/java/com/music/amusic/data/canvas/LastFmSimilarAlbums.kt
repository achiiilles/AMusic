package com.music.amusic.data.canvas

import com.music.amusic.BuildConfig
import com.music.amusic.data.DebugLog as Log
import com.music.amusic.data.Http
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import okhttp3.HttpUrl.Companion.toHttpUrl
import java.util.concurrent.atomic.AtomicInteger
import okhttp3.Request

/**
 * Similar artists from Last.fm, each with the albums Last.fm lists first for
 * it: the raw material of the "Talvez você goste" shelf when Apple has no
 * recommendations for an album (its you-might-also-like view answers 404).
 *
 * The Last.fm key is never in the source. It comes from BuildConfig.LASTFM_API_KEY,
 * which the build fills from the GitHub Actions secret LASTFM_API_KEY. A build
 * without the secret has an empty key, [available] is false, and the shelf is
 * simply not drawn from Last.fm. Nothing here logs the key or a request URL.
 */
object LastFmSimilarAlbums {
    private const val TAG = "LastFmSimilarAlbums"
    private const val ENDPOINT = "https://ws.audioscrobbler.com/2.0/"
    private const val SIMILAR_ARTISTS = 40

    /** Repeats after HTTP 429 or Last.fm error 29, each after a short pause. */
    private const val MAX_RETRIES = 2

    /**
     * Candidate albums kept per artist after the name filter and the dedupe, so a
     * bad first listing (remix, live, soundtrack) does not leave an artist empty.
     */
    private const val ALBUMS_PER_ARTIST = 4

    /** Top albums asked of Last.fm per artist, before the filter and the dedupe. */
    private const val TOP_ALBUMS_ASKED = 12

    /**
     * Lowest Last.fm similarity (the "match" field of artist.getSimilar, 0 to 1)
     * an artist needs to enter the shelf. This is the app's own cut-off, chosen
     * from the scores Last.fm returned for Olivia Rodrigo (the tail of the 40
     * artists sits between 0.25 and 0.30); it is a ranking score, not a probability.
     */
    const val MIN_MATCH = 0.25

    /** Top-album lookups in flight at once, shared across concurrent album pages. */
    private const val MAX_CONCURRENT_CALLS = 6
    private val topAlbumsGate = Semaphore(MAX_CONCURRENT_CALLS)

    private val rateLimited = AtomicInteger()
    private val failedCalls = AtomicInteger()
    @Volatile private var lastError = ""

    /** What Last.fm answered since the app opened, for the note on a page without the shelf. */
    fun diagnosis(): String =
        "respostas 429 desde que o app abriu: ${rateLimited.get()}; outras falhas: ${failedCalls.get()}; " +
            "último erro: ${lastError.ifEmpty { "nenhum" }}"

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    /**
     * A similar artist, its Last.fm [match] (0 to 1) and its candidate albums,
     * most listened first.
     */
    class SimilarArtist(val name: String, val albums: List<String>, val match: Double = 0.0)

    /**
     * Name markers of releases that are not an artist's own studio album or
     * single: live recordings, compilations, remixes, soundtracks, tributes and
     * similar. Each marker is bounded, so "Live Forever", "Alive" or
     * "Where We Live" are not caught.
     */
    private val NOT_ORIGINAL_MARKERS = listOf(
        """(?:[(\[:,]\s*|\s-\s+)live(?=$|[\s)\]\-:,!.?/])""",
        """\blive\s+(?:at|from|in|on|with|session|sessions|recording|recorded|album|version|tour|performance)\b""",
        """\bunplugged\b""", """\bin concert\b""",
        """\b(?:greatest|biggest|very best|ultimate|essential|essentials|definitive|platinum|gold)\s+(?:hits|collection|of|recordings|singles)\b""",
        """\bbest of\b""", """\bthe very best\b""", """\bhits\s+(?:vol|volume|\d)""", """^hits$""",
        """\bsingles\s+collection\b""", """\bcollection\b""", """\banthology\b""", """\bcompilation\b""",
        """\bremix(?:es|ed)?\b""", """\brmx\b""", """\bsoundtrack\b""", """\bost\b""",
        """\boriginal (?:motion picture|score|cast|series|television|broadway|film)\b""",
        """\bmusic from\b""", """\binspired by\b""", """\b(?:film|motion picture) score\b""",
        """\btribute\b""", """\btributo\b""", """\bkaraoke\b""", """\binstrumentals?\b""",
        """\bdemos?\b""", """\bb-?sides\b""", """\brarities\b""", """\bbootleg\b""",
        """\bsped up\b""", """\bslowed\b""", """\blullaby renditions\b""", """\bstring quartet\b""",
        """\bmade famous by\b""", """\boriginally performed\b""", """\bin the style of\b""",
    ).map { Regex(it, RegexOption.IGNORE_CASE) }

    /** False for a release name that carries one of the [NOT_ORIGINAL_MARKERS]. */
    fun isOriginalReleaseName(name: String): Boolean =
        NOT_ORIGINAL_MARKERS.none { it.containsMatchIn(name) }

    /** True when this build carries a Last.fm key. */
    val available: Boolean
        get() = BuildConfig.LASTFM_API_KEY.isNotBlank()

    /** Similar artists found for a credit, the artist name that produced them, and every name tried. */
    class Ranked(val artists: List<SimilarArtist>, val used: String?, val tried: List<String>)

    private val CREDIT_SPLIT = Regex("""\s*[,&/;]\s*|\s+(?:and|e|x|feat\.?|ft\.?|with|com|part\.?)\s+""", RegexOption.IGNORE_CASE)

    /** The credit as written, then each artist inside it ("A2O, A2O LITE" gives the whole text, A2O and A2O LITE). */
    fun creditNames(credit: String): List<String> {
        val whole = credit.trim()
        val parts = whole.split(CREDIT_SPLIT).map { it.trim() }.filter { it.isNotEmpty() }
        return (listOf(whole) + parts).filter { it.isNotEmpty() }.distinctBy { AppleReleaseMatcher.cleanTitle(it) }
    }

    /**
     * Similar artists for a credit that may name several artists. Each name is
     * tried in turn and the first one that returns artists wins; every credited
     * artist is left out of the result. Blocks the calling thread.
     */
    fun rankedFor(credit: String): Ranked {
        val names = creditNames(credit)
        if (!available || names.isEmpty()) return Ranked(emptyList(), null, names)
        val excluded = names.map { AppleReleaseMatcher.cleanTitle(it) }.toSet()
        val tried = mutableListOf<String>()
        for (name in names) {
            tried += name
            val found = rankedForName(name, excluded)
            if (found.isNotEmpty()) return Ranked(found, name, tried)
        }
        return Ranked(emptyList(), null, tried)
    }

    fun rankedArtists(artist: String): List<SimilarArtist> = rankedFor(artist).artists

    /**
     * Up to forty artists similar to [artist] (artist.getSimilar) whose Last.fm
     * match is at least [MIN_MATCH], highest match first, each with up to four
     * candidate albums (artist.getTopAlbums, name-filtered and deduplicated).
     * Empty without a key or without an answer. Blocks the calling thread, so
     * call it from a background thread.
     */
    private fun rankedForName(artist: String, excluded: Set<String>): List<SimilarArtist> {
        if (!available || artist.isBlank()) return emptyList()
        val similar = call(
            "artist.getsimilar",
            mapOf("artist" to artist, "limit" to SIMILAR_ARTISTS.toString(), "autocorrect" to "1"),
        )?.let { (it["similarartists"] as? JsonObject)?.get("artist") as? JsonArray }
            .orEmpty()
            .mapNotNull { element ->
                val entry = element as? JsonObject ?: return@mapNotNull null
                val name = entry.text("name") ?: return@mapNotNull null
                val match = entry.text("match")?.toDoubleOrNull()
                    ?.takeIf { it.isFinite() && it in 0.0..1.0 }
                    ?: return@mapNotNull null
                name to match
            }
            .filter { (name, _) -> AppleReleaseMatcher.cleanTitle(name) !in excluded }
            .distinctBy { (name, _) -> AppleReleaseMatcher.cleanTitle(name) }
            .filter { (_, match) -> match >= MIN_MATCH }
            .sortedByDescending { (_, match) -> match }
            .take(SIMILAR_ARTISTS)
        Log.d(TAG, "similar artists for '$artist' with match >= $MIN_MATCH: ${similar.size}")
        if (similar.isEmpty()) return emptyList()
        return similar.map { (name, match) -> SimilarArtist(name, emptyList(), match) }
    }

    /** Compatibility entry point; the shelf consumes ranked/top stages separately. */
    fun similarTo(artist: String): List<SimilarArtist> = runBlocking {
        coroutineScope {
            rankedArtists(artist).map { candidate ->
                async(Dispatchers.IO) { albumsFor(candidate) }
            }.awaitAll().filter { it.albums.isNotEmpty() }
        }
    }

    /** Shared gate across pages, with no batch barrier between Last.fm and Apple. */
    suspend fun albumsFor(candidate: SimilarArtist): SimilarArtist = topAlbumsGate.withPermit {
        currentCoroutineContext().ensureActive()
        SimilarArtist(candidate.name, topAlbums(candidate.name), candidate.match)
    }

    private fun topAlbums(artist: String): List<String> =
        call(
            "artist.gettopalbums",
            mapOf("artist" to artist, "limit" to TOP_ALBUMS_ASKED.toString(), "autocorrect" to "1"),
        )?.let { (it["topalbums"] as? JsonObject)?.get("album") as? JsonArray }
            .orEmpty()
            .mapNotNull { (it as? JsonObject)?.text("name") }
            .filter { !it.equals("(null)", ignoreCase = true) && isOriginalReleaseName(it) }
            .distinctBy { AppleReleaseMatcher.cleanTitle(it) }
            .take(ALBUMS_PER_ARTIST)

    private const val RESPONSE_TTL_MS = 6L * 60 * 60 * 1000
    private class ResponseEntry(val root: JsonObject, val at: Long)
    private val responses = object : LinkedHashMap<String, ResponseEntry>(256, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, ResponseEntry>) = size > 256
    }

    /** Successful responses only; no API key on disk, and no cached transient failure. */
    private fun call(method: String, params: Map<String, String>): JsonObject? {
        if (!available) return null
        val cacheKey = "lastfm-shelf-v1:$method:" + params.toSortedMap().entries.joinToString("|") { "${it.key}=${it.value}" }
        val now = System.currentTimeMillis()
        synchronized(responses) { responses[cacheKey] }?.takeIf { now - it.at < RESPONSE_TTL_MS }?.let { return it.root }
        val saved = AppleLookupStore.read(cacheKey, RESPONSE_TTL_MS)
            ?.let { runCatching { json.parseToJsonElement(it) as? JsonObject }.getOrNull() }
        if (saved != null) {
            synchronized(responses) { responses[cacheKey] = ResponseEntry(saved, now) }
            return saved
        }
        val loaded = callNetwork(method, params) ?: return null
        synchronized(responses) { responses[cacheKey] = ResponseEntry(loaded, now) }
        AppleLookupStore.write(cacheKey, loaded.toString())
        return loaded
    }

    private fun callNetwork(method: String, params: Map<String, String>): JsonObject? {
        val key = BuildConfig.LASTFM_API_KEY.trim()
        if (key.isEmpty()) return null
        val url = ENDPOINT.toHttpUrl().newBuilder().apply {
            addQueryParameter("method", method)
            params.forEach { (name, value) -> addQueryParameter(name, value) }
            addQueryParameter("api_key", key)
            addQueryParameter("format", "json")
        }.build()
        val request = Request.Builder().url(url).header("User-Agent", "AMusic").build()
        // Up to MAX_RETRIES short repeats, each after a longer pause. A Retry-After
        // above a second and a half ends this call rather than holding the shelf.
        for (attempt in 0..MAX_RETRIES) {
            var retryAfterMs: Long? = null
            val answer = runCatching {
                Http.client.newCall(request).execute().use { response ->
                    if (response.code == 429) {
                        Log.d(TAG, "$method: HTTP 429, attempt ${attempt + 1}")
                        rateLimited.incrementAndGet()
                        lastError = "HTTP 429"
                        val seconds = response.header("Retry-After")?.toLongOrNull()
                        retryAfterMs = if (seconds == null) 400L else seconds.coerceIn(0, 60) * 1000L
                        null
                    } else if (!response.isSuccessful) {
                        Log.d(TAG, "$method: HTTP ${response.code}")
                        failedCalls.incrementAndGet()
                        lastError = "HTTP ${response.code}"
                        null
                    } else {
                        val root = response.body?.string()?.let { json.parseToJsonElement(it) as? JsonObject }
                        if (root != null && root.containsKey("error")) {
                            Log.d(TAG, "$method: Last.fm error ${root.text("error")}")
                            lastError = "Last.fm erro ${root.text("error")}"
                            if (root.text("error") == "29") {
                                rateLimited.incrementAndGet()
                                retryAfterMs = 400L
                            }
                            null
                        } else root
                    }
                }
            }.onFailure {
                Log.d(TAG, "$method failed: ${it.javaClass.simpleName}")
                failedCalls.incrementAndGet()
                lastError = it.javaClass.simpleName
            }.getOrNull()
            if (answer != null) return answer
            val pause = retryAfterMs ?: return null
            if (attempt == MAX_RETRIES || pause > 1500L) return null
            Thread.sleep((pause * (attempt + 1)).coerceAtLeast(200L))
        }
        return null
    }

    private fun JsonObject.text(key: String): String? =
        (this[key] as? JsonPrimitive)?.contentOrNull?.trim()?.takeIf { it.isNotBlank() }
}
