import hashlib
import subprocess

DETAIL = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
EXPECTED = 'd88cb951e13e056d80e89d542b68f7cf8a5250c3'
EDITS = [('private val ABOUT_GUTTER = PAGE_GUTTER + 6.dp\n', "private val ABOUT_GUTTER = PAGE_GUTTER + 6.dp\n\n/**\n * Where Apple Music's album hairlines stop on both sides: a little past the three-dot button\n * on the right and, mirrored, a little before the track number on the left for the long lines.\n */\nprivate val ALBUM_LINE_EDGE = 12.dp\n"), ('                        if (numbered && position == 0) {\n                            HorizontalDivider(\n                                modifier = Modifier.padding(start = ABOUT_GUTTER, end = ABOUT_GUTTER),', '                        if (numbered && position == 0) {\n                            HorizontalDivider(\n                                modifier = Modifier.padding(start = ALBUM_LINE_EDGE, end = ALBUM_LINE_EDGE),'), ('Modifier.padding(start = NUMBERED_ROW_DIVIDER_INSET, end = ABOUT_GUTTER)', 'Modifier.padding(start = NUMBERED_ROW_DIVIDER_INSET, end = ALBUM_LINE_EDGE)'), ('        // The long line under the last track, the same length as the one above track 1.\n        HorizontalDivider(\n            modifier = Modifier.padding(start = ABOUT_GUTTER, end = ABOUT_GUTTER),', '        // The long line under the last track, the same length as the one above track 1.\n        HorizontalDivider(\n            modifier = Modifier.padding(start = ALBUM_LINE_EDGE, end = ALBUM_LINE_EDGE),')]

def blobsha(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

data = open(DETAIL, 'rb').read()
assert blobsha(data) == EXPECTED, ('changed file', blobsha(data))
s = data.decode('utf-8')
for old, new in EDITS:
    assert s.count(old) == 1, ('anchor', s.count(old), old[:90])
    s = s.replace(old, new)
with open(DETAIL, 'w', encoding='utf-8', newline='') as out:
    out.write(s)
subprocess.run(['git', 'config', 'user.name', 'pally-bot'], check=True)
subprocess.run(['git', 'config', 'user.email', 'pally-bot@users.noreply.github.com'], check=True)
subprocess.run(['git', 'add', DETAIL], check=True)
subprocess.run(['git', 'commit', '-m', 'Album e single: linhas largas e curtas terminam depois do menu, centradas [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
