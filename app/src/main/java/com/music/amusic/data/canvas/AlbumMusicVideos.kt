package com.music.amusic.data.canvas

import com.music.amusic.data.DebugLog as Log
import com.music.amusic.data.YtMusicRepository
import com.music.amusic.data.model.HomeShelf
import com.music.amusic.data.model.SearchFilter
import com.music.amusic.data.model.SearchResult
import com.music.amusic.data.model.ShelfItem
import com.music.amusic.data.model.Song
import com.music.amusic.data.model.durationMillis
import java.text.Normalizer
import java.util.Locale
import kotlin.coroutines.cancellation.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.withContext

/**
 * The "Videoclipes" section of an album page, found by searching YouTube.
 *
 * YouTube Music does not send an album's music videos with the album, so each
 * track is looked up on its own: "artista + faixa + official video", in the
 * Videos tab. A hit is kept only when it looks like the official clip of that
 * very track: the title holds the track's name, the credit is the album's
 * artist, the length is near the track's, and it is not a lyric video, an
 * audio upload, a live recording, a visualizer, a cover, a remix or a reaction.
 * The page draws nothing when no track has one.
 *
 * Nothing here has run against a real YouTube answer yet.
 */
object AlbumMusicVideos {
    const val TITLE = "Videoclipes"
    private const val TAG = "AlbumMusicVideos"
    private const val MAX_TRACKS = 25
    private const val PARALLEL = 3
    private const val CACHE_SIZE = 64
    private const val MAX_ROWS_PER_SEARCH = 8

    /** A clip may run this much shorter or longer than the album track (intro, outro, skit). */
    private const val SHORTER_MS = 20_000L
    private const val LONGER_MS = 60_000L

    /** An empty list means the album was searched and no clip was found. */
    private val cache = object : LinkedHashMap<String, List<HomeShelf>>(CACHE_SIZE, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, List<HomeShelf>>) =
            size > CACHE_SIZE
    }

    /** Words that mark an upload as something other than the official clip. */
    private val REJECT = listOf(
        "lyrics?", "lyric video", "letras?", "audio", "visuali[sz]er", "live", "ao vivo", "en vivo",
        "cover", "reaction", "karaoke", "instrumental", "8d", "slowed", "sped up", "nightcore",
        "behind the scenes", "making of", "teaser", "trailer", "snippet", "preview", "remix",
        "acoustic", "session", "concert", "performance", "tutorial", "vevo presents",
        "studio", "rehearsal", "ensaio", "fan[ -]?made", "unofficial", "documentary",
    ).map { Regex("""\b$it\b""") }

    private val OFFICIAL = Regex(
        """\bofficial\b.*\b(video|music video|clip)\b|\b(videoclipe|v[ií]deo oficial|clipe oficial|video oficial)\b|\bofficial mv\b""",
    )

    private val CREDIT_SPLIT = Regex("""\s*(?:,|&|;|\bfeat\b\.?|\bft\b\.?)\s*""", RegexOption.IGNORE_CASE)

    /** What is known for the page without a request. */
    fun cached(browseId: String): List<HomeShelf> = synchronized(cache) { cache[browseId] }.orEmpty()

    /**
     * The section for an album page. Null means nothing could be settled (every
     * search failed) and is tried again next time; an empty list means YouTube
     * answered and has no clip to show. Answers are kept per album.
     */
    suspend fun clipsFor(browseId: String, albumArtist: String, tracks: List<Song>): List<HomeShelf>? {
        if (browseId.isBlank() || tracks.isEmpty()) return null
        synchronized(cache) { cache[browseId] }?.let { return it }
        val clips = withContext(Dispatchers.IO) {
            try {
                load(albumArtist, tracks)
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (error: Throwable) {
                Log.d(TAG, "clips failed for $browseId: $error")
                null
            }
        } ?: return null
        synchronized(cache) { cache[browseId] = clips }
        return clips
    }

    private class Answer(val clip: Song?)

    private suspend fun load(albumArtist: String, tracks: List<Song>): List<HomeShelf>? {
        val wanted = tracks
            .filter { it.videoId.isNotBlank() && !it.videoId.startsWith("prerelease:") }
            .filter { core(it.title).isNotEmpty() }
            .distinctBy { core(it.title) }
            .take(MAX_TRACKS)
        if (wanted.isEmpty()) return emptyList()
        val gate = Semaphore(PARALLEL)
        val answers = coroutineScope {
            wanted.map { track ->
                async {
                    gate.withPermit {
                        val artist = creditFor(albumArtist, track)
                        val rows = YtMusicRepository
                            .search("$artist ${track.title} official video", SearchFilter.VIDEOS)
                            .getOrNull()
                        rows?.let { Answer(pick(it, track, artist)) }
                    }
                }
            }.awaitAll()
        }
        if (answers.all { it == null }) return null
        val items = LinkedHashMap<String, ShelfItem>()
        for (answer in answers) {
            val clip = answer?.clip ?: continue
            items.putIfAbsent(
                clip.videoId,
                ShelfItem(
                    title = clip.title,
                    subtitle = clip.artist,
                    thumbnailUrl = clip.thumbnailUrl,
                    videoId = clip.videoId,
                    browseId = null,
                    explicit = clip.isExplicit == true,
                    wide = true,
                ),
            )
        }
        Log.d(TAG, "clips: ${items.size} of ${wanted.size} tracks")
        return if (items.isEmpty()) emptyList() else listOf(HomeShelf(title = TITLE, items = items.values.toList()))
    }

    /** The artist to search for: the album's, or the track's own on a compilation. */
    private fun creditFor(albumArtist: String, track: Song): String {
        val album = albumArtist.trim()
        return if (album.isEmpty() || core(album).contains("various")) track.artist else album
    }

    /** The one search row that is this track's official clip, or null. */
    private fun pick(rows: List<SearchResult>, track: Song, artist: String): Song? {
        val wantTitle = core(track.title)
        val wantArtist = compact(core(artist.split(CREDIT_SPLIT).first()))
        val ownTitle = track.title.lowercase(Locale.ROOT)
        val trackMs = track.durationMillis()
        var best: Song? = null
        var bestScore = 0
        for (row in rows.take(MAX_ROWS_PER_SEARCH)) {
            val song = when (row) {
                is SearchResult.Track -> row.song
                is SearchResult.TopTrack -> row.song
                else -> null
            } ?: continue
            if (song.videoId == track.videoId || !song.isVideo) continue

            val title = song.title.lowercase(Locale.ROOT)
            // A word that is part of the track's own name does not count against it.
            if (REJECT.any { it.containsMatchIn(title) && !it.containsMatchIn(ownTitle) }) continue

            val got = core(song.title)
            if (got.isEmpty() || !" $got ".contains(" $wantTitle ")) continue

            val credits = listOf(song.artist) + song.artists.map { it.name }
            val sameArtist = wantArtist.isNotEmpty() && credits.any { credit ->
                val have = compact(core(credit))
                have.length >= 3 && (have.contains(wantArtist) || wantArtist.contains(have))
            }
            if (!sameArtist) continue

            val songMs = song.durationMillis()
            if (trackMs > 0 && songMs > 0) {
                val delta = songMs - trackMs
                if (delta < -SHORTER_MS || delta > LONGER_MS) continue
            }

            // A linked artist on its own only means the row named that performer:
            // fan uploads may also credit them. Match the album track's actual
            // channel, or a linked VEVO channel whose name exactly fits the artist.
            // A label in the title cannot make a third-party upload official.
            val channel = compact(core(song.artist.split(CREDIT_SPLIT).first()))
            val artistChannel = channel == wantArtist && track.artistId != null &&
                song.artistId == track.artistId
            val vevoChannel = channel == "${wantArtist}vevo" && song.artistId != null
            if (!artistChannel && !vevoChannel) continue
            val official = OFFICIAL.containsMatchIn(title)
            // Untagged videos need the same verified channel and an exact track
            // name after removing the channel prefix, never merely a search hit.
            if (!official && got != wantTitle && got != "$wantArtist $wantTitle".trim()) continue

            var score = 0
            if (artistChannel) score += 3
            if (vevoChannel) score += 3
            if (official) score += 2
            if (got == wantTitle) score += 1
            if (trackMs > 0 && songMs > 0 && kotlin.math.abs(songMs - trackMs) <= 10_000L) score += 1
            if (score > bestScore) {
                best = song
                bestScore = score
            }
        }
        return best
    }

    private fun compact(text: String): String = text.replace(" ", "")

    /** Lower case, no accents, no bracketed tags, letters and digits only. */
    private fun core(text: String): String {
        val plain = Normalizer.normalize(text, Normalizer.Form.NFD).replace(Regex("""\p{Mn}+"""), "")
        return plain.lowercase(Locale.ROOT)
            .replace(Regex("""\([^)]*\)|\[[^\]]*]"""), " ")
            .replace("&", " and ")
            .replace(Regex("""[^\p{L}\p{Nd}]+"""), " ")
            .trim()
    }
}
