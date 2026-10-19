#!/bin/bash
OUT=tmp-polish/out-rec.txt
: > $OUT
sec() { echo "=== $1" >> $OUT; }
sec "android res: pt same as en"
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
n=0
for k in en:
    if k in pt and pt[k]==en[k] and re.search('[A-Za-z]{4}',en[k]):
        n+=1
        if n<=170: print(k+'|'+en[k].replace('\n','\\n')[:100])
print('total same',n)
PY
sec "localizeShelfTitle 640-700"
sed -n '640,700p' sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt >> $OUT
sec "Home RecentShelf usage 262-285 and 306-316"
sed -n '262,285p;306,316p' sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt >> $OUT
sec "AccountChannelDialog 110-118, 165-176"
sed -n '110,118p;165,176p' app/src/main/java/com/music/amusic/ui/components/AccountChannelDialog.kt >> $OUT
sec "ReplayModel 185-200"
sed -n '185,200p' app/src/main/java/com/music/amusic/ui/replay/ReplayModel.kt >> $OUT
sec "ListeningStats 1018-1034"
sed -n '1018,1034p' app/src/main/java/com/music/amusic/data/stats/ListeningStats.kt >> $OUT
sec "AppSettings 95-102 and usage of ThemeMode label"
sed -n '95,102p' app/src/main/java/com/music/amusic/data/settings/AppSettings.kt >> $OUT
grep -rIn --include=*.kt -E 'ThemeMode|themeMode' app/src/main/java sharedUi/src | grep -E 'label|entries' | cut -c1-200 | head -10 >> $OUT
sec "AudioPipelineDialog 325-342"
sed -n '325,342p' app/src/main/java/com/music/amusic/ui/components/AudioPipelineDialog.kt >> $OUT
sec "SettingsSheet 1570-1590"
sed -n '1570,1590p' app/src/main/java/com/music/amusic/ui/screens/SettingsSheet.kt >> $OUT
sec "DownloadService 203-212, 240-248"
sed -n '203,212p;240,248p' app/src/main/java/com/music/amusic/download/DownloadService.kt >> $OUT
sec "SourceKind 68-76, 90-96, 118-124"
sed -n '68,76p;90,96p;118,124p' app/src/main/java/com/music/amusic/data/sources/SourceKind.kt >> $OUT
sec "more multi-word literals in UI kotlin"
grep -rIn --include=*.kt -E '"[A-Z][a-z]+ [a-z]+[^"]*"' sharedUi/src/jvmSharedMain sharedUi/src/androidMain app/src/main/java/com/music/amusic/ui app/src/main/java/com/music/amusic/MainActivity.kt | grep -v -E 'error\(|Log\.|throw |require|check\(|@Deprecated|^[^:]*:[0-9]+: *(//|\*|/\*)|TrackLog|stringResource|const val|\.log|println|Exception|contains\(|startsWith' | cut -c1-200 | head -120 >> $OUT
