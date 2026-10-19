#!/bin/bash
set -uo pipefail
O=tmp-polish/out-rec.txt
: > $O
python3 - <<'PY'
from pathlib import Path
import re
p=Path('app/src/main/java/com/music/amusic/ui/components/AccountChannelDialog.kt')
s=p.read_text()
old=s
s,n1=re.subn(r'"Couldn\'t list this account\'s channels\. You can still pick "\s*\+\s*"one in YouTube Music itself\."', '"N\u00e3o foi poss\u00edvel listar os canais desta conta. Voc\u00ea ainda pode escolher " +\n                    "um no pr\u00f3prio YouTube Music."', s)
s,n2=re.subn(r'"Your library, likes and history come from the channel "\s*\+\s*"you pick here\."', '"Sua biblioteca, curtidas e hist\u00f3rico v\u00eam do canal " +\n                    "escolhido aqui."', s)
s,n3=re.subn(r'\$subtitle \u00b7 default', '$subtitle \u00b7 padr\u00e3o', s)
print('channel dialog',n1,n2,n3)
if s!=old: p.write_text(s)
PY
git config user.name 'AMusic translations'
git config user.email 'translations@users.noreply.github.com'
git add app/src/main/java/com/music/amusic/ui/components/AccountChannelDialog.kt
git commit -m 'Traduzir frases restantes do dialogo de canais [skip ci]' || true
git push origin HEAD:polish-refresh-transitions || true
EX='/(desktop|tv|wear)[A-Za-z]*/|/build/|/test/'
sec() { echo "=== $1" >> $O; }
sec 'artist album literals'
grep -rnE --include=*.kt '"(Artist|Album|Song|Songs|Video|Videos|Playlist|Podcast|Episode|Single|EP|Profile|Artists|Albums)"' app/src sharedUi/src shared/src 2>/dev/null | grep -vE "$EX" | cut -c1-220 | head -60 >> $O
sec 'text literals english screens'
grep -rnE --include=*.kt '(text|label|title|subtitle|placeholder|contentDescription|description) = "[A-Z][a-z]+[^"]*"' app/src/main sharedUi/src 2>/dev/null | grep -vE "$EX" | cut -c1-200 | head -120 >> $O
sec 'Text( literals'
grep -rnE --include=*.kt 'Text\("[A-Z][a-z]+[^"]*"' app/src/main sharedUi/src 2>/dev/null | grep -vE "$EX" | cut -c1-200 | head -60 >> $O
