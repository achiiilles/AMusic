#!/bin/bash
OUT=tmp-polish/out-rec.txt
: > $OUT
sec() { echo "=== $1" >> $OUT; }
R=sharedUi/src/commonMain/composeResources
sec "resource dirs"
ls $R >> $OUT
sec "pt count vs en count"
grep -c '<string ' $R/values/strings.xml $R/values-pt/strings.xml >> $OUT
sec "other xml files in values"
ls $R/values >> $OUT
sec "android res strings"
find app/src/main/res -name 'strings*.xml' | head -20 >> $OUT
sec "HomeScreen 560-600"
sed -n '560,600p' sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt >> $OUT
sec "RecentSectionHeader"
sed -n '300,330p;372,408p' sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt >> $OUT
sec "keys in en missing in pt (key|english)"
python3 - <<'PY' >> $OUT
import re
R='sharedUi/src/commonMain/composeResources/'
def load(p):
    t=open(R+p,encoding='utf-8').read()
    d={}
    for m in re.finditer(r'<string name="([^"]+)"([^>]*)>(.*?)</string>',t,re.S):
        d[m.group(1)]=m.group(3)
    return d,t
en,ent=load('values/strings.xml')
pt,ptt=load('values-pt/strings.xml')
miss=[k for k in en if k not in pt]
print('missing',len(miss))
for k in miss: print(k+'|'+en[k].replace('\n','\\n'))
print('--- same text in pt as en')
for k in en:
    if k in pt and pt[k]==en[k] and re.search('[a-z]{4}',en[k]): print(k+'|'+en[k])
print('--- plurals/arrays in en')
print(len(re.findall('<plurals',ent)),len(re.findall('<string-array',ent)))
PY
