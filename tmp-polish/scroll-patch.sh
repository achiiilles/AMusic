#!/bin/bash
set -euo pipefail
O=tmp-polish/out-scroll.txt
: > "$O"
python3 - <<'PY' >> "$O" 2>&1
from pathlib import Path
changes={
'app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt': [
('''    pullFraction: () -> Float = { 0f },
    /**
     * A page control filling''',
'''    pullFraction: () -> Float = { 0f },
    /**
     * Home and Explore only: how far the page's list has scrolled, in pixels.
     * The action group then rides up with the content and leaves through the
     * top edge, as the large heading does. It stays put while the list is
     * pulled down, since only a positive scroll moves it. Null on every other
     * page, where the actions stay fixed.
     */
    actionsScrollPx: (() -> Float)? = null,
    /**
     * A page control filling'''),
('''                modifier = Modifier
                    .align(Alignment.CenterEnd)
                    .then(if (accessory != null)''',
'''                modifier = Modifier
                    .align(Alignment.CenterEnd)
                    .then(
                        if (actionsScrollPx != null) {
                            Modifier.graphicsLayer {
                                translationY = -actionsScrollPx().coerceIn(0f, actionsTravelPx)
                            }
                        } else Modifier,
                    )
                    .then(if (accessory != null)'''),
('''    val reduceDynamicBlur by AppSettings.reduceDynamicBlur.collectAsStateWithLifecycle()
    val useFloatingChrome = artworkPageChrome ||''',
'''    val reduceDynamicBlur by AppSettings.reduceDynamicBlur.collectAsStateWithLifecycle()
    // Far enough to carry the action group (and its shadow) past the top edge.
    val actionsTravelPx = with(androidx.compose.ui.platform.LocalDensity.current) {
        androidx.compose.foundation.layout.WindowInsets.statusBars.getTop(this) +
            (TopBarContentHeight + 8.dp).toPx()
    }
    val useFloatingChrome = artworkPageChrome ||'''),
],
'app/src/main/java/com/music/amusic/MainActivity.kt': [
('''                FrostedTopBar(
                    title = when {
                        showSpotify && detail == null''',
'''                // Home and Explore: the lone profile photo scrolls with the list
                // like the large heading, and stays still while the list is pulled
                // down. Every other page keeps its actions fixed.
                val topBarDownloadState by DownloadSession.state.collectAsStateWithLifecycle()
                val photoRidesWithList = (selectedTab == TAB_HOME || selectedTab == TAB_EXPLORE) &&
                    detail == null && selectedMoodGenre == null && libraryShowAll == null &&
                    !showSettings && !showAccountScrobbling && !showSources && !showListenTogether &&
                    !showWearOs && !showEqualizer && !showHistory && !showReplay && !showDiscord &&
                    !showSpotify && !topBarDownloadState.visible &&
                    !(selectedTab == TAB_HOME && updateNotice != null)
                val photoList = if (selectedTab == TAB_EXPLORE) exploreListState else homeListState
                val photoHeadSize = remember(photoList) { androidx.compose.runtime.mutableFloatStateOf(0f) }
                LaunchedEffect(photoList) {
                    androidx.compose.runtime.snapshotFlow {
                        photoList.layoutInfo.visibleItemsInfo.firstOrNull { it.index == 0 }?.size
                    }.collect { size -> if (size != null) photoHeadSize.floatValue = size.toFloat() }
                }

                FrostedTopBar(
                    title = when {
                        showSpotify && detail == null'''),
('''                    pullFraction = { currentPull?.distanceFraction ?: 0f },
                    onBack = when {''',
'''                    pullFraction = { currentPull?.distanceFraction ?: 0f },
                    actionsScrollPx = if (photoRidesWithList) ({
                        when (photoList.firstVisibleItemIndex) {
                            0 -> photoList.firstVisibleItemScrollOffset.toFloat()
                            1 -> photoHeadSize.floatValue + photoList.firstVisibleItemScrollOffset
                            else -> Float.MAX_VALUE
                        }
                    }) else null,
                    onBack = when {'''),
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
git commit -m 'Início e Explorar: foto de perfil rola com a lista e fica parada ao puxar [skip ci]' >> "$O" 2>&1
git push origin HEAD:polish-refresh-transitions >> "$O" 2>&1
