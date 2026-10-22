import sys

BASE = "app/src/main/java/com/music/amusic/"


def edit(path, pairs):
    s = open(path, encoding="utf-8").read()
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            print("ANCHOR COUNT", n, "for", old[:80].replace("\n", "\\n"))
            sys.exit(1)
        s = s.replace(old, new)
    open(path, "w", encoding="utf-8").write(s)
    print("ok", path)


edit(BASE + "ui/screens/DetailScreen.kt", [
    (
        '                        val song = if (preReleaseOff) rowSong.copy(artist = "Ainda n\u00e3o lan\u00e7ada") else rowSong\n',
        '                        val song = rowSong\n',
    ),
    (
        '                            showArtist = !numbered || preReleaseOff ||\n',
        '                            showArtist = !numbered ||\n',
    ),
])

edit(BASE + "ui/screens/PreReleaseScreen.kt", [
    (
        '            if (!track.released) {\n'
        '                Text(\n'
        '                    text = "Ainda n\u00e3o lan\u00e7ada",\n'
        '                    style = MaterialTheme.typography.bodySmall,\n'
        '                    color = colors.onSurfaceVariant.copy(alpha = 0.6f),\n'
        '                    maxLines = 1,\n'
        '                )\n'
        '            }\n',
        '',
    ),
])

edit("shared/src/jvmSharedMain/kotlin/com/music/amusic/data/ApplePreRelease.kt", [
    (
        '                name = rawName?.takeIf { it.isNotEmpty() } ?: "Track $number",\n',
        '                name = if (placeholder) "Faixa $number" else rawName.orEmpty(),\n',
    ),
])
