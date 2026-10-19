import re
base='app/src/main/java/com/music/amusic/'
files=['MainActivity.kt','ui/MainViewModel.kt','ui/screens/DetailScreen.kt']
pat=re.compile(r'BackHandler|popBack|backStack|BackStack|navStack|onBack|goBack|navigateBack|screenStack|closeDetail|pushDetail|openArtist|openDetail|detailStack|browseStack')
out=[]
for f in files:
    L=open(base+f,encoding='utf-8').read().split('\n')
    out.append('=== '+f+' lines '+str(len(L)))
    for i,l in enumerate(L):
        if pat.search(l):
            out.append(f'{i+1}: {l.strip()[:200]}')
open('tmp-polish/out.txt','w',encoding='utf-8').write('\n'.join(out))
