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

old_chunk = '''        // ---- Album / playlist detail ----
        // ---- Long-press track actions ----
        // One body for both presentations of the track menu: the sheet the ⋮
        // and the player open, and the popup a held row lifts into. Every
        // callback below is the same in either; only the frame differs.
        val songMenuBody: @Composable (Song, SongActionsPresentation) -> Unit = { song, presentation ->
            // Set by whoever opened it — see [menuFromPlayer]. It cannot be
            // read off the player's own visibility any more, because on a
            // tablet the player is visible whatever the menu was opened from.
            val fromPlayer = menuFromPlayer
            val share: () -> Unit = {
                val sendIntent = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, "https://music.youtube.com/watch?v=${song.videoId}")
                }
                context.startActivity(Intent.createChooser(sendIntent, song.title))
                songActions = null
            }
            // Navigating has to take the player down with the sheet, or the
            // page it opens lands behind a still-covering player.
            // The track's cover stands in for an album's, but never for an
            // artist's picture — that page loads its own.
            val openPage: (String, String, String, BrowseType) -> Unit = { id, title, sub, type ->
                songActions = null
                dismissPlayer()
                val art = song.thumbnailUrl.takeUnless { type == BrowseType.ARTIST }
                viewModel.openDetail(id, title, sub, art, type)
            }
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
            }'''

new_chunk = '''        // ---- Album / playlist detail ----
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
        }
        // ---- Long-press track actions ----
        // One body for both presentations of the track menu: the sheet the ⋮
        // and the player open, and the popup a held row lifts into. Every
        // callback below is the same in either; only the frame differs.
        val songMenuBody: @Composable (Song, SongActionsPresentation) -> Unit = { song, presentation ->
            // Set by whoever opened it — see [menuFromPlayer]. It cannot be
            // read off the player's own visibility any more, because on a
            // tablet the player is visible whatever the menu was opened from.
            val fromPlayer = menuFromPlayer
            val share: () -> Unit = {
                val sendIntent = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, "https://music.youtube.com/watch?v=${song.videoId}")
                }
                context.startActivity(Intent.createChooser(sendIntent, song.title))
                songActions = null
            }
            // Navigating has to take the player down with the sheet, or the
            // page it opens lands behind a still-covering player.
            // The track's cover stands in for an album's, but never for an
            // artist's picture — that page loads its own.
            val openPage: (String, String, String, BrowseType) -> Unit = { id, title, sub, type ->
                songActions = null
                dismissPlayer()
                val art = song.thumbnailUrl.takeUnless { type == BrowseType.ARTIST }
                viewModel.openDetail(id, title, sub, art, type)
            }'''

if new_chunk in src:
    print("Patch already applied.")
else:
    assert old_chunk in src, "old_chunk not found in MainActivity.kt"
    src = src.replace(old_chunk, new_chunk, 1)
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(src)
    print("Patch applied successfully to MainActivity.kt.")
