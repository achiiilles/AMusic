package com.music.amusic.data

import com.music.amusic.data.model.SearchFilter
import com.music.amusic.data.model.SearchResult
import com.music.amusic.data.model.Song
import com.music.amusic.data.sources.TrackMatcher
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.withTimeoutOrNull
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Finds, on YouTube Music, the songs of an Apple Music playlist.
 *
 * An Apple playlist page lists its tracks by name and artist only, under ids
 * of the form `prerelease:<playlistId>:<n>` that nothing can play. Playing the
 * playlist therefore needs every track found first; the search and the pick
 * are the ones a Spotify import uses (see `SpotifyImporter.matchTrack`). A
 * track that was found is remembered, so a second play starts at once.
 */
object AppleTrackResolver {
    private const val PENDING_PREFIX = "prerelease:"
    private const val PARALLEL_SEARCHES = 10
    private const val SEARCH_TIMEOUT_MS = 8_000L

    private val found = ConcurrentHashMap<String, Song>()
    private val preparing = AtomicBoolean(false)

    /** Whether [song] is an Apple track that has not been matched to a playable one yet. */
    fun isPending(song: Song): Boolean = song.videoId.startsWith(PENDING_PREFIX)

    /** The Apple playlist id a queue source or page id names, or null when it names none. */
    fun appleIdOf(sourceId: String?): String? {
        if (sourceId == null) return null
        return when {
            sourceId.startsWith(PENDING_PREFIX) -> sourceId.removePrefix(PENDING_PREFIX).takeIf { it.isNotBlank() }
            sourceId.startsWith("local:playlist:apple_") ->
                sourceId.removePrefix("local:playlist:apple_").takeIf { it.isNotBlank() }
            else -> null
        }
    }

    /** True for the caller that gets to prepare a queue; a second tap meanwhile gets false. */
    fun tryBeginPreparing(): Boolean = preparing.compareAndSet(false, true)

    fun endPreparing() {
        preparing.set(false)
    }

    private fun keyOf(song: Song): String =
        song.title.trim().lowercase() + "|" + song.artist.trim().lowercase()

    /** The playable song for [pending], or null when YouTube Music has none. */
    suspend fun resolve(pending: Song): Song? {
        if (!isPending(pending)) return pending
        val key = keyOf(pending)
        found[key]?.let { return carryArtwork(it, pending) }
        val query = listOf(pending.title, pending.artist).filter { it.isNotBlank() }.joinToString(" ")
        if (query.isBlank()) return null
        val candidates = try {
            YtMusicRepository.search(query, SearchFilter.SONGS).getOrNull()
                ?.filterIsInstance<SearchResult.Track>()
                ?.map { it.song }
                .orEmpty()
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            emptyList()
        }
        val best = TrackMatcher.best(
            candidates,
            TrackMatcher.Target(title = pending.title, artist = pending.artist),
        ) ?: candidates.firstOrNull()
        if (best != null) found[key] = best
        return best?.let { carryArtwork(it, pending) }
    }

    private fun carryArtwork(song: Song, pending: Song): Song =
        if (song.thumbnailUrl.isNullOrBlank()) song.copy(thumbnailUrl = pending.thumbnailUrl) else song

    /**
     * Every song of [songs] as a playable one, in the same order. A track that
     * is already playable comes back as it is; one that could not be found, or
     * took too long, is null at its place.
     */
    suspend fun resolveAll(songs: List<Song>): List<Song?> = coroutineScope {
        val gate = Semaphore(PARALLEL_SEARCHES)
        songs.map { song ->
            async(Dispatchers.IO) {
                if (!isPending(song)) {
                    song
                } else {
                    gate.withPermit { withTimeoutOrNull(SEARCH_TIMEOUT_MS) { resolve(song) } }
                }
            }
        }.awaitAll()
    }
}
