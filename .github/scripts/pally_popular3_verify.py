from pathlib import Path
import re

def edit(path, old, new):
    p = Path(path)
    s = p.read_text()
    if new in s:
        return
    assert s.count(old) == 1, (path, s.count(old), old[:100])
    p.write_text(s.replace(old, new))
base = 'shared/src/jvmSharedMain/kotlin/com/music/amusic/data/'
edit(base+'innertube/InnertubeParser.kt',
'''            playCount = columns.drop(1).firstNotNullOfOrNull { column ->
                playCountOf(column.o("musicResponsiveListItemFlexColumnRenderer").o("text").runs())
            },''',
'''            playCount = columns.drop(1).firstNotNullOfOrNull { column ->
                column.o("musicResponsiveListItemFlexColumnRenderer").o("text").runs()
                    .split(" • ", " · ").firstNotNullOfOrNull { part -> playCountOf(part) }
            } ?: renderer.a("fixedColumns").orEmpty().firstNotNullOfOrNull { column ->
                playCountOf(column.o("musicResponsiveListItemFixedColumnRenderer").o("text").runs())
            },''')
# A dedicated light lookup avoids fetching the entire discography or Apple's pre-releases.
edit(base+'YtMusicRepository.kt', '    private suspend fun <T> call(label: String, block: suspend () -> T): Result<T> =',
'''    /** YouTube's popular-song order and counts, without unrelated release shelves. */
    suspend fun artistPopularTracks(browseId: String): Result<List<Song>> = call("popular:$browseId") {
        val page = InnertubeParser.parseArtistPage(Innertube.browse(browseId))
        val expanded = page.moreSongsBrowseId?.let { songsPaged(it) }.orEmpty()
        val counts = page.songs.associate { it.videoId to it.playCount }
        val songs = if (expanded.isEmpty()) page.songs else expanded
        songs.map { song -> song.copy(playCount = counts[song.videoId] ?: song.playCount) }
    }

    private suspend fun <T> call(label: String, block: suspend () -> T): Result<T> =''')
p = 'app/src/main/java/com/music/amusic/data/stats/AlbumPopularTracks.kt'
edit(p, 'YtMusicRepository.artistPage(it).getOrNull()?.songs', 'YtMusicRepository.artistPopularTracks(it).getOrNull()')
parser = Path(base+'innertube/InnertubeParser.kt').read_text()
pattern = re.search(r'private val PUBLIC_PLAYS = Regex\(\s*"""(.*?)"""', parser, re.S).group(1)
regex = re.compile(pattern, re.I)
multipliers = {'k':1000,'mil':1000,'thousand':1000,'m':1000000,'mi':1000000,'million':1000000,'millions':1000000,'milhão':1000000,'milhões':1000000,'milhao':1000000,'milhoes':1000000,'b':1000000000,'bi':1000000000,'billion':1000000000,'billions':1000000000,'bilhão':1000000000,'bilhões':1000000000,'bilhao':1000000000,'bilhoes':1000000000}
def number(label):
    m = regex.fullmatch(label.replace('\u00a0',' ').replace('\u202f',' ').strip())
    if not m: return None
    raw = m[1].replace(' ','')
    suffix = (m[2] or '').lower()
    if suffix:
        split = max(raw.rfind(','), raw.rfind('.'))
        raw = ''.join(c for c in raw[:split] if c.isdigit())+'.'+raw[split+1:] if split >= 0 else raw
    else:
        if not re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+|\d+',raw): return None
        raw = ''.join(c for c in raw if c.isdigit())
    return int(float(raw)*multipliers.get(suffix,1))
fixtures = {'Tocou 763 mi vezes':763000000,'Tocou 1,2 mi vezes':1200000,'1.2M plays':1200000,'1,234,567 plays':1234567,'1.234 plays':1234,'763\u00a0mi reproduções':763000000,'Tocou 2 mil vezes':2000,'Tocou 1 bi vezes':1000000000,'0 plays':0,'21 Savage':None,'3:45':None,'13 songs':None,'2M likes':None,'unknown':None}
for label, expected in fixtures.items():
    got = number(label)
    assert got == expected, (label, got, expected)
    print('numeric fixture', repr(label), got)
rank = lambda rows: [r[0] for r in sorted(enumerate(rows),key=lambda v:(-v[1][1],v[0]))[:3]]
assert len(rank([('a',5),('b',10),('c',9),('d',11)])) == 3
ui = Path('sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components/Common.kt').read_text()
assert ui.count('mostPlayedOverride = mostPlayedOverride,') == 2
assert 'if (mostPlayedAlpha > 0f)' in ui
assert 'MOST_PLAYED_DOT_FADE_MS = 180' in ui
resolver = Path(p).read_text()
assert 'private const val LIMIT = 3' in resolver
assert resolver.index('rankedCounts(songs)') < resolver.index('artistPopularTracks') < resolver.index('ListeningStats.exportAll()')
print('source assertions passed; numeric regex fixtures passed; no Kotlin compilation or phone test')
