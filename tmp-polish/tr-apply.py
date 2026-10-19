import re, sys, io

SCREEN = "sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/SearchScreen.kt"
RES = "sharedUi/src/commonMain/composeResources"
EN = RES + "/values/strings.xml"
PT = RES + "/values-pt/strings.xml"
OUT = "tmp-polish/out-tr.txt"
log = []

def say(m):
    log.append(m)
    print(m)

def rd(p):
    with io.open(p, encoding="utf-8", newline="") as f:
        return f.read()

def wr(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)

KEYS = [
    ("search_filter_all", "All", "Todos"),
    ("search_filter_songs", "Songs", "Músicas"),
    ("search_filter_videos", "Videos", "Vídeos"),
    ("search_filter_albums", "Albums", "Álbuns"),
    ("search_filter_artists", "Artists", "Artistas"),
    ("search_filter_playlists", "Playlists", "Playlists"),
    ("search_top_result", "Top result", "Resultado principal"),
    ("search_section_songs", "Songs", "Músicas"),
    ("search_section_artists", "Artists", "Artistas"),
    ("search_section_albums", "Albums", "Álbuns"),
    ("search_section_playlists", "Playlists", "Playlists"),
    ("search_section_more", "More", "Mais"),
]

def add_strings(path, idx):
    s = rd(path)
    if "</resources>" not in s:
        raise SystemExit("no </resources> in " + path)
    nl = "\r\n" if "\r\n" in s else "\n"
    lines = []
    for k in KEYS:
        if 'name="%s"' % k[0] in s:
            raise SystemExit("key already exists: " + k[0] + " in " + path)
        lines.append('    <string name="%s">%s</string>' % (k[0], k[idx]))
    block = nl.join(lines) + nl
    i = s.rindex("</resources>")
    s = s[:i] + block + s[i:]
    wr(path, s)
    say("strings added to " + path)

def sub1(pattern, repl, s, label, flags=0):
    new, n = re.subn(pattern, repl, s, flags=flags)
    if n != 1:
        raise SystemExit("patch '%s' matched %d times (expected 1)" % (label, n))
    say("patched: " + label)
    return new

try:
    s = rd(SCREEN)
    if "search_top_result" in s:
        raise SystemExit("already patched")
    # imports
    s = sub1(r"(import androidx\.compose\.animation\.AnimatedVisibility\r?\n)",
             r"\1import androidx.compose.animation.animateColorAsState\nimport androidx.compose.animation.core.tween\n", s, "imports")
    # top result label
    s = sub1(r'text = "Top result",', 'text = stringResource(Res.string.search_top_result),', s, "top result label")
    # section title
    s = sub1(r'(item\(key = "search-section:\$title"\) \{\s*Text\(\s*text = )title,',
             r'\1searchSectionTitle(title),', s, "section title")
    # chip label
    s = sub1(r'text = entry\.label,', 'text = entry.localizedLabel(),', s, "chip label")
    # chip colors: animate with a short fade
    s = sub1(r'val selected = entry == filter\r?\n',
             'val selected = entry == filter\n'
             '            val pillColor = animateColorAsState(\n'
             '                targetValue = if (selected) MaterialTheme.colorScheme.onBackground\n'
             '                else MaterialTheme.colorScheme.surfaceVariant,\n'
             '                animationSpec = tween(durationMillis = 160),\n'
             '                label = "searchFilterPill",\n'
             '            ).value\n'
             '            val pillTextColor = animateColorAsState(\n'
             '                targetValue = if (selected) MaterialTheme.colorScheme.background\n'
             '                else MaterialTheme.colorScheme.onBackground,\n'
             '                animationSpec = tween(durationMillis = 160),\n'
             '                label = "searchFilterPillText",\n'
             '            ).value\n', s, "pill color vals")
    s = sub1(r'\.background\(\s*if \(selected\) MaterialTheme\.colorScheme\.onBackground\s*else MaterialTheme\.colorScheme\.surfaceVariant,\s*\)',
             '.background(pillColor)', s, "pill background")
    s = sub1(r'color = if \(selected\) MaterialTheme\.colorScheme\.background\s*else MaterialTheme\.colorScheme\.onBackground,',
             'color = pillTextColor,', s, "pill text color")
    # helpers at end
    if not s.endswith("\n"):
        s += "\n"
    s += '''
/** The pill's label in the app's language; [SearchFilter.label] stays the English fallback. */
@Composable
private fun SearchFilter.localizedLabel(): String = when (this) {
    SearchFilter.ALL -> stringResource(Res.string.search_filter_all)
    SearchFilter.SONGS -> stringResource(Res.string.search_filter_songs)
    SearchFilter.VIDEOS -> stringResource(Res.string.search_filter_videos)
    SearchFilter.ALBUMS -> stringResource(Res.string.search_filter_albums)
    SearchFilter.ARTISTS -> stringResource(Res.string.search_filter_artists)
    SearchFilter.PLAYLISTS -> stringResource(Res.string.search_filter_playlists)
}

/**
 * The section heading in the app's language. [searchSections] keeps its English
 * titles as list keys; anything it does not recognise is shown as it is.
 */
@Composable
private fun searchSectionTitle(title: String): String = when (title) {
    "Songs" -> stringResource(Res.string.search_section_songs)
    "Artists" -> stringResource(Res.string.search_section_artists)
    "Albums" -> stringResource(Res.string.search_section_albums)
    "Playlists" -> stringResource(Res.string.search_section_playlists)
    "More" -> stringResource(Res.string.search_section_more)
    else -> title
}
'''
    add_strings(EN, 1)
    add_strings(PT, 2)
    wr(SCREEN, s)
    say("OK")
except SystemExit as e:
    say("FAILED: " + str(e))
except Exception as e:
    say("ERROR: " + repr(e))
wr(OUT, "\n".join(log) + "\n")
