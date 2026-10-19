import re

S = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/'
A = 'app/src/main/java/com/music/amusic/'
files = {}
log = []


class Fail(Exception):
    pass


def load(p):
    if p not in files:
        files[p] = open(p, encoding='utf-8').read()
    return files[p]


def sub(p, pat, repl):
    s = load(p)
    new, n = re.subn(pat, repl, s)
    log.append('%s | %s | matches=%d' % (p.split('/')[-1], pat[:60], n))
    if n != 1:
        raise Fail(p)
    files[p] = new


IMP = 'import coil3.compose.AsyncImage\n'


def add_import(p):
    s = load(p)
    n = s.count(IMP)
    log.append('%s | import | matches=%d' % (p.split('/')[-1], n))
    if n != 1:
        raise Fail(p)
    files[p] = s.replace(IMP, IMP + 'import com.music.amusic.ui.components.ArtistAwareImage\n')


REC = (
    'val artShape = if (entity.entityType == EntityType.ARTIST) CircleShape else RoundedCornerShape(8.dp)\n'
    '            ArtistAwareImage(\n'
    '                model = entity.artworkUrl,\n'
    '                artistName = entity.title.takeIf { entity.entityType == EntityType.ARTIST },\n'
    '                contentDescription = null,\n'
    '                modifier = Modifier\n'
    '                    .size(52.dp)\n'
    '                    .clip(artShape)\n'
    '                    .thumbnailBorder(artShape)\n'
    '                    .background(MaterialTheme.colorScheme.surfaceVariant),\n'
    '            )'
)

try:
    for f in (S + 'SearchScreen.kt', S + 'HomeScreen.kt', A + 'ui/screens/DetailScreen.kt'):
        add_import(f)

    sub(S + 'SearchScreen.kt',
        r'AsyncImage\(\s*model = entity\.artworkUrl,\s*contentDescription = null,\s*modifier = Modifier\s*\.size\(52\.dp\)\s*\.clip\(RoundedCornerShape\(8\.dp\)\)\s*\.thumbnailBorder\(RoundedCornerShape\(8\.dp\)\)\s*\.background\(MaterialTheme\.colorScheme\.surfaceVariant\),\s*\)',
        lambda m: REC)

    sub(S + 'SearchScreen.kt',
        r'AsyncImage\(\s*model = item\.thumbnailUrl\.artworkAt\(ROW_ART_PX\),',
        lambda m: 'ArtistAwareImage(\n            artistName = item.title.takeIf { item.type == BrowseType.ARTIST },\n            model = item.thumbnailUrl.artworkAt(ROW_ART_PX),')

    sub(S + 'HomeScreen.kt',
        r'AsyncImage\((\s*)model = item\.thumbnailUrl\.artworkAt\(CARD_ART_PX\),(\s*contentDescription = null,\s*contentScale = androidx\.compose\.ui\.layout\.ContentScale\.Crop,)',
        lambda m: 'ArtistAwareImage(' + m.group(1) + 'artistName = item.title.takeIf { item.browseId?.startsWith("UC") == true },' + m.group(1) + 'model = item.thumbnailUrl.artworkAt(CARD_ART_PX),' + m.group(2))

    sub(A + 'ui/screens/DetailScreen.kt',
        r'AsyncImage\((\s*)model = item\.thumbnailUrl\.artworkAt\(CARD_ART_PX\),(\s*contentDescription = null,\s*modifier = Modifier\s*\.fillMaxWidth\(\)\s*\.aspectRatio\(1f\)\s*\.clip\(item\.artistAwareShape)',
        lambda m: 'ArtistAwareImage(' + m.group(1) + 'artistName = item.title.takeIf { item.browseId?.startsWith("UC") == true },' + m.group(1) + 'model = item.thumbnailUrl.artworkAt(CARD_ART_PX),' + m.group(2))

    sub(A + 'AMusicApplication.kt',
        r'\n([ \t]*)SearchHistory\.init\(this\)\n',
        lambda m: '\n' + m.group(1) + 'SearchHistory.init(this)\n' + m.group(1) + '// Apple Music photos for artists in every list; YouTube photo stays until one arrives.\n' + m.group(1) + 'com.music.amusic.ui.components.ArtistPhotos.provider = com.music.amusic.data.canvas.AppleArtistPhotoProvider\n')

    sub(A + 'data/canvas/AppleArtistPhotoProvider.kt',
        r'\n    private fun remember\(key: String, @Suppress\("UNUSED_PARAMETER"\) art: AppleArtistArt\?, url: String\): String = url\n',
        lambda m: '')

    for p, s in files.items():
        open(p, 'w', encoding='utf-8').write(s)
    log.append('OK: all patches written')
except Fail as e:
    log.append('FAILED at %s: nothing written' % e)

open('tmp-polish/out-apply.txt', 'w').write('\n'.join(log) + '\n')
