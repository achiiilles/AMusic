import os, re

def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().split('\n')

def show(lines, start, count):
    for k in range(max(0, start), min(len(lines), start + count)):
        print('%d: %s' % (k + 1, lines[k].rstrip()[:200]))

m = read('shared/src/commonMain/kotlin/com/music/amusic/data/model/Models.kt')
print('== models lines', len(m))
for name in ('class ArtistPage', 'class HomeShelf', 'class ShelfItem'):
    for i, l in enumerate(m):
        if l.startswith('data class %s' % name.split()[1]) or l.strip().startswith('data class %s' % name.split()[1]):
            print('--- %s at %d' % (name, i + 1))
            show(m, i - 6, 50)
            break

h = read('shared/src/jvmSharedMain/kotlin/com/music/amusic/data/Http.kt')
print('== http head')
show(h, 0, 45)
for i, l in enumerate(h):
    if 'val client' in l or 'object Http' in l or 'fun get' in l:
        print('HTTP %d: %s' % (i + 1, l.strip()[:160]))

d = read('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt')
print('== detail section render')
shown = set()
for i, l in enumerate(d):
    if 'HomeShelf' in l or 'sections' in l or 'ArtistShelfGridPage(' in l:
        for k in range(max(0, i - 8), min(len(d), i + 9)):
            if k not in shown:
                shown.add(k)
                print('%d: %s' % (k + 1, d[k].rstrip()[:190]))
        print('---')
