import os, re

SKIP = {'.git', 'build', '.gradle', '.idea', 'node_modules', '.kotlin'}

def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().split('\n')

def kt(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for name in filenames:
            if name.endswith('.kt'):
                out.append(os.path.join(dirpath, name))
    return sorted(out)

print('== shared kt files')
for p in kt('shared'):
    print(p)

repo = 'shared/src/jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt'
lines = read(repo)
print('== repo lines', len(lines))
print('== repo head')
for i in range(0, min(70, len(lines))):
    print('%d: %s' % (i + 1, lines[i].rstrip()[:200]))

print('== artistPage')
for i, l in enumerate(lines):
    if 'suspend fun artistPage' in l:
        for k in range(max(0, i - 3), min(len(lines), i + 48)):
            print('%d: %s' % (k + 1, lines[k].rstrip()[:200]))
        break

print('== anchor lines')
print([k + 1 for k, l in enumerate(lines) if l.strip() == 'page.copy(songs = resolvedSongs, sections = fullShelves)'])

print('== shared network helpers')
for p in kt('shared'):
    for i, l in enumerate(read(p)):
        if re.search(r'java\.net|HttpURLConnection|okhttp|OkHttp|https://|suspend fun call', l):
            print('%s:%d: %s' % (p, i + 1, l.strip()[:180]))

print('== sectioncard body')
d = read('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt')
print('detail lines', len(d))
for k in range(2724, min(2790, len(d))):
    print('%d: %s' % (k + 1, d[k].rstrip()[:200]))

print('== detail sections usage')
for i, l in enumerate(d):
    if 'sections' in l:
        print('%d: %s' % (i + 1, l.strip()[:190]))
