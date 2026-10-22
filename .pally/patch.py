#!/usr/bin/env python3
import sys

D = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
M = 'app/src/main/java/com/music/amusic/MainActivity.kt'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def write(p, s):
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)


def after_line(text, needle, insert, where):
    n = text.count(needle)
    if n != 1:
        sys.exit('%s: expected 1 match, got %d' % (where, n))
    k = text.index(needle)
    start = text.rindex('\n', 0, k) + 1
    indent = text[start:k]
    return text[:k + len(needle)] + indent + insert + text[k + len(needle):]


NEW_PARAM = 'onPlayByName: ((name: String, artist: String?) -> Unit)? = null,\n'

# ---- DetailScreen.kt
d = read(D)

d = after_line(d, '    onSongSwipe: (Song) -> Unit,\n', NEW_PARAM, 'DetailScreen signature')

i = d.index('private fun SectionCard(')
j = d.index('    onLongPress: (() -> Unit)? = null,\n', i)
end = j + len('    onLongPress: (() -> Unit)? = null,\n')
d = d[:end] + '    ' + NEW_PARAM + d[end:]

d = after_line(d, 'onDismiss = { preReleaseOpen.value = false },\n', 'onOpenTrack = onPlayByName,\n', 'PreReleasePage call')

d = after_line(d, 'onLongPress = onSectionItemLongPress?.let { { it(item) } },\n', 'onPlayByName = onPlayByName,\n', 'SectionCard call')

# ---- MainActivity.kt
m = read(M)

hook = ('onPlayByName = { name, artist ->\n'
        '    scope.launch {\n'
        '        val query = listOfNotNull(name, artist).joinToString(" ")\n'
        '        val found = YtMusicRepository.search(query, SearchFilter.SONGS)\n'
        '            .getOrNull()\n'
        '            .orEmpty()\n'
        '        val track = found.filterIsInstance<SearchResult.Track>()\n'
        '            .firstOrNull()?.song\n'
        '            ?: found.filterIsInstance<SearchResult.TopTrack>()\n'
        '                .firstOrNull()?.song\n'
        '        if (track == null) {\n'
        '            Toast.makeText(\n'
        '                context,\n'
        '                context.getString(R.string.couldnt_find, name),\n'
        '                Toast.LENGTH_SHORT,\n'
        '            ).show()\n'
        '        } else {\n'
        '            playDetailSongs(listOf(track), 0)\n'
        '        }\n'
        '    }\n'
        '},\n')

m = after_line(m, 'onSongSwipe = { onSongSwipe(withAlbum(it)) },\n', hook, 'DetailScreen call')

write(D, d)
write(M, m)
print('patched DetailScreen.kt and MainActivity.kt')
