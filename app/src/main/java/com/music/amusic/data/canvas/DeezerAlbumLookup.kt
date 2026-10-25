package com.music.amusic.data.canvas

import com.music.amusic.data.DebugLog as Log
import org.json.JSONObject
import java.net.URLEncoder
import java.text.Normalizer
import java.util.Locale

/**
 * What Deezer's public catalogue says about a release that Apple Music does not carry:
 * the genre, the release date and the label. Deezer sends no copyright line, so none is
 * filled in. A field Deezer leaves empty stays null.
 */
class DeezerAlbumInfo(
    val genre: String?,
    /** yyyy-MM-dd, as Deezer sends it. */
    val releaseDate: String?,
    val label: String?,
)

/**
 * Fills the details Apple cannot give for an album or single (genre, date, label) from
 * Deezer's keyless public API. A release is only taken when the artist's name, the
 * title without its "- Single" or "- EP" tail, the track count and the song names all
 * agree with the page; otherwise nothing is filled in, never a different release.
 */
object DeezerAlbumLookup {
    private const val TAG = "DeezerAlbum"
    private const val BASE = "https://api.deezer.com"
    private const val MAX_DETAIL_READS = 3

    private val NONE = DeezerAlbumInfo(null, null, null)

    private fun key(raw: String): String =
        Normalizer.normalize(raw.lowercase(Locale.ROOT), Normalizer.Form.NFD).filter { it.isLetterOrDigit() }

    private fun releaseTitle(raw: String): String =
        raw.replace(Regex("\\s*[-\u2013]\\s*(EP|Single)\\s*$", RegexOption.IGNORE_CASE), "").trim()

    private fun leadArtist(raw: String): String =
        raw.split(Regex("\\s*(,|&|\\bfeat\\.?|\\bft\\.?)\\s*", RegexOption.IGNORE_CASE)).firstOrNull().orEmpty().trim()

    private fun parse(body: String?): JSONObject? {
        val json = runCatching { JSONObject(body ?: return null) }.getOrNull() ?: return null
        return if (json.has("error")) null else json
    }

    /**
     * The details of the release, [NONE]-like (all null) when Deezer has no confident
     * match, or null when Deezer could not be asked at all (so the caller tries again later).
     */
    fun lookup(album: String, artist: String, trackCount: Int, trackTitles: List<String>): DeezerAlbumInfo? {
        val lead = leadArtist(artist)
        val title = releaseTitle(album)
        val wantArtist = key(lead)
        val wantTitle = key(title)
        if (wantArtist.isEmpty() || wantTitle.isEmpty()) return NONE

        val query = "artist:\"" + lead.replace("\"", " ") + "\" album:\"" + title.replace("\"", " ") + "\""
        val search = parse(canvasGet("$BASE/search/album?limit=25&q=" + URLEncoder.encode(query, "UTF-8"))) ?: return null
        val data = search.optJSONArray("data") ?: return NONE

        var reads = 0
        var failed = false
        for (i in 0 until data.length()) {
            if (reads >= MAX_DETAIL_READS) break
            val item = data.optJSONObject(i) ?: continue
            if (key(item.optJSONObject("artist")?.optString("name").orEmpty()) != wantArtist) continue
            if (key(releaseTitle(item.optString("title"))) != wantTitle) continue
            val id = item.optLong("id")
            if (id <= 0L) continue
            reads++
            val detail = parse(canvasGet("$BASE/album/$id"))
            if (detail == null) {
                failed = true
                continue
            }
            if (key(detail.optJSONObject("artist")?.optString("name").orEmpty()) != wantArtist) continue
            if (trackCount > 0 && detail.optInt("nb_tracks") != trackCount) continue
            if (!tracksAgree(detail, trackTitles)) continue
            val genre = detail.optJSONObject("genres")?.optJSONArray("data")
                ?.optJSONObject(0)?.optString("name")?.ifBlank { null }
            val date = detail.optString("release_date").takeIf { it.length >= 4 && it.take(4).all(Char::isDigit) }
            val label = detail.optString("label").ifBlank { null }
            Log.d(TAG, "filled $album from deezer $id")
            return DeezerAlbumInfo(genre, date, label)
        }
        return if (failed) null else NONE
    }

    /** At least half of the page's song names are among Deezer's tracks for the release. */
    private fun tracksAgree(detail: JSONObject, pageTitles: List<String>): Boolean {
        val array = detail.optJSONObject("tracks")?.optJSONArray("data") ?: return true
        val theirs = (0 until array.length()).map { key(array.optJSONObject(it)?.optString("title").orEmpty()) }
            .filter { it.isNotEmpty() }
        val ours = pageTitles.map { key(it) }.filter { it.isNotEmpty() }
        if (theirs.isEmpty() || ours.isEmpty()) return true
        val shared = ours.count { mine -> theirs.any { it == mine || it.startsWith(mine) || mine.startsWith(it) } }
        return shared * 2 >= ours.size
    }
}
