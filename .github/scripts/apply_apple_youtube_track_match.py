from pathlib import Path

shelf_path = Path('app/src/main/java/com/music/amusic/data/canvas/AppleAlbumShelves.kt')
shelf = shelf_path.read_text(encoding='utf-8')
if 'private suspend fun completeYouTubeTrackTitles(' not in shelf:
    start_marker = '    /**\n     * Match one Apple recommendation to a YouTube Music album.'
    end_marker = '    /**\n     * An Apple Music playlist with the songs the catalog returns for it (its'
    if shelf.count(start_marker) != 1:
        raise SystemExit(f'Expected one Apple recommendation resolver, found {shelf.count(start_marker)}')
    start = shelf.index(start_marker)
    end = shelf.find(end_marker, start)
    if end < 0:
        raise SystemExit('Could not find the playlist resolver after the Apple album resolver')
    new_method = """    /**
     * Match one Apple recommendation to a YouTube Music album.
     * Compare card metadata first, then require the complete released Apple
     * track list and the complete YouTube album track list to agree.
     */
    suspend fun youtubeAlbumFor(target: AppleShelfTarget): String? {
        youtubeIds[target.id]?.let { return it.takeIf { id -> id.isNotEmpty() } }
        if (!target.isAlbum || AppleReleaseMatcher.cleanTitle(target.title).isBlank()) return null
        val appleAlbum = ApplePreRelease.album(target.appleId) ?: return null
        val appleTracks = appleAlbum.tracks
        if (appleTracks.isEmpty() || appleTracks.size >= 200 || appleTracks.any { !it.released || it.name.isBlank() }) return null
        val hits = YtMusicRepository.search("${target.artist} ${target.title}".trim(), SearchFilter.ALBUMS)
            .getOrNull() ?: return null
        val candidates = hits.mapNotNull { hit ->
            val item = (hit as? SearchResult.Browse)?.item ?: return@mapNotNull null
            YouTubeAlbumCandidate(item.browseId, item.title, item.subtitle)
        }
        val metadataMatches = AppleYouTubeAlbumMatcher.matchingBrowseIds(
            appleDisplayTitle = target.title,
            appleCatalogTitle = target.appleCatalogTitle,
            appleArtist = target.artist,
            appleReleaseLine = target.releaseLine,
            candidates = candidates,
        )
        if (metadataMatches.isEmpty()) {
            youtubeIds[target.id] = ""
            return null
        }
        val appleTitles = appleTracks.map { it.name }
        val gate = Semaphore(3)
        val checked = coroutineScope {
            metadataMatches.map { browseId ->
                async<Pair<Boolean, String?>>(Dispatchers.IO) {
                    gate.withPermit {
                        val youtubeTitles = completeYouTubeTrackTitles(browseId) ?: return@withPermit false to null
                        true to browseId.takeIf { AppleYouTubeAlbumMatcher.sameTrackList(appleTitles, youtubeTitles) }
                    }
                }
            }.awaitAll()
        }
        // An unreadable candidate could still be the match, so never choose around it.
        if (checked.any { !it.first }) return null
        val found = checked.mapNotNull { it.second }.distinct().singleOrNull()
        youtubeIds[target.id] = found.orEmpty()
        return found
    }

    private suspend fun completeYouTubeTrackTitles(browseId: String): List<String>? {
        val first = YtMusicRepository.browseSongs(browseId).getOrNull() ?: return null
        val songs = first.songs.toMutableList()
        var continuation = first.continuation
        var pages = 1
        while (continuation != null && pages < YtMusicRepository.MAX_PAGES) {
            val page = YtMusicRepository.moreSongs(continuation).getOrNull() ?: return null
            if (page.songs.isEmpty() && page.continuation != null) return null
            songs += page.songs
            continuation = page.continuation
            pages++
        }
        if (continuation != null || songs.isEmpty()) return null
        return songs.map { it.title }
    }

"""
    shelf_path.write_text(shelf[:start] + new_method + shelf[end:], encoding='utf-8')

matcher_path = Path('app/src/main/java/com/music/amusic/data/canvas/AppleYouTubeAlbumMatcher.kt')
matcher = matcher_path.read_text(encoding='utf-8')
if 'fun sameTrackList(' not in matcher:
    closing = matcher.rfind('\n}')
    if closing < 0:
        raise SystemExit('Could not find the end of AppleYouTubeAlbumMatcher')
    addition = """

    /** Requires both complete lists to contain the same normalized titles and duplicate counts. */
    fun sameTrackList(appleTitles: List<String>, youtubeTitles: List<String>): Boolean {
        if (appleTitles.isEmpty() || appleTitles.size != youtubeTitles.size) return false
        val appleKeys = appleTitles.map(::trackKey)
        val youtubeKeys = youtubeTitles.map(::trackKey)
        if (appleKeys.any { it.isBlank() } || youtubeKeys.any { it.isBlank() }) return false
        return appleKeys.groupingBy { it }.eachCount() == youtubeKeys.groupingBy { it }.eachCount()
    }

    private fun trackKey(title: String): String =
        java.text.Normalizer.normalize(title, java.text.Normalizer.Form.NFKD)
            .lowercase(java.util.Locale.ROOT)
            .filter { it.isLetterOrDigit() }
"""
    matcher = matcher[:closing] + addition + matcher[closing:]
    matcher_path.write_text(matcher, encoding='utf-8')

test_path = Path('app/src/test/java/com/music/amusic/data/canvas/AppleYouTubeAlbumMatcherTest.kt')
tests = test_path.read_text(encoding='utf-8')
marker = 'fun `complete track lists compare every title and duplicate count`()'
if marker not in tests:
    closing = tests.rfind('\n}')
    if closing < 0:
        raise SystemExit('Could not find the end of AppleYouTubeAlbumMatcherTest')
    addition = """

    @Test
    fun `complete track lists compare every title and duplicate count`() {
        assertTrue(
            AppleYouTubeAlbumMatcher.sameTrackList(
                listOf("Don't Start Now", "Levitating", "Physical"),
                listOf("Physical", "Don’t Start Now", "Levitating"),
            ),
        )
        assertTrue(
            !AppleYouTubeAlbumMatcher.sameTrackList(
                listOf("Intro", "Song", "Song"),
                listOf("Intro", "Song", "Different Song"),
            ),
        )
        assertTrue(
            !AppleYouTubeAlbumMatcher.sameTrackList(
                listOf("Intro", "Song", "Outro"),
                listOf("Intro", "Song"),
            ),
        )
        assertTrue(!AppleYouTubeAlbumMatcher.sameTrackList(emptyList(), emptyList()))
    }
"""
    tests = tests[:closing] + addition + tests[closing:]
    test_path.write_text(tests, encoding='utf-8')
