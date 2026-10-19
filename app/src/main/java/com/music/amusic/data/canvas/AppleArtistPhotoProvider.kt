package com.music.amusic.data.canvas

import com.music.amusic.ui.components.ArtistPhotoProvider
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import java.text.Normalizer
import java.util.Locale

/**
 * The Apple Music photo for an artist, for every list in the app that shows one.
 *
 * It reuses [AppleArtistArtRepository], the lookup the library artist page
 * already makes, and keeps only a small picture URL per artist, so a list of
 * artists costs memory for strings rather than for pictures.
 *
 * Kept light on purpose: at most two lookups run at once, a lookup waits for
 * its turn inside the composable that asked for it (so scrolling past a row
 * cancels it before it starts), an answer "Apple has nobody by that name" is
 * remembered like any other, and a failed lookup is not retried for five
 * minutes. The YouTube picture is on screen the whole time.
 */
object AppleArtistPhotoProvider : ArtistPhotoProvider {

    private const val CACHE_SIZE = 400
    private const val NONE = ""
    private const val RETRY_AFTER_MS = 5 * 60 * 1000L
    private const val AVATAR_PX = 400

    private val gate = Semaphore(2)

    private val cache = object : LinkedHashMap<String, String>(CACHE_SIZE, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, String>) =
            size > CACHE_SIZE
    }
    private val failedAt = HashMap<String, Long>()

    override fun peek(artistName: String): String? {
        val key = artistName.keyOf()
        if (key.isEmpty()) return NONE
        synchronized(cache) { cache[key] }?.let { return it }
        AppleArtistArtRepository.cached(artistName)?.let { return remember(key, it) }
        val failed = synchronized(failedAt) { failedAt[key] }
        if (failed != null && System.currentTimeMillis() - failed < RETRY_AFTER_MS) return NONE
        return null
    }

    override suspend fun fetch(artistName: String): String? {
        val key = artistName.keyOf()
        if (key.isEmpty()) return NONE
        synchronized(cache) { cache[key] }?.let { return it }
        // Waiting for a permit is where a row that left the screen gives up.
        return gate.withPermit {
            synchronized(cache) { cache[key] }?.let { return@withPermit it }
            val art = AppleArtistArtRepository.artFor(artistName)
            if (art == null) {
                // No such artist on Apple and a network hiccup look the same here;
                // the first is cached by the repository, so a retry costs nothing.
                synchronized(failedAt) { failedAt[key] = System.currentTimeMillis() }
                NONE
            } else {
                remember(key, art)
            }
        }
    }

    private fun remember(key: String, art: AppleArtistArt): String {
        val url = art.heroUrl.asAvatar()
        synchronized(cache) { cache[key] = url }
        return url
    }

    /** The page's hero picture is 1200 px wide; a list row needs a fraction of that. */
    private fun String.asAvatar(): String =
        replace(Regex("/\\d+x\\d+bb\\.jpg$"), "/${AVATAR_PX}x${AVATAR_PX}bb.jpg")

    private fun String.keyOf(): String =
        Normalizer.normalize(lowercase(Locale.ROOT), Normalizer.Form.NFD)
            .filter { it.isLetterOrDigit() }
}
