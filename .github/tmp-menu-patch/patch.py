#!/usr/bin/env python3
import sys
import os

song_path = 'app/src/main/java/com/music/amusic/ui/components/SongActionsSheet.kt'
browse_path = 'app/src/main/java/com/music/amusic/ui/components/BrowseActionsSheet.kt'

# 1. Patch SongActionsSheet.kt
with open(song_path, 'r', encoding='utf-8') as f:
    song_src = f.read()

song_call_old = "SheetTrackHeader(song, subtitleColor = palette.onBackgroundVariant)"
song_call_new = "SheetTrackHeader(song, subtitleColor = palette.onBackgroundVariant, onOpenAlbum = onOpenAlbum, onOpenArtist = onOpenArtist)"
if song_call_old not in song_src:
    print(f"ERROR: {song_call_old} not found in {song_path}")
    sys.exit(1)
song_src_norm = song_src.replace(song_call_old, song_call_new)

sig_old = '''internal fun SheetTrackHeader(
    song: Song,
    modifier: Modifier = Modifier,
    subtitleColor: Color = MaterialTheme.colorScheme.onSurfaceVariant,
) {'''

sig_new = '''internal fun SheetTrackHeader(
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

song_src_norm = song_src_norm.replace('\r\n', '\n')
sig_old_norm = sig_old.replace('\r\n', '\n')
sig_new_norm = sig_new.replace('\r\n', '\n')
if sig_old_norm not in song_src_norm:
    print(f"ERROR: sig_old not found in {song_path}")
    sys.exit(1)
song_src_norm = song_src_norm.replace(sig_old_norm, sig_new_norm)

img_old = '''.background(MaterialTheme.colorScheme.surfaceVariant),
        )
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            ExplicitSongTitle('''

img_new = '''.background(MaterialTheme.colorScheme.surfaceVariant)
                .then(if (albumTap != null) Modifier.clickable(onClick = albumTap) else Modifier),
        )
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Box(modifier = if (albumTap != null) Modifier.clip(RoundedCornerShape(4.dp)).clickable(onClick = albumTap) else Modifier) {
                ExplicitSongTitle('''

img_old_norm = img_old.replace('\r\n', '\n')
img_new_norm = img_new.replace('\r\n', '\n')
if img_old_norm not in song_src_norm:
    print(f"ERROR: img_old not found in {song_path}")
    sys.exit(1)
song_src_norm = song_src_norm.replace(img_old_norm, img_new_norm)

title_end_old = '''color = MaterialTheme.colorScheme.onBackground,
            )
            Text(
                text = song.artist,'''

title_end_new = '''color = MaterialTheme.colorScheme.onBackground,
                )
            }
            Text(
                text = song.artist,
                modifier = if (artistTap != null) Modifier.clip(RoundedCornerShape(4.dp)).clickable(onClick = artistTap) else Modifier,'''

title_end_old_norm = title_end_old.replace('\r\n', '\n')
title_end_new_norm = title_end_new.replace('\r\n', '\n')
if title_end_old_norm not in song_src_norm:
    print(f"ERROR: title_end_old not found in {song_path}")
    sys.exit(1)
song_src_norm = song_src_norm.replace(title_end_old_norm, title_end_new_norm)

with open(song_path, 'w', encoding='utf-8') as f:
    f.write(song_src_norm)

print("SongActionsSheet.kt patched successfully.")

# 2. Patch BrowseActionsSheet.kt
with open(browse_path, 'r', encoding='utf-8') as f:
    browse_src = f.read()

browse_src_norm = browse_src.replace('\r\n', '\n')

b_call_old = "BrowseSheetHeader(target, onArtistClick = artistTap)"
b_call_new = "BrowseSheetHeader(target, onOpen = onOpen, onArtistClick = artistTap)"
if b_call_old not in browse_src_norm:
    print(f"ERROR: {b_call_old} not found in {browse_path}")
    sys.exit(1)
browse_src_norm = browse_src_norm.replace(b_call_old, b_call_new)

b_sig_old = "private fun BrowseSheetHeader(target: BrowseTarget, onArtistClick: (() -> Unit)? = null) {"
b_sig_new = "private fun BrowseSheetHeader(target: BrowseTarget, onOpen: (() -> Unit)? = null, onArtistClick: (() -> Unit)? = null) {"
if b_sig_old not in browse_src_norm:
    print(f"ERROR: {b_sig_old} not found in {browse_path}")
    sys.exit(1)
browse_src_norm = browse_src_norm.replace(b_sig_old, b_sig_new)

b_img_old = '''.background(MaterialTheme.colorScheme.surfaceVariant),
        )
        Spacer(Modifier.width(14.dp))'''
b_img_new = '''.background(MaterialTheme.colorScheme.surfaceVariant)
                .then(if (onOpen != null) Modifier.clickable(onClick = onOpen) else Modifier),
        )
        Spacer(Modifier.width(14.dp))'''
b_img_old_norm = b_img_old.replace('\r\n', '\n')
b_img_new_norm = b_img_new.replace('\r\n', '\n')
if b_img_old_norm not in browse_src_norm:
    print(f"ERROR: b_img_old not found in {browse_path}")
    sys.exit(1)
browse_src_norm = browse_src_norm.replace(b_img_old_norm, b_img_new_norm)

b_title_old = '''Text(
                text = target.title,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onBackground,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )'''

b_title_new = '''Text(
                text = target.title,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onBackground,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                modifier = if (onOpen != null) Modifier.clip(RoundedCornerShape(4.dp)).clickable(onClick = onOpen) else Modifier,
            )'''
b_title_old_norm = b_title_old.replace('\r\n', '\n')
b_title_new_norm = b_title_new.replace('\r\n', '\n')
if b_title_old_norm not in browse_src_norm:
    print(f"ERROR: b_title_old not found in {browse_path}")
    sys.exit(1)
browse_src_norm = browse_src_norm.replace(b_title_old_norm, b_title_new_norm)

with open(browse_path, 'w', encoding='utf-8') as f:
    f.write(browse_src_norm)

print("BrowseActionsSheet.kt patched successfully.")
