#!/usr/bin/env python3
import sys
import os

song_path = 'app/src/main/java/com/music/amusic/ui/components/SongActionsSheet.kt'
main_path = 'app/src/main/java/com/music/amusic/MainActivity.kt'

# 1. Patch SongActionsSheet.kt
with open(song_path, 'r', encoding='utf-8') as f:
    song_src = f.read()

song_src = song_src.replace('\r\n', '\n')

func_sig_old = '''      onAddToPlaylist: () -> Unit,
      onOpenAlbum: (String) -> Unit,
      onOpenArtist: (String) -> Unit,
      modifier: Modifier = Modifier,'''

func_sig_new = '''      onAddToPlaylist: () -> Unit,
      onOpenAlbum: () -> Unit,
      onOpenArtist: () -> Unit,
      modifier: Modifier = Modifier,'''

if func_sig_old not in song_src:
    print(f"ERROR: func_sig_old not found in {song_path}")
    sys.exit(1)
song_src = song_src.replace(func_sig_old, func_sig_new, 1)

rows_old = '''          when (val id = song.albumId) {
              null -> if (resolvingLinks) {
                  LoadingActionRow(Icons.Rounded.Album, stringResource(R.string.open_album), palette)
              }
              else -> ActionRow(
                  Icons.Rounded.Album,
                  stringResource(R.string.open_album),
                  accent = palette.accent,
              ) { onOpenAlbum(id) }
          }
          when (val id = song.artistId) {
              null -> if (resolvingLinks) {
                  LoadingActionRow(Icons.Rounded.Person, stringResource(R.string.open_artist), palette)
              }
              else -> ActionRow(
                  Icons.Rounded.Person,
                  stringResource(R.string.open_artist),
                  accent = palette.accent,
              ) { onOpenArtist(id) }
          }'''

rows_new = '''          when {
              song.albumId != null || !song.albumName.isNullOrBlank() || song.title.isNotBlank() -> ActionRow(
                  Icons.Rounded.Album,
                  stringResource(R.string.open_album),
                  accent = palette.accent,
                  onClick = onOpenAlbum,
              )
              resolvingLinks -> LoadingActionRow(Icons.Rounded.Album, stringResource(R.string.open_album), palette)
          }
          when {
              song.artistId != null || song.artists.isNotEmpty() || song.artist.isNotBlank() -> ActionRow(
                  Icons.Rounded.Person,
                  stringResource(R.string.open_artist),
                  accent = palette.accent,
                  onClick = onOpenArtist,
              )
              resolvingLinks -> LoadingActionRow(Icons.Rounded.Person, stringResource(R.string.open_artist), palette)
          }'''

if rows_old not in song_src:
    print(f"ERROR: rows_old not found in {song_path}")
    sys.exit(1)
song_src = song_src.replace(rows_old, rows_new, 1)

header_old = '''  @Composable
  internal fun SheetTrackHeader(
      song: Song,
      modifier: Modifier = Modifier,
      subtitleColor: Color = MaterialTheme.colorScheme.onSurfaceVariant,
      onOpenAlbum: ((String) -> Unit)? = null,
      onOpenArtist: ((String) -> Unit)? = null,
  ) {
      val albumTap: (() -> Unit)? = onOpenAlbum?.let { open ->
          song.albumId?.let { id -> { open(id) } }
      }
      val artistTap: (() -> Unit)? = onOpenArtist?.let { open ->
          song.artistId?.let { id -> { open(id) } }
      }'''

header_new = '''  @Composable
  internal fun SheetTrackHeader(
      song: Song,
      modifier: Modifier = Modifier,
      subtitleColor: Color = MaterialTheme.colorScheme.onSurfaceVariant,
      onOpenAlbum: (() -> Unit)? = null,
      onOpenArtist: (() -> Unit)? = null,
  ) {
      val albumTap: (() -> Unit)? = onOpenAlbum
      val artistTap: (() -> Unit)? = onOpenArtist'''

if header_old not in song_src:
    print(f"ERROR: header_old not found in {song_path}")
    sys.exit(1)
song_src = song_src.replace(header_old, header_new, 1)

with open(song_path, 'w', encoding='utf-8') as f:
    f.write(song_src)

print("SongActionsSheet.kt patched successfully.")

# 2. Patch MainActivity.kt
with open(main_path, 'r', encoding='utf-8') as f:
    main_src = f.read()

main_src = main_src.replace('\r\n', '\n')

actions_old = '''                onOpenAlbum = { id ->
                    openPage(
                        id,
                        song.albumName ?: song.title,
                        song.artist,
                        BrowseType.ALBUM,
                    )
                },
                onOpenArtist = { id ->
                    openPage(id, song.artist, context.getString(R.string.artist), BrowseType.ARTIST)
                },'''

actions_new = '''                onOpenAlbum = {
                    songActions = null
                    dismissPlayer()
                    val albumBrowseId = song.albumId
                    val albumName = song.albumName ?: song.title
                    openByName(
                        browseId = albumBrowseId,
                        name = albumName,
                        subtitle = song.artist,
                        type = BrowseType.ALBUM,
                        artwork = song.thumbnailUrl,
                    )
                },
                onOpenArtist = {
                    songActions = null
                    dismissPlayer()
                    val artistBrowseId = song.artistId ?: song.artists.firstOrNull()?.browseId
                    val artistName = song.artists.firstOrNull()?.name?.ifBlank { null } ?: song.artist
                    openByName(
                        browseId = artistBrowseId,
                        name = artistName,
                        subtitle = null,
                        type = BrowseType.ARTIST,
                    )
                },'''

if actions_old not in main_src:
    print(f"ERROR: actions_old not found in {main_path}")
    sys.exit(1)
main_src = main_src.replace(actions_old, actions_new, 1)

preview_old = '''            // Tapping the lifted track opens its album, as Apple Music's does.
            onPreviewClick = { song ->
                song.albumId?.let { id ->
                    songActions = null
                    viewModel.openDetail(id, song.albumName ?: song.title, song.artist, song.thumbnailUrl, BrowseType.ALBUM)
                }
            },'''

preview_new = '''            // Tapping the lifted track opens its album, as Apple Music's does.
            onPreviewClick = { song ->
                songActions = null
                dismissPlayer()
                val albumBrowseId = song.albumId
                val albumName = song.albumName ?: song.title
                openByName(
                    browseId = albumBrowseId,
                    name = albumName,
                    subtitle = song.artist,
                    type = BrowseType.ALBUM,
                    artwork = song.thumbnailUrl,
                )
            },'''

if preview_old not in main_src:
    print(f"ERROR: preview_old not found in {main_path}")
    sys.exit(1)
main_src = main_src.replace(preview_old, preview_new, 1)

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_src)

print("MainActivity.kt patched successfully.")
