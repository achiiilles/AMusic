import hashlib, os, subprocess, sys

DP = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
EXPECT = {DP: 'a61276b77ea797cccb47f12d030c1fdee6b78798'}
EDITS = {DP: [('                        val isCurrent = isCurrentRow(song)\n                        SongRow(\n', "                        val isCurrent = isCurrentRow(song)\n                        // Apple Music draws the same hairline above an album's first track,\n                        // between the description and track 1, as it does between tracks.\n                        // It starts at the description's own margin, a shade darker than the page.\n                        if (numbered && position == 0) {\n                            HorizontalDivider(\n                                modifier = Modifier.padding(start = ABOUT_GUTTER),\n                                thickness = 0.5.dp,\n                                color = palette.divider,\n                            )\n                        }\n                        SongRow(\n", 1), ('                                    start = if (numbered) NUMBERED_ROW_DIVIDER_INSET else ROW_DIVIDER_INSET,\n', "                                    // On an album or single the line runs from the description's margin.\n                                    start = if (numbered) ABOUT_GUTTER else ROW_DIVIDER_INSET,\n", 1)]}

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
subprocess.run(['git', 'commit', '-m', 'Album e single: divisoria fina antes da primeira faixa e entre as faixas, a partir da margem da descricao [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
