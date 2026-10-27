import os
import re
import urllib.request

print("--- Step 1: Downloading SF Symbols and generating Android Vector Drawables ---")

SYMBOLS = {
    "ic_sf_share": "square.and.arrow.up",
    "ic_sf_play_next": "text.line.first.and.arrowtriangle.forward",
    "ic_sf_play_last": "text.line.last.and.arrowtriangle.forward",
    "ic_sf_radio": "dot.radiowaves.left.and.right",
    "ic_sf_heart": "heart",
    "ic_sf_heart_fill": "heart.fill",
    "ic_sf_thumbsdown": "hand.thumbsdown",
    "ic_sf_playlist_add": "text.badge.plus",
    "ic_sf_playlist_remove": "text.badge.minus",
    "ic_sf_library_add": "plus",
    "ic_sf_library_check": "checkmark",
    "ic_sf_download": "arrow.down.circle",
    "ic_sf_download_done": "checkmark.circle",
    "ic_sf_error": "exclamationmark.circle",
    "ic_sf_sleep_timer": "moon.zzz",
    "ic_sf_lyrics_offset": "slider.horizontal.3",
    "ic_sf_revert": "arrow.uturn.backward",
    "ic_sf_sparkles": "sparkles",
    "ic_sf_video": "video",
    "ic_sf_sort": "arrow.up.arrow.down",
    "ic_sf_play": "play.fill",
    "ic_sf_pencil": "pencil",
    "ic_sf_trash": "trash",
    "ic_sf_trash_fill": "trash.fill",
    "ic_sf_upload": "arrow.up.circle",
    "ic_sf_bug": "ant",
}

drawable_dir = "app/src/main/res/drawable"
os.makedirs(drawable_dir, exist_ok=True)

for drawable_name, sf_name in SYMBOLS.items():
    url = f"https://raw.githubusercontent.com/brendanballon/sfsymbols-svg/master/symbols/{sf_name}.svg"
    req = urllib.request.Request(url, headers={'User-Agent': 'AMusic-SF-Patch/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        svg_text = resp.read().decode('utf-8')
    
    w_match = re.search(r"width=['\"]([\d.]+)px?['\"]", svg_text)
    h_match = re.search(r"height=['\"]([\d.]+)px?['\"]", svg_text)
    assert w_match and h_match, f"Dimensions not found in {sf_name}"
    w = float(w_match.group(1))
    h = float(h_match.group(1))
    
    paths = re.findall(r"<path[^>]*\bd=['\"]([^'\"]+)['\"]", svg_text, re.DOTALL)
    assert len(paths) > 0, f"Paths not found in {sf_name}"
    
    s = max(w, h) * 1.15
    tx = round((s - w) / 2.0, 2)
    ty = round((s - h) / 2.0 + h, 2)
    s = round(s, 2)
    
    path_elements = "\n".join([f'        <path android:fillColor="#FFFFFFFF" android:pathData="{" ".join(p.split())}" />' for p in paths])
    
    xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="{s}"
    android:viewportHeight="{s}">
    <group
        android:translateX="{tx}"
        android:translateY="{ty}"
        android:scaleY="-1">
{path_elements}
    </group>
</vector>
"""
    out_path = os.path.join(drawable_dir, f"{drawable_name}.xml")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    print(f"Generated {out_path} from SF Symbol {sf_name}")

print("--- Step 2: Patching SongActionsSheet.kt ---")
song_sheet_path = "app/src/main/java/com/music/amusic/ui/components/SongActionsSheet.kt"
assert os.path.exists(song_sheet_path), f"File {song_sheet_path} not found"
with open(song_sheet_path, "r", encoding="utf-8") as f:
    song_sheet = f.read().replace("\r\n", "\n")

# 1. Imports
if "import androidx.compose.ui.res.painterResource" not in song_sheet:
    song_sheet = song_sheet.replace(
        "import com.music.amusic.R\n",
        "import com.music.amusic.R\nimport androidx.compose.ui.res.painterResource\nimport androidx.compose.ui.graphics.painter.Painter\nimport androidx.compose.ui.graphics.vector.rememberVectorPainter\n",
        1
    )

# 2. ActionRow overloads
old_action_row = """@Composable
internal fun ActionRow(
    icon: ImageVector,
    label: String,
    value: String? = null,
    tint: Color? = null,
    accent: Color = MaterialTheme.colorScheme.primary,
    enabled: Boolean = true,
    animateLabel: Boolean = false,
    onClick: () -> Unit,
) {
    val menu = LocalActionRowStyle.current == ActionRowStyle.Menu
    // The popup sits on a surface rather than the page background, so its
    // text follows the surface's colour — the two differ in light mode.
    val foreground = if (menu) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onBackground
    val alpha = if (enabled) 1f else 0.4f
    val iconView: @Composable () -> Unit = {
        Crossfade(targetState = icon, animationSpec = tween(durationMillis = 200), label = "actionIcon") { shown ->
            Icon(
                imageVector = shown,
                contentDescription = null,
                tint = (tint ?: foreground).copy(alpha = alpha),
                modifier = Modifier.size(if (menu) 20.dp else 22.dp),
            )
        }
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = enabled, onClick = onClick)
            .then(
                if (menu) {
                    Modifier.heightIn(min = 46.dp).padding(horizontal = 18.dp, vertical = 11.dp)
                } else {
                    Modifier.padding(horizontal = 22.dp, vertical = 15.dp)
                },
            ),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // A context menu reads label-first with the glyph at the far edge;
        // the sheet keeps the glyph leading, like every other list in the app.
        if (!menu) {
            iconView()
            Spacer(Modifier.width(18.dp))
        }
        if (animateLabel) {
            Box(Modifier.weight(1f)) {
                Crossfade(targetState = label, animationSpec = tween(durationMillis = 200), label = "actionLabel") { shown ->
                    Text(
                        text = shown,
                        style = MaterialTheme.typography.bodyLarge,
                        color = foreground.copy(alpha = alpha),
                        maxLines = if (menu) 2 else Int.MAX_VALUE,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
        } else {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                color = foreground.copy(alpha = alpha),
                maxLines = if (menu) 2 else Int.MAX_VALUE,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f),
            )
        }
        if (value != null) {
            Spacer(Modifier.width(12.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.bodyLarge,
                color = accent.copy(alpha = alpha),
                maxLines = 1,
            )
        }
        if (menu) {
            Spacer(Modifier.width(14.dp))
            iconView()
        }
    }
}"""

new_action_row = """@Composable
internal fun ActionRow(
    painter: Painter,
    label: String,
    value: String? = null,
    tint: Color? = null,
    accent: Color = MaterialTheme.colorScheme.primary,
    enabled: Boolean = true,
    animateLabel: Boolean = false,
    onClick: () -> Unit,
) {
    val menu = LocalActionRowStyle.current == ActionRowStyle.Menu
    val foreground = if (menu) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onBackground
    val alpha = if (enabled) 1f else 0.4f
    val iconView: @Composable () -> Unit = {
        Crossfade(targetState = painter, animationSpec = tween(durationMillis = 200), label = "actionIcon") { shown ->
            Icon(
                painter = shown,
                contentDescription = null,
                tint = (tint ?: foreground).copy(alpha = alpha),
                modifier = Modifier.size(if (menu) 20.dp else 22.dp),
            )
        }
    }
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = enabled, onClick = onClick)
            .then(
                if (menu) {
                    Modifier.heightIn(min = 46.dp).padding(horizontal = 18.dp, vertical = 11.dp)
                } else {
                    Modifier.padding(horizontal = 22.dp, vertical = 15.dp)
                },
            ),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (!menu) {
            iconView()
            Spacer(Modifier.width(18.dp))
        }
        if (animateLabel) {
            Box(Modifier.weight(1f)) {
                Crossfade(targetState = label, animationSpec = tween(durationMillis = 200), label = "actionLabel") { shown ->
                    Text(
                        text = shown,
                        style = MaterialTheme.typography.bodyLarge,
                        color = foreground.copy(alpha = alpha),
                        maxLines = if (menu) 2 else Int.MAX_VALUE,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
        } else {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyLarge,
                color = foreground.copy(alpha = alpha),
                maxLines = if (menu) 2 else Int.MAX_VALUE,
                overflow = TextOverflow.Ellipsis,
                modifier = Modifier.weight(1f),
            )
        }
        if (value != null) {
            Spacer(Modifier.width(12.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.bodyLarge,
                color = accent.copy(alpha = alpha),
                maxLines = 1,
            )
        }
        if (menu) {
            Spacer(Modifier.width(14.dp))
            iconView()
        }
    }
}

@Composable
internal fun ActionRow(
    icon: ImageVector,
    label: String,
    value: String? = null,
    tint: Color? = null,
    accent: Color = MaterialTheme.colorScheme.primary,
    enabled: Boolean = true,
    animateLabel: Boolean = false,
    onClick: () -> Unit,
) {
    ActionRow(
        painter = rememberVectorPainter(icon),
        label = label,
        value = value,
        tint = tint,
        accent = accent,
        enabled = enabled,
        animateLabel = animateLabel,
        onClick = onClick,
    )
}"""

assert old_action_row in song_sheet, "old ActionRow block not found in SongActionsSheet.kt"
song_sheet = song_sheet.replace(old_action_row, new_action_row, 1)

# 3. Main actions in SongActionsSheet
old_rows_block = """        if (onRollbackToOriginal != null || onUpgradeQuality != null || onToggleAudioVersion != null) {
            (onRollbackToOriginal ?: onUpgradeQuality)?.let {
                ActionRow(
                    icon = if (onRollbackToOriginal != null) {
                        Icons.AutoMirrored.Rounded.Undo
                    } else {
                        Icons.Rounded.HighQuality
                    },
                    label = stringResource(
                        if (onRollbackToOriginal != null) {
                            R.string.revert_to_original
                        } else {
                            R.string.upgrade_quality
                        },
                    ),
                    accent = palette.accent,
                    enabled = onRollbackToOriginal != null || !upgradeQualityInProgress,
                    onClick = it,
                )
            }
            // Which recording, not which quality — a different question from
            // the row above, so it sits right under it rather than merged
            // into it, but still ahead of the divider both share.
            onToggleAudioVersion?.let {
                ActionRow(
                    icon = if (isAudioVersion) Icons.Rounded.Videocam else AMusicIcons.MusicNote,
                    label = stringResource(
                        if (isAudioVersion) R.string.convert_to_video else R.string.convert_to_audio,
                    ),
                    accent = palette.accent,
                    onClick = it,
                )
            }
            GroupSeparator(palette)
        }

        if (signedIn && !isOffline) {
            ActionRow(
                icon = if (liked) Icons.Rounded.Favorite else Icons.Rounded.FavoriteBorder,
                label = if (liked) stringResource(R.string.remove_from_liked) else stringResource(R.string.like),
                tint = if (liked) palette.accent else null,
                accent = palette.accent,
                animateLabel = true,
                onClick = onToggleLike,
            )
            ActionRow(
                icon = if (disliked) Icons.Rounded.ThumbDown else Icons.Rounded.ThumbDownOffAlt,
                label = if (disliked) stringResource(R.string.undo_dislike) else stringResource(R.string.dislike),
                tint = if (disliked) palette.accent else null,
                accent = palette.accent,
                animateLabel = true,
                onClick = onToggleDislike,
            )
            ActionRow(
                icon = Icons.AutoMirrored.Rounded.PlaylistAdd,
                label = stringResource(R.string.add_to_playlist),
                accent = palette.accent,
                onClick = onAddToPlaylist,
            )
            onRemoveFromPlaylist?.let {
                ActionRow(
                    icon = Icons.Rounded.PlaylistRemove,
                    label = stringResource(R.string.remove_from_playlist),
                    accent = palette.accent,
                    onClick = it,
                )
            }
            onToggleLibrary?.let {
                ActionRow(
                    icon = if (inLibrary) Icons.Rounded.LibraryAddCheck else Icons.Rounded.LibraryAdd,
                    label = stringResource(
                        if (inLibrary) R.string.remove_from_library else R.string.add_to_library,
                    ),
                    accent = palette.accent,
                    animateLabel = true,
                    onClick = it,
                )
            }
            GroupSeparator(palette)
        }

        DownloadRow(song, palette, isOffline, onDownload)
        WebDavUploadRow(song, palette, isOffline, onUploadToWebDav)
        ActionRow(
            icon = Icons.Rounded.Radio,
            label = stringResource(R.string.start_radio),
            accent = palette.accent,
            onClick = onStartRadio,
        )
        ActionRow(
            icon = Icons.AutoMirrored.Rounded.PlaylistPlay,
            label = stringResource(R.string.play_next),
            accent = palette.accent,
            onClick = onPlayNext,
        )
        ActionRow(
            icon = Icons.AutoMirrored.Rounded.QueueMusic,
            label = stringResource(R.string.add_to_queue),
            accent = palette.accent,
            onClick = onAddToQueue,
        )
        if (showSleepTimer) {
            ActionRow(
                icon = Icons.Rounded.Bedtime,
                label = stringResource(R.string.sleep_timer),
                value = sleepTimerStatus(),
                accent = palette.accent,
            ) { pickingSleepTimer = true }
        }
        // Deliberately outside the online-only block below. Local files and
        // completed downloads use the same player lyric clock (including
        // embedded synced lyrics), so they need this control just as much as
        // streamed songs do.
        onLyricsOffset?.let {
            ActionRow(
                icon = Icons.Rounded.Tune,
                label = stringResource(R.string.lyrics_offset),
                accent = palette.accent,
                onClick = it,
            )
        }
        if (!isOffline) {
            onShare?.let {
                ActionRow(Icons.Rounded.Share, stringResource(R.string.share), accent = palette.accent, onClick = it)
            }
        }
        // Last, and only from the player: it is about the track playing right
        // now rather than about the song as a thing in a library, and it is
        // the one row here nobody reaches for by accident.
        onCopyLog?.let {
            ActionRow(Icons.Rounded.BugReport, stringResource(R.string.copy_log), accent = palette.accent, onClick = it)
        }"""

new_rows_block = """        if (onRollbackToOriginal != null || onUpgradeQuality != null || onToggleAudioVersion != null) {
            (onRollbackToOriginal ?: onUpgradeQuality)?.let {
                ActionRow(
                    painter = if (onRollbackToOriginal != null) {
                        painterResource(R.drawable.ic_sf_revert)
                    } else {
                        painterResource(R.drawable.ic_sf_sparkles)
                    },
                    label = stringResource(
                        if (onRollbackToOriginal != null) {
                            R.string.revert_to_original
                        } else {
                            R.string.upgrade_quality
                        },
                    ),
                    accent = palette.accent,
                    enabled = onRollbackToOriginal != null || !upgradeQualityInProgress,
                    onClick = it,
                )
            }
            // Which recording, not which quality — a different question from
            // the row above, so it sits right under it rather than merged
            // into it, but still ahead of the divider both share.
            onToggleAudioVersion?.let {
                ActionRow(
                    painter = if (isAudioVersion) painterResource(R.drawable.ic_sf_video) else rememberVectorPainter(AMusicIcons.MusicNote),
                    label = stringResource(
                        if (isAudioVersion) R.string.convert_to_video else R.string.convert_to_audio,
                    ),
                    accent = palette.accent,
                    onClick = it,
                )
            }
            GroupSeparator(palette)
        }

        if (signedIn && !isOffline) {
            ActionRow(
                painter = if (liked) painterResource(R.drawable.ic_sf_heart_fill) else painterResource(R.drawable.ic_sf_heart),
                label = if (liked) stringResource(R.string.remove_from_liked) else stringResource(R.string.like),
                tint = if (liked) palette.accent else null,
                accent = palette.accent,
                animateLabel = true,
                onClick = onToggleLike,
            )
            ActionRow(
                painter = painterResource(R.drawable.ic_sf_thumbsdown),
                label = if (disliked) stringResource(R.string.undo_dislike) else stringResource(R.string.dislike),
                tint = if (disliked) palette.accent else null,
                accent = palette.accent,
                animateLabel = true,
                onClick = onToggleDislike,
            )
            ActionRow(
                painter = painterResource(R.drawable.ic_sf_playlist_add),
                label = stringResource(R.string.add_to_playlist),
                accent = palette.accent,
                onClick = onAddToPlaylist,
            )
            onRemoveFromPlaylist?.let {
                ActionRow(
                    painter = painterResource(R.drawable.ic_sf_playlist_remove),
                    label = stringResource(R.string.remove_from_playlist),
                    accent = palette.accent,
                    onClick = it,
                )
            }
            onToggleLibrary?.let {
                ActionRow(
                    painter = if (inLibrary) painterResource(R.drawable.ic_sf_library_check) else painterResource(R.drawable.ic_sf_library_add),
                    label = stringResource(
                        if (inLibrary) R.string.remove_from_library else R.string.add_to_library,
                    ),
                    accent = palette.accent,
                    animateLabel = true,
                    onClick = it,
                )
            }
            GroupSeparator(palette)
        }

        DownloadRow(song, palette, isOffline, onDownload)
        WebDavUploadRow(song, palette, isOffline, onUploadToWebDav)
        ActionRow(
            painter = painterResource(R.drawable.ic_sf_radio),
            label = stringResource(R.string.start_radio),
            accent = palette.accent,
            onClick = onStartRadio,
        )
        ActionRow(
            painter = painterResource(R.drawable.ic_sf_play_next),
            label = stringResource(R.string.play_next),
            accent = palette.accent,
            onClick = onPlayNext,
        )
        ActionRow(
            painter = painterResource(R.drawable.ic_sf_play_last),
            label = stringResource(R.string.add_to_queue),
            accent = palette.accent,
            onClick = onAddToQueue,
        )
        if (showSleepTimer) {
            ActionRow(
                painter = painterResource(R.drawable.ic_sf_sleep_timer),
                label = stringResource(R.string.sleep_timer),
                value = sleepTimerStatus(),
                accent = palette.accent,
            ) { pickingSleepTimer = true }
        }
        // Deliberately outside the online-only block below. Local files and
        // completed downloads use the same player lyric clock (including
        // embedded synced lyrics), so they need this control just as much as
        // streamed songs do.
        onLyricsOffset?.let {
            ActionRow(
                painter = painterResource(R.drawable.ic_sf_lyrics_offset),
                label = stringResource(R.string.lyrics_offset),
                accent = palette.accent,
                onClick = it,
            )
        }
        if (!isOffline) {
            onShare?.let {
                ActionRow(painter = painterResource(R.drawable.ic_sf_share), label = stringResource(R.string.share), accent = palette.accent, onClick = it)
            }
        }
        // Last, and only from the player: it is about the track playing right
        // now rather than about the song as a thing in a library, and it is
        // the one row here nobody reaches for by accident.
        onCopyLog?.let {
            ActionRow(painter = painterResource(R.drawable.ic_sf_bug), label = stringResource(R.string.copy_log), accent = palette.accent, onClick = it)
        }"""

assert old_rows_block in song_sheet, "old rows block not found in SongActionsSheet.kt"
song_sheet = song_sheet.replace(old_rows_block, new_rows_block, 1)

# 4. DownloadRow
old_download_block = """        when (val state = active[song.videoId]) {
            is DownloadState.Queued -> ActionRow(
                icon = Icons.Rounded.Downloading,
                label = stringResource(R.string.queued),
                value = stringResource(R.string.cancel),
                accent = palette.accent,
            ) { Downloads.cancel(song.videoId) }

            is DownloadState.Running -> ActionRow(
                icon = Icons.Rounded.Downloading,
                label = stringResource(R.string.download_notification_title),
                // Indeterminate until the first response names a length; a
                // stuck "0%" reads as broken where a bare label reads as starting.
                value = if (state.fraction > 0f) "${(state.fraction * 100).toInt()}%" else null,
                tint = palette.accent,
                accent = palette.accent,
            ) { Downloads.cancel(song.videoId) }

            is DownloadState.Failed -> ActionRow(
                icon = Icons.Rounded.ErrorOutline,
                label = state.reason,
                value = stringResource(R.string.retry),
                // Not the artwork's colour: a failure has to stay legible as a
                // failure whatever the sleeve happens to be tinted.
                tint = MaterialTheme.colorScheme.error,
                accent = MaterialTheme.colorScheme.error,
                onClick = onDownload,
            )

            null -> if (file != null) {
                ActionRow(
                    icon = Icons.Rounded.DownloadDone,
                    label = stringResource(R.string.saved_to_downloads),
                    value = stringResource(R.string.delete),
                    tint = palette.accent,
                    accent = palette.accent,
                ) { scope.launch { Downloads.delete(context, song.videoId) } }
            } else if (!isOffline) {
                ActionRow(
                    icon = Icons.Rounded.Download,
                    label = stringResource(R.string.download),
                    accent = palette.accent,
                    onClick = onDownload,
                )
            }
        }"""

new_download_block = """        when (val state = active[song.videoId]) {
            is DownloadState.Queued -> ActionRow(
                painter = painterResource(R.drawable.ic_sf_download),
                label = stringResource(R.string.queued),
                value = stringResource(R.string.cancel),
                accent = palette.accent,
            ) { Downloads.cancel(song.videoId) }

            is DownloadState.Running -> ActionRow(
                painter = painterResource(R.drawable.ic_sf_download),
                label = stringResource(R.string.download_notification_title),
                value = if (state.fraction > 0f) "${(state.fraction * 100).toInt()}%" else null,
                tint = palette.accent,
                accent = palette.accent,
            ) { Downloads.cancel(song.videoId) }

            is DownloadState.Failed -> ActionRow(
                painter = painterResource(R.drawable.ic_sf_error),
                label = state.reason,
                value = stringResource(R.string.retry),
                tint = MaterialTheme.colorScheme.error,
                accent = MaterialTheme.colorScheme.error,
                onClick = onDownload,
            )

            null -> if (file != null) {
                ActionRow(
                    painter = painterResource(R.drawable.ic_sf_download_done),
                    label = stringResource(R.string.saved_to_downloads),
                    value = stringResource(R.string.delete),
                    tint = palette.accent,
                    accent = palette.accent,
                ) { scope.launch { Downloads.delete(context, song.videoId) } }
            } else if (!isOffline) {
                ActionRow(
                    painter = painterResource(R.drawable.ic_sf_download),
                    label = stringResource(R.string.download),
                    accent = palette.accent,
                    onClick = onDownload,
                )
            }
        }"""

assert old_download_block in song_sheet, "old download block not found in SongActionsSheet.kt"
song_sheet = song_sheet.replace(old_download_block, new_download_block, 1)

# 5. WebDavUploadRow
old_webdav_block = """        when (val state = active[song.videoId]) {
            is WebDavUploads.TrackState.Running -> ActionRow(
                icon = Icons.Rounded.FileUpload,
                label = stringResource(R.string.upload_to_webdav),
                value = "${(state.fraction * 100).toInt()}%",
                tint = palette.accent,
                accent = palette.accent,
                // In flight already; there is no cancel, so the row only reports.
                onClick = {},
            )
            is WebDavUploads.TrackState.Failed -> ActionRow(
                icon = Icons.Rounded.FileUpload,
                label = state.reason,
                value = stringResource(R.string.try_again),
                tint = MaterialTheme.colorScheme.error,
                accent = MaterialTheme.colorScheme.error,
                onClick = onUpload,
            )
            else -> ActionRow(
                icon = Icons.Rounded.FileUpload,
                label = stringResource(R.string.upload_to_webdav),
                accent = palette.accent,
                onClick = onUpload,
            )
        }"""

new_webdav_block = """        when (val state = active[song.videoId]) {
            is WebDavUploads.TrackState.Running -> ActionRow(
                painter = painterResource(R.drawable.ic_sf_upload),
                label = stringResource(R.string.upload_to_webdav),
                value = "${(state.fraction * 100).toInt()}%",
                tint = palette.accent,
                accent = palette.accent,
                onClick = {},
            )
            is WebDavUploads.TrackState.Failed -> ActionRow(
                painter = painterResource(R.drawable.ic_sf_upload),
                label = state.reason,
                value = stringResource(R.string.try_again),
                tint = MaterialTheme.colorScheme.error,
                accent = MaterialTheme.colorScheme.error,
                onClick = onUpload,
            )
            else -> ActionRow(
                painter = painterResource(R.drawable.ic_sf_upload),
                label = stringResource(R.string.upload_to_webdav),
                accent = palette.accent,
                onClick = onUpload,
            )
        }"""

assert old_webdav_block in song_sheet, "old webdav block not found in SongActionsSheet.kt"
song_sheet = song_sheet.replace(old_webdav_block, new_webdav_block, 1)

with open(song_sheet_path, "w", encoding="utf-8") as f:
    f.write(song_sheet)
print("Successfully patched SongActionsSheet.kt")

print("--- Step 3: Patching BrowseActionsSheet.kt ---")
browse_sheet_path = "app/src/main/java/com/music/amusic/ui/components/BrowseActionsSheet.kt"
assert os.path.exists(browse_sheet_path), f"File {browse_sheet_path} not found"
with open(browse_sheet_path, "r", encoding="utf-8") as f:
    browse_sheet = f.read().replace("\r\n", "\n")

if "import androidx.compose.ui.res.painterResource" not in browse_sheet:
    browse_sheet = browse_sheet.replace(
        "import com.music.amusic.R\n",
        "import com.music.amusic.R\nimport androidx.compose.ui.res.painterResource\n",
        1
    )

old_browse_rows = """            onSort?.let { ActionRow(Icons.Rounded.Sort, stringResource(R.string.sort_songs), onClick = it) }
            onPlay?.let { ActionRow(Icons.Rounded.PlayArrow, stringResource(R.string.play), onClick = it) }
            onShuffle?.let { ActionRow(AMusicIcons.Shuffle, stringResource(R.string.shuffle), onClick = it) }
            ActionRow(
                Icons.AutoMirrored.Rounded.PlaylistPlay,
                stringResource(R.string.play_next),
                onClick = onPlayNext,
            )
            ActionRow(
                Icons.AutoMirrored.Rounded.QueueMusic,
                stringResource(R.string.add_to_queue),
                onClick = onAddToQueue,
            )"""

new_browse_rows = """            onSort?.let { ActionRow(painter = painterResource(R.drawable.ic_sf_sort), label = stringResource(R.string.sort_songs), onClick = it) }
            onPlay?.let { ActionRow(painter = painterResource(R.drawable.ic_sf_play), label = stringResource(R.string.play), onClick = it) }
            onShuffle?.let { ActionRow(AMusicIcons.Shuffle, stringResource(R.string.shuffle), onClick = it) }
            ActionRow(
                painter = painterResource(R.drawable.ic_sf_play_next),
                label = stringResource(R.string.play_next),
                onClick = onPlayNext,
            )
            ActionRow(
                painter = painterResource(R.drawable.ic_sf_play_last),
                label = stringResource(R.string.add_to_queue),
                onClick = onAddToQueue,
            )"""

assert old_browse_rows in browse_sheet, "old browse rows not found in BrowseActionsSheet.kt"
browse_sheet = browse_sheet.replace(old_browse_rows, new_browse_rows, 1)

old_share_row = """            onShare?.let {
                ActionRow(Icons.Rounded.Share, stringResource(R.string.share), onClick = it)
            }"""
new_share_row = """            onShare?.let {
                ActionRow(painter = painterResource(R.drawable.ic_sf_share), label = stringResource(R.string.share), onClick = it)
            }"""
assert old_share_row in browse_sheet, "old share row not found in BrowseActionsSheet.kt"
browse_sheet = browse_sheet.replace(old_share_row, new_share_row, 1)

old_rename_row = """            if (onRename != null) {
                ActionRow(Icons.Rounded.Edit, stringResource(R.string.rename)) {"""
new_rename_row = """            if (onRename != null) {
                ActionRow(painter = painterResource(R.drawable.ic_sf_pencil), label = stringResource(R.string.rename)) {"""
assert old_rename_row in browse_sheet, "old rename row not found in BrowseActionsSheet.kt"
browse_sheet = browse_sheet.replace(old_rename_row, new_rename_row, 1)

old_reorder_row = """            onReorder?.let {
                ActionRow(Icons.Rounded.SwapVert, stringResource(R.string.reorder_songs), onClick = it)
            }"""
new_reorder_row = """            onReorder?.let {
                ActionRow(painter = painterResource(R.drawable.ic_sf_sort), label = stringResource(R.string.reorder_songs), onClick = it)
            }"""
assert old_reorder_row in browse_sheet, "old reorder row not found in BrowseActionsSheet.kt"
browse_sheet = browse_sheet.replace(old_reorder_row, new_reorder_row, 1)

old_delete_block = """            if (onDelete != null) {
                if (confirmingDelete) {
                    ActionRow(
                        icon = Icons.Rounded.DeleteForever,
                        label = stringResource(R.string.delete_playlist_confirmation, target.title),
                        tint = MaterialTheme.colorScheme.error,
                        onClick = onDelete,
                    )
                } else {
                    ActionRow(Icons.Rounded.Delete, stringResource(R.string.delete_playlist)) { confirmingDelete = true }
                }
            }
            if (onDeleteDownload != null) {
                if (confirmingDeleteDownload) {
                    ActionRow(
                        icon = Icons.Rounded.DeleteForever,
                        label = stringResource(R.string.delete_download_confirmation, target.title),
                        tint = MaterialTheme.colorScheme.error,
                        onClick = onDeleteDownload,
                    )
                } else {
                    ActionRow(Icons.Rounded.Delete, stringResource(R.string.delete_download)) {
                        confirmingDeleteDownload = true
                    }
                }
            }"""

new_delete_block = """            if (onDelete != null) {
                if (confirmingDelete) {
                    ActionRow(
                        painter = painterResource(R.drawable.ic_sf_trash_fill),
                        label = stringResource(R.string.delete_playlist_confirmation, target.title),
                        tint = MaterialTheme.colorScheme.error,
                        onClick = onDelete,
                    )
                } else {
                    ActionRow(painter = painterResource(R.drawable.ic_sf_trash), label = stringResource(R.string.delete_playlist)) { confirmingDelete = true }
                }
            }
            if (onDeleteDownload != null) {
                if (confirmingDeleteDownload) {
                    ActionRow(
                        painter = painterResource(R.drawable.ic_sf_trash_fill),
                        label = stringResource(R.string.delete_download_confirmation, target.title),
                        tint = MaterialTheme.colorScheme.error,
                        onClick = onDeleteDownload,
                    )
                } else {
                    ActionRow(painter = painterResource(R.drawable.ic_sf_trash), label = stringResource(R.string.delete_download)) {
                        confirmingDeleteDownload = true
                    }
                }
            }"""

assert old_delete_block in browse_sheet, "old delete block not found in BrowseActionsSheet.kt"
browse_sheet = browse_sheet.replace(old_delete_block, new_delete_block, 1)

with open(browse_sheet_path, "w", encoding="utf-8") as f:
    f.write(browse_sheet)
print("Successfully patched BrowseActionsSheet.kt")
print("All patches completed successfully!")
