package com.music.amusic.data.canvas

import com.music.amusic.BuildConfig
import com.music.amusic.data.DebugLog as Log
import com.music.amusic.data.Http
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

    /**
     * Up to forty artists similar to [artist] (artist.getSimilar) whose Last.fm
     * match is at least [MIN_MATCH], highest match first, each with up to four
     * candidate albums (artist.getTopAlbums, name-filtered and deduplicated).
     * Empty without a key or without an answer. Blocks the calling thread, so
     * call it from a background thread.
     */
    fun similarTo(artist: String): List<SimilarArtist> {
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
            .filter { (name, _) ->
                AppleReleaseMatcher.cleanTitle(name) != AppleReleaseMatcher.cleanTitle(artist)
            }
            .distinctBy { (name, _) -> AppleReleaseMatcher.cleanTitle(name) }
            .filter { (_, match) -> match >= MIN_MATCH }
            .sortedByDescending { (_, match) -> match }
            .take(SIMILAR_ARTISTS)
        Log.d(TAG, "similar artists for '$artist' with match >= $MIN_MATCH: ${similar.size}")
        if (similar.isEmpty()) return emptyList()
        return runBlocking {
            coroutineScope {
                similar.map { (name, match) ->
                    async(Dispatchers.IO) {
                        topAlbumsGate.withPermit { SimilarArtist(name, topAlbums(name), match) }
                    }
                }.awaitAll()
            }
        }.filter { it.albums.isNotEmpty() }
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

    private fun call(method: String, params: Map<String, String>): JsonObject? {
        val key = BuildConfig.LASTFM_API_KEY.trim()
        if (key.isEmpty()) return null
        val url = ENDPOINT.toHttpUrl().newBuilder().apply {
            addQueryParameter("method", method)
            params.forEach { (name, value) -> addQueryParameter(name, value) }
            addQueryParameter("api_key", key)
            addQueryParameter("format", "json")
        }.build()
        val request = Request.Builder().url(url).header("User-Agent", "AMusic").build()
        return runCatching {
            Http.client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    Log.d(TAG, "$method: HTTP ${response.code}")
                    null
                } else {
                    val root = response.body?.string()
                        ?.let { json.parseToJsonElement(it) as? JsonObject }
                    if (root != null && root.containsKey("error")) {
                        Log.d(TAG, "$method: Last.fm error ${root.text("error")}")
                        null
                    } else {
                        root
                    }
                }
            }
        }.onFailure {
            Log.d(TAG, "$method failed: ${it.javaClass.simpleName}")
        }.getOrNull()
    }

    private fun JsonObject.text(key: String): String? =
        (this[key] as? JsonPrimitive)?.contentOrNull?.trim()?.takeIf { it.isNotBlank() }
}
