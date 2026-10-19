#!/bin/bash
OUT=tmp-polish/out-rec.txt
: > $OUT
sec() { echo "=== $1" >> $OUT; }
sec "long same-as-en android values (full)"
python3 - <<'PY' >> $OUT
import re
def load(p):
    t=open(p,encoding='utf-8').read()
    d={}
    for m in re.finditer(r'<string name="([^"]+)"([^>]*)>(.*?)</string>',t,re.S):
        if 'translatable="false"' in m.group(2): continue
        d[m.group(1)]=m.group(3)
    return d
en=load('app/src/main/res/values/strings.xml')
pt=load('app/src/main/res/values-pt/strings.xml')
for k in en:
    if k in pt and pt[k]==en[k] and re.search('[A-Za-z]{4}',en[k]) and len(en[k])>=95:
        print(k+'|'+en[k].replace('\n','\\n'))
print('--- sample pt style')
for k in ['replay_this_week','this_month','all_time','show_all','downloads_empty']:
    print(k, pt.get(k))
PY
sec "AccountChannelDialog 120-135, 230-240"
sed -n '120,135p;230,240p' app/src/main/java/com/music/amusic/ui/components/AccountChannelDialog.kt >> $OUT
sec "DiscordScreen 74-96"
sed -n '74,96p' app/src/main/java/com/music/amusic/ui/screens/DiscordScreen.kt >> $OUT
sec "MainActivity 5482-5490"
sed -n '5482,5490p' app/src/main/java/com/music/amusic/MainActivity.kt >> $OUT
sec "MainViewModel 2994-2998"
sed -n '2994,2998p' app/src/main/java/com/music/amusic/ui/MainViewModel.kt >> $OUT
sec "AudioPipelineDialog 434-438, 483-487, 501-505"
sed -n '434,438p;483,487p;501,505p' app/src/main/java/com/music/amusic/ui/components/AudioPipelineDialog.kt >> $OUT
sec "uses of ListeningStats label("
grep -rIn --include=*.kt -E '\.label\((today|LocalDate)' app/src/main/java | cut -c1-180 | head -6 >> $OUT
sec "pt string-arrays"
grep -n -A3 '<string-array' sharedUi/src/commonMain/composeResources/values-pt/strings.xml | head -12 >> $OUT
