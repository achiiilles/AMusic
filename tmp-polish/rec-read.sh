#!/bin/bash
set -uo pipefail
O=tmp-polish/out-rec.txt
: > $O
python3 - <<'PY' >> $O 2>&1
from pathlib import Path
import re
sp=Path('sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/SearchScreen.kt')
s=sp.read_text()
a1='entity.subtitle.ifBlank { entity.entityType.name.lowercase(Locale.ROOT).replaceFirstChar { it.uppercase(Locale.ROOT) } }'
a2='item.subtitle.ifBlank { item.type.name.lowercase(Locale.ROOT).replaceFirstChar { it.uppercase(Locale.ROOT) } }'
print('a1', s.count(a1), 'a2', s.count(a2))
s=s.replace(a1,'entity.subtitle.ifBlank { entityTypeLabel(entity.entityType.name) }')
s=s.replace(a2,'item.subtitle.ifBlank { entityTypeLabel(item.type.name) }')
if 'fun entityTypeLabel' not in s:
    s=s.rstrip('\n')+'''

/** The type name shown under a result that has no subtitle of its own, in the app's language. */
@Composable
private fun entityTypeLabel(name: String): String = when (name.uppercase(Locale.ROOT)) {
    "ARTIST" -> stringResource(Res.string.search_type_artist)
    "ALBUM" -> stringResource(Res.string.search_type_album)
    "PLAYLIST" -> stringResource(Res.string.search_type_playlist)
    "TRACK", "SONG" -> stringResource(Res.string.search_type_song)
    "VIDEO" -> stringResource(Res.string.search_type_video)
    "PODCAST" -> stringResource(Res.string.search_type_podcast)
    "EPISODE" -> stringResource(Res.string.search_type_episode)
    else -> name.lowercase(Locale.ROOT).replaceFirstChar { it.uppercase(Locale.ROOT) }
}
'''
sp.write_text(s)
def add(path, vals):
    p=Path(path); t=p.read_text()
    for k,v in vals.items():
        if re.search(r'<string name="'+k+r'"', t):
            print('EXISTS',path,k); continue
        t=t.replace('</resources>','    <string name="%s">%s</string>\n</resources>' % (k,v))
    p.write_text(t)
base='sharedUi/src/commonMain/composeResources/'
add(base+'values/strings.xml',{'search_type_artist':'Artist','search_type_album':'Album','search_type_playlist':'Playlist','search_type_song':'Song','search_type_video':'Video','search_type_podcast':'Podcast','search_type_episode':'Episode'})
add(base+'values-pt/strings.xml',{'search_type_artist':'Artista','search_type_album':'Álbum','search_type_playlist':'Playlist','search_type_song':'Música','search_type_video':'Vídeo','search_type_podcast':'Podcast','search_type_episode':'Episódio'})
print('done')
PY
git config user.name 'AMusic translations'
git config user.email 'translations@users.noreply.github.com'
git add sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/SearchScreen.kt sharedUi/src/commonMain/composeResources/values/strings.xml sharedUi/src/commonMain/composeResources/values-pt/strings.xml
git commit -m 'Traduzir tipos exibidos nas linhas de busca sem subtitulo [skip ci]' >> $O 2>&1 || true
git push origin HEAD:polish-refresh-transitions >> $O 2>&1 || true
