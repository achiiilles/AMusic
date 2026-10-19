import re
P = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
OUT = 'tmp-polish/fade-out.txt'
log = []
src = open(P, encoding='utf-8').read()
old = 'fadeIn(animationSpec = tween(220)) togetherWith fadeOut(animationSpec = tween(180))'
new = 'fadeIn(animationSpec = tween(180)) togetherWith fadeOut(animationSpec = tween(180))'
n = src.count(old)
log.append('occurrences of old transition: ' + str(n))
if n == 1:
    src = src.replace(old, new)
    open(P, 'w', encoding='utf-8').write(src)
    log.append('patched: yes')
else:
    log.append('patched: no')
lines = src.split('\n')
log.append('total lines: ' + str(len(lines)))
for i in range(519, min(560, len(lines))):
    log.append(str(i + 1) + ': ' + lines[i])
hits = 0
for i, l in enumerate(lines, 1):
    if re.search(r'val pageColor|pageColor =|layerBackdrop|PageBackground\(', l) and hits < 40:
        log.append('grep ' + str(i) + ': ' + l)
        hits += 1
open(OUT, 'w', encoding='utf-8').write('\n'.join(log) + '\n')
