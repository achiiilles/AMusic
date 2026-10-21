
P_DS = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
P_CM = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components/Common.kt'

def rep(s, old, new, cnt=1):
    assert s.count(old) == cnt, (old, s.count(old))
    return s.replace(old, new)

ds = open(P_DS, encoding='utf-8').read()

ds = rep(ds, """                        text = description?.takeIf { it.isNotBlank() },
                        palette = palette,
                        horizontalPadding = if (isArtist) ARTIST_CONTENT_GUTTER else ABOUT_GUTTER,
""", """                        text = description?.takeIf { it.isNotBlank() },
                        palette = palette,
                        // A release opens straight on its description, two lines with MAIS at
                        // the end of the second; the artist page keeps its heading and Mais.
                        showTitle = isArtist,
                        inlineMore = !isArtist,
                        horizontalPadding = if (isArtist) ARTIST_CONTENT_GUTTER else ABOUT_GUTTER,
""")

ds = rep(ds, """    /** Drawn last, under the stats. */
    footer: (@Composable () -> Unit)? = null,
) {
    var expanded by remember(text) { mutableStateOf(false) }
    var clipped by remember(text) { mutableStateOf(false) }
    Column {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,""", """    /** Drawn last, under the stats. */
    footer: (@Composable () -> Unit)? = null,
    /** False on a release page, which opens straight on the description. */
    showTitle: Boolean = true,
    /** Two lines with MAIS at the end of the second; a tap opens the rest. */
    inlineMore: Boolean = false,
) {
    var expanded by remember(text) { mutableStateOf(false) }
    var clipped by remember(text) { mutableStateOf(false) }
    Column {
        if (showTitle) Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,""")

ds = rep(ds, """        if (text != null) Text(
            text = text,
            style = MaterialTheme.typography.bodyLarge,
            fontWeight = FontWeight.Medium,
            color = palette.onBackgroundVariant,
            maxLines = if (expanded) Int.MAX_VALUE else 3,""", """        if (text != null && inlineMore) {
            // Apple Music's layout: the description stops at two lines and MAIS sits at
            // the end of the second, over a short fade into the page colour. Tapping the
            // text opens the rest in place and tapping it again folds it back.
            val more = stringResource(R.string.more).uppercase()
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .animateContentSize(animationSpec = tween(durationMillis = 250, easing = FastOutSlowInEasing))
                    .padding(start = horizontalPadding, end = horizontalPadding, top = 2.dp, bottom = 8.dp)
                    .let { m -> if (clipped || expanded) m.clickable { expanded = !expanded } else m },
            ) {
                Text(
                    text = text,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium,
                    color = palette.onBackgroundVariant,
                    maxLines = if (expanded) Int.MAX_VALUE else 2,
                    overflow = TextOverflow.Clip,
                    onTextLayout = { result -> if (!expanded) clipped = result.hasVisualOverflow },
                )
                AnimatedVisibility(
                    visible = clipped && !expanded,
                    modifier = Modifier.align(Alignment.BottomEnd),
                    enter = fadeIn(animationSpec = tween(durationMillis = 180)),
                    exit = fadeOut(animationSpec = tween(durationMillis = 180)),
                ) {
                    Text(
                        text = more,
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.SemiBold,
                        color = palette.accent,
                        maxLines = 1,
                        modifier = Modifier
                            .background(
                                Brush.horizontalGradient(
                                    0f to palette.background.copy(alpha = 0f),
                                    0.35f to palette.background,
                                    1f to palette.background,
                                ),
                            )
                            .padding(start = 28.dp),
                    )
                }
            }
        }
        if (text != null && !inlineMore) Text(
            text = text,
            style = MaterialTheme.typography.bodyLarge,
            fontWeight = FontWeight.Medium,
            color = palette.onBackgroundVariant,
            maxLines = if (expanded) Int.MAX_VALUE else 3,""")

ds = rep(ds, """        if (clipped || expanded) {
            Text(
                text = stringResource(if (expanded) R.string.less else R.string.more),""", """        if (!inlineMore && (clipped || expanded)) {
            Text(
                text = stringResource(if (expanded) R.string.less else R.string.more),""")

ds = rep(ds, """                            activeTint = palette.accent,
                            searchPlayingStyle = true,
                        )
                        if (position < matches.lastIndex) {""", """                            activeTint = palette.accent,
                            searchPlayingStyle = true,
                            // Apple Music's track rows on an album or single: no running time,
                            // and the artist only when it is not the release's own credit.
                            showDuration = !numbered,
                            showArtist = !numbered ||
                                !song.artist.trim().equals(appleAlbumCredit.trim(), ignoreCase = true),
                        )
                        if (position < matches.lastIndex) {""")
open(P_DS, 'w', encoding='utf-8').write(ds)

cm = open(P_CM, encoding='utf-8').read()
cm = rep(cm, """    showSourceQuality: Boolean = false,
) {
    val haptics = rememberHaptics()""", """    showSourceQuality: Boolean = false,
    /** False drops the running time at the row's right edge. */
    showDuration: Boolean = true,
    /** False drops the artist from under the title, e.g. when it is the page's own artist. */
    showArtist: Boolean = true,
) {
    val haptics = rememberHaptics()""")
cm = rep(cm, """    showSourceQuality: Boolean = false,
) {
    val titleColor by animateColorAsState(""", """    showSourceQuality: Boolean = false,
    showDuration: Boolean = true,
    showArtist: Boolean = true,
) {
    val titleColor by animateColorAsState(""")
cm = rep(cm, """            showSourceQuality = showSourceQuality,
        )
""", """            showSourceQuality = showSourceQuality,
            showDuration = showDuration,
            showArtist = showArtist,
        )
""", 2)
cm = rep(cm, """            Spacer(Modifier.height(2.dp))
            val subtitle = listOfNotNull(
                song.artist.takeIf { it.isNotBlank() },""", """            Spacer(Modifier.height(if (showArtist) 2.dp else 0.dp))
            val subtitle = listOfNotNull(
                song.artist.takeIf { showArtist && it.isNotBlank() },""")
cm = rep(cm, """            Row(verticalAlignment = Alignment.CenterVertically) {
                if (quality != null) {
                    SourceQualityBadge(""", """            if (quality != null || subtitle.isNotEmpty()) Row(verticalAlignment = Alignment.CenterVertically) {
                if (quality != null) {
                    SourceQualityBadge(""")
cm = rep(cm, """            song.durationText?.let {""", """            song.durationText?.takeIf { showDuration }?.let {""")
open(P_CM, 'w', encoding='utf-8').write(cm)
