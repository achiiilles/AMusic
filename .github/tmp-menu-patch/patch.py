#!/usr/bin/env python3
import sys
import os

main_path = 'app/src/main/java/com/music/amusic/MainActivity.kt'
if not os.path.exists(main_path):
    print(f"ERROR: {main_path} not found")
    sys.exit(1)

with open(main_path, 'r', encoding='utf-8') as f:
    src = f.read()

src = src.replace('\r\n', '\n')

old_open_funcs = """        // ---- Album / playlist detail ----
        val openAlbumForSong: (Song) -> Unit = { targetSong ->
            songActions = null
            dismissPlayer()
            val albumId = targetSong.albumId
            if (albumId != null) {
                viewModel.openDetail(
                    albumId,
                    targetSong.albumName ?: targetSong.title,
                    targetSong.artist,
                    targetSong.thumbnailUrl,
                    BrowseType.ALBUM,
                )
            } else {
                val searchTerm = targetSong.albumName?.takeIf { it.isNotBlank() }
                    ?: "${targetSong.title} ${targetSong.artist}".trim()
                if (searchTerm.isNotBlank()) {
                    selectedTab = TAB_SEARCH
                    viewModel.searchFor(searchTerm)
                }
            }
        }
        val openArtistForSong: (Song) -> Unit = { targetSong ->
            songActions = null
            dismissPlayer()
            val artistId = targetSong.artistId
                ?: targetSong.artists.firstOrNull { it.browseId != null }?.browseId
            val artistName = targetSong.artists.firstOrNull { it.name.isNotBlank() }?.name
                ?: targetSong.artist
            if (artistId != null) {
                viewModel.openDetail(
                    artistId,
                    artistName,
                    context.getString(R.string.artist),
                    null,
                    BrowseType.ARTIST,
                )
            } else if (artistName.isNotBlank()) {
                selectedTab = TAB_SEARCH
                viewModel.searchFor(artistName)
            }
        }"""

new_open_funcs = """        // ---- Album / playlist detail ----
        val openAlbumForSong: (Song) -> Unit = { targetSong ->
            songActions = null
            dismissPlayer()
            val albumId = targetSong.albumId
            if (albumId != null) {
                viewModel.openDetail(
                    albumId,
                    targetSong.albumName ?: targetSong.title,
                    targetSong.artist,
                    targetSong.thumbnailUrl,
                    BrowseType.ALBUM,
                )
            } else {
                scope.launch {
                    val resolvedSong = if (targetSong.videoId.isNotBlank()) {
                        runCatching { YtMusicRepository.trackLinks(targetSong.videoId).getOrNull() }.getOrNull()
                    } else null
                    val resolvedAlbumId = resolvedSong?.albumId
                    val resolvedAlbumName = resolvedSong?.albumName ?: targetSong.albumName ?: targetSong.title
                    if (resolvedAlbumId != null) {
                        viewModel.openDetail(
                            resolvedAlbumId,
                            resolvedAlbumName,
                            targetSong.artist,
                            targetSong.thumbnailUrl,
                            BrowseType.ALBUM,
                        )
                    } else {
                        val query = targetSong.albumName?.takeIf { it.isNotBlank() }
                            ?: "${targetSong.title} ${targetSong.artist}".trim()
                        if (query.isNotBlank()) {
                            val hit = runCatching {
                                YtMusicRepository.search(query, SearchFilter.ALBUMS).getOrNull()
                                    ?.filterIsInstance<SearchResult.Browse>()
                                    ?.firstOrNull()
                                    ?.item
                            }.getOrNull()
                            if (hit?.browseId != null) {
                                viewModel.openDetail(
                                    hit.browseId,
                                    hit.title,
                                    hit.subtitle,
                                    hit.thumbnailUrl ?: targetSong.thumbnailUrl,
                                    hit.type,
                                )
                            }
                        }
                    }
                }
            }
        }
        val openArtistForSong: (Song) -> Unit = { targetSong ->
            songActions = null
            dismissPlayer()
            val artistId = targetSong.artistId
                ?: targetSong.artists.firstOrNull { it.browseId != null }?.browseId
            val artistName = targetSong.artists.firstOrNull { it.name.isNotBlank() }?.name
                ?: targetSong.artist
            if (artistId != null) {
                viewModel.openDetail(
                    artistId,
                    artistName,
                    context.getString(R.string.artist),
                    null,
                    BrowseType.ARTIST,
                )
            } else {
                scope.launch {
                    val resolvedSong = if (targetSong.videoId.isNotBlank()) {
                        runCatching { YtMusicRepository.trackLinks(targetSong.videoId).getOrNull() }.getOrNull()
                    } else null
                    val resolvedArtistId = resolvedSong?.artistId
                        ?: (if (artistName.isNotBlank()) {
                            runCatching {
                                YtMusicRepository.findArtistPageIdForRelease(
                                    artistName,
                                    targetSong.albumName,
                                    listOf(targetSong.title),
                                ).getOrNull()
                            }.getOrNull()
                        } else null)
                    if (resolvedArtistId != null) {
                        viewModel.openDetail(
                            resolvedArtistId,
                            artistName,
                            context.getString(R.string.artist),
                            null,
                            BrowseType.ARTIST,
                        )
                    } else if (artistName.isNotBlank()) {
                        val hit = runCatching {
                            YtMusicRepository.search(artistName, SearchFilter.ARTISTS).getOrNull()
                                ?.filterIsInstance<SearchResult.Browse>()
                                ?.firstOrNull()
                                ?.item
                        }.getOrNull()
                        if (hit?.browseId != null) {
                            viewModel.openDetail(
                                hit.browseId,
                                hit.title,
                                context.getString(R.string.artist),
                                null,
                                BrowseType.ARTIST,
                            )
                        }
                    }
                }
            }
        }"""

old_browse_actions = """                // The artist's name in the header, opened by the id that came with the
                // release. Closes the sheet first, as every other row here does.
                onOpenArtist = { id: String, name: String ->
                    browseActions = null
                    dismissPlayer()
                    if (id.isNotBlank()) {
                        viewModel.openDetail(id, name, context.getString(R.string.artist), null, BrowseType.ARTIST)
                    } else if (name.isNotBlank()) {
                        selectedTab = TAB_SEARCH
                        viewModel.searchFor(name)
                    }
                },
                onRenameInSheet = {
                    browseRenameInSheet = true
                    browseMenuOrigin = null
                },
                startRenaming = browseRenameInSheet,
                onPlayNext = act(playSongsNext),
                onAddToQueue = act(addSongsToQueue),
                onPlay = act { songs -> play(songs, 0) }.takeIf { target.fromCard },
                onShuffle = act { songs ->
                    // As on a release page: shuffle goes on before the queue
                    // is built, so it is built shuffled rather than played
                    // out of order.
                    QueueShuffle.enableForNextQueue()
                    play(songs, songs.indices.random())
                }.takeIf { target.fromCard },
                onOpen = {
                    val id = target.browseId
                    browseActions = null
                    dismissPlayer()
                    if (target.fromCard) {
                        if (id != null) {
                            viewModel.openDetail(
                                browseId = id,
                                title = target.title,
                                subtitle = target.subtitle,
                                thumbnailUrl = target.thumbnailUrl,
                                type = target.type,
                            )
                        } else if (target.title.isNotBlank()) {
                            selectedTab = TAB_SEARCH
                            viewModel.searchFor(target.title)
                        }
                    }
                },"""

new_browse_actions = """                // The artist's name in the header, opened by the id that came with the
                // release. Closes the sheet first, as every other row here does.
                onOpenArtist = { id: String, name: String ->
                    browseActions = null
                    dismissPlayer()
                    if (id.isNotBlank()) {
                        viewModel.openDetail(id, name, context.getString(R.string.artist), null, BrowseType.ARTIST)
                    } else if (name.isNotBlank()) {
                        scope.launch {
                            val hit = runCatching {
                                YtMusicRepository.search(name, SearchFilter.ARTISTS).getOrNull()
                                    ?.filterIsInstance<SearchResult.Browse>()
                                    ?.firstOrNull()
                                    ?.item
                            }.getOrNull()
                            if (hit?.browseId != null) {
                                viewModel.openDetail(
                                    hit.browseId,
                                    hit.title,
                                    context.getString(R.string.artist),
                                    null,
                                    BrowseType.ARTIST,
                                )
                            }
                        }
                    }
                },
                onRenameInSheet = {
                    browseRenameInSheet = true
                    browseMenuOrigin = null
                },
                startRenaming = browseRenameInSheet,
                onPlayNext = act(playSongsNext),
                onAddToQueue = act(addSongsToQueue),
                onPlay = act { songs -> play(songs, 0) }.takeIf { target.fromCard },
                onShuffle = act { songs ->
                    // As on a release page: shuffle goes on before the queue
                    // is built, so it is built shuffled rather than played
                    // out of order.
                    QueueShuffle.enableForNextQueue()
                    play(songs, songs.indices.random())
                }.takeIf { target.fromCard },
                onOpen = {
                    val id = target.browseId
                    browseActions = null
                    dismissPlayer()
                    if (target.fromCard) {
                        if (id != null) {
                            viewModel.openDetail(
                                browseId = id,
                                title = target.title,
                                subtitle = target.subtitle,
                                thumbnailUrl = target.thumbnailUrl,
                                type = target.type,
                            )
                        } else if (target.title.isNotBlank()) {
                            scope.launch {
                                val filter = if (target.type == BrowseType.ARTIST) {
                                    SearchFilter.ARTISTS
                                } else {
                                    SearchFilter.ALBUMS
                                }
                                val query = listOfNotNull(target.title, target.subtitle.takeIf { it.isNotBlank() }).joinToString(" ")
                                val hit = runCatching {
                                    YtMusicRepository.search(query, filter).getOrNull()
                                        ?.filterIsInstance<SearchResult.Browse>()
                                        ?.firstOrNull()
                                        ?.item
                                }.getOrNull()
                                if (hit?.browseId != null) {
                                    viewModel.openDetail(
                                        browseId = hit.browseId,
                                        title = hit.title,
                                        subtitle = hit.subtitle,
                                        thumbnailUrl = hit.thumbnailUrl ?: target.thumbnailUrl,
                                        type = hit.type,
                                    )
                                }
                            }
                        }
                    }
                },"""

old_context_menu = """        HeldContextMenu(
            item = browseActions,
            held = browseMenuOrigin,
            hazeState = hazeState,
            onDismiss = { browseActions = null },
            // Tapping the lifted card opens it, as a tap on it in the list
            // would have. Not for a Local Music grouping, which has no page.
            onPreviewClick = { target ->
                browseActions = null
                dismissPlayer()
                val id = target.browseId
                if (id != null) {
                    viewModel.openDetail(
                        browseId = id,
                        title = target.title,
                        subtitle = target.subtitle,
                        thumbnailUrl = target.thumbnailUrl,
                        type = target.type,
                    )
                } else if (target.title.isNotBlank()) {
                    selectedTab = TAB_SEARCH
                    viewModel.searchFor(target.title)
                }
            },
        )"""

new_context_menu = """        HeldContextMenu(
            item = browseActions,
            held = browseMenuOrigin,
            hazeState = hazeState,
            onDismiss = { browseActions = null },
            // Tapping the lifted card opens it, as a tap on it in the list
            // would have. Not for a Local Music grouping, which has no page.
            onPreviewClick = { target ->
                browseActions = null
                dismissPlayer()
                val id = target.browseId
                if (id != null) {
                    viewModel.openDetail(
                        browseId = id,
                        title = target.title,
                        subtitle = target.subtitle,
                        thumbnailUrl = target.thumbnailUrl,
                        type = target.type,
                    )
                } else if (target.title.isNotBlank()) {
                    scope.launch {
                        val filter = if (target.type == BrowseType.ARTIST) {
                            SearchFilter.ARTISTS
                        } else {
                            SearchFilter.ALBUMS
                        }
                        val query = listOfNotNull(target.title, target.subtitle.takeIf { it.isNotBlank() }).joinToString(" ")
                        val hit = runCatching {
                            YtMusicRepository.search(query, filter).getOrNull()
                                ?.filterIsInstance<SearchResult.Browse>()
                                ?.firstOrNull()
                                ?.item
                        }.getOrNull()
                        if (hit?.browseId != null) {
                            viewModel.openDetail(
                                browseId = hit.browseId,
                                title = hit.title,
                                subtitle = hit.subtitle,
                                thumbnailUrl = hit.thumbnailUrl ?: target.thumbnailUrl,
                                type = hit.type,
                            )
                        }
                    }
                }
            },
        )"""

assert old_open_funcs in src, "old_open_funcs not found"
src = src.replace(old_open_funcs, new_open_funcs, 1)

assert old_browse_actions in src, "old_browse_actions not found"
src = src.replace(old_browse_actions, new_browse_actions, 1)

assert old_context_menu in src, "old_context_menu not found"
src = src.replace(old_context_menu, new_context_menu, 1)

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(src)

print("MainActivity.kt patched successfully!")
