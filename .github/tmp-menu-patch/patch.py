#!/usr/bin/env python3
import sys
import os

song_path = 'app/src/main/java/com/music/amusic/ui/components/SongActionsSheet.kt'
browse_path = 'app/src/main/java/com/music/amusic/ui/components/BrowseActionsSheet.kt'

# 1. Patch SongActionsSheet.kt
with open(song_path, 'r', encoding='utf-8') as f:
    song_src = f.read()

call_old = "SheetTrackHeader(song, subtitleColor = palette.onBackgroundVariant)"
call_new = "SheetTrackHeader(song, subtitleColor = palette.onBackgroundVariant, onOpenAlbum = onOpenAlbum, onOpenArtist = onOpenArtist)"

if call_old not in song_src:
    print(f"ERROR: {call_old} not found in {song_path}")
    sys.exit(1)

song_src = song_src.replace(call_old, call_new)

header_old = """@Composable
internal fun SheetTrackHeader(
    song: Song,
    modifier: Modifier = Modifier,
    subtitleColor: Color = MaterialTheme.colorScheme.onSurfaceVariant,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        AsyncImage(
            model = song.artworkAt(ROW_ART_PX),
            contentDescription = null,
            modifier = Modifier
                .size(52.dp)
                .clip(RoundedCornerShape(8.dp))
                .thumbnailBorder(RoundedCornerShape(8.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant),
        )
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            ExplicitSongTitle(
                song = song,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onBackground,
            )
            Text(
                text = song.artist,
                style = MaterialTheme.typography.bodyMedium,
                color = subtitleColor,
                maxLines = 1,
                overffow = TextOverflow.Ellipsis,
            )
        }
    }
}"""

header_new = """@Composable
internal fun SheetTrackHeader(
    song: Song,
    modifier: Modifier = Modifier,
    subtitleColor: Color = MaterialTheme.colorScheme.onSurfaceVariant,
    onOpenAlbum: ((String) -> Unit)? = null,
    onOpenArtist: ((String) -> Unit)? = null,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        val albumTap: (() -> Unit)? = onOpenAlbum?.let { open ->
            song.albumId?.let { id -> { open(id) } }
        }
        val artistTap: (() -> Unit)? = onOpenArtist?.let { open ->
            song.artistId?.let { id -> { open(id) } }
        }
        AsyncImage(
            model = song.artworkAt(ROW_ART_PX),
            contentDescription = null,
            modifier = Modifier
                .size(52.dp)
                .clip(RoundedCornerShape(8.dp))
                .thumbnailBorder(RoundedCornerShape(8.dp))
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .then(if (albumTap != null) Modifier.clickable(onClick = albumTap) else Modifier),
        )
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Box(modifier = if (albumTap != null) Modifier.clip(RoundedCornerShape(4.dp)).clickable(onClick = albumTap) else Modifier) {
                ExplicitSongTitle(
                    song = song,
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onBackground,
                )
            }
            Text(
                text = song.artist,
                style = MaterialTheme.typography.bodyMedium,
                color = subtitleColor,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = if (artistTap != null) Modifier.clip(RoundedCornerShape(4.dp)).clickable(onClick = artistTap) else Modifier,
            )
        }
    }
}"""

song_src_norm = song_src.replace('\r\n', '\n')
header_old_norm = header_old.replace('\r\n', '\n')
header_new_norm = header_new.replace('\r\n', '\n')

if header_old_norm not in song_src_norm:
    print(f"ERROR: header_old not found in {song_path}")
    sys.exit(1)

song_src_norm = song_src_norm.replace(header_old_norm, header_new_norm)

with open(song_path, 'w', encoding='utf-8') as f:
    f.write(song_src_norm)

print("SongActionsSheet.kt patched successfully.")

# 2. Patch BrowseActionsSheet.kt
with open(browse_path, 'r', encoding='utf-8') as f:
    browse_src = f.read()

b_call_old = "BrowseSheetHeader(target, onArtistClick = artistTap)"
b_call_new = "BrowseSheetHeader(target, onOpen = onOpen, onArtistClick = artistTap)"

if b_call_old not in browse_src:
    print(f"ERROR: {b_call_old} not found in {browse_path}")
    sys.exit(1)

browse_src = browse_src.replace(b_call_old, b_call_new)

b_header_old = """@Composable
private fun BrowseSheetHeader(target: BrowseTarget, onArtistClick: (() -> Unit)? = null) {
    val shape = if (target.type == BrowseType.ARTIST) CircleShape else RoundedCornerShape(8.dp)
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        AsyncImage(
            model = target.thumbnailUrl.artworkAt(ROW_ART_PX),
            contentDescription = null,
            modifier = Modifier
                .size(52.dp)
                .clip(shape)
                .thumbnailBorder(shape)
                .background(MaterialTheme.colorScheme.surfaceVariant),
        )
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text(
                text = target.title,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onBackground,
                maxLines = 1,
                overffow = TextOverflow.Ellipsis,
            )"""

b_header_new = """@Composable
private fun BrowseSheetHeader(
    target: BrowseTarget,
    onOpen: (() -> Unit)? = null,
    onArtistClick: (() -> Unit)? = null,
) {
    val shape = if (target.type == BrowseType.ARTIST) CircleShape else RoundedCornerShape(8.dp)
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        AsyncImage(
            model = target.thumbnailUrl.artworkAt(ROW_ART_PX),
            contentDescription = null,
            modifier = Modifier
                .size(52.dp)
                .clip(shape)
                .thumbnailBorder(shape)
                .background(MaterialTheme.colorScheme.surfaceVariant)
                .then(if (onOpen != null) Modifier.clickable(onClick = onOpen) else Modifier),
        )
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text(
                text = target.title,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onBackground,
                maxLines = 1,
                overffow = TextOverflow.Ellipsis,
                modifier = if (onOpen != null) Modifier.clip(RoundedCornerShape(4.dp)).clickable(onClick = onOpen) else Modifier,
            )"""

browse_src_norm = browse_src.replace('\r\n', '\n')
b_header_old_norm = b_header_old.replace('\r\n', '\n')
b_header_new_norm = b_header_new.replace('\r\n', '\n')

if b_header_old_norm not in browse_src_norm:
    print(f"ERROR: b_header_old not found in {browse_path}")
    sys.exit(1)

browse_src_norm = browse_src_norm.replace(b_header_old_norm, b_header_new_norm)

with open(browse_path, 'w', encoding='utf-8') as f:
    f.write(browse_src_norm)

print("BrowseActionsSheet.kt patched successfully.")
