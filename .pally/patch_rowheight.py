import hashlib, os, subprocess, sys

DP = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
CP = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components/Common.kt'
EXPECT = {DP: 'f351ebaad7bc6558b668b26a4752f546214e6983', CP: '01831053aa31942987bb2189d7722362e54868f1'}
EDITS = {
    CP: [('val NUMBERED_ROW_DIVIDER_INSET = PAGE_GUTTER + TRACK_NUMBER_WIDTH + PAGE_GUTTER\n', "val NUMBERED_ROW_DIVIDER_INSET = PAGE_GUTTER + TRACK_NUMBER_WIDTH + PAGE_GUTTER\n\n/**\n * How tall a numbered row's number column is, which sets the row's height: the\n * row is this plus its 4dp of padding above and below. The default matches the\n * artwork the other rows carry, so only a caller that asks for less changes them.\n */\nval DEFAULT_TRACK_NUMBER_HEIGHT = 52.dp\n\n/**\n * The number column an album or single page asks for. Apple Music's track rows\n * there are about 80% as tall as the 52dp ones (60dp a row becomes 48dp).\n */\nval ALBUM_TRACK_NUMBER_HEIGHT = 40.dp\n", 1), ('    showArtist: Boolean = true,\n) {\n    val haptics = rememberHaptics()', "    showArtist: Boolean = true,\n    /** Height of the track-number column, which sets a numbered row's height. */\n    trackNumberHeight: Dp = DEFAULT_TRACK_NUMBER_HEIGHT,\n) {\n    val haptics = rememberHaptics()", 1), ('            showArtist = showArtist,\n        )', '            showArtist = showArtist,\n            trackNumberHeight = trackNumberHeight,\n        )', 2), ('    showArtist: Boolean = true,\n) {\n    val titleColor by', '    showArtist: Boolean = true,\n    trackNumberHeight: Dp = DEFAULT_TRACK_NUMBER_HEIGHT,\n) {\n    val titleColor by', 1), ('Modifier.width(TRACK_NUMBER_WIDTH).height(52.dp),', 'Modifier.width(TRACK_NUMBER_WIDTH).height(trackNumberHeight),', 1), ('            // [TRACK_NUMBER_WIDTH]). Same height as the artwork, so rows stay\n            // level.', "            // [TRACK_NUMBER_WIDTH]). Its height is the row's: the artwork's by\n            // default, so rows stay level, or less where the caller asks.", 1)],
    DP: [('import com.music.amusic.ui.components.NUMBERED_ROW_DIVIDER_INSET\n', 'import com.music.amusic.ui.components.ALBUM_TRACK_NUMBER_HEIGHT\nimport com.music.amusic.ui.components.NUMBERED_ROW_DIVIDER_INSET\n', 1), ('                            showArtist = !numbered ||\n                                !song.artist.trim().equals(appleAlbumCredit.trim(), ignoreCase = true),\n                        )', "                            showArtist = !numbered ||\n                                !song.artist.trim().equals(appleAlbumCredit.trim(), ignoreCase = true),\n                            // Only an album or single numbers its rows (trackNumber is null\n                            // otherwise), and there they are as tall as Apple Music's.\n                            trackNumberHeight = ALBUM_TRACK_NUMBER_HEIGHT,\n                        )", 1)],
}

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
if os.environ.get('DRY') == '1':
    print('dry ok')
    sys.exit(0)
subprocess.run(['git', 'config', 'user.name', 'pally-bot'], check=True)
subprocess.run(['git', 'config', 'user.email', 'pally-bot@users.noreply.github.com'], check=True)
subprocess.run(['git', 'add'] + list(EXPECT), check=True)
subprocess.run(['git', 'commit', '-m', 'Album e single: linha de faixa mais baixa (60dp para 48dp), como no Apple Music; demais telas seguem em 60dp [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
