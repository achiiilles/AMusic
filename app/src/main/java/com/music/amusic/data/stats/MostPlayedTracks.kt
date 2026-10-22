package com.music.amusic.data.stats

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.Locale

/**
 * The track each release is played most on this device, for the dot Apple Music
 * puts beside its number.
 *
 * ## Why the history and not the catalogue
 *
 * Apple Music's own album page carries a genre, a year, a label, a copyright
 * line and the sleeve's colours, and no per-track popularity of any kind — the
 * lookup this app already makes is in `AppleAlbumColorRepository`, and a
 * popularity figure is not among what it can return. YouTube Music's album
 * response does not rank its tracks either. So the only answer to "the one you
 * play most" that this app can honestly give is the listening it has counted
 * itself, which is the same history [ListeningStats] keeps and the Replay page
 * draws.
 *
 * ## One walk, shared
 *
 * Answering the question is a pass over every month on disk, so it is done
 * once and kept: every numbered row on the screen, and every release opened
 * after it, reads the same set. It is walked again only once the answer has had
 * time to go stale, which is what lets a track played a minute ago become the
 * dotted one the next time its album is opened.
 */
object MostPlayedTracks {

    private val _ids = MutableStateFlow<Set<String>>(emptySet())

    /** Ids of the tracks that top their release; empty until the first walk lands. */
    val ids: StateFlow<Set<String>> = _ids.asStateFlow()

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    @Volatile
    private var lastWalk = 0L

    private var walking: Job? = null

    /**
     * Walks the history again if the last walk is older than [STALE_AFTER_MS].
     *
     * Called as a release's numbered rows compose, because opening an album is
     * the one moment the answer is looked at — and a walk that only ever
     * happened at launch would still describe the listening from before the
     * track that just played.
     */
    fun refreshIfStale() {
        if (walking?.isActive == true) return
        val now = System.currentTimeMillis()
        if (lastWalk != 0L && now - lastWalk < STALE_AFTER_MS) return
        lastWalk = now
        walking = scope.launch {
            runCatching { walk() }.onSuccess { _ids.value = it }
        }
    }

    /**
     * The top track of every release with plays in it.
     *
     * A release whose top two tracks are level is left out: a tie has no most,
     * and dotting whichever of them the loop happened to reach first would be
     * inventing the answer rather than reading it.
     */
    private suspend fun walk(): Set<String> {
        // Reads every month off disk and flushes what is in memory first, so the
        // dot agrees with the track that has just been playing.
        val buckets = ListeningStats.exportAll()
        val playsByRelease = HashMap<String, HashMap<String, Int>>()
        buckets.forEach { bucket ->
            bucket.tracks.forEach { entry ->
                if (entry.plays <= 0) return@forEach
                val release = releaseKey(entry) ?: return@forEach
                val plays = playsByRelease.getOrPut(release) { HashMap() }
                plays[entry.id] = (plays[entry.id] ?: 0) + entry.plays
            }
        }
        val marks = HashSet<String>(playsByRelease.size)
        playsByRelease.values.forEach { plays ->
            val ranked = plays.entries.sortedByDescending { it.value }
            val top = ranked.firstOrNull() ?: return@forEach
            if (ranked.size > 1 && ranked[1].value == top.value) return@forEach
            marks += top.key
        }
        return marks
    }

    /**
     * How a track's release is identified: the catalogue's own id where the
     * history recorded one, else the name and the credit folded the way the
     * album chart folds them.
     */
    private fun releaseKey(entry: TrackEntry): String? {
        entry.albumId?.takeIf { it.isNotBlank() }?.let { return it }
        val album = entry.album?.trim()?.takeIf { it.isNotEmpty() } ?: return null
        return album.lowercase(Locale.ROOT) + RELEASE_KEY_SEPARATOR + entry.artist.lowercase(Locale.ROOT)
    }

    /**
     * ASCII 0x1F, the one character neither half of the key can contain — the
     * same separator `ListeningStats` joins names on, for the same reason.
     */
    private val RELEASE_KEY_SEPARATOR = Char(31).toString()

    /**
     * How long a walk is trusted. Short enough that the dot follows what has
     * been played since the album was last opened; long enough that flipping
     * through a shelf of releases does not walk the history once per page.
     */
    private const val STALE_AFTER_MS = 60_000L
}
