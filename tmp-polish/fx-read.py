import re
BASE = 'app/src/main/java/com/music/amusic/'
out = []

def load(p):
    with open(BASE + p, encoding='utf-8') as f:
        return f.read().split('\n')

def grep(p, pats, ctx):
    lines = load(p)
    out.append('=== %s (%d lines) grep %s ctx %d' % (p, len(lines), pats, ctx))
    shown = set()
    for i, l in enumerate(lines):
        if any(re.search(x, l) for x in pats):
            for j in range(max(0, i - ctx), min(len(lines), i + ctx + 1)):
                if j not in shown:
                    if shown and (j - 1) not in shown:
                        out.append('  ...')
                    shown.add(j)
                    out.append('%d: %s' % (j + 1, lines[j]))

def rng(p, a, b):
    lines = load(p)
    out.append('=== %s lines %d-%d' % (p, a, b))
    for j in range(a - 1, min(len(lines), b)):
        out.append('%d: %s' % (j + 1, lines[j]))

grep('MainActivity.kt', [r'detailActiveShelf', r'shelfReturn', r'shelfDetailId', r'activeShelf'], 3)
grep('ui/screens/DetailScreen.kt', [r'activeShelf', r'onActiveShelfChange', r'onShelfChange'], 2)
lines = load('ui/MainViewModel.kt')
for i, l in enumerate(lines):
    if 'fun toggleSongLibrary' in l:
        rng('ui/MainViewModel.kt', max(1, i - 15), i + 75)
        break
grep('ui/MainViewModel.kt', [r'songMenuJob', r'fun loadSongMenu', r'fun dropFromLibrarySongs', r'libraryShown', r'libraryToggleJob', r'songMenuVideoId'], 2)
grep('MainActivity.kt', [r'libraryShown', r'libraryMenu', r'toggleSongLibrary'], 3)
grep('ui/components/SongActionsSheet.kt', [r'inLibrary', r'onToggleLibrary'], 3)
with open('tmp-polish/out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')
