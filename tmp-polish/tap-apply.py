import re, subprocess
p = 'app/src/main/java/com/music/amusic/MainActivity.kt'
s = open(p, encoding='utf-8').read()
pat = re.compile(r'(onClick = \{)\n(\s*)if \(signedIn\) \{\n\s*viewModel\.loadChannels\(\)\n\s*showAccountSelector = true\n\s*\} else showSettings = true\n(\s*\},\n\s*onSwipeProfile)')
m = pat.findall(s)
out = ['matches=%d' % len(m)]
if len(m) == 1:
    def rep(mo):
        ind = mo.group(2)
        return mo.group(1) + '\n' + ind + '// Opens Settings directly; account actions live in Settings > Conta.\n' + ind + 'showSettings = true\n' + mo.group(3)
    s2 = pat.sub(rep, s)
    open(p, 'w', encoding='utf-8').write(s2)
    out.append('patched')
open('tmp-polish/tap-out.txt', 'w').write('\n'.join(out) + '\n')
print(out)
