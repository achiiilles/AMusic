base='app/src/main/java/com/music/amusic/'
req=[('MainActivity.kt',[(2536,2615),(3650,3695)]),('ui/MainViewModel.kt',[(2650,2705),(3210,3235)])]
out=[]
for f,rs in req:
    L=open(base+f,encoding='utf-8').read().split('\n')
    for a,b in rs:
        out.append(f'=== {f} {a}-{b}')
        for i in range(a-1,min(b,len(L))):
            out.append(f'{i+1}: {L[i]}')
open('tmp-polish/out.txt','w',encoding='utf-8').write('\n'.join(out))
