import re
p='app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
src=open(p,encoding='utf-8').read().splitlines()
keys=re.compile(r'activeShelf|onActiveShelfChange|AnimatedContent|Crossfade|AnimatedVisibility|layerBackdrop|hazeSource|hazeEffect|drawBehind|\.background\(|windowBackground|MaterialTheme\.colorScheme\.background')
hits=[i for i,l in enumerate(src) if keys.search(l)]
show=set()
for i in hits:
    if re.search(r'activeShelf|onActiveShelfChange',src[i]):
        for j in range(max(0,i-6),min(len(src),i+7)): show.add(j)
    else:
        show.add(i)
out=['total lines: '+str(len(src))]
last=-2
for j in sorted(show):
    if j!=last+1: out.append('----')
    out.append(str(j+1)+': '+src[j])
    last=j
open('tmp-polish/out.txt','w',encoding='utf-8').write('\n'.join(out))
print(len(src),len(show))
