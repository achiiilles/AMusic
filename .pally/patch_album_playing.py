import hashlib
import subprocess

FILES = {
    'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt': ('df742da3e9769420ccb5c84d3cdbb1244933d997', [('                            titleSize = if (numbered) ALBUM_TRACK_TITLE_SIZE else TextUnit.Unspecified,\n                        )\n                        if (position < matches.lastIndex) {', '                            titleSize = if (numbered) ALBUM_TRACK_TITLE_SIZE else TextUnit.Unspecified,\n                            // Apple Music does not mark the playing track on an album or single:\n                            // only its moving bars sit where the number was.\n                            plainCurrent = numbered,\n                        )\n                        if (position < matches.lastIndex) {')]),
    'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components/Common.kt': ('b22c22209d096ca7785d5aab49720a9ab326f6c9', [('    /** Size of the title, or unspecified for the usual one. */\n    titleSize: TextUnit = TextUnit.Unspecified,\n) {\n    val haptics = rememberHaptics()', '    /** Size of the title, or unspecified for the usual one. */\n    titleSize: TextUnit = TextUnit.Unspecified,\n    /**\n     * True leaves the current track unmarked apart from its moving bars: no tinted row\n     * background, no accent title, and no plate behind the bars. Album and single pages use\n     * it, as Apple Music does.\n     */\n    plainCurrent: Boolean = false,\n) {\n    val haptics = rememberHaptics()'), ('            titleWeight = titleWeight,\n            titleSize = titleSize,\n        )\n        return\n    }', '            titleWeight = titleWeight,\n            titleSize = titleSize,\n            plainCurrent = plainCurrent,\n        )\n        return\n    }'), ('            titleWeight = titleWeight,\n            titleSize = titleSize,\n        )\n    }\n}\n', '            titleWeight = titleWeight,\n            titleSize = titleSize,\n            plainCurrent = plainCurrent,\n        )\n    }\n}\n'), ('    titleSize: TextUnit = TextUnit.Unspecified,\n) {\n    val titleColor by animateColorAsState(\n        targetValue = if (isCurrent) activeTint else MaterialTheme.colorScheme.onBackground,', '    titleSize: TextUnit = TextUnit.Unspecified,\n    plainCurrent: Boolean = false,\n) {\n    val titleColor by animateColorAsState(\n        targetValue = if (isCurrent && !plainCurrent) activeTint else MaterialTheme.colorScheme.onBackground,'), ('targetValue = if (isCurrent || selected) activeTint.copy(alpha = 0.14f) else Color.Transparent,', 'targetValue = if ((isCurrent && !plainCurrent) || selected) activeTint.copy(alpha = 0.14f) else Color.Transparent,'), ('                if (searchPlayingStyle && isCurrent && isPlaying) {\n                    SearchPlayingBars()\n                } else if (isCurrent) {\n                    Icon(\n                        imageVector = if (isPlaying) Icons.Rounded.GraphicEq else Icons.Rounded.PlayArrow,\n                        contentDescription = stringResource(Res.string.now_playing),\n                        tint = activeTint,', "                if (searchPlayingStyle && isCurrent && isPlaying) {\n                    // Loose bars in the title's colour, no plate, when the page asks for it.\n                    if (plainCurrent) SearchPlayingBars(plate = false, color = titleColor) else SearchPlayingBars()\n                } else if (isCurrent) {\n                    Icon(\n                        imageVector = if (isPlaying) Icons.Rounded.GraphicEq else Icons.Rounded.PlayArrow,\n                        contentDescription = stringResource(Res.string.now_playing),\n                        tint = if (plainCurrent) titleColor else activeTint,"), ('@Composable\nfun SearchPlayingBars(modifier: Modifier = Modifier) {', '@Composable\nfun SearchPlayingBars(\n    modifier: Modifier = Modifier,\n    /** False draws only the bars, with no dark rounded square behind them. */\n    plate: Boolean = true,\n    /** Colour of the bars. */\n    color: Color = Color.White,\n) {'), ('        modifier = modifier\n            .size(24.dp)\n            .clip(RoundedCornerShape(6.dp))\n            .background(Color.Black.copy(alpha = 0.52f)),\n        contentAlignment = Alignment.Center,', '        modifier = if (plate) {\n            modifier\n                .size(24.dp)\n                .clip(RoundedCornerShape(6.dp))\n                .background(Color.Black.copy(alpha = 0.52f))\n        } else {\n            modifier.size(24.dp)\n        },\n        contentAlignment = Alignment.Center,'), ('                        .clip(RoundedCornerShape(2.dp))\n                        .background(Color.White),', '                        .clip(RoundedCornerShape(2.dp))\n                        .background(color),')]),
}

def blobsha(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()

paths = []
for path, (expected, edits) in FILES.items():
    data = open(path, 'rb').read()
    assert blobsha(data) == expected, ('changed file', path, blobsha(data))
    original = data.decode('utf-8')
    s = original
    for old, new in edits:
        assert s.count(old) == 1, ('anchor', path, s.count(old), old[:90])
        s = s.replace(old, new)
    assert s.count('{') - s.count('}') == original.count('{') - original.count('}'), ('braces', path)
    with open(path, 'w', encoding='utf-8', newline='') as out:
        out.write(s)
    paths.append(path)
subprocess.run(['git', 'config', 'user.name', 'pally-bot'], check=True)
subprocess.run(['git', 'config', 'user.email', 'pally-bot@users.noreply.github.com'], check=True)
subprocess.run(['git', 'add'] + paths, check=True)
subprocess.run(['git', 'commit', '-m', 'Album e single: faixa tocando sem destaque e barrinhas sem bloco [skip ci]'], check=True)
subprocess.run(['git', 'pull', '--rebase', 'origin', 'polish-refresh-transitions'], check=True)
subprocess.run(['git', 'push', 'origin', 'HEAD:polish-refresh-transitions'], check=True)
