import hashlib, subprocess

DP = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
CP = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components/Common.kt'
EXPECT = {DP: 'c603a1f17ac1222651a50747ef43fbe31a7129bf', CP: 'cc30ef3f2e7853559e2c3ce750ed3246261d83c8'}
EDITS = {'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components/Common.kt': [('val ALBUM_TRACK_NUMBER_HEIGHT = 40.dp\n', "val ALBUM_TRACK_NUMBER_HEIGHT = 40.dp\n\n/**\n * The weight of a track's title on an album or single page. Apple Music sets\n * those titles in regular weight, lighter than the semibold the other lists use.\n */\nval ALBUM_TRACK_TITLE_WEIGHT = FontWeight.W400\n", 1), ('    trackNumberHeight: Dp = DEFAULT_TRACK_NUMBER_HEIGHT,\n) {\n    val haptics = rememberHaptics()\n', '    trackNumberHeight: Dp = DEFAULT_TRACK_NUMBER_HEIGHT,\n    /** Weight of the title, or null for the usual one. */\n    titleWeight: FontWeight? = null,\n) {\n    val haptics = rememberHaptics()\n', 1), ('            trackNumberHeight = trackNumberHeight,\n        )\n        return\n', '            trackNumberHeight = trackNumberHeight,\n            titleWeight = titleWeight,\n        )\n        return\n', 1), ('            trackNumberHeight = trackNumberHeight,\n        )\n    }\n}\n', '            trackNumberHeight = trackNumberHeight,\n            titleWeight = titleWeight,\n        )\n    }\n}\n', 1), ('    trackNumberHeight: Dp = DEFAULT_TRACK_NUMBER_HEIGHT,\n) {\n    val titleColor by animateColorAsState(\n', '    trackNumberHeight: Dp = DEFAULT_TRACK_NUMBER_HEIGHT,\n    titleWeight: FontWeight? = null,\n) {\n    val titleColor by animateColorAsState(\n', 1), ('                style = MaterialTheme.typography.titleMedium,\n                color = titleColor,\n', '                style = MaterialTheme.typography.titleMedium.let { base ->\n                    if (titleWeight != null) base.copy(fontWeight = titleWeight) else base\n                },\n                color = titleColor,\n', 1)], 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt': [('import com.music.amusic.ui.components.ALBUM_TRACK_NUMBER_HEIGHT\n', 'import com.music.amusic.ui.components.ALBUM_TRACK_NUMBER_HEIGHT\nimport com.music.amusic.ui.components.ALBUM_TRACK_TITLE_WEIGHT\n', 1), ('                            trackNumberHeight = ALBUM_TRACK_NUMBER_HEIGHT,\n                        )\n', "                            trackNumberHeight = ALBUM_TRACK_NUMBER_HEIGHT,\n                            // Apple Music's track titles on an album or single are lighter.\n                            titleWeight = if (numbered) ALBUM_TRACK_TITLE_WEIGHT else null,\n                        )\n", 1)]}

def gh(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

def bal(s):
    return (s.count('{') - s.count('}'), s.count('(') - s.count(')'))

new = {}
for p, sha in EXPECT.items():
    b = open(p, 'rb').read()
    assert gh(b) == sha, ('sha changed', p, gh(b))
    s = b.decode('utf-8')
    o = s
    for old, rep, cnt in EDITS[p]:
        assert s.count(old) == cnt, ('anchor count', s.count(old), old[:80])
        s = s.replace(old, rep)
    assert bal(s) == bal(o), ('balance', p)
    new[p] = s

for p, s in new.items():
    open(p, 'w', encoding='utf-8', newline='').write(s)
subprocess.run(['git', 'config', 'user.name', 'pally-bot'], check=True)
subprocess.run(['git', 'config', 'user.email', 'pally-bot@users.noreply.github.com'], check=True)
subprocess.run(['git', 'add'] + list(EXPECT), check=True)
subprocess.run(['git', 'commit', '-m', 'Album e single: titulo das faixas mais leve, como no Apple Music [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
