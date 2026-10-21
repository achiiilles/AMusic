import sys, os
def rd(p):
    with open(p, encoding='utf-8') as f:
        return f.read()
def wr(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)
def rep(s, old, new, label):
    n = s.count(old)
    if n != 1:
        print('FALHOU', label, 'ocorrencias:', n)
        sys.exit(1)
    return s.replace(old, new)

P_AM = 'app/src/main/java/com/music/amusic/data/canvas/AppleMusicCanvas.kt'
P_REPO = 'app/src/main/java/com/music/amusic/data/canvas/AppleAlbumColorRepository.kt'
P_PAL = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/theme/ArtworkPalette.kt'
P_DS = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
P_MA = 'app/src/main/java/com/music/amusic/MainActivity.kt'

REPO_KT = r'''package com.music.amusic.data.canvas

import androidx.compose.ui.graphics.Color
import com.music.amusic.data.DebugLog as Log
import com.music.amusic.ui.theme.ArtworkKeyColors
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.withContext

/**
 * Apple Music's own colours for an album or single: the background colour the
 * release is shown on and the text colour that goes with it (both ARGB).
 * They come from `attributes.artwork` on the catalog API, so nothing has to be
 * decoded from the sleeve to find them.
 */
data class AppleAlbumColors(
    val background: Int,
    val accent: Int,
)

/**
 * What a lookup settled on. [colors] is null when Apple answered but has no
 * confident match for the release; a lookup that could not be answered at all
 * (no token, no network) is not a result and is returned as null instead.
 */
class AppleAlbumColorsResult(val colors: AppleAlbumColors?)

/** Apple's colours for this release, in the form the palette takes. */
fun AppleAlbumColors.keyColors() = ArtworkKeyColors(Color(background), Color(accent))

/**
 * Finds [AppleAlbumColors] for an album or single page from its title and
 * artist, through the same catalog search the animated sleeves use.
 *
 * The answer is kept by the page's browse id, so the page and the bars around
 * it read the same thing. Only a settled answer (including "Apple has none") is
 * remembered; a network hiccup is tried again the next time the page opens.
 * Every miss leaves the page on the colours taken from the sleeve.
 */
object AppleAlbumColorRepository {

    private const val TAG = "AppleAlbumColors"
    private const val CACHE_SIZE = 128

    private class Entry(val colors: AppleAlbumColors?)

    private val cache = object : LinkedHashMap<String, Entry>(CACHE_SIZE, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, Entry>) =
            size > CACHE_SIZE
    }

    private val _updates = MutableStateFlow(0)

    /** Ticks whenever a lookup settles, so the bars drawn outside the page re-read [cached]. */
    val updates: StateFlow<Int> = _updates

    /** What is known for [browseId] without a request; null for never looked up and for no colours. */
    fun cached(browseId: String): AppleAlbumColors? =
        synchronized(cache) { cache[browseId] }?.colors

    /** Apple's colours for the release, or null when it has none. Never throws. */
    suspend fun colorsFor(browseId: String, album: String, artist: String): AppleAlbumColors? {
        if (browseId.isBlank() || album.isBlank() || artist.isBlank()) return null
        synchronized(cache) { cache[browseId] }?.let { return it.colors }

        val result = withContext(Dispatchers.IO) {
            runCatching { AppleMusicCanvas.albumColors(album, artist) }
                .onFailure { Log.d(TAG, "lookup failed for $album: $it") }
                .getOrNull()
        } ?: return null
        synchronized(cache) { cache[browseId] = Entry(result.colors) }
        _updates.value++
        return result.colors
    }
}
'''
ALBUMCOLORS_FN = r'''
    /**
     * Apple's background and text colours for a release, for the album and
     * single pages. Same search and the same scoring as [searchAlbum], so a
     * different release by the same artist is never taken for the one asked
     * about; only the answer differs: `attributes.artwork.bgColor` and
     * `textColor1` instead of the motion artwork.
     *
     * Null means nothing could be settled (no token, a network failure, an
     * answer that is not JSON). A result with null colours means Apple answered
     * and has no match worth trusting.
     */
    fun albumColors(album: String, artist: String): AppleAlbumColorsResult? {
        val bearer = token() ?: return null
        val term = if (album.contains(artist, ignoreCase = true)) album else "$artist $album"

        val url = "$AMP/$storefront/search".toHttpUrl().newBuilder()
            .addQueryParameter("term", term)
            .addQueryParameter("types", "albums")
            .addQueryParameter("limit", "10")
            .build()
            .toString()

        val body = get(url, bearer) ?: return null
        val root = runCatching { json.parseToJsonElement(body).jsonObject }.getOrNull() ?: return null
        val hits = root["results"]?.jsonObject
            ?.get("albums")?.jsonObject
            ?.get("data")?.jsonArray
            ?: return AppleAlbumColorsResult(null)

        val ranked = hits.mapNotNull { hit ->
            val record = hit as? JsonObject ?: return@mapNotNull null
            val score = score(record, album, artist, album, albumIsSelf = true)
                ?: return@mapNotNull null
            score to record
        }.sortedByDescending { it.first }

        for ((score, record) in ranked) {
            if (score < MIN_SCORE) break
            val attributes = record["attributes"]?.jsonObject ?: continue
            val name = attributes["name"]?.jsonPrimitive?.contentOrNull
            if (name != null && isCompilation(name)) continue
            val artwork = attributes["artwork"]?.jsonObject ?: continue
            val background = artwork["bgColor"]?.jsonPrimitive?.contentOrNull?.hexToArgb() ?: continue
            val accent = artwork["textColor1"]?.jsonPrimitive?.contentOrNull?.hexToArgb() ?: background
            Log.d(TAG, "album colours for '$name'")
            return AppleAlbumColorsResult(AppleAlbumColors(background, accent))
        }
        return AppleAlbumColorsResult(null)
    }

    /** Apple's colours are six hex digits with no prefix. */
    private fun String.hexToArgb(): Int? =
        takeIf { it.length == 6 }?.toIntOrNull(16)?.let { 0xFF000000.toInt() or it }
'''

# 1. AppleMusicCanvas.kt: a colours lookup next to searchAlbum
s = rd(P_AM)
s = rep(s, "\n    // ---- Search scoring ------------------------------------------------\n",
        ALBUMCOLORS_FN + "\n    // ---- Search scoring ------------------------------------------------\n", 'am')
wr(P_AM, s)

# 2. new repository file
wr(P_REPO, REPO_KT)

# 3. ArtworkPalette.kt
s = rd(P_PAL)
s = rep(s, "    val shaped = if (accentWhenNeutral) seed?.withAccentWhenNeutral() else seed\n",
"""    // Apple's own colours for a release already say what the page should be, so
    // the grey-sleeve fallback only applies to a page tinted from the sleeve.
    val shaped = if (accentWhenNeutral && keyColors == null) seed?.withAccentWhenNeutral() else seed
""", 'pal-shaped')
s = rep(s, "    val knownUpFront = remember(imageUrl) { decoded != null }\n",
"""    val knownUpFront = remember(imageUrl) { decoded != null }
    // Apple's colours for an album can arrive after the page was first drawn in
    // the sleeve's colours. That is a change of colour on a surface already on
    // screen, so it fades like any other late tint instead of cutting.
    val keyColorsAtStart = remember(imageUrl) { keyColors != null }
    val keyColorsArrivedLate = keyColors != null && !keyColorsAtStart
""", 'pal-late')
s = rep(s, "    val spec: AnimationSpec<Color> = if (reduceAnimation || knownUpFront) {\n        snap()\n    } else {\n        tween(TINT_FADE_MS)\n    }\n    return ArtworkPalette(",
"    val spec: AnimationSpec<Color> = if (reduceAnimation || (knownUpFront && !keyColorsArrivedLate)) {\n        snap()\n    } else {\n        tween(TINT_FADE_MS)\n    }\n    return ArtworkPalette(", 'pal-spec')
wr(P_PAL, s)

# 4. DetailScreen.kt
s = rd(P_DS)
s = rep(s, "import com.music.amusic.data.canvas.AppleArtistArtRepository\n",
        "import com.music.amusic.data.canvas.AppleAlbumColorRepository\nimport com.music.amusic.data.canvas.AppleArtistArtRepository\n", 'ds-import')
s = rep(s, "    val palette = rememberArtworkPalette(\n        imageUrl = appleArt?.heroUrl ?: page.thumbnailUrl,\n        keyColors = appleArt?.keyColors(),\n",
"""    // Album and single pages: Apple Music's own background colour for the
    // release, found by title and credit. Null until (and unless) it arrives; the
    // colours taken from the sleeve stand in meanwhile and fade to Apple's. Artist
    // pages, playlists and device folders never take this path.
    val appleAlbumEligible = page.type == BrowseType.ALBUM && !artistColours &&
        !page.browseId.orEmpty().startsWith("local:")
    val appleAlbumCredit = page.headerLines(songs.size).first
        .ifBlank { songs.firstOrNull()?.artist.orEmpty() }
    var appleAlbum by remember(page.browseId) {
        mutableStateOf(
            if (appleAlbumEligible) AppleAlbumColorRepository.cached(page.browseId.orEmpty()) else null,
        )
    }
    LaunchedEffect(page.browseId, page.title, appleAlbumCredit, appleAlbumEligible) {
        if (!appleAlbumEligible || appleAlbumCredit.isBlank()) return@LaunchedEffect
        appleAlbum = AppleAlbumColorRepository.colorsFor(
            page.browseId.orEmpty(), page.title, appleAlbumCredit,
        ) ?: appleAlbum
    }
    val palette = rememberArtworkPalette(
        imageUrl = appleArt?.heroUrl ?: page.thumbnailUrl,
        keyColors = appleArt?.keyColors() ?: appleAlbum?.keyColors(),
""", 'ds-palette')
wr(P_DS, s)

# 5. MainActivity.kt
s = rd(P_MA)
s = rep(s, "import com.music.amusic.data.canvas.AppleArtistArtRepository\n",
        "import com.music.amusic.data.canvas.AppleAlbumColorRepository\nimport com.music.amusic.data.canvas.AppleArtistArtRepository\n", 'ma-import')
s = rep(s, "    // On the Light theme the coloured pages (album, single, playlist, artist and\n",
"""    // An album or single page is coloured from Apple's own colours for the release
    // when it has them, so the bars around the page read the same cache the page
    // fills, keyed by the same browse id.
    val appleAlbumVersion by AppleAlbumColorRepository.updates.collectAsStateWithLifecycle()
    val detailAppleAlbum = remember(detail?.browseId, detail?.type, appleAlbumVersion, detailIsLibraryArtist) {
        detail?.takeIf {
            it.type == BrowseType.ALBUM && !detailIsLibraryArtist &&
                !it.browseId.orEmpty().startsWith("local:")
        }?.let { AppleAlbumColorRepository.cached(it.browseId.orEmpty()) }
    }
    // On the Light theme the coloured pages (album, single, playlist, artist and
""", 'ma-block')
s = rep(s, "        keyColors = detailApple?.keyColors(),\n        dark = darkTheme || detailDarkPage,\n",
        "        keyColors = detailApple?.keyColors() ?: detailAppleAlbum?.keyColors(),\n        dark = darkTheme || detailDarkPage,\n", 'ma-palette')
wr(P_MA, s)
print('OK')
