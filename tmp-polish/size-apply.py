from pathlib import Path

BAR = Path('app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt')
MAIN = Path('app/src/main/java/com/music/amusic/MainActivity.kt')

def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one exact anchor, got {count}')
    return text.replace(old, new, 1)

bar = BAR.read_text()
bar = once(bar,
    'import androidx.compose.animation.core.animateFloatAsState\n',
    'import androidx.compose.animation.core.animateFloatAsState\nimport androidx.compose.animation.core.animateDpAsState\n', 'size animation import')
bar = once(bar,
    '    onSwipeProfile: ((forward: Boolean) -> Boolean)? = null,\n    modifier: Modifier = Modifier,\n',
    '    onSwipeProfile: ((forward: Boolean) -> Boolean)? = null,\n    avatarSize: Dp = AVATAR_SIZE,\n    modifier: Modifier = Modifier,\n', 'account size parameter')
bar = once(bar,
    '    val translation = remember { Animatable(0f) }\n    val scope = rememberCoroutineScope()\n',
    '''    val translation = remember { Animatable(0f) }
    val scope = rememberCoroutineScope()
    // The pill retains its original 28dp avatar and thumbnail edge.
    val displayedAvatarSize by animateDpAsState(
        targetValue = avatarSize,
        animationSpec = tween(160),
        label = "topBarAccountPhotoSize",
    )
    val enlarged = avatarSize > AVATAR_SIZE
    val avatarShadow = if (enlarged) Modifier.shadow(2.dp, CircleShape) else Modifier
    val avatarRing = if (enlarged) {
        Modifier.border(1.dp, Color.White.copy(alpha = 0.6f), CircleShape)
    } else {
        Modifier.thumbnailBorder(CircleShape)
    }
''', 'account avatar frame')
bar = once(bar,
    '''                    .size(AVATAR_SIZE)
                    .clip(CircleShape)
                    .thumbnailBorder(CircleShape),''',
    '''                    .size(displayedAvatarSize)
                    .then(avatarShadow)
                    .clip(CircleShape)
                    .then(avatarRing),''', 'portrait')
bar = once(bar,
    '''                    .size(AVATAR_SIZE)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.surfaceVariant)
                    .thumbnailBorder(CircleShape),''',
    '''                    .size(displayedAvatarSize)
                    .then(avatarShadow)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.surfaceVariant)
                    .then(avatarRing),''', 'signed-out portrait')

main = MAIN.read_text()
if 'import androidx.lifecycle.compose.collectAsStateWithLifecycle' not in main:
    main = once(main, 'package com.music.amusic\n',
        'package com.music.amusic\n\nimport androidx.lifecycle.compose.collectAsStateWithLifecycle\n', 'lifecycle import')
main = once(main, '''                            if (!isReleaseDetail) TopBarAccountButton(
                                account = account,
''', '''                            if (!isReleaseDetail) {
                                // A larger portrait belongs only to a single circular action;
                                // Library history, sort, sharing, update and download pills
                                // keep the original 28dp portrait and thumbnail border.
                                val downloadState by DownloadSession.state.collectAsStateWithLifecycle()
                                val updateAction = !showSettings && !showAccountScrobbling &&
                                    !showSources && !showListenTogether && !showWearOs && !showEqualizer &&
                                    detail == null && selectedTab == TAB_HOME && updateNotice != null
                                val historyAction = !showSettings && !showAccountScrobbling &&
                                    !showHistory && !showReplay && !showDiscord && libraryShowAll == null &&
                                    detail == null && selectedTab == TAB_LIBRARY
                                val librarySortAction = !showSettings && !showAccountScrobbling &&
                                    libraryShowAll != null && detail == null
                                val detailSortAction = !showSettings && !showAccountScrobbling &&
                                    isLocalDetail && detail != null
                                val artistShareAction = detail != null && !isLocalDetail &&
                                    detail.type == BrowseType.ARTIST && detailActiveShelf == null &&
                                    detail.browseId.startsWith("UC")
                                val standalonePhoto = !showListenTogether && !updateAction &&
                                    !historyAction && !librarySortAction && !detailSortAction &&
                                    !artistShareAction && !downloadState.visible
                                TopBarAccountButton(
                                account = account,
                                avatarSize = if (standalonePhoto) 44.dp else 28.dp,
''', 'profile call and adjacent actions')
main = once(main, '''                                onSwipeProfile = { forward -> viewModel.stepProfile(forward) },
                            )
''', '''                                onSwipeProfile = { forward -> viewModel.stepProfile(forward) },
                                )
                            }
''', 'profile call ending')
BAR.write_text(bar)
MAIN.write_text(main)
