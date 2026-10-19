
import subprocess
BASE = 'app/src/main/java/com/music/amusic/'

def rd(p):
    with open(BASE + p, encoding='utf-8') as f:
        return f.read()

def wr(p, s):
    with open(BASE + p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)

def cut(s, start, end, new):
    assert s.count(start) == 1, 'start not unique: ' + start[:60]
    i = s.index(start)
    j = s.index(end, i)
    assert j > i
    return s[:i] + new + s[j + len(end):]

def once(s, old, new):
    assert s.count(old) == 1, 'not unique: ' + old[:60]
    return s.replace(old, new)

# ---- MainActivity.kt: restore the Ver tudo list in the same composition as the back
m = rd('MainActivity.kt')
sync_block = (
"    // Runs while composing, not in an effect after it: an effect would let the\n"
"    // first frame of the artist page draw without its Ver tudo list, which then\n"
"    // faded in over it.\n"
"    val shelfNavId = detail?.browseId\n"
"    if (shelfNavId != shelfDetailId) {\n"
"        // Opening an album from the artist Ver tudo list pushes the album over\n"
"        // the artist page. Keep that list here, so going back to the artist opens it again.\n"
"        val prevId = shelfDetailId\n"
"        shelfDetailId = shelfNavId\n"
"        val openShelf = detailActiveShelf\n"
"        if (shelfNavId == null) {\n"
"            shelfReturn = null\n"
"        } else if (openShelf != null && prevId != null && prevId != shelfNavId) {\n"
"            shelfReturn = prevId to openShelf\n"
"        }\n"
"        val back = shelfReturn\n"
"        val restore = back != null && back.first == shelfNavId\n"
"        detailActiveShelf = if (restore) back?.second else null\n"
"        if (restore) shelfReturn = null\n"
"    }\n"
)
m = cut(m,
    "    LaunchedEffect(detail?.browseId) {\n        // Opening an album from the artist Ver tudo list",
    "        if (restore) shelfReturn = null\n    }\n",
    sync_block)
m = once(m,
    "                    if (live != null) held.value = live\n",
    "                    if (live != null) held.value = live\n"
    "                    // The Ver tudo list this slot shows. Kept per slot, like the page\n"
    "                    // above: a page fading out keeps its own list instead of following\n"
    "                    // the one the page that replaced it has open.\n"
    "                    val shelfHeld = remember(key) { mutableStateOf<HomeShelf?>(null) }\n"
    "                    if (live != null) shelfHeld.value = detailActiveShelf\n")
m = once(m, "activeShelf = detailActiveShelf,\n", "activeShelf = shelfHeld.value,\n")
wr('MainActivity.kt', m)

# ---- MainViewModel.kt: the library row toggles at once both ways
v = rd('ui/MainViewModel.kt')
new_fn = (
"    fun toggleSongLibrary(videoId: String, onFailed: () -> Unit) {\n"
"        if (!requireSignIn()) return\n"
"        // A tap that lands while the last request is still running is not\n"
"        // dropped: it shows its state at once and runs after that request.\n"
"        val menu = _songMenu.value.takeIf { songMenuVideoId == videoId }\n"
"        val adding = !(_libraryShown.value ?: menu?.inLibrary ?: libraryGuess(videoId))\n"
"        _libraryShown.value = adding\n"
"        val previous = libraryToggleJob\n"
"        val ticket = ++libraryToggleTicket\n"
"        libraryToggleJob = viewModelScope.launch {\n"
"            previous?.join()\n"
"            val current = _songMenu.value.takeIf { songMenuVideoId == videoId }\n"
"            val usable = current?.takeIf {\n"
"                (if (adding) it.addToLibraryToken else it.removeFromLibraryToken) != null\n"
"            } ?: YtMusicRepository.songMenu(videoId).getOrNull()\n"
"            if (usable == null) {\n"
"                settleLibraryShown(ticket)\n"
"                onFailed()\n"
"                return@launch\n"
"            }\n"
"            if (usable.inLibrary == adding) {\n"
"                // The guess behind the first frame was wrong: it is already so.\n"
"                if (songMenuVideoId == videoId) _songMenu.value = usable\n"
"                settleLibraryShown(ticket)\n"
"                return@launch\n"
"            }\n"
"            val token = if (adding) usable.addToLibraryToken else usable.removeFromLibraryToken\n"
"            val sent = token != null && YtMusicRepository.setLibraryStatus(token).isSuccess\n"
"            if (!sent) {\n"
"                // Only a failed request puts the old state back.\n"
"                if (songMenuVideoId == videoId) _songMenu.value = usable\n"
"                settleLibraryShown(ticket)\n"
"                onFailed()\n"
"                return@launch\n"
"            }\n"
"            val fresh = YtMusicRepository.songMenu(videoId).getOrNull()\n"
"            libraryStale = true\n"
"            // The request went through, so the new state stands even when the\n"
"            // read right after it still shows the old one. Without a matching\n"
"            // read there are no tokens for the way back; the row stays and\n"
"            // fetches them when it is tapped.\n"
"            val next = fresh?.takeIf { it.inLibrary == adding } ?: usable.copy(\n"
"                inLibrary = adding,\n"
"                addToLibraryToken = null,\n"
"                removeFromLibraryToken = null,\n"
"            )\n"
"            // The menu may have moved on to another track while this ran.\n"
"            if (songMenuVideoId == videoId) _songMenu.value = next\n"
"            settleLibraryShown(ticket)\n"
"            if (!adding) dropFromLibrarySongs(videoId)\n"
"        }\n"
"    }\n"
"\n"
"    /** Counts taps on the library row, so only the newest one clears [libraryShown]. */\n"
"    private var libraryToggleTicket = 0\n"
"\n"
"    private fun settleLibraryShown(ticket: Int) {\n"
"        if (ticket == libraryToggleTicket) _libraryShown.value = null\n"
"    }\n"
"\n"
)
v = cut(v,
    "    fun toggleSongLibrary(videoId: String, onFailed: () -> Unit) {",
    "    /**\n     * What the library row shows in the one-frame gap",
    new_fn + "    /**\n     * What the library row shows in the one-frame gap")
wr('ui/MainViewModel.kt', v)

d = subprocess.run(['git', 'diff', '--', 'app'], capture_output=True, text=True).stdout
with open('tmp-polish/out.txt', 'w', encoding='utf-8') as f:
    f.write(d)
print('patched')
