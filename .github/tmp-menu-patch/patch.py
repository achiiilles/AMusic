def patch_file(path, old, new):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert old in content, f"Target text not found in {path}"
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {path}")

# 1. MainViewModel.kt: increase cache entries
patch_file(
    "app/src/main/java/com/music/amusic/ui/MainViewModel.kt",
    """        const val SEARCH_CACHE_ENTRIES = 100

        /** Pages kept for a quick return; small on purpose, see [detailCache]. */
        const val DETAIL_CACHE_ENTRIES = 12""",
    """        const val SEARCH_CACHE_ENTRIES = 100

        /** Pages kept for a quick return; small on purpose, see [detailCache]. */
        const val DETAIL_CACHE_ENTRIES = 64"""
)

# 2. MainViewModel.kt: remember all public album and artist pages
patch_file(
    "app/src/main/java/com/music/amusic/ui/MainViewModel.kt",
    """    private fun rememberDetail(page: DetailPage) {
        val id = page.browseId
        val publicRelease = id.startsWith("UC") || id.startsWith("MPREb") ||
            id.startsWith("OLAK") || id.startsWith("VLOLAK")
        if (!publicRelease) return
        if (page.type != BrowseType.ARTIST && page.type != BrowseType.ALBUM) return
        if (page.songs !is UiState.Success) return
        detailCache.put(id, CachedDetail(page, System.currentTimeMillis()))
    }""",
    """    private fun rememberDetail(page: DetailPage) {
        val id = page.browseId
        if (page.type != BrowseType.ARTIST && page.type != BrowseType.ALBUM) return
        if (page.songs !is UiState.Success) return
        detailCache.put(id, CachedDetail(page, System.currentTimeMillis()))
    }"""
)

# 3. MainViewModel.kt: save in cache immediately upon successful load
patch_file(
    "app/src/main/java/com/music/amusic/ui/MainViewModel.kt",
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
                    val updatedPage = it.copy(
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
                    if (state is UiState.Success) {
                        rememberDetail(updatedPage)
                    }
                    updatedPage
                } else {
                    it
                }
            }"""
)

# 4. DetailScreen.kt: artist action row always rendered
patch_file(
    "app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt",
    """            if (songs.isNotEmpty() && isArtist) {
                item(key = "actions") {
                    ActionRow(
                        onPlay = { onSongClick(songs, 0) },
                        onShuffle = { onShuffle(songs) },
                        subscription = page.subscription?.takeIf { onToggleSubscription != null },
                        onToggleSubscription = onToggleSubscription,
                        // With the heading below, the gap above and below it is shared
                        // (6 + 14 above its text, 20 below) so it sits centred between
                        // the buttons and the album card.
                        bottomSpace = if (showLibraryHeading) 6.dp else 22.dp,
                        playColor = appleArt?.keyColor?.let { Color(it) },
                    )
                }
            }""",
    """            if (isArtist) {
                item(key = "actions") {
                    ActionRow(
                        onPlay = { if (songs.isNotEmpty()) onSongClick(songs, 0) },
                        onShuffle = { if (songs.isNotEmpty()) onShuffle(songs) },
                        subscription = page.subscription?.takeIf { onToggleSubscription != null },
                        onToggleSubscription = onToggleSubscription,
                        // With the heading below, the gap above and below it is shared
                        // (6 + 14 above its text, 20 below) so it sits centred between
                        // the buttons and the album card.
                        bottomSpace = if (showLibraryHeading) 6.dp else 22.dp,
                        playColor = appleArt?.keyColor?.let { Color(it) },
                    )
                }
            }"""
)

# 5. DetailScreen.kt: ReleaseHeader action row always rendered
patch_file(
    "app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt",
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
                        },"""
)

# 6. DetailScreen.kt: ReleaseHeader render buttons during loading
patch_file(
    "app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt",
    """        if (songs.isNotEmpty()) {
            // Only where YouTube said the release can be saved and the caller
            // is willing to take the write — see [onToggleLibrary].
            val library = page.library?.takeIf { onToggleLibrary != null }""",
    """        if (songs.isNotEmpty() || page.songs is UiState.Loading) {
            // Only where YouTube said the release can be saved and the caller
            // is willing to take the write — see [onToggleLibrary].
            val library = page.library?.takeIf { onToggleLibrary != null }"""
)

print("Patch applied successfully!")
