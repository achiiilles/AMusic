from pathlib import Path
import subprocess
p = Path('sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt')
s = p.read_text()
start = s.index('private fun HeroCard(')
end = s.index('private fun ', start + 10)
section = s[start:end]
old = '''        AsyncImage(
            model = item.thumbnailUrl.artworkAt(HEADER_ART_PX),
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize(),
        )'''
new = '''        ArtistAwareImage(
            artistName = item.title.takeIf { item.browseId?.startsWith("UC") == true },
            model = item.thumbnailUrl.artworkAt(HEADER_ART_PX),
            contentDescription = null,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize(),
        )'''
assert section.count(old) == 1, f'expected one hero artwork, saw {section.count(old)}'
s = s[:start] + section.replace(old, new, 1) + s[end:]
p.write_text(s)
with open('tmp-polish/out-g.txt', 'w') as out:
    subprocess.run(['git', 'diff', '--', str(p)], stdout=out, check=True)
