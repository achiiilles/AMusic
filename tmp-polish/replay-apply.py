import re, sys

R = 'app/src/main/java/com/music/amusic/ui/replay/'


def load(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def save(p, s):
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)


def rep(s, old, new, label):
    if s.count(old) != 1:
        print('FAIL', label, s.count(old))
        sys.exit(1)
    return s.replace(old, new)


def rex(s, pattern, fn, label):
    s2, n = re.subn(pattern, fn, s, flags=re.S)
    if n != 1:
        print('FAIL', label, n)
        sys.exit(1)
    return s2


# ReplayScreen.kt: artist chart rows
p = R + 'ReplayScreen.kt'
s = load(p)
s = rep(s, 'import com.music.amusic.ui.components.PAGE_GUTTER\n',
        'import com.music.amusic.ui.components.ArtistAwareImage\nimport com.music.amusic.ui.components.PAGE_GUTTER\n', 'screen-import')


def row_img(m):
    ind = m.group(1)
    return (
        ind + 'if (circular) {' +
        ind + '    ArtistAwareImage(' +
        ind + '        model = row.artworkUrl.artworkAt(ROW_ART_PX),' +
        ind + '        artistName = row.title,' +
        ind + '        contentDescription = null,' +
        ind + '        contentScale = ContentScale.Crop,' +
        ind + '        modifier = Modifier.size(48.dp).clip(shape),' +
        ind + '    )' +
        ind + '} else {' +
        ind + '    AsyncImage(' +
        ind + '        model = row.artworkUrl.artworkAt(ROW_ART_PX),' +
        ind + '        contentDescription = null,' +
        ind + '        contentScale = ContentScale.Crop,' +
        ind + '        modifier = Modifier.size(48.dp).clip(shape),' +
        ind + '    )' +
        ind + '}'
    )


s = rex(s, r'(\n[ ]*)AsyncImage\(\s*model = row\.artworkUrl\.artworkAt\(ROW_ART_PX\),\s*contentDescription = null,\s*contentScale = ContentScale\.Crop,\s*modifier = Modifier\.size\(48\.dp\)\.clip\(shape\),\s*\)', row_img, 'screen-row')
save(p, s)

# ReplayStories.kt: leaderboard and collage
p = R + 'ReplayStories.kt'
s = load(p)
s = rep(s, 'import coil3.compose.AsyncImage\n',
        'import coil3.compose.AsyncImage\nimport com.music.amusic.ui.components.ArtistAwareImage\n', 'stories-import')
s = rex(s, r'(elevated: Boolean = false,)(\s*\)\s*\{\s*val base = modifier)',
        lambda m: m.group(1) + '\n    artistName: String? = null,' + m.group(2), 'cover-sig')
s = rep(s, 'url != null -> AsyncImage(',
        'url != null && artistName != null -> ArtistAwareImage(\n              model = url.artworkAt(px),\n              artistName = artistName,\n              contentDescription = null,\n              contentScale = ContentScale.Crop,\n              modifier = base,\n          )\n          url != null -> AsyncImage(', 'cover-branch')
s = rep(s, 'Cover(lead.artworkUrl, lead.title, 116.dp, shape, HEADER_ART_PX, elevated = true)',
        'Cover(lead.artworkUrl, lead.title, 116.dp, shape, HEADER_ART_PX, elevated = true, artistName = if (circular) lead.title else null)', 'lead-cover')
s = rep(s, 'Cover(row.artworkUrl, row.title, 36.dp, shape, ROW_ART_PX)',
        'Cover(row.artworkUrl, row.title, 36.dp, shape, ROW_ART_PX, artistName = if (circular) row.title else null)', 'row-cover')
s = rex(s, r'summary\.artists\.mapNotNull \{ it\.artworkUrl \}\.distinct\(\)\s*\.filterNot \{ it in covers \}\s*\.take\(3\)',
        lambda m: 'summary.artists.mapNotNull { artist -> artist.artworkUrl?.let { it to artist.title } }\n              .distinctBy { it.first }\n              .filterNot { it.first in covers }\n              .take(3)', 'faces')
s = rep(s, 'faces.forEachIndexed { index, url ->', 'faces.forEachIndexed { index, (url, faceName) ->', 'faces-loop')
s = rex(s, r'(shape = CircleShape,\s*px = CARD_ART_PX,)',
        lambda m: m.group(1) + '\n                  artistName = faceName,', 'faces-cover')
save(p, s)
print('OK')
