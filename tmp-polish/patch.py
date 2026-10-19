p = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
s = open(p, encoding='utf-8').read()
old = '    "album", "single", "ep",'
assert s.count(old) == 1, s.count(old)
new = '    "album", "' + chr(225) + 'lbum", "single", "ep",'
s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8').write(s)
print('patched')
