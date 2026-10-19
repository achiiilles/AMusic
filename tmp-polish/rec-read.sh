#!/bin/bash
set -euo pipefail
O=tmp-polish/out-rec.txt
: > "$O"
python3 - <<'PY' >> "$O" 2>&1
from pathlib import Path
changes={
'app/src/main/java/com/music/amusic/ui/components/AudioPipelineDialog.kt': [('${DsdFormat.tapsFor(dsdRateHz)} taps"','${DsdFormat.tapsFor(dsdRateHz)} coeficientes"')],
'app/src/main/java/com/music/amusic/download/DownloadService.kt': [('"Downloads",','"Transferências",')],
'app/src/main/java/com/music/amusic/data/sources/SourceKind.kt': [('"Lossless"','"Sem perdas"'),('"Plugins"','"Extensões"')],
}
edited={}
for name,pairs in changes.items():
    text=Path(name).read_text()
    for before,after in pairs:
        count=text.count(before)
        if not count: raise ValueError(f'{name}: texto não encontrado: {before}')
        text=text.replace(before,after)
        print(name, before, count)
    edited[name]=text
for name,text in edited.items(): Path(name).write_text(text)
PY
git config user.name 'AMusic translations'
git config user.email 'translations@users.noreply.github.com'
git add app/src/main/java/com/music/amusic/ui/components/AudioPipelineDialog.kt app/src/main/java/com/music/amusic/download/DownloadService.kt app/src/main/java/com/music/amusic/data/sources/SourceKind.kt
git commit -m 'Traduzir rótulos residuais das fontes e do áudio [skip ci]' >> "$O" 2>&1
git push origin HEAD:polish-refresh-transitions >> "$O" 2>&1
