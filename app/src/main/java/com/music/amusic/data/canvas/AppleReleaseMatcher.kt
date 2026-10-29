package com.music.amusic.data.canvas

import com.music.amusic.data.DebugLog as Log
import org.json.JSONArray
import org.json.JSONObject
import java.net.URLEncoder
import java.util.concurrent.Callable
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.concurrent.Future
import kotlin.math.abs
import kotlin.math.roundToInt

/**
 * What [AppleReleaseMatcher] settled on. [collectionName] is Apple's own name for the
 * release, or null when the artist's releases were read and none of them scored well
 * enough to be trusted. [artistName] is the artist as Apple spells it.
 */
class AppleReleaseChoice(
    val collectionName: String?,
    val artistName: String,
    /** Apple's catalog id of the release, the same number as the iTunes collectionId. */
    val collectionId: Long? = null,
)

/**
 * Finds which Apple Music release an album, single or EP page is, starting from the
 * artist instead of the title.
 *
 * 1. The title is cleaned first: "Erotica (PA Version)" becomes "erotica"; suffixes such
 *    as "(Explicit)", "(Deluxe Edition)", "- Single" and "- EP" are dropped.
 * 2. The artist is looked up, and the list of that artist's albums, singles and EPs is
 *    read from Apple's public iTunes lookup.
 * 3. Each release is scored on its cleaned name, track count, year and song names. A
 *    score that is low for what the page told us is no match at all, so a wrong album
 *    is never taken for the right one.
 *
 * Apple's own name for the chosen release is then handed to the existing colour lookup.
 * A null answer means nothing could be settled (no artist found, no network); the
 * caller keeps its old behaviour in that case.
 *
 * Speed: the artist id, the artist's list of releases and the song names of a release
 * are remembered in memory and on disk ([AppleLookupStore]), the song names of the best
 * candidates are read at the same time instead of one after the other, and [prefetch]
 * lets the artist be looked up while the page's own songs are still loading. The scoring
 * is untouched, so the same page gets the same release. When the saved list of releases
 * finds nothing, it is read again from Apple once before giving up, so a release that
 * came out after the list was saved is still found.
 */
object AppleReleaseMatcher {

    private const val TAG = "AppleReleaseMatcher"
    private const val ITUNES = "https://itunes.apple.com"

    private const val NAME_EXACT = 50
    private const val NAME_PARTIAL = 25
    private const val COUNT_EXACT = 20
    private const val COUNT_CLOSE = 8
    private const val YEAR_EXACT = 15
    private const val YEAR_CLOSE = 6
    private const val SONGS_MAX = 30
    private const val FINALISTS = 3

    /** How many of a credit's artists are tried, in order, when the page has several. */
    private const val MAX_CANDIDATES = 3

    /** Share of the points the page's own facts could earn that a release must reach. */
    private const val MIN_RATIO = 0.6

    /** How long a list of releases kept in memory is used without asking Apple again. */
    private const val MEMORY_TTL_MS = 6L * 60 * 60 * 1000

    private class Release(
        val id: Long,
        val name: String,
        val artist: String,
        val trackCount: Int,
        val year: String?,
    )

    private class Scored(val release: Release, val score: Int)

    /** [id] is null when Apple answered and has no artist by that name. */
    private class ArtistHit(val id: Long?)

    private class Disc(val releases: List<Release>, val at: Long)

    private class Discography(val releases: List<Release>, val fromCache: Boolean)

    /** [noMatch] is true when the releases were read and none scored well enough. */
    private class Decision(val choice: AppleReleaseChoice?, val noMatch: Boolean)

    private val artistIds = ConcurrentHashMap<String, ArtistHit>()
    private val discographies = ConcurrentHashMap<Long, Disc>()
    private val songCache = ConcurrentHashMap<Long, List<String>>()
    private val locks = ConcurrentHashMap<String, Any>()

    private val pool = Executors.newFixedThreadPool(6) { task ->
        Thread(task, "apple-release-matcher").apply { isDaemon = true }
    }

    private fun lockFor(key: String): Any = locks.getOrPut(key) { Any() }

    private val PAREN_SUFFIX = Regex(
        """\s*[(\[][^)\]]*\b(?:pa version|explicit|clean|deluxe|remaster(?:ed)?|expanded|edition|version|bonus|anniversary|edited|special)\b[^)\]]*[)\]]""",
        RegexOption.IGNORE_CASE,
    )

    private val DASH_SUFFIX = Regex("""\s+-\s+(?:single|ep)\s*\z""", RegexOption.IGNORE_CASE)

    private val MINI_ALBUM_SUFFIX = Regex(
        """\s+-\s+(?:the\s+)?\d+(?:st|nd|rd|th)\s+(?:mini\s+)?album\s*\z""",
        RegexOption.IGNORE_CASE,
    )

    /** The title with edition suffixes removed and folded for comparison. */
    fun cleanTitle(raw: String): String {
        val stripped = DASH_SUFFIX.replace(PAREN_SUFFIX.replace(raw, ""), "")
            .let { DASH_SUFFIX.replace(it, "") }
            .let { MINI_ALBUM_SUFFIX.replace(it, "") }
            .normalizeForMatch()
        return stripped.ifBlank { raw.normalizeForMatch() }
    }

    /**
     * Starts looking up the artist and the artist's releases in the background, so the
     * answer is already there when [choose] runs. Returns at once and never throws.
     */
    fun prefetch(artist: String) {
        runCatching {
            val candidates = splitArtists(artist).distinct().take(MAX_CANDIDATES)
            for (primary in candidates) {
                pool.execute {
                    runCatching {
                        val id = findArtist(primary)
                        if (id != null) discography(id, false)
                    }
                }
            }
        }
    }

    /** Never throws; null means the lookup could not be settled. */
    fun choose(
        album: String,
        artist: String,
        trackCount: Int,
        year: String?,
        trackTitles: List<String>,
    ): AppleReleaseChoice? = runCatching { chooseUnsafe(album, artist, trackCount, year, trackTitles) }
        .onFailure { Log.d(TAG, "match failed for $album: $it") }
        .getOrNull()

    private fun chooseUnsafe(
        album: String,
        artist: String,
        trackCount: Int,
        year: String?,
        trackTitles: List<String>,
    ): AppleReleaseChoice? {
        val candidates = splitArtists(artist).distinct().take(MAX_CANDIDATES)
        if (candidates.isEmpty()) return null
        val want = cleanTitle(album)
        if (want.isBlank()) return null

        val wantYear = year?.take(4)?.takeIf { it.length == 4 && it.all(Char::isDigit) }
        val wantSongs = trackTitles.map { cleanTitle(it) }.filter { it.isNotBlank() }.toSet()

        // A credit such as "Olivia Rodrigo e Chappell Roan" is two artists. The release is
        // looked for in each artist's releases in turn; the first one that matches wins.
        // When none matches, the answer of the first artist that could be read stands,
        // which is what a page with a single artist always got.
        var settled: AppleReleaseChoice? = null
        for (primary in candidates) {
            val choice = chooseFor(primary, artist, want, trackCount, wantYear, wantSongs) ?: continue
            if (choice.collectionName != null) return choice
            if (settled == null) settled = choice
        }
        return settled
    }

    private fun chooseFor(
        primary: String,
        artist: String,
        want: String,
        trackCount: Int,
        wantYear: String?,
        wantSongs: Set<String>,
    ): AppleReleaseChoice? {
        val artistIds = findArtists(primary)
        if (artistIds.isEmpty()) return null
        var settled: AppleReleaseChoice? = null
        val matches = mutableListOf<AppleReleaseChoice>()
        for (artistId in artistIds) {
            val choice = chooseForId(artistId, artist, want, trackCount, wantYear, wantSongs) ?: continue
            if (choice.collectionName != null) matches += choice
            if (settled == null) settled = choice
        }
        // Two homonyms with the same release evidence are ambiguous, not a reason to pick the first.
        if (matches.mapNotNull { it.collectionId }.distinct().size > 1) return AppleReleaseChoice(null, artist)
        return matches.firstOrNull() ?: settled
    }

    private fun chooseForId(
        artistId: Long, artist: String, want: String, trackCount: Int,
        wantYear: String?, wantSongs: Set<String>,
    ): AppleReleaseChoice? {
        val first = discography(artistId, false)
        if (first.releases.isEmpty()) return null

        var decision = decide(first.releases, artist, want, trackCount, wantYear, wantSongs)
        if (decision.noMatch && first.fromCache) {
            // The saved list may be older than the release; read the current one once.
            val fresh = discography(artistId, true)
            if (fresh.releases.isNotEmpty()) {
                decision = decide(fresh.releases, artist, want, trackCount, wantYear, wantSongs)
            }
        }
        return decision.choice
    }

    private fun decide(
        releases: List<Release>,
        artist: String,
        want: String,
        trackCount: Int,
        wantYear: String?,
        wantSongs: Set<String>,
    ): Decision {
        val staged = releases.mapNotNull { release ->
            val name = nameScore(want, cleanTitle(release.name))
            if (name == 0) return@mapNotNull null
            Scored(release, name + countScore(trackCount, release.trackCount) + yearScore(wantYear, release.year))
        }.sortedByDescending { it.score }.take(FINALISTS)

        if (staged.isEmpty()) {
            Log.d(TAG, "no release of $artist is named like '$want'")
            return Decision(AppleReleaseChoice(null, artist), true)
        }

        // The song names of every finalist are read at the same time.
        val reads: List<Future<List<String>?>> = if (wantSongs.isEmpty()) {
            emptyList()
        } else {
            staged.map { scored ->
                pool.submit(Callable<List<String>?> { songNames(scored.release.id) })
            }
        }

        var songsRead = false
        val finalists = staged.mapIndexed { index, scored ->
            if (reads.isEmpty()) return@mapIndexed scored
            val songs = runCatching { reads[index].get() }.getOrNull() ?: return@mapIndexed scored
            songsRead = true
            Scored(scored.release, scored.score + songScore(wantSongs, songs))
        }

        var possible = NAME_EXACT
        if (trackCount > 0) possible += COUNT_EXACT
        if (wantYear != null) possible += YEAR_EXACT
        if (songsRead) possible += SONGS_MAX

        val best = finalists.maxByOrNull { it.score } ?: return Decision(AppleReleaseChoice(null, artist), true)
        val needed = (possible * MIN_RATIO).roundToInt()
        Log.d(TAG, "'$want' best '${best.release.name}' scored ${best.score} of $possible (needs $needed)")
        if (best.score < needed) return Decision(AppleReleaseChoice(null, artist), true)

        if (songsRead && wantSongs.size >= 2) {
            val songs = songNames(best.release.id).orEmpty()
            if (songScore(wantSongs, songs) < (SONGS_MAX * MIN_RATIO).roundToInt()) {
                Log.d(TAG, "rejected homonym/edition: track names disagree for ${best.release.id}")
                return Decision(AppleReleaseChoice(null, artist), true)
            }
        }
        val credited = best.release.artist.ifBlank { artist }
        return Decision(AppleReleaseChoice(best.release.name, credited, best.release.id), false)
    }

    private fun nameScore(want: String, got: String): Int = when {
        got.isBlank() -> 0
        got == want -> NAME_EXACT
        minOf(got.length, want.length) >= 4 && (got.contains(want) || want.contains(got)) -> NAME_PARTIAL
        else -> 0
    }

    private fun countScore(want: Int, got: Int): Int {
        if (want <= 0 || got <= 0) return 0
        return when {
            want == got -> COUNT_EXACT
            abs(want - got) <= 2 -> COUNT_CLOSE
            else -> 0
        }
    }

    private fun yearScore(want: String?, got: String?): Int {
        val a = want?.toIntOrNull() ?: return 0
        val b = got?.toIntOrNull() ?: return 0
        return when {
            a == b -> YEAR_EXACT
            abs(a - b) <= 1 -> YEAR_CLOSE
            else -> 0
        }
    }

    private fun songScore(want: Set<String>, got: List<String>): Int {
        if (want.isEmpty()) return 0
        val matched = want.count { w -> got.any { g -> sameSong(w, g) } }
        return (matched.toDouble() / want.size * SONGS_MAX).roundToInt()
    }

    private fun sameSong(a: String, b: String): Boolean =
        a == b || (minOf(a.length, b.length) >= 4 && (a.contains(b) || b.contains(a)))

    // ---- Apple's public lookup -----------------------------------------

    private fun get(url: String): String? = canvasGet(url, mapOf("User-Agent" to CANVAS_UA))

    private fun enc(value: String) = URLEncoder.encode(value, "UTF-8")

    private fun country() = AppleMusicCanvas.storefront

    private val artistCandidates = ConcurrentHashMap<String, List<Long>>()

    private fun findArtists(primary: String): List<Long> = synchronized(lockFor("artists-v2:$primary")) {
        val key = "artist-ids-v2:${country()}:$primary"
        artistCandidates[key]?.let { return@synchronized it }
        val saved = AppleLookupStore.read(key, AppleLookupStore.DISCOGRAPHY_MAX_AGE_MS)
            ?.let { runCatching { JSONArray(it) }.getOrNull() }
        if (saved != null) {
            val ids = (0 until saved.length()).map { saved.optLong(it) }.filter { it > 0 }
            if (ids.isNotEmpty()) { artistCandidates[key] = ids; return@synchronized ids }
        }
        val body = get("$ITUNES/search?term=${enc(primary)}&entity=musicArtist&limit=25&country=${country()}")
            ?: return@synchronized emptyList()
        val results = JSONObject(body).optJSONArray("results") ?: return@synchronized emptyList()
        val ids = (0 until results.length()).mapNotNull { index ->
            val hit = results.optJSONObject(index) ?: return@mapNotNull null
            if (hit.optString("artistName").normalizeForMatch() != primary) return@mapNotNull null
            hit.optLong("artistId").takeIf { it > 0 }
        }.distinct().take(5)
        if (ids.isNotEmpty()) {
            artistCandidates[key] = ids
            AppleLookupStore.write(key, JSONArray(ids).toString())
        }
        Log.d(TAG, "exact-name Apple artists for '$primary': ${ids.joinToString()}")
        ids
    }

    /** The Apple artist id, from memory, then disk, then Apple; null when there is none. */
    private fun findArtist(primary: String): Long? {
        artistIds[primary]?.let { return it.id }
        return synchronized(lockFor("artist:$primary")) {
            artistIds[primary]?.let { return@synchronized it.id }
            val diskKey = "artist-id:${country()}:$primary"
            val saved = AppleLookupStore.read(diskKey, AppleLookupStore.STABLE_MAX_AGE_MS)
                ?.toLongOrNull()?.takeIf { it > 0 }
            if (saved != null) {
                artistIds[primary] = ArtistHit(saved)
                return@synchronized saved
            }
            val body = get("$ITUNES/search?term=${enc(primary)}&entity=musicArtist&limit=5&country=${country()}")
                ?: return@synchronized null
            val results = JSONObject(body).optJSONArray("results") ?: return@synchronized null
            var found: Long? = null
            for (i in 0 until results.length()) {
                val hit = results.getJSONObject(i)
                if (hit.optString("artistName").normalizeForMatch() == primary) {
                    val id = hit.optLong("artistId")
                    if (id > 0) {
                        found = id
                        break
                    }
                }
            }
            artistIds[primary] = ArtistHit(found)
            found?.let { AppleLookupStore.write(diskKey, it.toString()) }
            found
        }
    }

    /**
     * The artist's albums, singles and EPs. [fresh] skips what is remembered and asks
     * Apple again.
     */
    private fun discography(artistId: Long, fresh: Boolean): Discography {
        if (!fresh) {
            val remembered = discographies[artistId]
            if (remembered != null && System.currentTimeMillis() - remembered.at < MEMORY_TTL_MS) {
                return Discography(remembered.releases, true)
            }
        }
        return synchronized(lockFor("disc:$artistId")) {
            val diskKey = "disc:${country()}:$artistId"
            if (!fresh) {
                val remembered = discographies[artistId]
                if (remembered != null && System.currentTimeMillis() - remembered.at < MEMORY_TTL_MS) {
                    return@synchronized Discography(remembered.releases, true)
                }
                val saved = AppleLookupStore.read(diskKey, AppleLookupStore.DISCOGRAPHY_MAX_AGE_MS)
                    ?.let { text -> runCatching { releasesFromJson(text) }.getOrNull() }
                    ?.takeIf { it.isNotEmpty() }
                if (saved != null) {
                    discographies[artistId] = Disc(saved, System.currentTimeMillis())
                    return@synchronized Discography(saved, true)
                }
            }
            val loaded = fetchDiscography(artistId)
            if (loaded.isNotEmpty()) {
                discographies[artistId] = Disc(loaded, System.currentTimeMillis())
                AppleLookupStore.write(diskKey, releasesToJson(loaded))
            }
            Discography(loaded, false)
        }
    }

    private fun fetchDiscography(artistId: Long): List<Release> {
        val body = get("$ITUNES/lookup?id=$artistId&entity=album&limit=200&country=${country()}")
            ?: return emptyList()
        val results = JSONObject(body).optJSONArray("results") ?: return emptyList()
        val out = ArrayList<Release>()
        for (i in 0 until results.length()) {
            val item = results.getJSONObject(i)
            if (item.optString("wrapperType") != "collection") continue
            val id = item.optLong("collectionId")
            val name = item.optString("collectionName")
            if (id <= 0 || name.isBlank()) continue
            val year = item.optString("releaseDate").take(4).takeIf { it.length == 4 && it.all(Char::isDigit) }
            out.add(Release(id, name, item.optString("artistName"), item.optInt("trackCount"), year))
        }
        return out
    }

    private fun releasesToJson(list: List<Release>): String {
        val array = JSONArray()
        for (release in list) {
            val row = JSONArray()
            row.put(release.id)
            row.put(release.name)
            row.put(release.artist)
            row.put(release.trackCount)
            row.put(release.year ?: "")
            array.put(row)
        }
        return array.toString()
    }

    private fun releasesFromJson(text: String): List<Release> {
        val array = JSONArray(text)
        val out = ArrayList<Release>()
        for (i in 0 until array.length()) {
            val row = array.getJSONArray(i)
            out.add(
                Release(
                    row.getLong(0),
                    row.getString(1),
                    row.getString(2),
                    row.getInt(3),
                    row.getString(4).ifBlank { null },
                ),
            )
        }
        return out
    }

    /** The cleaned song names on a release, or null when they could not be read. */
    private fun songNames(collectionId: Long): List<String>? {
        songCache[collectionId]?.let { return it }
        val diskKey = "songs:${country()}:$collectionId"
        val saved = AppleLookupStore.read(diskKey, AppleLookupStore.STABLE_MAX_AGE_MS)
            ?.let { text -> runCatching { JSONArray(text) }.getOrNull() }
        if (saved != null) {
            val list = ArrayList<String>()
            for (i in 0 until saved.length()) list.add(saved.getString(i))
            if (list.isNotEmpty()) {
                songCache[collectionId] = list
                return list
            }
        }
        val body = get("$ITUNES/lookup?id=$collectionId&entity=song&country=${country()}") ?: return null
        val results = JSONObject(body).optJSONArray("results") ?: return null
        val names = ArrayList<String>()
        for (i in 0 until results.length()) {
            val item = results.getJSONObject(i)
            if (item.optString("wrapperType") != "track") continue
            val name = item.optString("trackName")
            if (name.isNotBlank()) names.add(cleanTitle(name))
        }
        if (names.isEmpty()) return null
        songCache[collectionId] = names
        AppleLookupStore.write(diskKey, JSONArray(names).toString())
        return names
    }
}
