import re, glob
out = []
pat = re.compile(r'FrostedTopBar\(|searching|MoreVert|SongSort|onSearchingChange|isAlbum|BrowseType\.ALBUM')
files = glob.glob('app/src/main/java/**/*.kt', recursive=True)
for f in sorted(files):
    if f.endswith('DetailScreen.kt'):
        continue
    try:
        lines = open(f, encoding='utf-8').read().split('\n')
    except Exception:
        continue
    if not any('FrostedTopBar(' in l for l in lines):
        continue
    for i, l in enumerate(lines, 1):
        if pat.search(l):
            out.append(f'{f.split("/")[-1]}:{i}: {l.strip()[:180]}')
open('tmp-polish/out.txt', 'w', encoding='utf-8').write('\n'.join(out[:400]) + '\n')
print(len(out))
