import re, sys, subprocess
P = 'shared/src/jvmSharedMain/kotlin/com/music/amusic/data/lyrics/LyricsSource.kt'
raw = open(P, 'r', encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in raw else '\n'
lines = raw.split(nl)
start_re = re.compile(r'^\s*([A-Z][A-Z_]*)\(\s*$')
end_re = re.compile(r'^\s*\),?\s*$')
blocks = []
i = 0
first = None
last_end = None
while i < len(lines):
    m = start_re.match(lines[i])
    if m:
        j = i + 1
        while j < len(lines) and not end_re.match(lines[j]):
            j += 1
        if j >= len(lines):
            print('ERRO: bloco sem fim', m.group(1)); sys.exit(1)
        if first is None:
            first = i
        blocks.append((m.group(1), lines[i:j + 1]))
        last_end = j
        i = j + 1
    else:
        i += 1
names = [b[0] for b in blocks]
print('ANTES:', names)
if len(blocks) != 17:
    print('ERRO: esperava 17 fontes, achei', len(blocks)); sys.exit(1)
if last_end - first + 1 != sum(len(b[1]) for b in blocks):
    print('ERRO: ha linhas entre as fontes, nao mexo'); sys.exit(1)
top = ['BETTER_LYRICS', 'PAXSENIX', 'LYRICS_PLUS']
for t in top:
    if t not in names:
        print('ERRO: falta', t); sys.exit(1)
d = dict(blocks)
new_names = top + [n for n in names if n not in top]
new_lines = []
for n in new_names:
    new_lines.extend(d[n])
indent = re.match(r'^(\s*)', lines[first]).group(1)
note = [
    indent + '// Ordem padrao definida pelo dono do app: BETTER_LYRICS, PAXSENIX e',
    indent + '// LYRICS_PLUS nas tres primeiras posicoes; as demais seguem na ordem em',
    indent + '// que ja estavam. Vale so para quem nao tem ordem salva.',
]
out = lines[:first] + note + new_lines + lines[last_end + 1:]
open(P, 'w', encoding='utf-8', newline='').write(nl.join(out))
print('DEPOIS:', new_names)
print('--- usos de LyricsSource.entries/offered e ordem salva ---')
sys.stdout.flush()
subprocess.run('grep -rn "LyricsSource.entries\\|LyricsSource.offered\\|lyricsSourceOrder" --include=*.kt . | head -40', shell=True)
