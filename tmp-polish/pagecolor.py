import re, sys
F = 'app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt'
M = 'app/src/main/java/com/music/amusic/MainActivity.kt'
f = open(F, encoding='utf-8').read()
m = open(M, encoding='utf-8').read()
bad = []
def sub(text, pat, repl, expect, name):
    new, n = re.subn(pat, repl, text)
    print(name, 'matches', n)
    if n != expect:
        bad.append(name)
        return text
    return new
# ---- FrostedTopBar.kt ----
f = sub(f, r'veil: Boolean = false,(\s*)modifier: Modifier = Modifier,', r'veil: Boolean = false,\1pageColor: Color = Color.Unspecified,\1modifier: Modifier = Modifier,', 2, 'sig back+actions')
f = sub(f, r'(pageVeil: Boolean = false,)', r'\1\n/** The colour the page itself is drawn in right now: the base under the veiled circles. Unspecified falls back to the theme background. */\npageColor: Color = Color.Unspecified,', 1, 'sig FrostedTopBar')
f = sub(f, r'veil = pageVeil,', r'veil = pageVeil,\npageColor = pageColor,', 2, 'call sites')
f = sub(f, r'artworkPageSurface\(shape = shape, hazeState = hazeState, veil = veil\)', 'artworkPageSurface(shape = shape, hazeState = hazeState, veil = veil, pageColor = pageColor)', 1, 'surface back')
f = sub(f, r'artworkPageSurface\(shape = CircleShape, hazeState = hazeState, veil = veil\)', 'artworkPageSurface(shape = CircleShape, hazeState = hazeState, veil = veil, pageColor = pageColor)', 1, 'surface actions')
i = f.find('private fun artworkPageSurface')
print('surface idx', i)
if i < 0:
    bad.append('surface idx')
else:
    head, tail = f[:i], f[i:]
    tail = sub(tail, r'(veil: Boolean = false,)(\s*\): Modifier \{)', r'\1\n    pageColor: Color = Color.Unspecified,\2', 1, 'surface sig')
    tail = sub(tail, r'(label = "topBarVeil",\s*\))', r'\1\n    // The same page colour the screen is drawn in (Apple Music tint when the page uses it), so the circles keep that hue.\n    val veilBacking by animateColorAsState(\n        targetValue = if (pageColor == Color.Unspecified) MaterialTheme.colorScheme.background else pageColor,\n        animationSpec = tween(180),\n        label = "topBarVeilBacking",\n    )', 1, 'backing val')
    tail = sub(tail, r'container\.copy\(alpha = TOP_BAR_VEIL_BACKING_ALPHA \* veilAmount\)', 'veilBacking.copy(alpha = TOP_BAR_VEIL_BACKING_ALPHA * veilAmount)', 1, 'backing use')
    f = head + tail
f = sub(f, r'in the page surface colour, so back', 'in the page colour, so back', 1, 'doc')
# ---- MainActivity.kt ----
m = sub(m, r'(val chromePageColor = if \(isDetailVisible\) \{\s*detailPalette\.background\s*\} else \{\s*MaterialTheme\.colorScheme\.background\s*\})', r'\1\n// The colour the artist, album and playlist pages are actually drawn in: the flat wash on artist pages (public or the library own), the palette background on releases. The top circles wear it.\nval chromeButtonColor = if (isDetailVisible && (detail?.type == BrowseType.ARTIST || detailIsLibraryArtist)) {\n    detailPalette.wash\n} else {\n    chromePageColor\n}', 1, 'main color')
m = sub(m, r'pageVeil = isDetailVisible,', 'pageVeil = isDetailVisible,\npageColor = chromeButtonColor,', 1, 'main call')
if bad:
    print('ABORT', bad)
    sys.exit(3)
open(F, 'w', encoding='utf-8').write(f)
open(M, 'w', encoding='utf-8').write(m)
print('patched')
