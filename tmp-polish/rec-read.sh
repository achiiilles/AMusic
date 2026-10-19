#!/bin/bash
O=tmp-polish/out-rec.txt
: > $O
sec() { echo "=== $1" >> $O; }
rng() { sec "$1 $2-$3"; sed -n "$2,$3p" "$1" | cut -c1-200 >> $O; }
A=app/src/main/java/com/music/amusic
rng $A/ui/replay/ReplayModel.kt 170 200
rng $A/data/stats/ListeningStats.kt 984 994
rng $A/data/stats/ListeningStats.kt 1020 1030
rng $A/ui/components/AccountChannelDialog.kt 110 128
rng $A/ui/components/AccountChannelDialog.kt 164 176
rng $A/ui/components/AccountChannelDialog.kt 230 238
rng $A/ui/screens/DiscordScreen.kt 70 100
rng $A/MainActivity.kt 5480 5490
rng $A/ui/MainViewModel.kt 2990 2998
rng $A/ui/components/AudioPipelineDialog.kt 430 440
rng $A/ui/components/AudioPipelineDialog.kt 440 520
sec "Innertube.kt"
sed -n '60,80p;805,825p' shared/src/jvmSharedMain/kotlin/com/music/amusic/data/innertube/Innertube.kt | cut -c1-200 >> $O
sec "gl/currentLanguage/currentCountry in Innertube"
grep -rnE 'currentLanguage|currentCountry|"gl"|gl\b.*=|hl\b.*=|setLanguage|language *=' shared/src/jvmSharedMain/kotlin/com/music/amusic/data/innertube/*.kt | cut -c1-200 | head -40 >> $O
sec "setLanguage callers"
grep -rnE 'Innertube\.(setLanguage|currentLanguage|language|configure|locale)|innertubeLanguage|appLanguage|AppLocale|setApplicationLocales' app/src/main shared/src/jvmSharedMain --include=*.kt | cut -c1-200 | head -30 >> $O
sec "parser TYPE_WORDS"
grep -nE 'TYPE_WORDS *=|LOCALIZED_TYPE_WORDS *=|RELEASE_WORDS *=|TALLY *=' -A6 shared/src/jvmSharedMain/kotlin/com/music/amusic/data/innertube/InnertubeParser.kt | cut -c1-220 | head -60 >> $O
sec "Artist/Album literals main"
grep -rnE '"(Artist|Album|Song|Video|Playlist|Podcast|Episode|Single|EP|Profile)"' app/src/main shared/src/jvmSharedMain shared/src/commonMain sharedUi/src --include=*.kt | cut -c1-220 | head -40 >> $O
python3 - <<'PY' >> $O
import re,os
def load(p):
    if not os.path.exists(p): return None
    s=open(p,encoding='utf8').read()
    d={}
    for m in re.finditer(r'<string name="([^"]+)"[^>]*>(.*?)</string>',s,re.S):
        d[m.group(1)]=m.group(2)
    return d
pairs=[('app/src/main/res/values/strings.xml','app/src/main/res/values-pt/strings.xml'),
       ('sharedUi/src/commonMain/composeResources/values/strings.xml','sharedUi/src/commonMain/composeResources/values-pt/strings.xml')]
for b,p in pairs:
    B=load(b);P=load(p)
    print("=== PAIR",b,p, None if B is None else len(B), None if P is None else len(P))
    if B is None or P is None: continue
    miss=[k for k in B if k not in P]
    print("--- MISSING in pt:",len(miss))
    for k in miss[:150]: print("M",k,"=",B[k][:90].replace("\n"," "))
    same=[k for k in B if k in P and P[k]==B[k] and re.search(r'[A-Za-z]{3,}',B[k])]
    print("--- SAME as en:",len(same))
    for k in same[:100]: print("S",k,"=",B[k][:90].replace("\n"," "))
PY
echo "=== list res dirs" >> $O
ls app/src/main/res | grep values >> $O
ls sharedUi/src/commonMain/composeResources 2>/dev/null >> $O
