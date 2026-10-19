import os, re, subprocess

roots = ['app/src/main/java', 'sharedUi/src']
files = []
for r in roots:
    for d, _, fs in os.walk(r):
        for f in fs:
            if f.endswith('.kt'):
                files.append(os.path.join(d, f))

def grep(pats, name, cap=9000):
    out = []
    rx = re.compile('|'.join(pats))
    for p in sorted(files):
        with open(p, encoding='utf-8') as fh:
            for i, l in enumerate(fh, 1):
                if rx.search(l):
                    out.append('%s:%d: %s' % (p.replace('app/src/main/java/com/music/amusic/', 'A/').replace('sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/', 'S/'), i, l.strip()[:170]))
    with open('tmp-polish/' + name, 'w', encoding='utf-8') as o:
        o.write('\n'.join(out)[:cap * 3])

grep(['inLibraryArtistPage', 'onLibraryArtistClick', 'libraryArtist'], 'out-a.txt')
grep(['pluralStringResource', 'artist_library', 'songs_count', 'n_songs'], 'out-b.txt')
grep(['heroUrl', 'AppleArtistArt\\b', 'artFor\\(', 'cached\\(page'], 'out-c.txt')

sr = []
for d, _, fs in os.walk('app/src/main/res'):
    for f in fs:
        if f == 'strings.xml' and ('values' == os.path.basename(d) or 'values-pt' in d):
            with open(os.path.join(d, f), encoding='utf-8') as fh:
                for i, l in enumerate(fh, 1):
                    if re.search(r'song|música|library|biblioteca', l, re.I):
                        sr.append('%s:%d: %s' % (d, i, l.strip()[:170]))
with open('tmp-polish/out-d.txt', 'w', encoding='utf-8') as o:
    o.write('\n'.join(sr)[:20000])
