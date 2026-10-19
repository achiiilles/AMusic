import pathlib

R = pathlib.Path("app/src/main/java/com/music/amusic")


def edit(rel, fn):
    p = R / rel
    t = p.read_text(encoding="utf-8")
    t2 = fn(t)
    assert t2 != t, rel
    p.write_text(t2, encoding="utf-8")


def rep(t, old, new):
    assert t.count(old) == 1, (t.count(old), old[:80])
    return t.replace(old, new)


def vm(t):
    t = rep(t,
"""     * Unlike [setLike] nothing is written to the screen first. The token says
     * which way the change goes, and YouTube can answer a refusal with a
     * success status, so the menu is read again and only a state that matches
     * the request counts as done. [onFailed] runs when it does not.
     */
""",
"""     * Like [setLike] the new state is shown at once through [libraryShown],
     * and the request runs in the background. The row is on screen before the
     * menu has fetched its tokens, so a tap that comes first fetches them
     * itself. YouTube can answer a refusal with a success status, so the menu
     * is read again, and a state that does not match the request puts the
     * old state back and runs [onFailed].
     */
""")
    start = t.index("    fun toggleSongLibrary(videoId: String, onFailed: () -> Unit) {")
    end_marker = """    /**
     * Takes a track out of the Library tab's saved-songs list right away"""
    end = t.index(end_marker)
    assert start < end
    new_fn = """    fun toggleSongLibrary(videoId: String, onFailed: () -> Unit) {
        if (!requireSignIn()) return
        if (libraryToggleJob?.isActive == true) return
        val menu = _songMenu.value.takeIf { songMenuVideoId == videoId }
        val adding = !(_libraryShown.value ?: menu?.inLibrary ?: libraryGuess(videoId))
        _libraryShown.value = adding
        libraryToggleJob = viewModelScope.launch {
            val usable = menu?.takeIf {
                (if (adding) it.addToLibraryToken else it.removeFromLibraryToken) != null
            } ?: YtMusicRepository.songMenu(videoId).getOrNull()
            if (usable == null) {
                _libraryShown.value = null
                onFailed()
                return@launch
            }
            if (usable.inLibrary == adding) {
                // The guess behind the first frame was wrong: it is already so.
                if (songMenuVideoId == videoId) _songMenu.value = usable
                _libraryShown.value = null
                return@launch
            }
            val token = if (adding) usable.addToLibraryToken else usable.removeFromLibraryToken
            val sent = token != null && YtMusicRepository.setLibraryStatus(token).isSuccess
            val fresh = if (sent) YtMusicRepository.songMenu(videoId).getOrNull() else null
            if (!sent || (fresh != null && fresh.inLibrary != adding)) {
                if (songMenuVideoId == videoId) _songMenu.value = usable
                _libraryShown.value = null
                onFailed()
                return@launch
            }
            libraryStale = true
            // Without a fresh read there are no tokens for the way back; the
            // row stays and fetches them when it is tapped.
            val next = fresh ?: usable.copy(
                inLibrary = adding,
                addToLibraryToken = null,
                removeFromLibraryToken = null,
            )
            // The menu may have moved on to another track while this ran.
            if (songMenuVideoId == videoId) _songMenu.value = next
            _libraryShown.value = null
            if (!adding) dropFromLibrarySongs(videoId)
        }
    }

    /**
     * What the library row shows in the one-frame gap before the track menu
     * has loaded: whether the lists already on screen hold the track.
     */
    fun libraryGuess(videoId: String): Boolean {
        val library = (_library.value as? UiState.Success)?.data ?: return false
        return library.librarySongs.any { it.videoId == videoId } ||
            library.likedSongs.any { it.videoId == videoId }
    }

    /** The library row's state while a toggle is in flight, else null. */
    private val _libraryShown = MutableStateFlow<Boolean?>(null)
    val libraryShown: StateFlow<Boolean?> = _libraryShown.asStateFlow()

    private var libraryToggleJob: Job? = null

    /** The track the open menu in [songMenu] belongs to. */
    private var songMenuVideoId: String? = null

"""
    t = t[:start] + new_fn + t[end:]
    t = rep(t,
"""        songMenuJob?.cancel()
        _songMenu.value = null
        if (videoId == null || !_signedIn.value) return
""",
"""        songMenuJob?.cancel()
        _songMenu.value = null
        songMenuVideoId = videoId
        if (videoId == null || !_signedIn.value) return
""")
    return t


def act(t):
    t = rep(t,
"""            val libraryMenu by viewModel.songMenu.collectAsStateWithLifecycle()
""",
"""            val libraryMenu by viewModel.songMenu.collectAsStateWithLifecycle()
            val libraryShown by viewModel.libraryShown.collectAsStateWithLifecycle()
""")
    t = rep(t,
"""                inLibrary = libraryMenu?.inLibrary == true,
                onToggleLibrary = if (libraryToken != null) {
                    {
                        viewModel.toggleSongLibrary(song.videoId) {
                            Toast.makeText(context, R.string.something_went_wrong, Toast.LENGTH_SHORT).show()
                        }
                    }
                } else {
                    null
                },
""",
"""                // Shown with the menu, before its tokens arrive; a tap changes
                // it at once and the request runs behind it.
                inLibrary = libraryShown ?: libraryMenu?.inLibrary ?: viewModel.libraryGuess(song.videoId),
                onToggleLibrary = {
                    viewModel.toggleSongLibrary(song.videoId) {
                        Toast.makeText(context, R.string.something_went_wrong, Toast.LENGTH_SHORT).show()
                    }
                },
""")
    return t


edit("ui/MainViewModel.kt", vm)
edit("MainActivity.kt", act)
print("patched")
