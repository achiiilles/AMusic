#!/usr/bin/env python3
import sys
import os

def apply_patch(file_path, replacements):
    if not os.path.exists(file_path):
        print(f"ERROR: {file_path} not found")
        sys.exit(1)
    with open(file_path, 'r', encoding='utf-8') as f:
        src = f.read()
    src = src.replace('\r\n', '\n')
    
    for old, new, desc in replacements:
        if new in src:
            print(f"INFO: {desc} already applied in {file_path}")
            continue
        if old not in src:
            print(f"ERROR: {desc} not found in {file_path}")
            sys.exit(1)
        src = src.replace(old, new, 1)
        print(f"SUCCESS: {desc} applied to {file_path}")
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(src)

# 1. SongActionsSheet.kt
song_path = 'app/src/main/java/com/music/amusic/ui/components/SongActionsSheet.kt'
song_replacements = [
    (
        '''    onAddToPlaylist: () -> Unit,
    onOpenAlbum: (String) -> Unit,
    onOpenArtist: (String) -> Unit,
    modifier: Modifier = Modifier,''',
        '''    onAddToPlaylist: () -> Unit,
    onOpenAlbum: () -> Unit,
    onOpenArtist: () -> Unit,
    modifier: Modifier = Modifier,''',
        'SongActionsSheet signature'
    ),
    (
        '''        when (val id = song.albumId) {
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
        }''',
        '''        when {
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
        }''',
        'SongActionsSheet open album/artist rows'
    ),
    (
        '''@Composable
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
    }''',
        '''@Composable
internal fun SheetTrackHeader(
    song: Song,
    modifier: Modifier = Modifier,
    subtitleColor: Color = MaterialTheme.colorScheme.onSurfaceVariant,
    onOpenAlbum: (() -> Unit)? = null,
    onOpenArtist: (() -> Unit)? = null,
) {
    val albumTap: (() -> Unit)? = onOpenAlbum
    val artistTap: (() -> Unit)? = onOpenArtist''',
        'SheetTrackHeader tap callbacks'
    )
]

# 2. BrowseActionsSheet.kt
browse_path = 'app/src/main/java/com/music/amusic/ui/components/BrowseActionsSheet.kt'
browse_replacements = [
    (
        '''            if (!menu) {
                // One artist with a channel id opens straight away, several ask which one.
                // With no id there is nothing to open by, so the name stays plain text.
                val creditArtists = target.credit?.artists.orEmpty()
                val onlyArtist = creditArtists.singleOrNull()
                val onlyArtistId = onlyArtist?.browseId
                val artistTap: (() -> Unit)? = onOpenArtist?.let { open ->
                    when {
                        creditArtists.size > 1 -> ({ choosingArtist = true })
                        onlyArtist != null && onlyArtistId != null -> ({ open(onlyArtistId, onlyArtist.name) })
                        else -> null
                    }
                }
                BrowseSheetHeader(target, onOpen = onOpen, onArtistClick = artistTap)
                HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.outline)
            }''',
        '''            if (!menu) {
                // One artist with a channel id opens straight away, several ask which one.
                // With no id there is nothing to open by, so the name stays plain text.
                val creditArtists = target.credit?.artists.orEmpty()
                val onlyArtist = creditArtists.singleOrNull()
                val onlyArtistId = onlyArtist?.browseId
                val artistTap: (() -> Unit)? = when {
                    creditArtists.size > 1 -> ({ choosingArtist = true })
                    onlyArtist != null && onlyArtistId != null && onOpenArtist != null -> ({ onOpenArtist(onlyArtistId, onlyArtist.name) })
                    onOpenArtist != null && target.subtitle.isNotBlank() -> ({
                        val candidateName = target.credit?.text?.ifBlank { null }
                            ?: target.subtitle.split("•", "·").lastOrNull()?.trim()?.ifBlank { null }
                            ?: target.subtitle.trim()
                        onOpenArtist("", candidateName)
                    })
                    else -> null
                }
                BrowseSheetHeader(target, onOpen = onOpen, onArtistClick = artistTap)
                HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.outline)
            }''',
        'BrowseActionsSheet artistTap'
    ),
    (
        '''            } else {
                SheetSubtitle(subtitleText)
            }''',
        '''            } else if (onArtistClick != null && subtitleText.isNotBlank()) {
                Text(
                    text = subtitleText,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier
                        .clip(RoundedCornerShape(4.dp))
                        .clickable(onClick = onArtistClick),
                )
            } else {
                SheetSubtitle(subtitleText)
            }''',
        'BrowseSheetHeader clickable subtitle fallback'
    )
]

# 3. MainActivity.kt
main_path = 'app/src/main/java/com/music/amusic/MainActivity.kt'
main_replacements = [
    (
        '''            val openPage: (String, String, String, BrowseType) -> Unit = { id, title, sub, type ->
                songActions = null
                dismissPlayer()
                val art = song.thumbnailUrl.takeUnless { type == BrowseType.ARTIST }
                viewModel.openDetail(id, title, sub, art, type)
            }''',
        '''            val openPage: (String, String, String, BrowseType) -> Unit = { id, title, sub, type ->
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
            }''',
        'MainActivity openAlbumForSong / openArtistForSong helpers'
    ),
    (
        '''                onOpenAlbum = { id ->
                    openPage(
                        id,
                        song.albumName ?: song.title,
                        song.artist,
                        BrowseType.ALBUM,
                    )
                },
                onOpenArtist = { id ->
                    openPage(id, song.artist, context.getString(R.string.artist), BrowseType.ARTIST)
                },''',
        '''                onOpenAlbum = { openAlbumForSong(song) },
                onOpenArtist = { openArtistForSong(song) },''',
        'MainActivity SongActionsSheet onOpenAlbum / onOpenArtist'
    ),
    (
        '''            // Tapping the lifted track opens its album, as Apple Music's does.
            onPreviewClick = { song ->
                song.albumId?.let { id ->
                    songActions = null
                    viewModel.openDetail(id, song.albumName ?: song.title, song.artist, song.thumbnailUrl, BrowseType.ALBUM)
                }
            },''',
        '''            // Tapping the lifted track opens its album, as Apple Music's does.
            onPreviewClick = { song ->
                openAlbumForSong(song)
            },''',
        'MainActivity HeldContextMenu song onPreviewClick'
    ),
    (
        '''                // The artist's name in the header, opened by the id that came with the
                // release. Closes the sheet first, as every other row here does.
                onOpenArtist = target.credit?.let {
                    { id: String, name: String ->
                        browseActions = null
                        viewModel.openDetail(id, name, "Artist", null, BrowseType.ARTIST)
                    }
                },''',
        '''                // The artist's name in the header, opened by the id that came with the
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
                },''',
        'MainActivity BrowseActionsSheet onOpenArtist'
    ),
    (
        '''                onOpen = target.browseId
                    ?.takeIf { target.fromCard }
                    ?.let { id ->
                        {
                            browseActions = null
                            viewModel.openDetail(
                                browseId = id,
                                title = target.title,
                                subtitle = target.subtitle,
                                thumbnailUrl = target.thumbnailUrl,
                                type = target.type,
                            )
                        }
                    },''',
        '''                onOpen = {
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
                },''',
        'MainActivity BrowseActionsSheet onOpen'
    ),
    (
        '''            // Tapping the lifted card opens it, as a tap on it in the list
            // would have. Not for a Local Music grouping, which has no page.
            onPreviewClick = { target ->
                target.browseId?.let { id ->
                    browseActions = null
                    viewModel.openDetail(
                        browseId = id,
                        title = target.title,
                        subtitle = target.subtitle,
                        thumbnailUrl = target.thumbnailUrl,
                        type = target.type,
                    )
                }
            },''',
        '''            // Tapping the lifted card opens it, as a tap on it in the list
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
            },''',
        'MainActivity HeldContextMenu browse onPreviewClick'
    )
]

print("Applying SongActionsSheet patches...")
apply_patch(song_path, song_replacements)

print("Applying BrowseActionsSheet patches...")
apply_patch(browse_path, browse_replacements)

print("Applying MainActivity patches...")
apply_patch(main_path, main_replacements)

print("All patches applied successfully!")
