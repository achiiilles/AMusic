import hashlib
import subprocess

DETAIL = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
EXPECTED = '3f833d93c5e3175d5f4055155cadb7af0524b057'
EDITS = [('                        style = MaterialTheme.typography.bodyMedium.copy(lineHeight = 16.sp),\n                        color = palette.onBackgroundVariant,\n', '                        style = MaterialTheme.typography.bodyMedium.copy(\n                            fontSize = ALBUM_FOOTER_FONT_SIZE,\n                            lineHeight = ALBUM_FOOTER_LINE_HEIGHT,\n                        ),\n                        color = palette.onBackgroundVariant,\n'), ('/**\n * The closing block of an album or single page, as Apple Music draws it under the last\n', "/**\n * Size of the closing block's text: 14sp before. Apple Music's lines measure about 1.19 times as\n * wide as ours did at 14sp on the same screen width (279px against 234px for the song count),\n * and their line pitch is 33px against 29px, so 16.5sp with an 18sp line.\n */\nprivate val ALBUM_FOOTER_FONT_SIZE = 16.5.sp\nprivate val ALBUM_FOOTER_LINE_HEIGHT = 18.sp\n\n/**\n * The closing block of an album or single page, as Apple Music draws it under the last\n")]

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
subprocess.run(['git', 'commit', '-m', 'Album e single: texto do bloco do fim da lista maior [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
