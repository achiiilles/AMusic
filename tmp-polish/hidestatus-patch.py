import sys


def edit(path, reps):
    raw = open(path, 'r', encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    for old, new in reps:
        old = old.replace('\n', nl)
        new = new.replace('\n', nl)
        n = raw.count(old)
        if n != 1:
            print('ERRO:', path, 'trecho aparece', n, 'vezes:', old[:70])
            sys.exit(1)
        raw = raw.replace(old, new)
    open(path, 'w', encoding='utf-8', newline='').write(raw)


edit('app/src/main/java/com/music/amusic/data/settings/AppSettings.kt', [
    (
        '    /** Hides the "Playing from" / "Played by" caption at the top of the main player. */\n'
        '    val hideSongStatus = MutableStateFlow(false)\n',
        '    /**\n'
        '     * Hides the "Playing from" / "Played by" caption at the top of the main player,\n'
        '     * and the drag handle above it. On by default; a value already saved on the\n'
        '     * device is kept (see readAll).\n'
        '     */\n'
        '    val hideSongStatus = MutableStateFlow(true)\n',
    ),
    (
        'hideSongStatus.value = prefs.getBoolean(KEY_HIDE_SONG_STATUS, false)',
        'hideSongStatus.value = prefs.getBoolean(KEY_HIDE_SONG_STATUS, true)',
    ),
])

edit('sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/player/NowPlayingScreen.kt', [
    (
        '        label = "spotifyCanvasChrome",\n    )\n',
        '        label = "spotifyCanvasChrome",\n    )\n'
        '    // The drag handle above the "Playing from" caption leaves with the caption when\n'
        '    // Hide Song Status is on. It fades instead of being removed, so toggling the\n'
        '    // option never makes the top of the player jump.\n'
        '    val dismissHandleHideAlpha by animateFloatAsState(\n'
        '        targetValue = if (hideSongStatus) 0f else 1f,\n'
        '        animationSpec = tween(durationMillis = 180, easing = FastOutSlowInEasing),\n'
        '        label = "dismissHandleHide",\n'
        '    )\n',
    ),
    (
        '                                .graphicsLayer { alpha = spotifyChromeAlpha }\n',
        '                                .graphicsLayer { alpha = spotifyChromeAlpha * dismissHandleHideAlpha }\n',
    ),
])
print('OK: padrao ligado em AppSettings; tracinho some com o texto no NowPlayingScreen')
