from pathlib import Path

def edit(path, old, new):
    p = Path(path)
    s = p.read_text()
    if new in s:
        return
    assert s.count(old) == 1, (path, s.count(old), old[:100])
    p.write_text(s.replace(old, new))

p = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components/Common.kt'
s = Path(p).read_text()
old = '    plainCurrent: Boolean = false,\n) {'
new = '    plainCurrent: Boolean = false,\n    /** Album-owned popularity; false elsewhere, null opts into the legacy local mark. */\n    mostPlayedOverride: Boolean? = false,\n) {'
if new not in s:
    assert s.count(old) == 2
    s = s.replace(old, new)
old = '            plainCurrent = plainCurrent,\n'
new = old+'            mostPlayedOverride = mostPlayedOverride,\n'
if new not in s:
    assert s.count(old) == 2
    s = s.replace(old, new)
s = s.replace('val mostPlayedIds = if (trackNumber != null) AppUi.host.mostPlayedTrackIds() else emptySet()',
    'val mostPlayedIds = if (mostPlayedOverride == null && trackNumber != null) AppUi.host.mostPlayedTrackIds() else emptySet()')
s = s.replace('val mostPlayed = song.videoId in mostPlayedIds',
    'val mostPlayed = mostPlayedOverride ?: (song.videoId in mostPlayedIds)')
s = s.replace('                if (mostPlayed) {', '                if (mostPlayedAlpha > 0f) {')
Path(p).write_text(s)
p = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
edit(p, '    val isPreRelease = page.browseId.startsWith("prerelease:")',
'''    val isPreRelease = page.browseId.startsWith("prerelease:")
    // Catalogue popularity belongs to the album, never to the filtered or sorted list.
    val albumDotEligible = page.type == BrowseType.ALBUM && !isPreRelease && folder == null
    var albumPopularIds by remember(page.browseId) {
        mutableStateOf(com.music.amusic.data.stats.AlbumPopularTracks.cached(page.browseId).orEmpty())
    }
    LaunchedEffect(page.browseId, rawSongs, albumDotEligible) {
        if (albumDotEligible && rawSongs.isNotEmpty()) {
            albumPopularIds = com.music.amusic.data.stats.AlbumPopularTracks.resolve(page.browseId, rawSongs)
        }
    }''')
edit(p, '                            plainCurrent = numbered,',
'''                            plainCurrent = numbered,
                            mostPlayedOverride = numbered && albumDotEligible && !preReleaseOff && song.videoId in albumPopularIds,''')
