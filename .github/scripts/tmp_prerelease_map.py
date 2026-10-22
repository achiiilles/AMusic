import re

REPO = 'shared/src/jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt'
VM = 'app/src/main/java/com/music/amusic/ui/MainViewModel.kt'

def lines_of(path):
    with open(path, encoding='utf-8') as f:
        return f.read().split('\n')

def block(lines, idx):
    start = idx
    while start > 0:
        s = lines[start].lstrip()
        if s.startswith('fun ') or s.startswith('suspend fun ') or s.startswith('private fun ') or s.startswith('internal fun '):
            break
        start -= 1
    depth = 0
    end = start
    for j in range(start, len(lines)):
        depth += lines[j].count('{') - lines[j].count('}')
        if depth == 0 and j > start:
            end = j
            break
    return start, end

def dump(path, needle, limit=400):
    lines = lines_of(path)
    hits = [i for i, l in enumerate(lines) if needle in l]
    print('FILE', path, 'lines', len(lines), 'hits', len(hits))
    seen = set()
    printed = 0
    for i in hits:
        start, end = block(lines, i)
        if (start, end) in seen:
            continue
        seen.add((start, end))
        print('--- function at line', start + 1, 'to', end + 1)
        for k in range(start, end + 1):
            print('%d: %s' % (k + 1, lines[k]))
            printed += 1
            if printed > limit:
                print('--- cut')
                return

print('== repo artist page')
dump(REPO, 'ArtistPage(')
print('== viewmodel artist page')
dump(VM, 'ArtistPage(')
