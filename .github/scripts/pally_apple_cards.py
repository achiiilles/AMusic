#!/usr/bin/env python3
"""Apple Music cards of the album page open inside the app. Anchored edits only."""
import sys

BASE = "app/src/main/java/com/music/amusic/"


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        sys.exit("anchor %s found %d times" % (label, count))
    return text.replace(old, new)


# ---------------------------------------------------------------- AppleAlbumShelves.kt
path = BASE + "data/canvas/AppleAlbumShelves.kt"
text = read(path)

text = replace_once(
    text,
    """    val url: String,
    val isAlbum: Boolean,
)
""",
    """    val url: String,
    val isAlbum: Boolean,
    /** "Álbum • 2026", "Single • 2026" or "EP • 2026": the line an in-app page draws under the credit. */
    val releaseLine: String = "",
) {
    /** The id Apple's catalog uses for the card: what follows the last colon of [id]. */
    val appleId: String
        get() = id.substringAfterLast(':')
}

/** One song of an Apple Music playlist, in the playlist's own order. */
class ApplePlaylistTrack(
    val number: Int,
    val name: String,
    val artist: String,
    val artworkUrl: String?,
)

/** An Apple Music playlist read from the catalog, with the songs it returns. */
class ApplePlaylist(
    val id: String,
    val name: String,
    val curator: String,
    val artworkUrl: String?,
    val tracks: List<ApplePlaylistTrack>,
)
""",
    "target-class",
)

text = replace_once(
    text,
    """    private val targets = ConcurrentHashMap<String, AppleShelfTarget>()
""",
    """    private val targets = ConcurrentHashMap<String, AppleShelfTarget>()
    private val playlists = ConcurrentHashMap<String, ApplePlaylist>()

    /** The YouTube Music album found for an Apple card; an empty string means there is none. */
    private val youtubeIds = ConcurrentHashMap<String, String>()
    private val opening: MutableSet<String> = ConcurrentHashMap.newKeySet()

    /** False while a tap on the same card is still being resolved, so a second tap opens nothing twice. */
    fun beginOpen(id: String): Boolean = opening.add(id)

    fun endOpen(id: String) {
        opening.remove(id)
    }
""",
    "targets-field",
)

text = replace_once(
    text,
    """        val key = (if (isAlbum) "apple:album:" else "apple:playlist:") + id
        targets[key] = AppleShelfTarget(key, name, subtitle, url, isAlbum)
""",
    """        val key = (if (isAlbum) "apple:album:" else "apple:playlist:") + id
        val year = attributes.text("releaseDate")?.take(4)?.takeIf { it.length == 4 && it.all(Char::isDigit) }
        val kind = when {
            name.trimEnd().endsWith("- EP", ignoreCase = true) -> "EP"
            attributes.text("isSingle") == "true" || name.trimEnd().endsWith("- Single", ignoreCase = true) -> "Single"
            else -> "Álbum"
        }
        val releaseLine = if (isAlbum) listOfNotNull(kind, year).joinToString(" • ") else ""
        targets[key] = AppleShelfTarget(key, name, subtitle, url, isAlbum, releaseLine)
""",
    "card-target",
)

start = text.index("    /**\n     * The YouTube Music album that is the same release as an Apple card")
end = text.index("    private fun JsonObject.text(key: String)")
new_block = '''    /**
     * The YouTube Music album that is the same release as an Apple card, found
     * by search and accepted only when the cleaned title and the artist agree.
     * Null when there is none, and the caller then opens the app's own album
     * page built from Apple's track list. The answer is remembered, so a
     * second tap on the same card opens at once.
     */
    suspend fun youtubeAlbumFor(target: AppleShelfTarget): String? {
        youtubeIds[target.id]?.let { return it.takeIf { id -> id.isNotEmpty() } }
        val want = AppleReleaseMatcher.cleanTitle(target.title)
        if (want.isBlank()) return null
        val hits = runCatching {
            YtMusicRepository.search("${target.artist} ${target.title}".trim(), SearchFilter.ALBUMS)
                .getOrNull()
        }.getOrNull() ?: return null
        val artistKey = target.artist.substringBefore(",").substringBefore("&").trim().lowercase()
        val found = hits.firstNotNullOfOrNull { hit ->
            val item = (hit as? SearchResult.Browse)?.item ?: return@firstNotNullOfOrNull null
            when {
                !item.browseId.startsWith("MPRE") -> null
                AppleReleaseMatcher.cleanTitle(item.title) != want -> null
                artistKey.isNotEmpty() && !item.subtitle.lowercase().contains(artistKey) -> null
                else -> item.browseId
            }
        }
        youtubeIds[target.id] = found.orEmpty()
        return found
    }

    /**
     * An Apple Music playlist with the songs the catalog returns for it (its
     * first page, up to 100), for the app's own playlist page. Null when
     * Apple does not answer; remembered once it has.
     */
    suspend fun playlistFor(playlistId: String): ApplePlaylist? {
        if (playlistId.isBlank()) return null
        playlists[playlistId]?.let { return it }
        val playlist = withContext(Dispatchers.IO) {
            runCatching { loadPlaylist(playlistId) }
                .onFailure { Log.d(TAG, "playlist failed for $playlistId: $it") }
                .getOrNull()
        } ?: return null
        playlists[playlistId] = playlist
        return playlist
    }

    private fun loadPlaylist(playlistId: String): ApplePlaylist? {
        val body = AppleMusicCanvas.catalogGet(
            "playlists/$playlistId",
            mapOf("include" to "tracks", "l" to "pt-BR"),
        ) ?: return null
        val record = Json.parseToJsonElement(body).jsonObject["data"]?.jsonArray
            ?.firstOrNull() as? JsonObject ?: return null
        val attributes = record["attributes"] as? JsonObject
        val songs = (((record["relationships"] as? JsonObject)?.get("tracks") as? JsonObject)
            ?.get("data")?.jsonArray).orEmpty()
            .mapNotNull { it as? JsonObject }
            .filter { it.text("type") == "songs" }
        val tracks = songs.mapIndexedNotNull { index, song ->
            val songAttributes = song["attributes"] as? JsonObject ?: return@mapIndexedNotNull null
            val name = songAttributes.text("name") ?: return@mapIndexedNotNull null
            ApplePlaylistTrack(
                number = index + 1,
                name = name,
                artist = songAttributes.text("artistName").orEmpty(),
                artworkUrl = artworkOf(songAttributes),
            )
        }
        return ApplePlaylist(
            id = playlistId,
            name = attributes?.text("name").orEmpty(),
            curator = attributes?.text("curatorName").orEmpty(),
            artworkUrl = attributes?.let { artworkOf(it) },
            tracks = tracks,
        )
    }

    private fun artworkOf(attributes: JsonObject): String? =
        (attributes["artwork"] as? JsonObject)?.text("url")
            ?.replace("{w}", "480")?.replace("{h}", "480")?.replace("{c}", "bb")?.replace("{f}", "jpg")

'''
text = text[:start] + new_block + text[end:]
write(path, text)

# ---------------------------------------------------------------- MainViewModel.kt
path = BASE + "ui/MainViewModel.kt"
text = read(path)
anchor = "    private val _refreshingDetail = MutableStateFlow<Set<String>>(emptySet())\n"
playlist_fun = '''    /**
     * Opens an Apple Music playlist (a "Com participação em" card) as a playlist
     * page inside the app. The songs come from Apple's catalog and are drawn the
     * way a pre-release page draws its own: each one is played by name, with its
     * own artist, through YouTube Music.
     */
    fun openApplePlaylist(
        playlistId: String,
        title: String,
        curator: String,
        thumbnailUrl: String?,
    ) {
        val pageId = "prerelease:$playlistId"
        if (_detailStack.value.lastOrNull()?.browseId == pageId) return
        val credit = curator.trim().ifEmpty { "Apple Music" }
        _detailStack.value += DetailPage(
            browseId = pageId,
            title = title,
            subtitle = "$credit • Playlist • Apple Music",
            thumbnailUrl = thumbnailUrl,
            songs = UiState.Loading,
            type = BrowseType.PLAYLIST,
        )
        viewModelScope.launch {
            val playlist = com.music.amusic.data.canvas.AppleAlbumShelves.playlistFor(playlistId)
            val state: UiState<List<Song>> = if (playlist == null || playlist.tracks.isEmpty()) {
                UiState.Error("Não foi possível carregar as faixas.")
            } else {
                UiState.Success(
                    playlist.tracks.map { track ->
                        Song(
                            videoId = "prerelease:$playlistId:${track.number}",
                            title = track.name,
                            artist = track.artist,
                            thumbnailUrl = track.artworkUrl ?: playlist.artworkUrl ?: thumbnailUrl,
                            albumName = playlist.name.ifBlank { title },
                            trackNumber = track.number,
                        )
                    },
                )
            }
            val count = (state as? UiState.Success)?.data?.size ?: 0
            val countText = if (count == 1) "1 faixa" else "$count faixas"
            _detailStack.value = _detailStack.value.map { page ->
                if (page.browseId == pageId) {
                    page.copy(
                        songs = state,
                        subtitle = if (count > 0) "$credit • Playlist • $countText" else page.subtitle,
                    )
                } else {
                    page
                }
            }
        }
    }

'''
text = replace_once(text, anchor, playlist_fun + anchor, "viewmodel-anchor")
write(path, text)

# ---------------------------------------------------------------- DetailScreen.kt
path = BASE + "ui/screens/DetailScreen.kt"
text = read(path)
text = replace_once(
    text,
    "if (!preReleaseOff) onPlayByName?.invoke(song.title, appleAlbumCredit)",
    "if (!preReleaseOff) {\n"
    "                                        // A playlist's songs each have their own artist; an album's share the page's credit.\n"
    "                                        onPlayByName?.invoke(\n"
    "                                            song.title,\n"
    "                                            if (page.type == BrowseType.PLAYLIST) song.artist else appleAlbumCredit,\n"
    "                                        )\n"
    "                                    }",
    "detail-play",
)
write(path, text)

# ---------------------------------------------------------------- MainActivity.kt
path = BASE + "MainActivity.kt"
text = read(path)
start_marker = "                                val appleCard = item.browseId?.let { com.music.amusic.data.canvas.AppleAlbumShelves.target(it) }\n"
end_marker = "                                // A music video has no page: it plays, and the radio carries on after it.\n"
if text.count(start_marker) != 1 or text.count(end_marker) != 1:
    sys.exit("MainActivity anchors not unique")
start = text.index(start_marker)
end = text.index(end_marker)
if not start < end or end - start > 2500:
    sys.exit("MainActivity block has an unexpected size")
old_block = text[start:end]
if "ACTION_VIEW" not in old_block:
    sys.exit("MainActivity block is not the browser one")
new_block = '''                                val appleCard = item.browseId?.let { com.music.amusic.data.canvas.AppleAlbumShelves.target(it) }
                                if (appleCard != null) {
                                    // An Apple Music card opens inside the app, never in the browser:
                                    // an album, single or EP opens the app's album page (the YouTube
                                    // Music one when the same release exists there, otherwise a page
                                    // built from Apple's own track list), a playlist opens the app's
                                    // playlist page.
                                    if (!appleCard.isAlbum) {
                                        viewModel.openApplePlaylist(
                                            playlistId = appleCard.appleId,
                                            title = appleCard.title,
                                            curator = appleCard.artist,
                                            thumbnailUrl = item.thumbnailUrl,
                                        )
                                    } else if (com.music.amusic.data.canvas.AppleAlbumShelves.beginOpen(appleCard.id)) {
                                        scope.launch {
                                            try {
                                                val youtubeId =
                                                    com.music.amusic.data.canvas.AppleAlbumShelves.youtubeAlbumFor(appleCard)
                                                if (youtubeId != null) {
                                                    viewModel.openDetail(
                                                        browseId = youtubeId,
                                                        title = appleCard.title,
                                                        subtitle = appleCard.artist,
                                                        thumbnailUrl = item.thumbnailUrl,
                                                        type = BrowseType.ALBUM,
                                                    )
                                                } else {
                                                    viewModel.openPreRelease(
                                                        collectionId = appleCard.appleId,
                                                        title = appleCard.title,
                                                        badge = appleCard.releaseLine,
                                                        thumbnailUrl = item.thumbnailUrl,
                                                        artist = appleCard.artist,
                                                    )
                                                }
                                            } finally {
                                                com.music.amusic.data.canvas.AppleAlbumShelves.endOpen(appleCard.id)
                                            }
                                        }
                                    }
                                }
'''
text = text[:start] + new_block + text[end:]
write(path, text)
print("ok")
