#!/bin/bash
OUT=tmp-polish/out-rec.txt
: > $OUT
sec() { echo "=== $1" >> $OUT; }
sec "android res: keys in en missing in pt"
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
print(len(en),len(pt))
for k in en:
    if k not in pt: print(k+'|'+en[k].replace('\n','\\n')[:120])
PY
sec "string-arrays in sharedUi en and pt"
grep -n -A8 '<string-array' sharedUi/src/commonMain/composeResources/values/strings.xml | head -40 >> $OUT
grep -n -c '<string-array' sharedUi/src/commonMain/composeResources/values-pt/strings.xml >> $OUT
sec "locale hl"
grep -rIn --include=*.kt -E '"hl"|"gl"|languageCode|Locale\.' shared/src app/src/main/java | cut -c1-200 | head -25 >> $OUT
sec "HomeScreen 600-650 localizeShelfTitle rest"
sed -n '600,650p' sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt >> $OUT
sec "hardcoded literals in UI kotlin (file:line:text)"
grep -rIn --include=*.kt -E '(text|title|subtitle|label|contentDescription|placeholder|description|hint|message|summary) = "[A-Z][a-z]+' sharedUi/src/jvmSharedMain sharedUi/src/androidMain app/src/main/java | grep -v -E 'Log\.|label = "[a-z]' | cut -c1-210 | head -150 >> $OUT
sec "Text(\"literal\")"
grep -rIn --include=*.kt -E 'Text\(\s*"[A-Z][a-z]+' sharedUi/src/jvmSharedMain sharedUi/src/androidMain app/src/main/java | cut -c1-210 | head -60 >> $OUT
sec "other literals: listOf/to/when branches with capitalised words"
grep -rIn --include=*.kt -E '(->|to|=|\() *"[A-Z][a-z]+( [A-Za-z&]+)*"[,)]?$' sharedUi/src/jvmSharedMain sharedUi/src/androidMain app/src/main/java | grep -v -E 'Log\.|Exception|\.equals|http|key' | cut -c1-200 | head -120 >> $OUT
