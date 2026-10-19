import re
src = open('app/src/main/java/com/music/amusic/MainActivity.kt', encoding='utf-8').read().splitlines()
keys = re.compile(r'BackHandler|popBack|backStack|Ver tudo|seeAll|SeeAll|AnimatedContent|appBackdrop|windowBackground|paintBackdrop|slideIn|slideOut|fadeIn|fadeOut|enterTransition|exitTransition|Crossfade|detail|lastArtist|restore|saved|return', re.I)
out = []
for i, l in enumerate(src, 1):
    if keys.search(l):
        out.append(str(i) + ': ' + l)
open('tmp-polish/out.txt', 'w', encoding='utf-8').write('total lines: ' + str(len(src)) + '\n' + '\n'.join(out[:700]))
print(len(src), len(out))
