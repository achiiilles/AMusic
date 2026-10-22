import os, re

SKIP = {'.git', 'build', '.gradle', '.idea', 'node_modules', '.kotlin'}

def kt_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for name in filenames:
            if name.endswith('.kt'):
                out.append(os.path.join(dirpath, name))
    return sorted(out)

def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().split('\n')

files = kt_files('.')
print('== total kt files', len(files))

print('== shelfitem context')
printed = 0
for p in files:
    lines = read(p)
    hits = [i for i, l in enumerate(lines) if 'ShelfItem' in l]
    if not hits:
        continue
    print('FILE %s lines=%d hits=%d' % (p, len(lines), len(hits)))
    shown = set()
    for i in hits[:12]:
        for k in range(max(0, i - 4), min(len(lines), i + 5)):
            if k in shown or printed > 1400:
                continue
            shown.add(k)
            printed += 1
            print('%s:%d: %s' % (os.path.basename(p), k + 1, lines[k].rstrip()[:200]))
        print('---')

print('== homeshelf files')
for p in files:
    lines = read(p)
    n = sum(1 for l in lines if 'HomeShelf' in l)
    if n:
        print('FILE %s hits=%d' % (p, n))

print('== artistpage files')
for p in files:
    text = '\n'.join(read(p))
    if 'ArtistPage' in text:
        print('FILE %s count=%d' % (p, text.count('ArtistPage')))

print('== subtitle usage')
printed = 0
for p in files:
    lines = read(p)
    if not any('ShelfItem' in l for l in lines):
        continue
    for i, l in enumerate(lines):
        if re.search(r'\.subtitle\b|subtitle\s*=', l):
            if printed > 400:
                continue
            printed += 1
            print('%s:%d: %s' % (os.path.basename(p), i + 1, l.strip()[:190]))

print('== artistpage body')
p = 'shared/src/jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt'
lines = read(p)
print('lines', len(lines))
start = None
for i, l in enumerate(lines):
    if 'suspend fun artistPage' in l:
        start = i
        break
print('start', start + 1 if start is not None else None)
if start is not None:
    for k in range(max(0, start - 2), min(len(lines), start + 50)):
        print('%d: %s' % (k + 1, lines[k].rstrip()[:200]))
    print('== anchor count')
    a = [k + 1 for k, l in enumerate(lines) if l.strip() == 'page.copy(songs = resolvedSongs, sections = fullShelves)']
    print(a)

print('== canvasget definition')
for p2 in files:
    lines2 = read(p2)
    for i, l in enumerate(lines2):
        if 'canvasGet' in l and 'fun ' in l:
            print('%s:%d: %s' % (p2, i + 1, l.strip()[:180]))

print('== shared http and serialization')
for p2 in kt_files('shared'):
    lines2 = read(p2)
    for i, l in enumerate(lines2):
        if re.search(r'import kotlinx\.serialization|HttpURLConnection|java\.net\.URL|fun .*[Gg]et.*\(', l):
            print('%s:%d: %s' % (p2, i + 1, l.strip()[:170]))
