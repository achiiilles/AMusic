import sys
NL = chr(10)
PATH = 'app/src/main/java/com/music/amusic/MainActivity.kt'
OUT = 'tmp-polish/out.txt'
TARGET = 'LaunchedEffect(detail?.browseId) { detailActiveShelf = null }'
NEW = '''    var shelfDetailId by remember { mutableStateOf<String?>(null) }
    var shelfReturn by remember { mutableStateOf<Pair<String, HomeShelf>?>(null) }
    LaunchedEffect(detail?.browseId) {
        // Opening an album from the artist Ver tudo list pushes the album over
        // the artist page. Keep that list here, so going back to the artist opens it again.
        val nowId = detail?.browseId
        val prevId = shelfDetailId
        shelfDetailId = nowId
        val openShelf = detailActiveShelf
        if (nowId == null) {
            shelfReturn = null
        } else if (openShelf != null && prevId != null && prevId != nowId) {
            shelfReturn = prevId to openShelf
        }
        val back = shelfReturn
        val restore = back != null && back.first == nowId
        detailActiveShelf = if (restore) back?.second else null
        if (restore) shelfReturn = null
    }'''
out = []
src = open(PATH, encoding='utf-8').read()
lines = src.split(NL)
hits = [i for i, l in enumerate(lines) if l.strip() == TARGET]
if 'shelfReturn = prevId to openShelf' in src:
    out.append('already patched, no change')
elif len(hits) != 1:
    out.append('anchor found %d times, no change' % len(hits))
    open(OUT, 'w', encoding='utf-8').write(NL.join(out) + NL)
    sys.exit(1)
else:
    i = hits[0]
    lines[i:i + 1] = NEW.split(NL)
    open(PATH, 'w', encoding='utf-8').write(NL.join(lines))
    out.append('patched %s at line %d' % (PATH, i + 1))
    out.append(NEW)
open(OUT, 'w', encoding='utf-8').write(NL.join(out) + NL)
