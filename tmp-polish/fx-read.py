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

rng('MainActivity.kt', 1125, 1165)
rng('MainActivity.kt', 2634, 2800)
with open('tmp-polish/out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')
