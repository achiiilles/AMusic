import hashlib
import subprocess

DETAIL = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
EXPECTED = 'e1b8441991bb13ddbba880076bb8f0893dc6080b'
EDITS = [("                        // Apple Music draws the same hairline above an album's first track,\n                        // between the description and track 1, as it does between tracks.\n                        // It starts at the description's own margin, a shade darker than the page.\n                        if (numbered && position == 0) {\n                            HorizontalDivider(\n                                modifier = Modifier.padding(start = ABOUT_GUTTER),\n", "                        // Apple Music draws two lengths of hairline on an album or single: a long\n                        // one above track 1 (and under the last track, see AlbumFooter), running\n                        // between the description's margins, and a short one between tracks.\n                        if (numbered && position == 0) {\n                            HorizontalDivider(\n                                modifier = Modifier.padding(start = ABOUT_GUTTER, end = ABOUT_GUTTER),\n"), ("                                modifier = Modifier.padding(\n                                    // On an album or single the line runs from the description's margin.\n                                    start = if (numbered) ABOUT_GUTTER else ROW_DIVIDER_INSET,\n                                ),\n", '                                modifier = if (numbered) {\n                                    // Short line: from the title, past the number, to the ⋮ and no\n                                    // further, never out to the screen edge.\n                                    Modifier.padding(start = NUMBERED_ROW_DIVIDER_INSET, end = ABOUT_GUTTER)\n                                } else {\n                                    Modifier.padding(start = ROW_DIVIDER_INSET)\n                                },\n'), ('    if (lines.isEmpty()) return\n    Column(\n        Modifier\n            .fillMaxWidth()\n            .padding(start = ABOUT_GUTTER, end = ABOUT_GUTTER, top = 24.dp, bottom = 28.dp),\n    ) {\n        lines.forEach { line ->\n            Text(\n                text = line,\n                style = MaterialTheme.typography.bodyMedium.copy(lineHeight = 16.sp),\n                color = palette.onBackgroundVariant,\n            )\n        }\n    }\n}\n', '    Column(Modifier.fillMaxWidth()) {\n        // The long line under the last track, the same length as the one above track 1.\n        HorizontalDivider(\n            modifier = Modifier.padding(start = ABOUT_GUTTER, end = ABOUT_GUTTER),\n            thickness = 0.5.dp,\n            color = palette.divider,\n        )\n        if (lines.isNotEmpty()) {\n            Column(\n                Modifier\n                    .fillMaxWidth()\n                    .padding(start = ABOUT_GUTTER, end = ABOUT_GUTTER, top = 24.dp, bottom = 28.dp),\n            ) {\n                lines.forEach { line ->\n                    Text(\n                        text = line,\n                        style = MaterialTheme.typography.bodyMedium.copy(lineHeight = 16.sp),\n                        color = palette.onBackgroundVariant,\n                    )\n                }\n            }\n        }\n    }\n}\n')]

def blobsha(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

data = open(DETAIL, 'rb').read()
assert blobsha(data) == EXPECTED, ('changed file', blobsha(data))
s = data.decode('utf-8')
for old, new in EDITS:
    assert s.count(old) == 1, ('anchor', s.count(old), old[:90])
    s = s.replace(old, new)
assert s.count('{') - s.count('}') == data.decode('utf-8').count('{') - data.decode('utf-8').count('}'), 'braces'
with open(DETAIL, 'w', encoding='utf-8', newline='') as out:
    out.write(s)
subprocess.run(['git', 'config', 'user.name', 'pally-bot'], check=True)
subprocess.run(['git', 'config', 'user.email', 'pally-bot@users.noreply.github.com'], check=True)
subprocess.run(['git', 'add', DETAIL], check=True)
subprocess.run(['git', 'commit', '-m', 'Album e single: linha larga antes e depois das faixas, linha curta entre faixas [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
