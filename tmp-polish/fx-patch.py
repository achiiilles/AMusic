import sys

BASE = "app/src/main/java/com/music/amusic/"
SB = "sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/"


def edit(path, fn):
    with open(path, encoding="utf-8") as f:
        t = f.read()
    n = fn(t)
    if n == t:
        print("NO CHANGE", path)
        sys.exit(1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(n)
    print("ok", path)


def rep(t, old, new, label):
    c = t.count(old)
    if c != 1:
        print("FAIL", label, c)
        sys.exit(1)
    return t.replace(old, new)


def add_imports(t, imports, label):
    first = "import androidx.compose.foundation"
    i = t.find("\n" + first)
    if i < 0:
        print("FAIL imports", label)
        sys.exit(1)
    add = "".join("\nimport " + x for x in imports if ("import " + x + "\n") not in t)
    return t[: i] + add + t[i:]


def detail(t):
    t = add_imports(t, ["androidx.compose.animation.Crossfade"], "detail")
    t = rep(
        t,
        "                    ) { position, entry ->\n                        songRow(position, entry)\n                    }\n",
        "                    ) { position, entry ->\n"
        "                        Column(\n"
        "                            Modifier.fillMaxWidth().animateItem(\n"
        "                                fadeInSpec = tween(200),\n"
        "                                placementSpec = tween(200),\n"
        "                                fadeOutSpec = tween(200),\n"
        "                            ),\n"
        "                        ) {\n"
        "                            songRow(position, entry)\n"
        "                        }\n"
        "                    }\n",
        "songRow",
    )
    old_search = (
        "                item(key = \"search\") {\n"
        "                    DetailSearchField(\n"
        "                        query = query,\n"
        "                        onQueryChange = { query = it },\n"
        "                        onClose = closeSearch,\n"
        "                        autoFocus = focusSearch,\n"
        "                        onFocused = { focusSearch = false },\n"
        "                        palette = palette,\n"
        "                        type = page.type,\n"
        "                    )\n"
        "                }\n"
    )
    new_search = (
        "                item(key = \"search\") {\n"
        "                    Box(\n"
        "                        Modifier.animateItem(\n"
        "                            fadeInSpec = tween(180),\n"
        "                            placementSpec = null,\n"
        "                            fadeOutSpec = tween(180),\n"
        "                        ),\n"
        "                    ) {\n"
        "                        DetailSearchField(\n"
        "                            query = query,\n"
        "                            onQueryChange = { query = it },\n"
        "                            onClose = closeSearch,\n"
        "                            autoFocus = focusSearch,\n"
        "                            onFocused = { focusSearch = false },\n"
        "                            palette = palette,\n"
        "                            type = page.type,\n"
        "                        )\n"
        "                    }\n"
        "                }\n"
    )
    t = rep(t, old_search, new_search, "search")
    t = rep(
        t,
        "                .animateContentSize()\n                .padding(horizontal = horizontalPadding)",
        "                .animateContentSize(animationSpec = tween(durationMillis = 250, easing = FastOutSlowInEasing))\n                .padding(horizontal = horizontalPadding)",
        "bio",
    )
    old_label = (
        "            Text(\n"
        "                text = showAllText ?: stringResource(R.string.show_all),\n"
        "                style = MaterialTheme.typography.titleSmall,\n"
        "                color = palette.accent,\n"
        "                modifier = Modifier\n"
        "                    .clickable(onClick = onShowAll)\n"
        "                    .padding(start = 12.dp, top = 4.dp, bottom = 4.dp),\n"
        "            )\n"
    )
    new_label = (
        "            Crossfade(\n"
        "                targetState = showAllText ?: stringResource(R.string.show_all),\n"
        "                modifier = Modifier\n"
        "                    .clickable(onClick = onShowAll)\n"
        "                    .padding(start = 12.dp, top = 4.dp, bottom = 4.dp),\n"
        "                animationSpec = tween(durationMillis = 180),\n"
        "                label = \"showAllLabel\",\n"
        "            ) { shownLabel ->\n"
        "                Text(\n"
        "                    text = shownLabel,\n"
        "                    style = MaterialTheme.typography.titleSmall,\n"
        "                    color = palette.accent,\n"
        "                )\n"
        "            }\n"
    )
    t = rep(t, old_label, new_label, "showall")
    return t


def sheet(t):
    t = rep(t, "    enabled: Boolean = true,\n    onClick: () -> Unit,\n) {\n    val menu = LocalActionRowStyle.current == ActionRowStyle.Menu",
            "    enabled: Boolean = true,\n    animateLabel: Boolean = false,\n    onClick: () -> Unit,\n) {\n    val menu = LocalActionRowStyle.current == ActionRowStyle.Menu", "sig")
    old = (
        "        Text(\n"
        "            text = label,\n"
        "            style = MaterialTheme.typography.bodyLarge,\n"
        "            color = foreground.copy(alpha = alpha),\n"
        "            maxLines = if (menu) 2 else Int.MAX_VALUE,\n"
        "            overflow = TextOverflow.Ellipsis,\n"
        "            modifier = Modifier.weight(1f),\n"
        "        )\n"
    )
    new = (
        "        if (animateLabel) {\n"
        "            Box(Modifier.weight(1f)) {\n"
        "                Crossfade(targetState = label, animationSpec = tween(durationMillis = 200), label = \"actionLabel\") { shown ->\n"
        "                    Text(\n"
        "                        text = shown,\n"
        "                        style = MaterialTheme.typography.bodyLarge,\n"
        "                        color = foreground.copy(alpha = alpha),\n"
        "                        maxLines = if (menu) 2 else Int.MAX_VALUE,\n"
        "                        overflow = TextOverflow.Ellipsis,\n"
        "                        modifier = Modifier.fillMaxWidth(),\n"
        "                    )\n"
        "                }\n"
        "            }\n"
        "        } else {\n"
        "            Text(\n"
        "                text = label,\n"
        "                style = MaterialTheme.typography.bodyLarge,\n"
        "                color = foreground.copy(alpha = alpha),\n"
        "                maxLines = if (menu) 2 else Int.MAX_VALUE,\n"
        "                overflow = TextOverflow.Ellipsis,\n"
        "                modifier = Modifier.weight(1f),\n"
        "            )\n"
        "        }\n"
    )
    t = rep(t, old, new, "label")
    t = rep(t, "                tint = if (liked) palette.accent else null,\n                accent = palette.accent,\n                onClick = onToggleLike,",
            "                tint = if (liked) palette.accent else null,\n                accent = palette.accent,\n                animateLabel = true,\n                onClick = onToggleLike,", "like")
    t = rep(t, "                tint = if (disliked) palette.accent else null,\n                accent = palette.accent,\n                onClick = onToggleDislike,",
            "                tint = if (disliked) palette.accent else null,\n                accent = palette.accent,\n                animateLabel = true,\n                onClick = onToggleDislike,", "dislike")
    t = rep(t, "                        if (inLibrary) R.string.remove_from_library else R.string.add_to_library,\n                    ),\n                    accent = palette.accent,\n                    onClick = it,",
            "                        if (inLibrary) R.string.remove_from_library else R.string.add_to_library,\n                    ),\n                    accent = palette.accent,\n                    animateLabel = true,\n                    onClick = it,", "lib")
    t = add_imports(t, ["androidx.compose.foundation.layout.Box", "androidx.compose.foundation.layout.fillMaxWidth"], "sheet")
    return t


def home(t):
    t = add_imports(t, [
        "androidx.compose.animation.AnimatedContent",
        "androidx.compose.animation.Crossfade",
        "androidx.compose.animation.SizeTransform",
        "androidx.compose.animation.core.tween",
        "androidx.compose.animation.fadeIn",
        "androidx.compose.animation.fadeOut",
        "androidx.compose.animation.togetherWith",
    ], "home")
    start_marker = "        if (viewType == LibraryViewType.LIST) {\n            BoxWithConstraints {\n                val columnWidth"
    end_marker = "\n    }\n}\n\n@Composable\nprivate fun RecentSectionHeader"
    s = t.find(start_marker)
    if s < 0 or t.count(start_marker) != 1:
        print("FAIL home start")
        sys.exit(1)
    e = t.find(end_marker, s)
    if e < 0:
        print("FAIL home end")
        sys.exit(1)
    block = t[s:e].replace("viewType == LibraryViewType.LIST", "shownViewType == LibraryViewType.LIST", 1)
    block = "\n".join(("    " + l if l.strip() else l) for l in block.split("\n"))
    head = (
        "        AnimatedContent(\n"
        "            targetState = viewType,\n"
        "            transitionSpec = {\n"
        "                (fadeIn(tween(200)) togetherWith fadeOut(tween(150)))\n"
        "                    .using(SizeTransform(clip = false) { _, _ -> tween(220) })\n"
        "            },\n"
        "            label = \"recentViewType\",\n"
        "        ) { shownViewType ->\n"
    )
    t = t[:s] + head + block + "\n        }" + t[e:]
    old_icon_start = "            Icon(\n                imageVector = if (viewType == LibraryViewType.LIST) {\n                    AMusicIcons.GridView"
    i = t.find(old_icon_start)
    if i < 0 or t.count(old_icon_start) != 1:
        print("FAIL home icon")
        sys.exit(1)
    j = t.find("                modifier = Modifier.size(19.dp),\n            )\n", i)
    if j < 0:
        print("FAIL home icon end")
        sys.exit(1)
    j_end = j + len("                modifier = Modifier.size(19.dp),\n            )\n")
    icon = t[i:j_end]
    icon = icon.replace("viewType == LibraryViewType.LIST", "shownType == LibraryViewType.LIST")
    icon = "\n".join(("    " + l if l.strip() else l) for l in icon.split("\n"))
    new_icon = (
        "            Crossfade(targetState = viewType, animationSpec = tween(180), label = \"recentViewIcon\") { shownType ->\n"
        + icon.rstrip(" ") + "            }\n"
    )
    t = t[:i] + new_icon + t[j_end:]
    return t


def mini(t):
    t = add_imports(t, ["androidx.compose.animation.Crossfade", "androidx.compose.animation.core.tween"], "mini")
    old = (
        "            Column(Modifier.weight(1f)) {\n"
        "                ExplicitSongTitle(\n"
        "                    song = song,\n"
        "                    style = MaterialTheme.typography.titleMedium,\n"
        "                    color = MaterialTheme.colorScheme.onBackground,\n"
        "                )\n"
        "                Text(\n"
        "                    text = song.artist,\n"
        "                    style = MaterialTheme.typography.bodyMedium,\n"
        "                    color = MaterialTheme.colorScheme.onSurfaceVariant,\n"
        "                    maxLines = 1,\n"
        "                    overflow = TextOverflow.Ellipsis,\n"
        "                )\n"
        "            }\n"
    )
    new = (
        "            Crossfade(\n"
        "                targetState = song.title to song.artist,\n"
        "                modifier = Modifier.weight(1f),\n"
        "                animationSpec = tween(durationMillis = 200),\n"
        "                label = \"miniPlayerText\",\n"
        "            ) { (shownTitle, shownArtist) ->\n"
        "                Column(Modifier.fillMaxWidth()) {\n"
        "                    ExplicitSongTitle(\n"
        "                        song = song.copy(title = shownTitle, artist = shownArtist),\n"
        "                        style = MaterialTheme.typography.titleMedium,\n"
        "                        color = MaterialTheme.colorScheme.onBackground,\n"
        "                    )\n"
        "                    Text(\n"
        "                        text = shownArtist,\n"
        "                        style = MaterialTheme.typography.bodyMedium,\n"
        "                        color = MaterialTheme.colorScheme.onSurfaceVariant,\n"
        "                        maxLines = 1,\n"
        "                        overflow = TextOverflow.Ellipsis,\n"
        "                    )\n"
        "                }\n"
        "            }\n"
    )
    t = rep(t, old, new, "minitext")
    old = (
        "                    Icon(\n"
        "                        imageVector = if (isPlaying) Icons.Rounded.Pause else Icons.Rounded.PlayArrow,\n"
        "                        contentDescription = stringResource(if (isPlaying) R.string.pause else R.string.play),\n"
        "                        tint = MaterialTheme.colorScheme.onBackground,\n"
        "                        modifier = Modifier.size(GLYPH_SIZE),\n"
        "                    )\n"
    )
    new = (
        "                    Crossfade(targetState = isPlaying, animationSpec = tween(durationMillis = 150), label = \"miniPlayerPlayPause\") { playing ->\n"
        "                        Icon(\n"
        "                            imageVector = if (playing) Icons.Rounded.Pause else Icons.Rounded.PlayArrow,\n"
        "                            contentDescription = stringResource(if (playing) R.string.pause else R.string.play),\n"
        "                            tint = MaterialTheme.colorScheme.onBackground,\n"
        "                            modifier = Modifier.size(GLYPH_SIZE),\n"
        "                        )\n"
        "                    }\n"
    )
    t = rep(t, old, new, "miniplay")
    return t


edit(BASE + "ui/screens/DetailScreen.kt", detail)
edit(BASE + "ui/components/SongActionsSheet.kt", sheet)
edit(SB + "screens/HomeScreen.kt", home)
edit(BASE + "ui/components/MiniPlayer.kt", mini)
