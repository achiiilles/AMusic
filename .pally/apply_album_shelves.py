'''Adds "Videoclipes" and the Apple Music shelves to the album page, once.

Temporary helper: the files are too big to upload whole through the GitHub file
API, so the edits are made in place on the checked-out copy. Every anchor must
match exactly once, otherwise nothing is written and the job fails.
'''
import io
import os
import sys

ROOT = os.environ.get("PALLY_ROOT", ".")
MODELS = "shared/src/commonMain/kotlin/com/music/amusic/data/model/Models.kt"
PARSER = "shared/src/jvmSharedMain/kotlin/com/music/amusic/data/innertube/InnertubeParser.kt"
REPO = "shared/src/jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt"
VIEWMODEL = "app/src/main/java/com/music/amusic/ui/MainViewModel.kt"
DETAIL = "app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt"
MAIN = "app/src/main/java/com/music/amusic/MainActivity.kt"
MATCHER = "app/src/main/java/com/music/amusic/data/canvas/AppleReleaseMatcher.kt"
CANVAS = "app/src/main/java/com/music/amusic/data/canvas/AppleMusicCanvas.kt"
SHELVES = "app/src/main/java/com/music/amusic/data/canvas/AppleAlbumShelves.kt"


def read(path):
    with io.open(os.path.join(ROOT, path), encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    with io.open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def apply(source, old, new, label):
    count = source.count(old)
    if count != 1:
        sys.exit("anchor %s matched %d times" % (label, count))
    return source.replace(old, new)


NEW_FILE = r'''package com.music.amusic.data.canvas

import com.music.amusic.data.DebugLog as Log
import com.music.amusic.data.YtMusicRepository
import com.music.amusic.data.model.HomeShelf
import com.music.amusic.data.model.SearchFilter
import com.music.amusic.data.model.SearchResult
import com.music.amusic.data.model.ShelfItem
import java.util.concurrent.ConcurrentHashMap
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject

/** An Apple Music card of the album page: what a tap on it has to open. */
class AppleShelfTarget(
    val id: String,
    val title: String,
    val artist: String,
    val url: String,
    val isAlbum: Boolean,
)

/**
 * The shelves Apple Music draws under an album, read from Apple's catalog with
 * the same anonymous token and storefront the album colours use.
 *
 * Only what the catalog really returns is shown: "Mais de <artista>" from the
 * artist's own albums and singles, "Com participação em" from the album's
 * appears-on view and "Talvez você goste" from its related-albums view. A view
 * Apple leaves empty is simply not drawn. Apple's cards have no YouTube page,
 * so each carries an id starting with "apple:" and is resolved when tapped.
 */
object AppleAlbumShelves {
    private const val TAG = "AppleAlbumShelves"
    private const val MAX_CARDS = 20
    private const val CACHE_SIZE = 64

    private val cache = object : LinkedHashMap<String, List<HomeShelf>>(CACHE_SIZE, 0.75f, true) {
        override fun removeEldestEntry(eldest: MutableMap.MutableEntry<String, List<HomeShelf>>) =
            size > CACHE_SIZE
    }
    private val targets = ConcurrentHashMap<String, AppleShelfTarget>()

    /** What is known for the page without a request. */
    fun cached(browseId: String): List<HomeShelf> = synchronized(cache) { cache[browseId] }.orEmpty()

    /** What an Apple card id stands for; null for anything that is not one. */
    fun target(id: String): AppleShelfTarget? = targets[id]

    /**
     * The shelves for an album page. Null means nothing could be settled (no
     * token, no network) and is tried again next time; an empty list means
     * Apple answered and has nothing to show.
     */
    suspend fun shelvesFor(
        browseId: String,
        album: String,
        artist: String,
        trackCount: Int,
        year: String?,
        trackTitles: List<String>,
    ): List<HomeShelf>? {
        if (browseId.isBlank() || album.isBlank() || artist.isBlank()) return null
        synchronized(cache) { cache[browseId] }?.let { return it }
        val shelves = withContext(Dispatchers.IO) {
            runCatching { load(album, artist, trackCount, year, trackTitles) }
                .onFailure { Log.d(TAG, "shelves failed for $album: $it") }
                .getOrNull()
        } ?: return null
        synchronized(cache) { cache[browseId] = shelves }
        return shelves
    }

    private fun load(
        album: String,
        artist: String,
        trackCount: Int,
        year: String?,
        trackTitles: List<String>,
    ): List<HomeShelf>? {
        val choice = AppleReleaseMatcher.choose(album, artist, trackCount, year, trackTitles) ?: return null
        val albumId = choice.collectionId?.toString() ?: return emptyList()
        val body = AppleMusicCanvas.catalogGet(
            "albums/$albumId",
            mapOf("views" to "appears-on,related-albums", "include" to "artists", "l" to "pt-BR"),
        ) ?: return null
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: return emptyList()
        val views = record["views"] as? JsonObject
        val artistRecord = ((record["relationships"] as? JsonObject)?.get("artists") as? JsonObject)
            ?.get("data")?.jsonArray?.firstOrNull() as? JsonObject
        val artistId = artistRecord?.text("id")
        val artistName = (artistRecord?.get("attributes") as? JsonObject)?.text("name") ?: choice.artistName

        val shelves = mutableListOf<HomeShelf>()
        if (artistId != null) {
            val more = moreFromArtist(artistId, albumId)
            if (more.isNotEmpty()) shelves += HomeShelf(title = "Mais de $artistName", items = more)
        }
        val appearsOn = viewCards(views, "appears-on", isAlbum = false)
        if (appearsOn.isNotEmpty()) shelves += HomeShelf(title = "Com participação em", items = appearsOn)
        val related = viewCards(views, "related-albums", isAlbum = true)
        if (related.isNotEmpty()) shelves += HomeShelf(title = "Talvez você goste", items = related)
        Log.d(TAG, "apple shelves for '$album': ${shelves.joinToString { "${it.title} (${it.items.size})" }}")
        return shelves
    }

    /** The artist's own albums, singles and EPs, newest first, without the page's own album. */
    private fun moreFromArtist(artistId: String, currentAlbumId: String): List<ShelfItem> {
        val body = AppleMusicCanvas.catalogGet(
            "artists/$artistId",
            mapOf("views" to "full-albums,singles,appears-on-albums", "l" to "pt-BR"),
        ) ?: return emptyList()
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: return emptyList()
        val views = record["views"] as? JsonObject
        return listOf("full-albums", "singles", "appears-on-albums")
            .flatMap { dataOf(views, it) }
            .filter { it.text("id") != currentAlbumId }
            .distinctBy { it.text("id") }
            .sortedByDescending { (it["attributes"] as? JsonObject)?.text("releaseDate").orEmpty() }
            .take(MAX_CARDS)
            .mapNotNull { card(it, isAlbum = true) }
    }

    private fun viewCards(views: JsonObject?, name: String, isAlbum: Boolean): List<ShelfItem> =
        dataOf(views, name).take(MAX_CARDS).mapNotNull { card(it, isAlbum) }

    private fun dataOf(views: JsonObject?, name: String): List<JsonObject> =
        ((views?.get(name) as? JsonObject)?.get("data")?.jsonArray).orEmpty().mapNotNull { it as? JsonObject }

    private fun card(record: JsonObject, isAlbum: Boolean): ShelfItem? {
        val id = record.text("id") ?: return null
        val attributes = record["attributes"] as? JsonObject ?: return null
        val name = attributes.text("name") ?: return null
        val url = attributes.text("url") ?: return null
        val template = (attributes["artwork"] as? JsonObject)?.text("url")
        val thumbnail = template
            ?.replace("{w}", "480")?.replace("{h}", "480")?.replace("{c}", "bb")?.replace("{f}", "jpg")
        val subtitle = (if (isAlbum) attributes.text("artistName") else attributes.text("curatorName")).orEmpty()
        val key = (if (isAlbum) "apple:album:" else "apple:playlist:") + id
        targets[key] = AppleShelfTarget(key, name, subtitle, url, isAlbum)
        return ShelfItem(
            title = name,
            subtitle = subtitle,
            thumbnailUrl = thumbnail,
            videoId = null,
            browseId = key,
            explicit = attributes.text("contentRating") == "explicit",
        )
    }

    /**
     * The YouTube Music album that is the same release as an Apple card, found
     * by search and accepted only when the cleaned title and the artist agree.
     * Null when there is none, and the caller opens Apple's own page instead.
     */
    suspend fun youtubeAlbumFor(target: AppleShelfTarget): String? {
        val want = AppleReleaseMatcher.cleanTitle(target.title)
        if (want.isBlank()) return null
        val hits = runCatching {
            YtMusicRepository.search("${target.artist} ${target.title}".trim(), SearchFilter.ALBUMS)
                .getOrNull().orEmpty()
        }.getOrDefault(emptyList())
        val artistKey = target.artist.substringBefore(",").substringBefore("&").trim().lowercase()
        return hits.firstNotNullOfOrNull { hit ->
            val item = (hit as? SearchResult.Browse)?.item ?: return@firstNotNullOfOrNull null
            when {
                !item.browseId.startsWith("MPRE") -> null
                AppleReleaseMatcher.cleanTitle(item.title) != want -> null
                artistKey.isNotEmpty() && !item.subtitle.lowercase().contains(artistKey) -> null
                else -> item.browseId
            }
        }
    }

    private fun JsonObject.text(key: String): String? =
        (this[key] as? JsonPrimitive)?.contentOrNull?.trim()?.takeIf { it.isNotBlank() }
}
'''

PARSER_ADD = r'''    /**
     * The "Videoclipes" section of an album page: the music videos released for
     * the album's songs. Found by what the cards are, never by their heading:
     * a card that plays a video (a watch endpoint with a music-video type) and
     * opens no page. A card for the album's own audio track is not one. Null
     * when the page has no such cards, so the page reads exactly as before.
     */
    fun parseMusicVideos(root: JsonElement): HomeShelf? {
        val items = LinkedHashMap<String, ShelfItem>()
        for (carousel in collectRenderers(root, "musicCarouselShelfRenderer")) {
            for (entry in carousel.a("contents").orEmpty()) {
                val renderer = entry.o("musicTwoRowItemRenderer") ?: continue
                val item = parseVideoCard(renderer) ?: continue
                val id = item.videoId ?: continue
                items.putIfAbsent(id, item)
            }
        }
        if (items.isEmpty()) return null
        return HomeShelf(title = "Videoclipes", items = items.values.toList())
    }

    private fun parseVideoCard(renderer: JsonObject): ShelfItem? {
        val title = renderer.o("title").runs()
        if (title.isBlank()) return null
        val endpoint = renderer.o("navigationEndpoint")
        if (endpoint.o("browseEndpoint") != null) return null
        val watch = endpoint.o("watchEndpoint")
        val videoId = watch.s("videoId") ?: return null
        val type = watch.o("watchEndpointMusicSupportedConfigs").o("watchEndpointMusicConfig").s("musicVideoType")
        val thumbnails = renderer.o("thumbnailRenderer").o("musicThumbnailRenderer")
            .o("thumbnail").a("thumbnails")
        val isClip = if (type == null) {
            thumbnails.isNotSquare()
        } else {
            type == "MUSIC_VIDEO_TYPE_OMV" || type == "MUSIC_VIDEO_TYPE_UGC" ||
                type == "MUSIC_VIDEO_TYPE_OFFICIAL_SOURCE_MUSIC"
        }
        if (!isClip) return null
        val subtitle = renderer.o("subtitle").runs()
        return ShelfItem(
            title = title,
            subtitle = if (subtitle.isBlank()) "" else artistFromSubtitle(subtitle),
            thumbnailUrl = thumbnails.best(),
            videoId = videoId,
            browseId = null,
            explicit = renderer.hasExplicitBadge() == true,
            wide = true,
        )
    }

'''

CANVAS_ADD = r'''    /**
     * An authenticated catalog read of [path] under the device's storefront,
     * for callers outside this file. Null when there is no token or no answer.
     */
    fun catalogGet(path: String, params: Map<String, String> = emptyMap()): String? {
        val bearer = token() ?: return null
        val builder = "$AMP/$storefront/$path".toHttpUrl().newBuilder()
        params.forEach { (key, value) -> builder.addQueryParameter(key, value) }
        return get(builder.build().toString(), bearer)
    }

'''

DETAIL_EFFECT = r'''        ) ?: appleAlbumResult
    }
    // The shelves Apple Music draws under this album, read from Apple's
    // catalog once the page's songs are known. Empty until (and unless) Apple
    // sends them; the page reads as before in the meantime.
    var appleShelves by remember(page.browseId) {
        mutableStateOf(
            if (appleAlbumEligible) AppleAlbumShelves.cached(page.browseId.orEmpty()) else emptyList<HomeShelf>(),
        )
    }
    LaunchedEffect(page.browseId, page.title, appleAlbumCredit, appleAlbumEligible, songs.size) {
        if (!appleAlbumEligible || appleAlbumCredit.isBlank() || songs.isEmpty()) return@LaunchedEffect
        appleShelves = AppleAlbumShelves.shelvesFor(
            browseId = page.browseId.orEmpty(),
            album = page.title,
            artist = appleAlbumCredit,
            trackCount = songs.size,
            year = appleAlbumResult?.releaseYear,
            trackTitles = songs.map { it.title },
        ) ?: appleShelves
    }
    val appleAlbum = appleAlbumResult?.colors
    val palette = rememberArtworkPalette('''

MAIN_CLICK = r'''                                val appleCard = item.browseId?.let { com.music.amusic.data.canvas.AppleAlbumShelves.target(it) }
                                if (appleCard != null) {
                                    // An Apple Music card: the same album on YouTube Music when
                                    // there is one, otherwise Apple's own page for it.
                                    scope.launch {
                                        val youtubeId = if (appleCard.isAlbum) {
                                            com.music.amusic.data.canvas.AppleAlbumShelves.youtubeAlbumFor(appleCard)
                                        } else {
                                            null
                                        }
                                        if (youtubeId != null) {
                                            viewModel.openDetail(
                                                browseId = youtubeId,
                                                title = appleCard.title,
                                                subtitle = appleCard.artist,
                                                thumbnailUrl = item.thumbnailUrl,
                                                type = BrowseType.ALBUM,
                                            )
                                        } else {
                                            runCatching {
                                                context.startActivity(
                                                    android.content.Intent(
                                                        android.content.Intent.ACTION_VIEW,
                                                        android.net.Uri.parse(appleCard.url),
                                                    ).addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK),
                                                )
                                            }
                                        }
                                    }
                                }
                                // A music video has no page: it plays, and the radio carries on after it.
                                val clip = if (item.browseId == null && item.subtitle?.startsWith("Pré-Lançamento") != true) {
                                    shelfSong(item)
                                } else {
                                    null
                                }
                                if (clip != null) {
                                    playRadio(
                                        clip,
                                        QueueSource(shownPage.title, PlaybackSourceType.BROWSE, shownPage.browseId),
                                    )
                                }
                                item.browseId?.takeUnless { it.startsWith("apple:") }?.let { id ->
                                    viewModel.openDetail(
                                        browseId = id,
                                        title = item.title,
                                        subtitle = item.subtitle,
                                        thumbnailUrl = item.thumbnailUrl,
                                        type = BrowseType.ALBUM,'''

def main():
    models = read(MODELS)
    models = apply(
        models,
        '    /** Whether YouTube marks the card with its explicit badge (the "E" on an album). */\n    val explicit: Boolean = false,\n)\n',
        '    /** Whether YouTube marks the card with its explicit badge (the "E" on an album). */\n    val explicit: Boolean = false,\n    /** A 16:9 card, as a music video is drawn, instead of the square sleeve. */\n    val wide: Boolean = false,\n)\n',
        "models-shelf-item",
    )

    parser = read(PARSER)
    parser = apply(
        parser,
        '    /** The heading YouTube gives that carousel, in the languages the app is likely to be asked in. */\n',
        PARSER_ADD + '    /** The heading YouTube gives that carousel, in the languages the app is likely to be asked in. */\n',
        "parser-insert",
    )

    repo = read(REPO)
    repo = apply(
        repo,
        '         */\n        val otherVersions: com.music.amusic.data.model.HomeShelf? = null,\n    )',
        '         */\n        val otherVersions: com.music.amusic.data.model.HomeShelf? = null,\n        /**\n         * The album page\'s music videos, see [InnertubeParser.parseMusicVideos].\n         * Null for anything but an album, and for an album with none.\n         */\n        val musicVideos: com.music.amusic.data.model.HomeShelf? = null,\n    )',
        "repo-songpage",
    )
    repo = apply(
        repo,
        '                page.copy(otherVersions = InnertubeParser.parseOtherVersions(response))',
        '                page.copy(\n                    otherVersions = InnertubeParser.parseOtherVersions(response),\n                    musicVideos = InnertubeParser.parseMusicVideos(response),\n                )',
        "repo-copy",
    )

    vm = read(VIEWMODEL)
    vm = apply(
        vm,
        '                            page.otherVersions?.let { sections = listOf(it) }',
        '                            // Then "Videoclipes", the album\'s music videos, right below it.\n                            sections = listOfNotNull(page.otherVersions, page.musicVideos)',
        "vm-sections",
    )

    matcher = read(MATCHER)
    matcher = apply(
        matcher,
        'class AppleReleaseChoice(val collectionName: String?, val artistName: String)',
        'class AppleReleaseChoice(\n    val collectionName: String?,\n    val artistName: String,\n    /** Apple\'s catalog id of the release, the same number as the iTunes collectionId. */\n    val collectionId: Long? = null,\n)',
        "matcher-class",
    )
    matcher = apply(
        matcher,
        '        return Decision(AppleReleaseChoice(best.release.name, credited), false)',
        '        return Decision(AppleReleaseChoice(best.release.name, credited, best.release.id), false)',
        "matcher-decision",
    )

    canvas = read(CANVAS)
    canvas = apply(
        canvas,
        "    /** Apple's colours are six hex digits with no prefix. */\n",
        CANVAS_ADD + "    /** Apple's colours are six hex digits with no prefix. */\n",
        "canvas-insert",
    )

    detail = read(DETAIL)
    detail = apply(
        detail,
        'import com.music.amusic.data.canvas.AppleAlbumColorRepository\n',
        'import com.music.amusic.data.canvas.AppleAlbumColorRepository\nimport com.music.amusic.data.canvas.AppleAlbumShelves\n',
        "detail-import",
    )
    detail = apply(
        detail,
        '        ) ?: appleAlbumResult\n    }\n    val appleAlbum = appleAlbumResult?.colors\n    val palette = rememberArtworkPalette(',
        DETAIL_EFFECT,
        "detail-effect",
    )
    detail = apply(
        detail,
        '            items(visibleSections) { shelf ->',
        '            items(visibleSections + appleShelves) { shelf ->',
        "detail-items",
    )
    detail = apply(
        detail,
        '                                onClick = { onSectionItemClick(item) },\n                                onLongPress = onSectionItemLongPress?.let { { it(item) } },',
        '                                onClick = { onSectionItemClick(item) },\n                                modifier = Modifier.width(if (item.wide) SHELF_CARD_WIDTH * 1.7f else SHELF_CARD_WIDTH),\n                                onLongPress = onSectionItemLongPress?.let { { it(item) } },',
        "detail-card-call",
    )
    detail = apply(
        detail,
        '            model = item.thumbnailUrl.artworkAt(CARD_ART_PX),\n            contentDescription = null,\n            modifier = Modifier\n                .fillMaxWidth()\n                .aspectRatio(1f)\n                .clip(item.artistAwareShape(10.dp))',
        '            model = if (item.wide) item.thumbnailUrl else item.thumbnailUrl.artworkAt(CARD_ART_PX),\n            contentDescription = null,\n            modifier = Modifier\n                .fillMaxWidth()\n                .aspectRatio(if (item.wide) 16f / 9f else 1f)\n                .clip(item.artistAwareShape(10.dp))',
        "detail-card-art",
    )

    main_kt = read(MAIN)
    main_kt = apply(
        main_kt,
        '        val type = id?.let { viewModel.browseTypeOf(it) }\n        if (id != null && type != BrowseType.ARTIST) {',
        '        val type = id?.takeUnless { it.startsWith("apple:") }?.let { viewModel.browseTypeOf(it) }\n        if (id != null && !id.startsWith("apple:") && type != BrowseType.ARTIST) {',
        "main-longpress",
    )
    main_kt = apply(
        main_kt,
        '                                item.browseId?.let { id ->\n                                    viewModel.openDetail(\n                                        browseId = id,\n                                        title = item.title,\n                                        subtitle = item.subtitle,\n                                        thumbnailUrl = item.thumbnailUrl,\n                                        type = BrowseType.ALBUM,',
        MAIN_CLICK,
        "main-click",
    )

    for path, text in [
        (MODELS, models), (PARSER, parser), (REPO, repo), (VIEWMODEL, vm), (MATCHER, matcher),
        (CANVAS, canvas), (DETAIL, detail), (MAIN, main_kt), (SHELVES, NEW_FILE),
    ]:
        write(path, text)
    print("ok")


main()
