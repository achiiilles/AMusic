#!/usr/bin/env python3
import sys

D = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
M = 'app/src/main/java/com/music/amusic/MainActivity.kt'
PARAM = 'onPlayByName: ((name: String, artist: String?) -> Unit)? = null,\n'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def write(p, s):
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)


def after_line(text, needle, insert, where, unique=True):
    n = text.count(needle)
    if n == 0 or (unique and n != 1):
        sys.exit('%s: expected 1 match, got %d' % (where, n))
    out = []
    idx = 0
    while True:
        k = text.find(needle, idx)
        if k < 0:
            out.append(text[idx:])
            break
        start = text.rfind('\n', 0, k) + 1
        indent = text[start:k]
        out.append(text[idx:k + len(needle)])
        out.append(indent + insert)
        idx = k + len(needle)
    return ''.join(out)


d = read(D)
d = after_line(d, ' onSongSwipe: (Song) -> Unit,\n', PARAM, 'DetailScreen signature')

anchor = 'private fun SectionCard('
i = d.index(anchor)
needle = ' onLongPress: (() -> Unit)? = null,\n'
j = d.index(needle, i)
start = d.rfind('\n', 0, j) + 1
indent = d[start:j]
end = j + len(needle)
d = d[:end] + indent + PARAM + d[end:]

d = after_line(
    d,
    'onDismiss = { preReleaseOpen.value = false },\n',
    'onOpenTrack = onPlayByName,\n',
    'PreReleasePage call',
)
d = after_line(
    d,
    'onLongPress = onSectionItemLongPress?.let { { it(item) } },\n',
    'onPlayByName = onPlayByName,\n',
    'SectionCard call',
)

HOOK = (
    'onPlayByName = { name, artist ->\n'
    '                        scope.launch {\n'
    '                            val query = listOfNotNull(name, artist).joinToString(" ")\n'
    '                            val hits = YtMusicRepository.search(query, SearchFilter.SONGS)\n'
    '                                .getOrNull()\n'
    '                                .orEmpty()\n'
    '                            val song = hits.mapNotNull { hit ->\n'
    '                                (hit as? SearchResult.Track)?.song\n'
    '                                    ?: (hit as? SearchResult.TopTrack)?.song\n'
    '                            }.firstOrNull()\n'
    '                            if (song == null) {\n'
    '                                Toast.makeText(\n'
    '                                    context,\n'
    '                                    context.getString(R.string.couldnt_find, name),\n'
    '                                    Toast.LENGTH_SHORT,\n'
    '                                ).show()\n'
    '                            } else {\n'
    '                                playDetailSongs(listOf(song), 0)\n'
    '                            }\n'
    '                        }\n'
    '                    },\n'
)

m = read(M)
m = after_line(
    m,
    'onSongSwipe = { onSongSwipe(withAlbum(it)) },\n',
    HOOK,
    'MainActivity DetailScreen call',
)

write(D, d)
write(M, m)
print('patched DetailScreen.kt and MainActivity.kt')
