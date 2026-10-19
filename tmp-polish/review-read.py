
import re, os, glob
root='app/src/main/java/com/music/amusic'
files=[root+'/MainActivity.kt']+sorted(glob.glob(root+'/ui/**/*.kt', recursive=True))
pat=re.compile(r'AnimatedContent|AnimatedVisibility|Crossfade|animate\w*AsState|animateContentSize|animateItem|animateFloat|fadeIn|fadeOut|tween\(|spring\(|slideIn|slideOut|scaleIn|scaleOut|updateTransition|rememberInfiniteTransition|pressScale|pressable|bouncyClick|EnterTransition|ExitTransition|FastOutSlowIn|LinearOutSlowIn|BackHandler|NavHost|togetherWith|ContentTransform|Animatable|snap\(|keyframes|AnimationSpec|transitionSpec|SharedTransition|animateScroll|isPressed|collectIsPressedAsState')
counts=[];lines=[]
for f in files:
    try: src=open(f,encoding='utf-8').read().split('\n')
    except Exception as e: continue
    n=0
    for i,l in enumerate(src,1):
        if pat.search(l):
            n+=1
            lines.append('%s:%d: %s'%(f.replace(root+'/',''),i,l.strip()[:170]))
    counts.append('%d %s (%d lines)'%(n,f.replace(root+'/',''),len(src)))
os.makedirs('tmp-polish',exist_ok=True)
open('tmp-polish/out-counts.txt','w').write('\n'.join(counts))
open('tmp-polish/out-lines.txt','w').write('\n'.join(lines))
