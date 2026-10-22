package com.music.amusic.data.stats

import com.music.amusic.data.YtMusicRepository
import com.music.amusic.data.model.Song
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.ConcurrentHashMap

/** Album-only dots: public plays, artist's top songs, then device history. */
object AlbumPopularTracks {
    private const val LIMIT = 3
    private const val CACHE_MS = 5 * 60_000L
    private data class Cached(val ids: Set<String>, val at: Long, val signature: List<Pair<String, Long?>>)
    private val cache = ConcurrentHashMap<String, Cached>()

    fun cached(albumId: String): Set<String>? = cache[albumId]
        ?.takeIf { System.currentTimeMillis() - it.at < CACHE_MS }?.ids

    private fun rankedCounts(songs: List<Song>): Set<String>? {
        if (songs.none { it.playCount != null }) return null
        // Unknown numbers never become zero and never get topped up from local plays.
        return songs.withIndex().filter { (it.value.playCount ?: 0L) > 0L }
            .sortedWith(compareByDescending<IndexedValue<Song>> { it.value.playCount ?: 0L }.thenBy { it.index })
            .map { it.value.videoId }.distinct().take(LIMIT).toSet()
    }

    suspend fun resolve(albumId: String, songs: List<Song>): Set<String> = withContext(Dispatchers.IO) {
        val signature = songs.map { it.videoId to it.playCount }
        rankedCounts(songs)?.let { return@withContext store(albumId, signature, it) }
        cache[albumId]?.takeIf {
            it.signature == signature && System.currentTimeMillis() - it.at < CACHE_MS
        }?.let { return@withContext it.ids }

        if (!albumId.startsWith("local:") && !albumId.startsWith("prerelease:")) {
            // Some library/local mappings omit the per-track counts; reread the album itself.
            val publicSongs = YtMusicRepository.browseSongs(albumId).getOrNull()?.songs.orEmpty()
            val counts = publicSongs.associate { it.videoId to it.playCount }
            rankedCounts(songs.map { it.copy(playCount = counts[it.videoId] ?: it.playCount) })
                ?.let { return@withContext store(albumId, signature, it) }

            // Keep only identical catalogue track ids, so another version of a song
            // on a different release cannot claim the album's dot.
            val artistId = songs.firstNotNullOfOrNull { it.artistId }
            val topSongs = artistId?.let { YtMusicRepository.artistPage(it).getOrNull()?.songs }.orEmpty()
            val albumIds = songs.mapTo(HashSet()) { it.videoId }
            val candidates = topSongs.filter { it.videoId in albumIds }.distinctBy { it.videoId }
            if (candidates.isNotEmpty()) {
                val ids = rankedCounts(candidates) ?: candidates.take(LIMIT).mapTo(LinkedHashSet()) { it.videoId }
                return@withContext store(albumId, signature, ids)
            }
        }

        // Last resort only. Rank the current album's ids, not every track on the device.
        val albumIds = songs.mapTo(HashSet()) { it.videoId }
        val plays = HashMap<String, Long>()
        val buckets = try {
            ListeningStats.exportAll()
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            emptyList()
        }
        buckets.forEach { bucket ->
            bucket.tracks.filter { it.id in albumIds && it.plays > 0 }.forEach {
                plays[it.id] = (plays[it.id] ?: 0L) + it.plays.toLong()
            }
        }
        // Album order resolves equal displayed counts; the cap remains exactly three.
        songs.withIndex().filter { (plays[it.value.videoId] ?: 0L) > 0L }
            .sortedWith(compareByDescending<IndexedValue<Song>> { plays[it.value.videoId] ?: 0L }.thenBy { it.index })
            .map { it.value.videoId }.distinct().take(LIMIT).toSet()
    }

    private fun store(albumId: String, signature: List<Pair<String, Long?>>, ids: Set<String>): Set<String> {
        cache[albumId] = Cached(ids, System.currentTimeMillis(), signature)
        return ids
    }
}
