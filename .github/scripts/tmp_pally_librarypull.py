import hashlib, os, subprocess, sys

BASE = 'app/src/main/java/com/music/amusic'
VMP = BASE + '/ui/MainViewModel.kt'
DP = BASE + '/ui/screens/DetailScreen.kt'
MP = BASE + '/MainActivity.kt'
EXPECT = {
    VMP: '4da813623a992a1b7503c10ad51d066f3e20c454',
    DP: 'aa13d2c4dc0148f4a7a444dc8189a8abe2227311',
    MP: 'd6174b5f7894a38c79efdc4d35daf0b25b638236',
}

def gh(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

def rd(p):
    return open(p, 'rb').read().decode('utf-8')

def bal(s):
    return (s.count('{') - s.count('}'), s.count('(') - s.count(')'))

def rep(s, old, new):
    assert s.count(old) == 1, ('anchor count', s.count(old), old[:80])
    return s.replace(old, new)

orig = {}
for p, sha in EXPECT.items():
    b = open(p, 'rb').read()
    assert gh(b) == sha, ('sha changed', p, gh(b))
    orig[p] = b.decode('utf-8')

# ---------------- MainViewModel.kt ----------------
s = orig[VMP]
s = rep(s, """    fun reloadLocalDetail(browseId: String) {
""", """    private val _refreshingDetail = MutableStateFlow<Set<String>>(emptySet())

    /** Pages (by browse id) whose track list is being re-fetched by a pull down. */
    val refreshingDetail: StateFlow<Set<String>> = _refreshingDetail.asStateFlow()

    /**
     * Pull-to-refresh on a library artist page: fetches the track list again and
     * swaps in only the tracks and their continuation. A failed fetch leaves the
     * list as it was.
     */
    fun refreshDetail(browseId: String) {
        if (browseId in _refreshingDetail.value) return
        val current = _detailStack.value.lastOrNull { it.browseId == browseId } ?: return
        _refreshingDetail.update { it + browseId }
        viewModelScope.launch {
            try {
                val page = YtMusicRepository.browseSongs(browseId).getOrNull() ?: return@launch
                val artwork = current.thumbnailUrl
                val state: UiState<List<Song>> = if (page.songs.isEmpty()) {
                    UiState.Error(text(R.string.no_tracks_here))
                } else {
                    UiState.Success(page.songs.withArtwork(artwork))
                }
                _detailStack.value = _detailStack.value.map {
                    if (it.browseId == browseId) {
                        it.copy(songs = state, continuation = page.continuation)
                    } else {
                        it
                    }
                }
                page.continuation?.let { fillIn(browseId, it, artwork) }
            } finally {
                _refreshingDetail.update { it - browseId }
            }
        }
    }

    fun reloadLocalDetail(browseId: String) {
""")
s = rep(s, """        val library = (_library.value as? UiState.Success)?.data ?: return
        if (library.librarySongs.any { it.videoId == videoId }) {
""", """        val library = (_library.value as? UiState.Success)?.data ?: return
        // A library artist page lists its tracks from its own fetch, so it also
        // has to let go of the track, or the row stays until the page is reopened.
        val artistPageIds = library.shelves
            .firstOrNull { it.title == "Artists" }
            ?.items
            ?.mapNotNull { it.browseId }
            ?.toSet()
            .orEmpty()
        if (artistPageIds.isNotEmpty()) {
            _detailStack.value = _detailStack.value.map { page ->
                val songs = page.songs
                if (page.type == BrowseType.ARTIST ||
                    page.browseId !in artistPageIds ||
                    songs !is UiState.Success ||
                    songs.data.none { it.videoId == videoId }
                ) {
                    page
                } else {
                    val left = songs.data.filterNot { it.videoId == videoId }
                    page.copy(
                        songs = if (left.isEmpty()) {
                            UiState.Error(text(R.string.no_tracks_here))
                        } else {
                            UiState.Success(left)
                        },
                    )
                }
            }
        }
        if (library.librarySongs.any { it.videoId == videoId }) {
""")
new = {VMP: s}

# ---------------- DetailScreen.kt ----------------
s = orig[DP]
s = rep(s, "import androidx.compose.material3.Text\n", "import androidx.compose.material3.ExperimentalMaterial3Api\nimport androidx.compose.material3.Text\nimport androidx.compose.material3.pulltorefresh.PullToRefreshState\n")
s = rep(s, "import com.music.amusic.ui.components.PAGE_GUTTER\n", "import com.music.amusic.ui.components.PAGE_GUTTER\nimport com.music.amusic.ui.components.PullToRefresh\n")
s = rep(s, "@Composable\nfun DetailScreen(\n", "@OptIn(ExperimentalMaterial3Api::class)\n@Composable\nfun DetailScreen(\n")
s = rep(s, "    publicArtistId: String? = null,\n) {\n    val rawSongs", """    publicArtistId: String? = null,
    /** Pull-to-refresh, used by the library artist page; off when [onRefresh] is null. */
    refreshing: Boolean = false,
    onRefresh: (() -> Unit)? = null,
    pullState: PullToRefreshState? = null,
) {
    val rawSongs""")
s = rep(s, "    val foldedMatches = if (foldSongs) matches.drop(5) else emptyList()\n", """    val foldedMatches = if (foldSongs) matches.drop(5) else emptyList()
    // On the library artist page a row is keyed by its track rather than by its
    // place in the list, so removing one lets the others stay put while it fades.
    val rowKeys = remember(matches, inLibraryArtistPage) {
        val seen = HashMap<String, Int>()
        matches.map { entry ->
            if (inLibraryArtistPage) {
                val id = "${entry.value.videoId}"
                val n = seen.getOrElse(id) { 0 }
                seen[id] = n + 1
                "${id}_$n"
            } else {
                "${entry.index}_${entry.value.videoId}"
            }
        }
    }
""")
s = rep(s, 'key = { _, entry -> "${entry.index}_${entry.value.videoId}" },', 'key = { position, entry -> rowKeys.getOrElse(position) { "${entry.index}_${entry.value.videoId}" } },')
s = rep(s, 'key("${entry.index}_${entry.value.videoId}") {', 'key(rowKeys.getOrElse(shownMatches.size + offset) { "${entry.index}_${entry.value.videoId}" }) {')
s = rep(s, """                LazyColumn(
                    state = listState,
                    modifier = Modifier.fillMaxSize(),
                    // The artist photo runs edge-to-edge""", """                DetailPullHost(refreshing = refreshing, onRefresh = onRefresh, pullState = pullState) {
                LazyColumn(
                    state = listState,
                    modifier = Modifier.fillMaxSize(),
                    // The artist photo runs edge-to-edge""")
s = rep(s, "            if (isArtist) aboutItem()\n        }\n", "            if (isArtist) aboutItem()\n        }\n                }\n")
assert s.endswith('\n')
s += """
/** Wraps a page's list in the shared pull-to-refresh, only when a refresh is wired in. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DetailPullHost(
    refreshing: Boolean,
    onRefresh: (() -> Unit)?,
    pullState: PullToRefreshState?,
    content: @Composable () -> Unit,
) {
    if (onRefresh != null && pullState != null) {
        PullToRefresh(refreshing = refreshing, onRefresh = onRefresh, state = pullState) { content() }
    } else {
        content()
    }
}
"""
new[DP] = s

# ---------------- MainActivity.kt ----------------
s = orig[MP]
s = rep(s, "    val libraryPull = rememberPullToRefreshState()\n", "    val libraryPull = rememberPullToRefreshState()\n    val detailPull = rememberPullToRefreshState()\n")
s = rep(s, "    val refreshing by viewModel.refreshing.collectAsStateWithLifecycle()\n", "    val refreshing by viewModel.refreshing.collectAsStateWithLifecycle()\n    val refreshingDetail by viewModel.refreshingDetail.collectAsStateWithLifecycle()\n")
s = rep(s, """                            folder = folder,
                            contentPadding = listPadding,
                        )
                        }
                    } else when""", """                            folder = folder,
                            contentPadding = listPadding,
                            refreshing = page.browseId in refreshingDetail,
                            onRefresh = if (isLibraryArtistPage) {
                                { viewModel.refreshDetail(page.browseId) }
                            } else {
                                null
                            },
                            pullState = if (isLibraryArtistPage) detailPull else null,
                        )
                        }
                    } else when""")
s = rep(s, """                    refreshing = currentFeed != null && currentFeed in refreshing,
                    pullFraction = { currentPull?.distanceFraction ?: 0f },
""", """                    refreshing = (currentFeed != null && currentFeed in refreshing) ||
                        (isLibraryArtistPageVisible && detail?.browseId?.let { it in refreshingDetail } == true),
                    pullFraction = {
                        if (isLibraryArtistPageVisible) detailPull.distanceFraction else (currentPull?.distanceFraction ?: 0f)
                    },
""")
new[MP] = s

for p in EXPECT:
    assert bal(new[p]) == bal(orig[p]), ('balance', p, bal(orig[p]), bal(new[p]))

if os.environ.get('DRY') == '1':
    for p, t in new.items():
        open(p, 'w', encoding='utf-8', newline='').write(t)
    print('dry ok')
    sys.exit(0)

for p, t in new.items():
    open(p, 'w', encoding='utf-8', newline='').write(t)
subprocess.run(['git', 'config', 'user.name', 'pally-bot'], check=True)
subprocess.run(['git', 'config', 'user.email', 'pally-bot@users.noreply.github.com'], check=True)
subprocess.run(['git', 'add'] + list(EXPECT), check=True)
subprocess.run(['git', 'commit', '-m', 'Biblioteca: puxar para atualizar na pagina de artista e faixa removida some da lista [skip ci]'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
