package com.music.amusic.data.canvas

import com.music.amusic.BuildConfig
import com.music.amusic.data.DebugLog as Log
import com.music.amusic.data.Http
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.runBlocking
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
    private const val SIMILAR_ARTISTS = 10
    private const val ALBUMS_PER_ARTIST = 3

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    /** A similar artist and its top albums, most listened first. */
    class SimilarArtist(val name: String, val albums: List<String>)

    /** True when this build carries a Last.fm key. */
    val available: Boolean
        get() = BuildConfig.LASTFM_API_KEY.isNotBlank()

    /**
     * About ten artists similar to [artist] (artist.getSimilar), each with its
     * top albums (artist.getTopAlbums). Empty without a key or without an
     * answer. Blocks the calling thread, so call it from a background thread.
     */
    fun similarTo(artist: String): List<SimilarArtist> {
        if (!available || artist.isBlank()) return emptyList()
        val names = call(
            "artist.getsimilar",
            mapOf("artist" to artist, "limit" to SIMILAR_ARTISTS.toString(), "autocorrect" to "1"),
        )?.let { (it["similarartists"] as? JsonObject)?.get("artist") as? JsonArray }
            .orEmpty()
            .mapNotNull { (it as? JsonObject)?.text("name") }
            .filter { !it.equals(artist, ignoreCase = true) }
            .distinct()
            .take(SIMILAR_ARTISTS)
        Log.d(TAG, "similar artists for '$artist': ${names.size}")
        if (names.isEmpty()) return emptyList()
        return runBlocking {
            coroutineScope {
                names.map { name ->
                    async(Dispatchers.IO) { SimilarArtist(name, topAlbums(name)) }
                }.awaitAll()
            }
        }.filter { it.albums.isNotEmpty() }
    }

    private fun topAlbums(artist: String): List<String> =
        call(
            "artist.gettopalbums",
            mapOf("artist" to artist, "limit" to "6", "autocorrect" to "1"),
        )?.let { (it["topalbums"] as? JsonObject)?.get("album") as? JsonArray }
            .orEmpty()
            .mapNotNull { (it as? JsonObject)?.text("name") }
            .filter { !it.equals("(null)", ignoreCase = true) }
            .distinct()
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
