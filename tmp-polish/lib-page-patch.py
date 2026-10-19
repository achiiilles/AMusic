import sys

BASE = "app/src/main/java/com/music/amusic/"
DETAIL = BASE + "ui/screens/DetailScreen.kt"
MAIN = BASE + "MainActivity.kt"


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, t):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(t)


def rep(t, old, new, label):
    c = t.count(old)
    if c != 1:
        print("FAIL", label, c)
        sys.exit(1)
    return t.replace(old, new)


def stage1(root):
    d = read(root + DETAIL)
    d = rep(d,
        "    inLibraryArtistPage: Boolean = false,\n) {\n    val rawSongs",
        "    inLibraryArtistPage: Boolean = false,\n"
        "    /** Public artist page this library page came from, when known. */\n"
        "    publicArtistId: String? = null,\n) {\n    val rawSongs", "d-param")
    d = rep(d,
        "                        onArtistClick = onArtistClick.takeIf { folder == null },\n"
        "                        onToggleLibrary = onToggleLibrary,\n                    )\n",
        "                        onArtistClick = onArtistClick.takeIf { folder == null },\n"
        "                        onToggleLibrary = onToggleLibrary,\n"
        "                        libraryArtist = inLibraryArtistPage,\n"
        "                        publicArtistId = publicArtistId,\n                    )\n", "d-call")
    d = rep(d,
        "    onArtistClick: ((String, String) -> Unit)?,\n    onToggleLibrary: (() -> Unit)?,\n) {\n    val (credit, meta)",
        "    onArtistClick: ((String, String) -> Unit)?,\n    onToggleLibrary: (() -> Unit)?,\n"
        "    libraryArtist: Boolean = false,\n    publicArtistId: String? = null,\n) {\n    val (credit, meta)", "d-sig")
    d = rep(d,
        "            maxLines = 2,\n            overflow = TextOverflow.Ellipsis,\n"
        "            modifier = Modifier.padding(horizontal = HEADER_GUTTER),\n        )\n        if (credit.isNotBlank()) {\n",
        "            maxLines = 2,\n            overflow = TextOverflow.Ellipsis,\n"
        "            // On the library artist page the name is the way into the public\n"
        "            // profile, and it opens the page's own artist, not the first track's.\n"
        "            modifier = Modifier\n"
        "                .padding(horizontal = HEADER_GUTTER)\n"
        "                .let { m ->\n"
        "                    if (libraryArtist && onArtistClick != null) {\n"
        "                        val targetId = publicArtistId ?: page.browseId\n"
        "                        m.clip(RoundedCornerShape(6.dp))\n"
        "                            .clickable { onArtistClick(targetId, page.title) }\n"
        "                    } else {\n"
        "                        m\n"
        "                    }\n"
        "                },\n        )\n        if (!libraryArtist && credit.isNotBlank()) {\n", "d-title")
    write(root + DETAIL, d)

    m = read(root + MAIN)
    m = rep(m,
        "                        val shownPage = if (libraryAlbumsShelf == null) {\n",
        "                        val libraryPublicArtistId = remember(detailStack, page.browseId, page.type, page.title) {\n"
        "                            if (page.type == BrowseType.ARTIST) {\n"
        "                                null\n"
        "                            } else {\n"
        "                                val pageIndex = detailStack.indexOfLast { it.browseId == page.browseId }\n"
        "                                detailStack.getOrNull(pageIndex - 1)\n"
        "                                    ?.takeIf {\n"
        "                                        pageIndex > 0 && it.type == BrowseType.ARTIST &&\n"
        "                                            isExactArtistMatch(it.title, page.title)\n"
        "                                    }\n"
        "                                    ?.browseId\n"
        "                            }\n"
        "                        }\n"
        "                        val shownPage = if (libraryAlbumsShelf == null) {\n", "m-id")
    m = rep(m,
        "                            inLibraryArtistPage = isLibraryArtistPage,\n",
        "                            inLibraryArtistPage = isLibraryArtistPage,\n"
        "                            publicArtistId = libraryPublicArtistId,\n", "m-pass")
    write(root + MAIN, m)


def stage2(root):
    d = read(root + DETAIL)
    d = rep(d,
        "    val palette = rememberArtworkPalette(\n        imageUrl = appleArt?.heroUrl ?: page.thumbnailUrl,",
        "    // Saved albums, EPs and singles all count as albums, from the same shelf\n"
        "    // the Na sua biblioteca section and its Ver tudo page list.\n"
        "    val libraryAlbumCount = if (inLibraryArtistPage) {\n"
        "        page.sections\n"
        "            .filter { shelf ->\n"
        "                val shelfTitle = shelf.title.trim()\n"
        "                shelfTitle.equals(hiddenFromLibraryTitle, ignoreCase = true) ||\n"
        "                    shelfTitle.equals(\"From your library\", ignoreCase = true)\n"
        "            }\n"
        "            .sumOf { it.items.size }\n"
        "    } else {\n"
        "        0\n"
        "    }\n"
        "    val palette = rememberArtworkPalette(\n        imageUrl = appleArt?.heroUrl ?: page.thumbnailUrl,", "d2-count")
    d = rep(d,
        "                        libraryArtist = inLibraryArtistPage,\n                        publicArtistId = publicArtistId,\n                    )\n",
        "                        libraryArtist = inLibraryArtistPage,\n                        publicArtistId = publicArtistId,\n"
        "                        libraryAlbumCount = libraryAlbumCount,\n                    )\n", "d2-call")
    d = rep(d,
        "    libraryArtist: Boolean = false,\n    publicArtistId: String? = null,\n) {\n    val (credit, meta) = page.headerLines(songs.size, songs.playtime())",
        "    libraryArtist: Boolean = false,\n    publicArtistId: String? = null,\n    libraryAlbumCount: Int = 0,\n) {\n"
        "    val (credit, meta) = page.headerLines(songs.size, songs.playtime(), libraryAlbumCount)", "d2-sig")
    d = rep(d,
        "private fun DetailPage.headerLines(trackCount: Int, playtime: String? = null): Pair<String, String> {",
        "private fun DetailPage.headerLines(\n    trackCount: Int,\n    playtime: String? = null,\n    albumCount: Int = 0,\n): Pair<String, String> {", "d2-hl")
    d = rep(d,
        "            pluralStringResource(R.plurals.track_count_plural, it, it).capitalizeWords()\n        },\n        playtime,\n",
        "            pluralStringResource(R.plurals.track_count_plural, it, it).capitalizeWords()\n        },\n"
        "        albumCount.takeIf { it > 0 }?.let { pluralStringResource(R.plurals.album_count, it, it) },\n        playtime,\n", "d2-meta")
    write(root + DETAIL, d)


def stage3(root):
    d = read(root + DETAIL)
    d = rep(d,
        "                        libraryAlbumCount = libraryAlbumCount,\n                    )\n",
        "                        libraryAlbumCount = libraryAlbumCount,\n                        artistPhotoUrl = appleArt?.heroUrl,\n                    )\n", "d3-call")
    d = rep(d,
        "    libraryAlbumCount: Int = 0,\n) {\n    val (credit, meta)",
        "    libraryAlbumCount: Int = 0,\n    artistPhotoUrl: String? = null,\n) {\n    val (credit, meta)", "d3-sig")
    d = rep(d,
        "        Box(\n            Modifier\n                .size(sleeveSize)\n                .shadow(SLEEVE_SHADOW, SLEEVE_SHAPE)\n"
        "                .background(palette.elevated)\n                .thumbnailBorder(SLEEVE_SHAPE),\n        ) {\n",
        "        // The library artist page shows the artist as a round photo, like the\n"
        "        // artist lists do; every other release keeps its square sleeve.\n"
        "        val sleeveShape = if (libraryArtist) CircleShape else SLEEVE_SHAPE\n"
        "        Box(\n            Modifier\n                .size(sleeveSize)\n                .shadow(SLEEVE_SHADOW, sleeveShape)\n"
        "                .clip(sleeveShape)\n"
        "                .background(palette.elevated)\n                .thumbnailBorder(sleeveShape),\n        ) {\n", "d3-box")
    d = rep(d,
        "            AsyncImage(\n                model = page.thumbnailUrl.artworkAt(HEADER_ART_PX),\n"
        "                contentDescription = null,\n                contentScale = ContentScale.Crop,\n"
        "                onState = { artFailed = it is AsyncImagePainter.State.Error },\n"
        "                modifier = Modifier.matchParentSize(),\n            )\n",
        "            if (libraryArtist) {\n"
        "                // The still photo the public artist page uses as its cover,\n"
        "                // never its video. The page's own thumbnail stands in until\n"
        "                // the photo arrives and the two cross-fade.\n"
        "                Crossfade(\n"
        "                    targetState = artistPhotoUrl ?: page.thumbnailUrl.artworkAt(HEADER_ART_PX),\n"
        "                    modifier = Modifier.matchParentSize(),\n"
        "                    animationSpec = tween(durationMillis = 250),\n"
        "                    label = \"libraryArtistPhoto\",\n"
        "                ) { shownPhoto ->\n"
        "                    AsyncImage(\n"
        "                        model = shownPhoto,\n"
        "                        contentDescription = null,\n"
        "                        contentScale = ContentScale.Crop,\n"
        "                        onState = { artFailed = it is AsyncImagePainter.State.Error },\n"
        "                        modifier = Modifier.fillMaxSize(),\n"
        "                    )\n"
        "                }\n"
        "            } else {\n"
        "                AsyncImage(\n                    model = page.thumbnailUrl.artworkAt(HEADER_ART_PX),\n"
        "                    contentDescription = null,\n                    contentScale = ContentScale.Crop,\n"
        "                    onState = { artFailed = it is AsyncImagePainter.State.Error },\n"
        "                    modifier = Modifier.matchParentSize(),\n                )\n            }\n", "d3-img")
    write(root + DETAIL, d)


if __name__ == "__main__":
    stage = sys.argv[1]
    root = sys.argv[2] if len(sys.argv) > 2 else ""
    {"1": stage1, "2": stage2, "3": stage3}[stage](root)
    print("ok stage", stage)
