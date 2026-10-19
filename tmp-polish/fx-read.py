import re
BASE = 'app/src/main/java/com/music/amusic/'
out = []

def load(p):
    with open(BASE + p, encoding='utf-8') as f:
        return f.read().split('\n')

def rng(p, a, b):
    lines = load(p)
    out.append('=== %s lines %d-%d' % (p, a, b))
    for j in range(a - 1, min(len(lines), b)):
        out.append('%d: %s' % (j + 1, lines[j]))

def grep(p, pats):
    lines = load(p)
    out.append('=== %s grep %s' % (p, pats))
    for i, l in enumerate(lines):
        if any(re.search(x, l) for x in pats):
            out.append('%d: %s' % (i + 1, l))

rng('MainActivity.kt', 3040, 3112)
rng('ui/screens/DetailScreen.kt', 270, 296)
rng('ui/screens/DetailScreen.kt', 470, 535)
grep('MainActivity.kt', [r'fun closeDetail', r'AnimatedContent', r'AnimatedVisibility', r'\bkey\(', r'detailStack', r'val detail by', r'val detail ='])
grep('ui/MainViewModel.kt', [r'fun closeDetail', r'detailStack', r'fun openDetail', r'_detail\b'])
with open('tmp-polish/out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')
