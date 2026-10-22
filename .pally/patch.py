import sys

BASE = "app/src/main/java/com/music/amusic/"


def edit(path, pairs):
    s = open(path, encoding="utf-8").read()
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            print("ANCHOR COUNT", n, "for", old[:80].replace("\n", "\\n"))
            sys.exit(1)
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8").write(s)
    print("ok", path)


VM_NEW = '''    /**
     * Opens a release that is still on pre-order as a normal album page.
     *
     * The page is the same [DetailPage] every album uses, so it gets the same
     * header, buttons, rows and footer. Its tracks come from Apple's catalogue:
     * a track already out is an ordinary row (`prerelease:` ids, played by
     * name), one still named "Track N" is a row marked "Ainda não lançada"
     * (`prerelease-off:` ids) that does nothing when tapped.
     */
    fun openPreRelease(
        collectionId: String,
        title: String,
        badge: String,
        thumbnailUrl: String?,
        artist: String,
    ) {
        val pageId = "prerelease:$collectionId"
        if (_detailStack.value.lastOrNull()?.browseId == pageId) return
        val dateBadge = badge.replace("·", "•").trim()
        fun subtitleFor(name: String) =
            listOf(name.trim(), dateBadge).filter { it.isNotEmpty() }.joinToString(" • ")
        _detailStack.value += DetailPage(
            browseId = pageId,
            title = title,
            subtitle = subtitleFor(artist),
            thumbnailUrl = thumbnailUrl,
            songs = UiState.Loading,
            type = BrowseType.ALBUM,
        )
        viewModelScope.launch {
            val album = com.music.amusic.data.ApplePreRelease.album(collectionId)
            val credit = album?.artistName?.takeIf { it.isNotBlank() } ?: artist
            val state: UiState<List<Song>> = if (album == null || album.tracks.isEmpty()) {
                UiState.Error("Não foi possível carregar as faixas.")
            } else {
                UiState.Success(
                    album.tracks.map { track ->
                        Song(
                            videoId = if (track.released) {
                                "prerelease:$collectionId:${track.number}"
                            } else {
                                "prerelease-off:$collectionId:${track.number}"
                            },
                            title = track.name,
                            artist = credit,
                            thumbnailUrl = album.artworkUrl ?: thumbnailUrl,
                            albumName = album.name.ifBlank { title },
                            trackNumber = track.number,
                        )
                    },
                )
            }
            _detailStack.value = _detailStack.value.map { page ->
                if (page.browseId == pageId) page.copy(songs = state, subtitle = subtitleFor(credit)) else page
            }
        }
    }

'''

VM_ANCHOR = "    private val _refreshingDetail = MutableStateFlow<Set<String>>(emptySet())\n"

edit(BASE + "ui/MainViewModel.kt", [(VM_ANCHOR, VM_NEW + VM_ANCHOR)])

MAIN_OLD = """                            onSectionItemClick = { item ->
                                item.browseId?.let { id ->"""
MAIN_NEW = """                            onSectionItemClick = { item ->
                                // A release still on pre-order has no YouTube page: it opens
                                // the same album page, filled from Apple's track list.
                                val preReleaseId = if (item.browseId == null &&
                                    item.subtitle?.startsWith("Pré-Lançamento") == true
                                ) {
                                    com.music.amusic.data.ApplePreRelease.collectionIdOf(item.title)
                                } else {
                                    null
                                }
                                if (preReleaseId != null) {
                                    viewModel.openPreRelease(
                                        collectionId = preReleaseId,
                                        title = item.title,
                                        badge = item.subtitle,
                                        thumbnailUrl = item.thumbnailUrl,
                                        artist = if (shownPage.type == BrowseType.ARTIST) shownPage.title else "",
                                    )
                                }
                                item.browseId?.let { id ->"""

edit(BASE + "MainActivity.kt", [(MAIN_OLD, MAIN_NEW)])

D1_OLD = "    val isArtist = page.type == BrowseType.ARTIST\n"
D1_NEW = D1_OLD + """    // A release still on pre-order is shown on this same page: its released
    // tracks play by name, the others are inert rows.
    val isPreRelease = page.browseId.startsWith("prerelease:")
    val playPreRelease: (Boolean) -> Unit = { shuffled ->
        val out = songs.filter { it.videoId.startsWith("prerelease:") }
        val pick = if (shuffled) out.randomOrNull() else out.firstOrNull()
        if (pick != null) onPlayByName?.invoke(pick.title, pick.artist)
    }
"""

D2_OLD = """                        onPlay = { onSongClick(songs, 0) },
                        onShuffle = { onShuffle(songs) },
                        // A folder's credit"""
D2_NEW = """                        onPlay = { if (isPreRelease) playPreRelease(false) else onSongClick(songs, 0) },
                        onShuffle = { if (isPreRelease) playPreRelease(true) else onShuffle(songs) },
                        // A folder's credit"""

D3_OLD = """                        val song = entry.value
                        val isCurrent = isCurrentRow(song)"""
D3_NEW = """                        val rowSong = entry.value
                        val preReleaseOff = rowSong.videoId.startsWith("prerelease-off:")
                        val song = if (preReleaseOff) rowSong.copy(artist = "Ainda não lançada") else rowSong
                        val isCurrent = isCurrentRow(song)"""

D4_OLD = """                            onClick = {
                                onSongClick(queue, position)
                            },
                            onLongPress = { onSongLongPress(song) },
                            onSwipeToQueue = { onSongSwipe(song) },"""
D4_NEW = """                            modifier = if (preReleaseOff) Modifier.alpha(0.4f) else Modifier,
                            onClick = {
                                if (isPreRelease) {
                                    if (!preReleaseOff) onPlayByName?.invoke(song.title, appleAlbumCredit)
                                } else {
                                    onSongClick(queue, position)
                                }
                            },
                            onLongPress = if (isPreRelease) null else ({ onSongLongPress(song) }),
                            onSwipeToQueue = if (isPreRelease) null else ({ onSongSwipe(song) }),"""

D5_OLD = """                            showArtist = !numbered ||
                                !song.artist.trim().equals(appleAlbumCredit.trim(), ignoreCase = true),"""
D5_NEW = """                            showArtist = !numbered || preReleaseOff ||
                                !song.artist.trim().equals(appleAlbumCredit.trim(), ignoreCase = true),"""

D6_OLD = "onClick = { if (preReleaseId != null) preReleaseOpen.value = true else onClick() },"
D6_NEW = "onClick = { onClick() },"

D7_OLD = '): Pair<String, String> {\n    val parts = subtitle.split("•", "·")'
D7_NEW = '''): Pair<String, String> {
    if (browseId.startsWith("prerelease:")) {
        # placeholder
    }
    val parts = subtitle.split("•", "·")'''
