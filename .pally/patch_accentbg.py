import sys
EDITS = [
('sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/theme/ArtworkPalette.kt', r'''    keyColors: ArtworkKeyColors? = null,
): ArtworkPalette {
''', r'''    keyColors: ArtworkKeyColors? = null,
    /**
     * Album and single pages only. When the sleeve's most common colour is
     * grey, white or black, the page takes the sleeve's accent colour as its
     * tint instead of staying neutral. Off by default, so the artist pages
     * (Apple's colours) and every other caller keep the palette they had.
     */
    accentWhenNeutral: Boolean = false,
): ArtworkPalette {
'''),
('sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/theme/ArtworkPalette.kt', r'''    val target = seed?.toPalette(dark) ?: ArtworkPalette(
''', r'''    val shaped = if (accentWhenNeutral) seed?.withAccentWhenNeutral() else seed
    val target = shaped?.toPalette(dark) ?: ArtworkPalette(
'''),
('sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/theme/ArtworkPalette.kt', r'''private const val CHROMATIC_SATURATION_THRESHOLD = 0.12f
''', r'''private const val CHROMATIC_SATURATION_THRESHOLD = 0.12f

/**
 * A sleeve whose most common colour is grey, white or black would give a grey
 * page, because [adaptedArtworkSaturation] keeps neutral colour neutral. For
 * release pages the page tint is then taken from the accent colour instead, the
 * same one that colours "Mais" and the playing title, as long as that accent is
 * a real colour. Only the tint inputs change: the accent, the edge and every
 * sleeve with a coloured dominant keep exactly what they had.
 */
private fun Seed.withAccentWhenNeutral(): Seed =
    if (dominant.isNeutralColor() && vibrant.chroma() >= TINT_MIN_CHROMA && !vibrant.isNeutralColor()) {
        copy(dominant = vibrant)
    } else {
        this
    }

/**
 * Grey, near-white or near-black. HSL saturation alone calls an off-white
 * "saturated", so a colour with almost no spread between its channels also
 * counts as neutral.
 */
private fun Color.isNeutralColor(): Boolean {
    val hsl = FloatArray(3).also { ColorUtils.colorToHSL(toArgb(), it) }
    return hsl[1] < CHROMATIC_SATURATION_THRESHOLD || chroma() < NEUTRAL_MAX_CHROMA
}

/** Channel spread (0..1) below which a colour reads as grey whatever its HSL saturation. */
private const val NEUTRAL_MAX_CHROMA = 0.04f
'''),
('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt', r'''    val palette = rememberArtworkPalette(
        imageUrl = appleArt?.heroUrl ?: page.thumbnailUrl,
        keyColors = appleArt?.keyColors(),
    )
''', r'''    val palette = rememberArtworkPalette(
        imageUrl = appleArt?.heroUrl ?: page.thumbnailUrl,
        keyColors = appleArt?.keyColors(),
        // Album and single pages only: a grey sleeve tints the page with its
        // accent colour. Artist pages (public and the library's own) and device
        // folders never take this path. MainActivity asks the same question for
        // the bars around the page.
        accentWhenNeutral = page.type == BrowseType.ALBUM && !artistColours &&
            !page.browseId.orEmpty().startsWith("local:"),
    )
'''),
('app/src/main/java/com/music/amusic/MainActivity.kt', r'''    val detailPalette = rememberArtworkPalette(
        imageUrl = detailApple?.heroUrl ?: detail?.thumbnailUrl,
        keyColors = detailApple?.keyColors(),
    )
''', r'''    val detailPalette = rememberArtworkPalette(
        imageUrl = detailApple?.heroUrl ?: detail?.thumbnailUrl,
        keyColors = detailApple?.keyColors(),
        // Same condition as DetailScreen's palette, so the bars keep matching
        // the page: album and single only, never an artist page.
        accentWhenNeutral = detail?.type == BrowseType.ALBUM && !detailIsLibraryArtist &&
            !detail?.browseId.orEmpty().startsWith("local:"),
    )
'''),
]
for path, old, new in EDITS:
    with open(path, encoding='utf-8') as f:
        text = f.read()
    n = text.count(old)
    if n != 1:
        sys.exit('expected exactly one match in %s, found %d' % (path, n))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text.replace(old, new, 1))
print('ok')
