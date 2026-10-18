import pathlib

R = pathlib.Path("app/src/main/java/com/music/amusic")


def edit(rel, fn):
    p = R / rel
    t = p.read_text(encoding="utf-8")
    t2 = fn(t)
    assert t2 != t, rel
    p.write_text(t2, encoding="utf-8")


def cut(t, start, end):
    a = t.index(start)
    b = t.index(end, a)
    return t[:a] + t[b:]


def drop(t, s):
    assert t.count(s) == 1, s
    return t.replace(s, "")


def vm(t):
    t = cut(t, "    /**\n     * Diagnostic only: why the track menu's library row", "    /** The account's own playlists, for the picker")
    old = "    private var libraryStale = false\n"
    assert t.count(old) == 1
    new = (
        old
        + "        set(value) {\n"
        + "            field = value\n"
        + "            if (value && _signedIn.value && _library.value is UiState.Success && Feed.LIBRARY !in _refreshing.value) {\n"
        + "                field = false\n"
        + "                refresh(Feed.LIBRARY)\n"
        + "            }\n"
        + "        }\n"
    )
    return t.replace(old, new)


def sheet(t):
    t = drop(t, "    /**\n     * Diagnostic only: shown in place of the library row while it has no token.\n     */\n    libraryDiagnostic: String? = null,\n")
    t = cut(t, "            if (onToggleLibrary == null && libraryDiagnostic != null) {", "            GroupSeparator(palette)")
    k = t.index("    val iconView: @Composable () -> Unit = {")
    old = (
        "        Icon(\n"
        "            imageVector = icon,\n"
        "            contentDescription = null,\n"
        "            tint = (tint ?: foreground).copy(alpha = alpha),\n"
        "            modifier = Modifier.size(if (menu) 20.dp else 22.dp),\n"
        "        )\n"
    )
    new = (
        "        Crossfade(targetState = icon, animationSpec = tween(durationMillis = 200), label = \"actionIcon\") { shown ->\n"
        "            Icon(\n"
        "                imageVector = shown,\n"
        "                contentDescription = null,\n"
        "                tint = (tint ?: foreground).copy(alpha = alpha),\n"
        "                modifier = Modifier.size(if (menu) 20.dp else 22.dp),\n"
        "            )\n"
        "        }\n"
    )
    j = t.index(old, k)
    assert j - k < 200
    t = t[:j] + new + t[j + len(old):]
    imp = "import android.net.Uri\n"
    assert t.count(imp) == 1
    assert "import androidx.compose.animation" not in t
    return t.replace(imp, imp + "import androidx.compose.animation.Crossfade\nimport androidx.compose.animation.core.tween\n")


def main(t):
    t = drop(t, "            LaunchedEffect(song.videoId) { viewModel.loadSongMenuDiag(song.videoId) }\n")
    t = drop(t, "            val libraryDiag by viewModel.songMenuDiag.collectAsStateWithLifecycle()\n")
    return drop(t, "                libraryDiagnostic = libraryDiag,\n")


def detail(t):
    k = t.index("items(shelf.items, key = { it.browseId ?: it.title }) { item ->")
    old = "modifier = Modifier.fillMaxWidth(),"
    j = t.index(old, k)
    assert j - k < 400
    new = "modifier = Modifier.fillMaxWidth().animateItem(fadeInSpec = tween(200), placementSpec = tween(200), fadeOutSpec = tween(200)),"
    return t[:j] + new + t[j + len(old):]


edit("ui/MainViewModel.kt", vm)
edit("ui/components/SongActionsSheet.kt", sheet)
edit("MainActivity.kt", main)
edit("ui/screens/DetailScreen.kt", detail)
print("ok")
