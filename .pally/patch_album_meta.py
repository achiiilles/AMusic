import hashlib
import subprocess

CANVAS = 'app/src/main/java/com/music/amusic/data/canvas/AppleMusicCanvas.kt'
REPO = 'app/src/main/java/com/music/amusic/data/canvas/AppleAlbumColorRepository.kt'
DETAIL = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
EXPECTED = {CANVAS: '50ca28dfb04d70b3388dcfcd35fdd537496030ef', REPO: '48e6f8c044b525e96e88f14a1b41e9352df2da90', DETAIL: '9e14b2d956ae443fed559871a5da70685b9fce8c'}

def replace(s, before, after):
    assert s.count(before) == 1, ('anchor', s.count(before), before[:90])
    return s.replace(before, after)

def blobsha(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

contents = {}
for path, sha in EXPECTED.items():
    data = open(path, 'rb').read()
    assert blobsha(data) == sha, ('changed file', path, blobsha(data))
    contents[path] = data.decode('utf-8')

s = contents[CANVAS]
s = replace(s, '            val source = sources.firstOrNull { candidate ->\n                candidate["bgColor"]?.jsonPrimitive?.contentOrNull?.hexToArgb() != null\n            } ?: continue\n', '''            // Use the same confidently matched Apple release for metadata and colour.
            // "Music" is the generic catalog category, not a useful genre label.
            val genre = attributes["genreNames"]?.jsonArray
                ?.mapNotNull { it.jsonPrimitive.contentOrNull?.trim() }
                ?.firstOrNull { it.isNotBlank() && !it.equals("Music", ignoreCase = true) }
            val year = attributes["releaseDate"]?.jsonPrimitive?.contentOrNull
                ?.take(4)?.takeIf { it.length == 4 && it.all(Char::isDigit) }
            val source = sources.firstOrNull { candidate ->
                candidate["bgColor"]?.jsonPrimitive?.contentOrNull?.hexToArgb() != null
            } ?: return AppleAlbumColorsResult(null, genre, year)
''')
s = replace(s, '            return AppleAlbumColorsResult(AppleAlbumColors(background, accent))\n', '            return AppleAlbumColorsResult(AppleAlbumColors(background, accent), genre, year)\n')
contents[CANVAS] = s

s = contents[REPO]
s = replace(s, 'class AppleAlbumColorsResult(val colors: AppleAlbumColors?)', '''class AppleAlbumColorsResult(
    val colors: AppleAlbumColors?,
    val genre: String? = null,
    val releaseYear: String? = null,
)''')
s = replace(s, '    private class Entry(val colors: AppleAlbumColors?)\n', '    private class Entry(val result: AppleAlbumColorsResult)\n')
s = replace(s, '''    fun cached(browseId: String): AppleAlbumColors? =
        synchronized(cache) { cache[browseId] }?.colors

    /** Apple's colours for the release, or null when it has none. Never throws. */
    suspend fun colorsFor(browseId: String, album: String, artist: String): AppleAlbumColors? {
''', '''    fun cached(browseId: String): AppleAlbumColors? = cachedResult(browseId)?.colors

    /** The already settled catalog match, including a match without page colours. */
    fun cachedResult(browseId: String): AppleAlbumColorsResult? =
        synchronized(cache) { cache[browseId] }?.result

    /** Genre and release year travel with the existing colour lookup; no second search. */
    suspend fun resultFor(browseId: String, album: String, artist: String): AppleAlbumColorsResult? {
''')
s = replace(s, '        synchronized(cache) { cache[browseId] }?.let { return it.colors }\n', '        synchronized(cache) { cache[browseId] }?.let { return it.result }\n')
s = replace(s, '''        synchronized(cache) { cache[browseId] = Entry(result.colors) }
        _updates.value++
        return result.colors
    }
}''', '''        synchronized(cache) { cache[browseId] = Entry(result) }
        _updates.value++
        return result
    }

    /** Existing callers that only need the background still get the same nullable colours. */
    suspend fun colorsFor(browseId: String, album: String, artist: String): AppleAlbumColors? =
        resultFor(browseId, album, artist)?.colors
}''')
contents[REPO] = s

s = contents[DETAIL]
s = replace(s, '''    var appleAlbum by remember(page.browseId) {
        mutableStateOf(
            if (appleAlbumEligible) AppleAlbumColorRepository.cached(page.browseId.orEmpty()) else null,
        )
    }
''', '''    var appleAlbumResult by remember(page.browseId) {
        mutableStateOf(
            if (appleAlbumEligible) AppleAlbumColorRepository.cachedResult(page.browseId.orEmpty()) else null,
        )
    }
''')
s = replace(s, '''        appleAlbum = AppleAlbumColorRepository.colorsFor(
            page.browseId.orEmpty(), page.title, appleAlbumCredit,
        ) ?: appleAlbum
    }
    val palette = rememberArtworkPalette(
''', '''        appleAlbumResult = AppleAlbumColorRepository.resultFor(
            page.browseId.orEmpty(), page.title, appleAlbumCredit,
        ) ?: appleAlbumResult
    }
    val appleAlbum = appleAlbumResult?.colors
    val palette = rememberArtworkPalette(
''')
s = replace(s, '''                        libraryAlbumCount = libraryAlbumCount,
                        artistPhotoUrl = appleArt?.heroUrl,
''', '''                        libraryAlbumCount = libraryAlbumCount,
                        artistPhotoUrl = appleArt?.heroUrl,
                        appleGenre = if (appleAlbumEligible) appleAlbumResult?.genre else null,
                        appleYear = if (appleAlbumEligible) appleAlbumResult?.releaseYear else null,
''')
s = replace(s, '''    libraryAlbumCount: Int = 0,
    artistPhotoUrl: String? = null,
) {
    val (credit, meta) = page.headerLines(songs.size, songs.playtime(), libraryAlbumCount)
''', '''    libraryAlbumCount: Int = 0,
    artistPhotoUrl: String? = null,
    appleGenre: String? = null,
    appleYear: String? = null,
) {
    val (credit, meta) = page.headerLines(
        songs.size, songs.playtime(), libraryAlbumCount, appleGenre, appleYear,
    )
''')
s = replace(s, '''    albumCount: Int = 0,
): Pair<String, String> {
    val parts = subtitle.split''', '''    albumCount: Int = 0,
    appleGenre: String? = null,
    appleYear: String? = null,
): Pair<String, String> {
    val parts = subtitle.split''')
s = replace(s, '''    val credit = parts.filter { it != year && it != kind }.joinToString(", ")
    // Title case, "Playlist · 2022 · 10 Tracks · 38 min" — except the
''', '''    val credit = parts.filter { it != year && it != kind }.joinToString(", ")
    if (type == BrowseType.ALBUM) {
        val releaseKind = when (kind?.lowercase(Locale.ROOT)) {
            "single" -> "Single"
            "ep" -> "EP"
            else -> stringResource(R.string.album)
        }
        val meta = listOfNotNull(
            appleGenre?.takeIf { it.isNotBlank() }, appleYear ?: year, releaseKind,
        ).joinToString(" • ")
        return credit to meta
    }
    // Title case, "Playlist · 2022 · 10 Tracks · 38 min" — except the
''')
contents[DETAIL] = s

for path, value in contents.items():
    assert value.count('{') == open(path, encoding='utf-8').read().count('{'), ('braces', path)
for path, value in contents.items():
    with open(path, 'w', encoding='utf-8', newline='') as out:
        out.write(value)
subprocess.run(['git', 'config', 'user.name', 'pally-bot'], check=True)
subprocess.run(['git', 'config', 'user.email', 'pally-bot@users.noreply.github.com'], check=True)
subprocess.run(['git', 'add'] + list(contents), check=True)
subprocess.run(['git', 'commit', '-m', 'Album e single: genero, ano e tipo na linha de metadados [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
