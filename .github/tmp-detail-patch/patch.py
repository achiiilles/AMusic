#!/usr/bin/env python3
import sys
from pathlib import Path

VM = Path("app/src/main/java/com/music/amusic/ui/MainViewModel.kt")
SCREEN = Path("app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt")


def replace(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print("ALREADY APPLIED:", label)
        return
    if old not in text:
        print("MISSING ANCHOR:", label)
        sys.exit(1)
    if text.count(old) != 1:
        print("AMBIGUOUS ANCHOR (%d matches): %s" % (text.count(old), label))
        sys.exit(1)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("APPLIED:", label)


# ---- 1. Bigger cache -------------------------------------------------------
replace(
    VM,
    """        /** Pages kept for a quick return; small on purpose, see [detailCache]. */
        const val DETAIL_CACHE_ENTRIES = 12""",
    """        /** Pages kept for a quick return; expanded to 64 for instant re-opening. */
        const val DETAIL_CACHE_ENTRIES = 64""",
    "DETAIL_CACHE_ENTRIES",
)

# ---- 2. Cache every release/artist page, not just the tagged ones ----------
replace(
    VM,
    """    /**
     * Only public artist and album pages: a playlist can be edited from here,
     * and downloaded, local and remote pages are read from the device afresh.
     */
    private fun rememberDetail(page: DetailPage) {
        val id = page.browseId
        val publicRelease = id.startsWith("UC") || id.startsWith("MPREb") ||
            id.startsWith("OLAK") || id.startsWith("VLOLAK")
        if (!publicRelease) return
        if (page.type != BrowseType.ARTIST && page.type != BrowseType.ALBUM) return
        if (page.songs !is UiState.Success) return
        detailCache.put(id, CachedDetail(page, System.currentTimeMillis()))
    }""",
    """    /**
     * Kept for every catalogue artist, album and playlist page, whatever its id
     * shape: an Apple-only release, a pre-release or an artist without the
     * usual prefix is still a page that should open at once the second time.
     *
     * Pages read from this device — folders, downloads, the local store — are
     * left out: those are read afresh anyway, and caching them would show a
     * file list that no longer matches the disk.
     */
    private fun rememberDetail(page: DetailPage) {
        val id = page.browseId
        if (id.startsWith("local:") || id.startsWith("spotify:")) return
        val release = when (page.type) {
            BrowseType.ARTIST, BrowseType.ALBUM, BrowseType.PLAYLIST -> true
            else -> false
        }
        if (!release) return
        if (page.songs !is UiState.Success) return
        detailCache.put(id, CachedDetail(page, System.currentTimeMillis()))
    }""",
    "rememberDetail body",
)

# ---- 3. Store the page the moment its rows land ---------------------------
replace(
    VM,
    """            _detailStack.value = _detailStack.value.map {
                if (it.browseId == browseId &&
                    (it.songs is UiState.Loading || (onDevice.isNotEmpty() && state is UiState.Success))
                ) {
                    it.copy(
                        songs = state,
                        sections = sections,
                        thumbnailUrl = artwork ?: it.thumbnailUrl,
                        title = name ?: it.title,
                        subtitle = credit ?: it.subtitle,
                        suggestedSongs = suggested,
                        continuation = more,
                        library = library,
                        description = description,
                        subscriberCountText = subscriberCountText,
                        monthlyListenerCount = monthlyListenerCount,
                        subscription = subscription,
                    )
                } else {
                    it
                }
            }""",
    """            _detailStack.value = _detailStack.value.map {
                if (it.browseId == browseId &&
                    (it.songs is UiState.Loading || (onDevice.isNotEmpty() && state is UiState.Success))
                ) {
                    val updated = it.copy(
                        songs = state,
                        sections = sections,
                        thumbnailUrl = artwork ?: it.thumbnailUrl,
                        title = name ?: it.title,
                        subtitle = credit ?: it.subtitle,
                        suggestedSongs = suggested,
                        continuation = more,
                        library = library,
                        description = description,
                        subscriberCountText = subscriberCountText,
                        monthlyListenerCount = monthlyListenerCount,
                        subscription = subscription,
                    )
                    // Kept the moment its rows arrive, not only when the page
                    // is closed: a return to it before that used to wait out
                    // the whole request again.
                    rememberDetail(updated)
                    updated
                } else {
                    it
                }
            }""",
    "openDetail cache write",
)

# ---- 4. The follow-up artist id write refreshes the cached copy -----------
replace(
    VM,
    """                    _detailStack.value = _detailStack.value.map { page ->
                        val songs = page.songs
                        if (page.browseId == browseId && songs is UiState.Success) {
                            page.copy(
                                songs = UiState.Success(
                                    songs.data.map { if (it.artistId == null) it.copy(artistId = artistId) else it },
                                ),
                            )
                        } else {
                            page
                        }
                    }""",
    """                    _detailStack.value = _detailStack.value.map { page ->
                        val songs = page.songs
                        if (page.browseId == browseId && songs is UiState.Success) {
                            val updated = page.copy(
                                songs = UiState.Success(
                                    songs.data.map { if (it.artistId == null) it.copy(artistId = artistId) else it },
                                ),
                            )
                            rememberDetail(updated)
                            updated
                        } else {
                            page
                        }
                    }""",
    "resolved artist id cache write",
)

# ---- 5. Pre-release pages and Apple playlists are cached too --------------
replace(
    VM,
    """            _detailStack.value = _detailStack.value.map { page ->
                if (page.browseId == pageId) page.copy(songs = state, subtitle = subtitleFor(credit)) else page
            }""",
    """            _detailStack.value = _detailStack.value.map { page ->
                if (page.browseId == pageId) {
                    val updated = page.copy(songs = state, subtitle = subtitleFor(credit))
                    rememberDetail(updated)
                    updated
                } else page
            }""",
    "openPreRelease cache write",
)

replace(
    VM,
    """            _detailStack.value = _detailStack.value.map { page ->
                if (page.browseId == pageId) {
                    page.copy(
                        songs = state,
                        subtitle = if (count > 0) "$credit • Playlist • $countText" else page.subtitle,
                    )
                } else {
                    page
                }
            }""",
    """            _detailStack.value = _detailStack.value.map { page ->
                if (page.browseId == pageId) {
                    val updated = page.copy(
                        songs = state,
                        subtitle = if (count > 0) "$credit • Playlist • $countText" else page.subtitle,
                    )
                    rememberDetail(updated)
                    updated
                } else {
                    page
                }
            }""",
    "openApplePlaylist cache update",
)

# ---- 6. DetailScreen: no dead Play/Shuffle while the rows are coming ------
replace(
    SCREEN,
    """                        onPlay = {
                            if (isPreRelease && page.type != BrowseType.PLAYLIST) playPreRelease(false) else onSongClick(songs, 0)
                        },
                        onShuffle = {
                            if (isPreRelease && page.type != BrowseType.PLAYLIST) playPreRelease(true) else onShuffle(songs)
                        },""",
    """                        onPlay = {
                            if (songs.isNotEmpty()) {
                                if (isPreRelease && page.type != BrowseType.PLAYLIST) playPreRelease(false) else onSongClick(songs, 0)
                            }
                        },
                        onShuffle = {
                            if (songs.isNotEmpty()) {
                                if (isPreRelease && page.type != BrowseType.PLAYLIST) playPreRelease(true) else onShuffle(songs)
                            }
                        },""",
    "ReleaseHeader play/shuffle guards",
)

# ---- 7. DetailScreen: the action row is there from the first frame --------
replace(
    SCREEN,
    """            if (songs.isNotEmpty() && isArtist) {
                item(key = "actions") {""",
    """            if (isArtist && (songs.isNotEmpty() || page.songs is UiState.Loading)) {
                item(key = "actions") {""",
    "artist action row during load",
)

# ---- 8. DetailScreen: the album action row too ----------------------------
replace(
    SCREEN,
    """        if (songs.isNotEmpty()) {
            // Only where YouTube said the release can be saved and the caller
            // is willing to take the write — see [onToggleLibrary].""",
    """        // Drawn while the rows are still coming, so the page is complete from
        // its first frame and the buttons do not appear late under the header.
        if (songs.isNotEmpty() || page.songs is UiState.Loading) {
            // Only where YouTube said the release can be saved and the caller
            // is willing to take the write — see [onToggleLibrary].""",
    "release action row during load",
)

print("PATCH OK")
