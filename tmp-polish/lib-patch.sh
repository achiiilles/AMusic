#!/bin/bash
set -euo pipefail
O=tmp-polish/out-lib.txt
: > "$O"
python3 - <<'PY' >> "$O" 2>&1
from pathlib import Path
changes={
'app/src/main/java/com/music/amusic/MainActivity.kt': [
('''                // Home and Explore: the lone profile photo scrolls with the list
                // like the large heading, and stays still while the list is pulled
                // down. Every other page keeps its actions fixed.''',
'''                // Home, Explore and Library: the profile photo (on Library the
                // whole history and photo pill) scrolls with the list like the
                // large heading, and stays still while the list is pulled down.
                // Every other page keeps its actions fixed.'''),
('''val photoRidesWithList = (selectedTab == TAB_HOME || selectedTab == TAB_EXPLORE) &&''',
'''val photoRidesWithList = (selectedTab == TAB_HOME || selectedTab == TAB_EXPLORE || selectedTab == TAB_LIBRARY) &&'''),
('''val photoList = if (selectedTab == TAB_EXPLORE) exploreListState else homeListState''',
'''val photoList = when (selectedTab) {
                    TAB_EXPLORE -> exploreListState
                    TAB_LIBRARY -> libraryListState
                    else -> homeListState
                }'''),
],
'app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt': [
('''     * Home and Explore only: how far''','''     * Home, Explore and Library only: how far'''),
],
}
edited={}
for name,pl in changes.items():
    text=Path(name).read_text()
    for before,after in pl:
        n=text.count(before)
        if n!=1: raise ValueError(f'{name}: {n} ocorrencias')
        text=text.replace(before,after)
        print(name,'ok')
    edited[name]=text
for name,text in edited.items(): Path(name).write_text(text)
PY
git config user.name 'AMusic polish'
git config user.email 'polish@users.noreply.github.com'
git add app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt app/src/main/java/com/music/amusic/MainActivity.kt
git commit -m 'Biblioteca: pílula de histórico e foto rola com a lista e fica parada ao puxar [skip ci]' >> "$O" 2>&1
git push origin HEAD:polish-refresh-transitions >> "$O" 2>&1
