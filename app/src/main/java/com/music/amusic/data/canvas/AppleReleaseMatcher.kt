package com.music.amusic.data.canvas

import com.music.amusic.data.DebugLog as Log
import org.json.JSONObject
import java.net.URLEncoder
import kotlin.math.abs
import kotlin.math.roundToInt

/**
 * What [AppleReleaseMatcher] settled on. [collectionName] is Apple's own name for the
 * release, or null when the artist's releases were read and none of them scored well
 * enough to be trusted. [artistName] is the artist as Apple spells it.
 */
class AppleReleaseChoice(val collectionName: String?, val artistName: String)

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

    /** Share of the points the page's own facts could earn that a release must reach. */
    private const val MIN_RATIO = 0.6

    private class Release(
        val id: Long,
        val name: String,
        val artist: String,
        val trackCount: Int,
        val year: String?,
    )

    private class Scored(val release: Release, val score: Int)

    private val PAREN_SUFFIX = Regex(
        """\s*[(\[][^)\]]*\b(?:pa version|explicit|clean|deluxe|remaster(?:ed)?|expanded|edition|version|bonus|anniversary|edited|special)\b[^)\]]*[)\]]""",
        RegexOption.IGNORE_CASE,
    )

    private val DASH_SUFFIX = Regex("""\s+-\s+(?:single|ep)\s*\z""", RegexOption.IGNORE_CASE)

    /** The title with edition suffixes removed and folded for comparison. */
    fun cleanTitle(raw: String): String {
        val stripped = DASH_SUFFIX.replace(PAREN_SUFFIX.replace(raw, ""), "")
            .let { DASH_SUFFIX.replace(it, "") }
            .normalizeForMatch()
        return stripped.ifBlank { raw.normalizeForMatch() }
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
        val primary = splitArtists(artist).firstOrNull() ?: return null
        val want = cleanTitle(album)
        if (want.isBlank()) return null

        val artistId = findArtist(primary) ?: return null
        val releases = discography(artistId)
        if (releases.isEmpty()) return null

        val wantYear = year?.take(4)?.takeIf { it.length == 4 && it.all(Char::isDigit) }
        val wantSongs = trackTitles.map { cleanTitle(it) }.filter { it.isNotBlank() }.toSet()

        val staged = releases.mapNotNull { release ->
            val name = nameScore(want, cleanTitle(release.name))
            if (name == 0) return@mapNotNull null
            Scored(release, name + countScore(trackCount, release.trackCount) + yearScore(wantYear, release.year))
        }.sortedByDescending { it.score }.take(FINALISTS)

        if (staged.isEmpty()) {
            Log.d(TAG, "no release of $artist is named like '$want'")
            return AppleReleaseChoice(null, artist)
        }

        var songsRead = false
        val finalists = staged.map { scored ->
            if (wantSongs.isEmpty()) return@map scored
            val songs = songNames(scored.release.id) ?: return@map scored
            songsRead = true
            Scored(scored.release, scored.score + songScore(wantSongs, songs))
        }

        var possible = NAME_EXACT
        if (trackCount > 0) possible += COUNT_EXACT
        if (wantYear != null) possible += YEAR_EXACT
        if (songsRead) possible += SONGS_MAX

        val best = finalists.maxByOrNull { it.score } ?: return AppleReleaseChoice(null, artist)
        val needed = (possible * MIN_RATIO).roundToInt()
        Log.d(TAG, "'$want' best '${best.release.name}' scored ${best.score} of $possible (needs $needed)")
        if (best.score < needed) return AppleReleaseChoice(null, artist)

        val credited = best.release.artist.ifBlank { artist }
        return AppleReleaseChoice(best.release.name, credited)
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

    private fun findArtist(primary: String): Long? {
        val body = get("$ITUNES/search?term=${enc(primary)}&entity=musicArtist&limit=5&country=${country()}")
            ?: return null
        val results = JSONObject(body).optJSONArray("results") ?: return null
        for (i in 0 until results.length()) {
            val hit = results.getJSONObject(i)
            if (hit.optString("artistName").normalizeForMatch() == primary) {
                val id = hit.optLong("artistId")
                if (id > 0) return id
            }
        }
        return null
    }

    /** The artist's albums, singles and EPs. */
    private fun discography(artistId: Long): List<Release> {
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

    /** The cleaned song names on a release, or null when they could not be read. */
    private fun songNames(collectionId: Long): List<String>? {
        val body = get("$ITUNES/lookup?id=$collectionId&entity=song&country=${country()}") ?: return null
        val results = JSONObject(body).optJSONArray("results") ?: return null
        val names = ArrayList<String>()
        for (i in 0 until results.length()) {
            val item = results.getJSONObject(i)
            if (item.optString("wrapperType") != "track") continue
            val name = item.optString("trackName")
            if (name.isNotBlank()) names.add(cleanTitle(name))
        }
        return names.takeIf { it.isNotEmpty() }
    }
}
