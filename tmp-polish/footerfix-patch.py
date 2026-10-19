import sys
P = 'app/src/main/java/com/music/amusic/ui/screens/SettingsSheet.kt'
raw = open(P, 'r', encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in raw else '\n'
lines = raw.split(nl)
OLD = 'LinkAnnotation.Url("https://github.com/kushagrasinghx/BitChord", linkStyles)'
NEW = 'LinkAnnotation.Url("https://github.com/achiiilles/AMusic", linkStyles)'
hits = [i for i, l in enumerate(lines) if OLD in l]
if len(hits) != 1:
    print('ERRO: link do GitHub aparece', len(hits), 'vezes'); sys.exit(1)
lines[hits[0]] = lines[hits[0]].replace(OLD, NEW)
targets = [
    'LinkAnnotation.Url("https://github.com/kushagrasinghx", linkStyles)',
    'LinkAnnotation.Url("https://discord.gg/pDdKfrdHY6", linkStyles)',
    'LinkAnnotation.Url("https://bitchord.kushagrasingh.in/", linkStyles)',
]
first_comment = None
for t in targets:
    idx = [i for i, l in enumerate(lines) if t in l]
    if len(idx) != 1:
        print('ERRO: link', t, 'aparece', len(idx), 'vezes'); sys.exit(1)
    i = idx[0]
    if lines[i - 1].strip() != 'append("  ")' or lines[i + 2].strip() != '}':
        print('ERRO: formato inesperado em volta de', t); sys.exit(1)
    if first_comment is None or i - 1 < first_comment:
        first_comment = i - 1
    for k in range(i - 1, i + 3):
        l = lines[k]
        ind = len(l) - len(l.lstrip())
        lines[k] = l[:ind] + '// ' + l[ind:]
ind = len(lines[first_comment]) - len(lines[first_comment].lstrip())
note = ' ' * ind + '// Links Developer, Discord e Website tirados do rodape a pedido do dono; o codigo fica comentado.'
lines.insert(first_comment, note)
open(P, 'w', encoding='utf-8', newline='').write(nl.join(lines))
print('OK: GitHub aponta para achiiilles/AMusic; Developer, Discord e Website comentados')
