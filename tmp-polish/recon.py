import glob, re
out = []
files = sorted(glob.glob('app/src/main/java/**/*.kt', recursive=True))
pat = re.compile(r'browseActions|BrowseTarget\(|BrowseActionsSheet|BrowseActions\b|isReleaseDetail\s*=|isLocalDetail\s*=|songSortMenuOpen|folderMenuOpen')
for f in files:
    try:
        lines = open(f, encoding='utf-8').read().split('\n')
    except Exception:
        continue
    for i, l in enumerate(lines, 1):
        if pat.search(l):
            out.append(f.split('/')[-1] + ':' + str(i) + ': ' + l.strip()[:170])
open('tmp-polish/out.txt', 'w', encoding='utf-8').write('\n'.join(out[:300]) + '\n')
print(len(out))
