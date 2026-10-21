import hashlib
import subprocess

CANVAS = 'app/src/main/java/com/music/amusic/data/canvas/AppleMusicCanvas.kt'
REPO = 'app/src/main/java/com/music/amusic/data/canvas/AppleAlbumColorRepository.kt'
DETAIL = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
EXPECTED = {CANVAS: 'fea6217a0d179d3dc01fd1b221a13ceaa3d3bcf9', REPO: '613c3ff5c6f777dbf2f9868d161be641ce3e9e55', DETAIL: '3860bf90094c3d7e3c7d130a3f08a493e6bbae99'}

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
s = replace(s, """            val source = sources.firstOrNull { candidate ->
                candidate["bgColor"]?.jsonPrimitive?.contentOrNull?.hexToArgb() != null
            } ?: return AppleAlbumColorsResult(null, genre, year)
""", """            // Full date, label and copyright come from the same matched release; no second search.
            fun text(key: String) = attributes[key]?.jsonPrimitive?.contentOrNull
                ?.trim()?.takeIf { it.isNotBlank() }
            val releaseDate = text("releaseDate")
            val copyright = text("copyright")
            val recordLabel = text("recordLabel")
            val source = sources.firstOrNull { candidate ->
                candidate["bgColor"]?.jsonPrimitive?.contentOrNull?.hexToArgb() != null
            } ?: return AppleAlbumColorsResult(null, genre, year, releaseDate, copyright, recordLabel)
""")
s = replace(s, "            return AppleAlbumColorsResult(AppleAlbumColors(background, accent), genre, year)\n",
 "            return AppleAlbumColorsResult(\n                AppleAlbumColors(background, accent), genre, year, releaseDate, copyright, recordLabel,\n            )\n")
contents[CANVAS] = s

s = contents[REPO]
s = replace(s, """    val genre: String? = null,
    val releaseYear: String? = null,
)""", """    val genre: String? = null,
    val releaseYear: String? = null,
    /** Apple's `releaseDate`, as sent (yyyy-MM-dd, or just the year on some releases). */
    val releaseDate: String? = null,
    /** Apple's `copyright` line for the release. */
    val copyright: String? = null,
    /** Apple's `recordLabel` for the release. */
    val recordLabel: String? = null,
)""")
contents[REPO] = s

s = contents[DETAIL]
s = replace(s, """            // Tracks YouTube offers to round the playlist out, never folded
""", """            // Apple Music closes an album's or single's track list with the release date, the
            // song count with the running time, and the label and copyright. The date and the
            // credits come from the Apple match the page colour already uses.
            if (page.type == BrowseType.ALBUM && folder == null && query.isBlank() &&
                page.songs is UiState.Success
            ) {
                item(key = "album-footer") {
                    AlbumFooter(
                        songs = songs,
                        releaseDate = if (appleAlbumEligible) appleAlbumResult?.releaseDate else null,
                        label = if (appleAlbumEligible) appleAlbumResult?.recordLabel else null,
                        copyright = if (appleAlbumEligible) appleAlbumResult?.copyright else null,
                        palette = palette,
                    )
                }
            }

            // Tracks YouTube offers to round the playlist out, never folded
""")
s = replace(s, """/** The glyph on a release page's placeholder sleeve: what kind of thing has no cover. */
""", """/**
 * The closing block of an album or single page, as Apple Music draws it under the last
 * track: the release date written out, "14 músicas, 49 minutos", and the label and
 * copyright line. Same margin and text colour as the description above the tracks. A line
 * with no source is left out rather than guessed.
 */
@Composable
private fun AlbumFooter(
    songs: List<Song>,
    releaseDate: String?,
    label: String?,
    copyright: String?,
    palette: ArtworkPalette,
) {
    val lines = listOfNotNull(
        releaseDate?.let { footerDate(it) },
        footerCount(songs),
        listOfNotNull(label, copyright).joinToString("; ").takeIf { it.isNotBlank() },
    )
    if (lines.isEmpty()) return
    Column(
        Modifier
            .fillMaxWidth()
            .padding(start = ABOUT_GUTTER, end = ABOUT_GUTTER, top = 24.dp, bottom = 28.dp),
    ) {
        lines.forEach { line ->
            Text(
                text = line,
                style = MaterialTheme.typography.bodyMedium.copy(lineHeight = 16.sp),
                color = palette.onBackgroundVariant,
            )
        }
    }
}

private val FOOTER_MONTHS = listOf(
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)

/** "2023-09-22" becomes "22 de setembro de 2023"; a bare year stays a year. */
private fun footerDate(raw: String): String? {
    val parts = raw.trim().take(10).split('-')
    val year = parts.getOrNull(0)?.takeIf { it.length == 4 && it.all(Char::isDigit) } ?: return null
    val month = parts.getOrNull(1)?.toIntOrNull()?.let { FOOTER_MONTHS.getOrNull(it - 1) } ?: return year
    val day = parts.getOrNull(2)?.toIntOrNull()?.takeIf { it in 1..31 } ?: return month + " de " + year
    return day.toString() + " de " + month + " de " + year
}

/** "14 músicas, 49 minutos" from the rows on the page; no duration when none carries one. */
private fun footerCount(songs: List<Song>): String? {
    if (songs.isEmpty()) return null
    val tracks = if (songs.size == 1) "1 música" else songs.size.toString() + " músicas"
    val minutes = ((songs.sumOf { it.durationMillis() } + 30_000L) / 60_000L).toInt()
    val time = when {
        minutes <= 0 -> return tracks
        minutes < 60 -> if (minutes == 1) "1 minuto" else minutes.toString() + " minutos"
        else -> {
            val hours = minutes / 60
            val rest = minutes % 60
            val h = if (hours == 1) "1 hora" else hours.toString() + " horas"
            if (rest == 0) h else h + " e " + (if (rest == 1) "1 minuto" else rest.toString() + " minutos")
        }
    }
    return tracks + ", " + time
}

/** The glyph on a release page's placeholder sleeve: what kind of thing has no cover. */
""")
contents[DETAIL] = s

for path, value in contents.items():
    old = open(path, encoding='utf-8').read()
    assert value.count('{') - value.count('}') == old.count('{') - old.count('}'), ('braces', path)
for path, value in contents.items():
    with open(path, 'w', encoding='utf-8', newline='') as out:
        out.write(value)
subprocess.run(['git', 'config', 'user.name', 'pally-bot'], check=True)
subprocess.run(['git', 'config', 'user.email', 'pally-bot@users.noreply.github.com'], check=True)
subprocess.run(['git', 'add'] + list(contents), check=True)
subprocess.run(['git', 'commit', '-m', 'Album e single: data, musicas, duracao e creditos no fim da lista [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
