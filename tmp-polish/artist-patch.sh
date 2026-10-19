#!/bin/bash
set -euo pipefail
O=tmp-polish/out-artist.txt
: > "$O"
python3 - <<'PY' >> "$O" 2>&1
from pathlib import Path
changes={
'app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt': [
('''     * Home, Explore and Library only: how far''',
'''     * Home, Explore, Library and the public artist page only: how far'''),
],
'app/src/main/java/com/music/amusic/MainActivity.kt': [
('''                    }.collect { size -> if (size != null) photoHeadSize.floatValue = size.toFloat() }
                }

                FrostedTopBar(
''',
'''                    }.collect { size -> if (size != null) photoHeadSize.floatValue = size.toFloat() }
                }

                // Public artist page: the share pill rides up with the list like
                // the large heading and stays still while the list is pulled down.
                // The back button is not part of the pill and stays fixed.
                val artistShareList = if (
                    detail != null && !isLocalDetail && detail.type == BrowseType.ARTIST &&
                    detailActiveShelf == null && detail.browseId.startsWith("UC")
                ) artistListState else null
                val artistHeadSize = remember(artistShareList) { androidx.compose.runtime.mutableFloatStateOf(0f) }
                LaunchedEffect(artistShareList) {
                    val list = artistShareList ?: return@LaunchedEffect
                    androidx.compose.runtime.snapshotFlow {
                        list.layoutInfo.visibleItemsInfo.firstOrNull { it.index == 0 }?.size
                    }.collect { size -> if (size != null) artistHeadSize.floatValue = size.toFloat() }
                }

                FrostedTopBar(
'''),
('''                            else -> Float.MAX_VALUE
                        }
                    }) else null,
                    onBack = when {''',
'''                            else -> Float.MAX_VALUE
                        }
                    }) else if (artistShareList != null) ({
                        when (artistShareList.firstVisibleItemIndex) {
                            0 -> artistShareList.firstVisibleItemScrollOffset.toFloat()
                            1 -> artistHeadSize.floatValue + artistShareList.firstVisibleItemScrollOffset
                            else -> Float.MAX_VALUE
                        }
                    }) else null,
                    onBack = when {'''),
('''                                TopBarAccountButton(
                                account = account,''',
'''                                // The public artist page's pill carries only share; the
                                // photo is simply not drawn there (Settings > Conta and the
                                // other pages still reach the account).
                                if (!artistShareAction) TopBarAccountButton(
                                account = account,'''),
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
git commit -m 'Artista publico: sem foto de perfil na pilula e compartilhar rola com a lista [skip ci]' >> "$O" 2>&1
git push origin HEAD:polish-refresh-transitions >> "$O" 2>&1
