import re, os

UI = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components'

def lines_of(path):
    with open(path, encoding='utf-8') as f:
        return f.read().split('\n')

print('== component files')
for root, dirs, files in os.walk(UI):
    for name in files:
        if not name.endswith('.kt'):
            continue
        path = os.path.join(root, name)
        lines = lines_of(path)
        hits = [i for i, l in enumerate(lines) if 'ShelfItem' in l]
        if hits:
            print(path, 'lines', len(lines), 'shelfitem hits', len(hits))

print('== subtitle draws')
for root, dirs, files in os.walk(UI):
    for name in files:
        if not name.endswith('.kt'):
            continue
        path = os.path.join(root, name)
        lines = lines_of(path)
        for i, l in enumerate(lines):
            if re.search(r'\.subtitle\b', l) and ('item' in l.lower() or 'Text' in l):
                print('%s:%d: %s' % (path, i + 1, l.strip()[:180]))
                for k in range(i - 2, i + 3):
                    if 0 <= k < len(lines) and k != i:
                        print('   %d: %s' % (k + 1, lines[k].strip()[:160]))
                print('--')
