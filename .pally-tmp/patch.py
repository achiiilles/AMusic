import sys

SHELVES = "app/src/main/java/com/music/amusic/data/canvas/AppleAlbumShelves.kt"
PRE = "shared/src/jvmSharedMain/kotlin/com/music/amusic/data/ApplePreRelease.kt"


def patch(path, pairs):
    with open(path, encoding="utf-8") as f:
        s = f.read()
    if "displayTitle" in s:
        sys.exit("already patched: " + path)
    for old, new in pairs:
        if s.count(old) != 1:
            sys.exit("expected one match in %s, got %d: %r" % (path, s.count(old), old[:80]))
        s = s.replace(old, new)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(s)


patch(SHELVES, [
    (
        "import com.music.amusic.data.DebugLog as Log\n",
        "import com.music.amusic.data.ApplePreRelease\nimport com.music.amusic.data.DebugLog as Log\n",
    ),
    (
        "    private fun card(record: JsonObject, isAlbum: Boolean): ShelfItem? {",
        '''    /**
     * One Apple card. For an album, single or EP the title is Apple's name without
     * its trailing " - Single" or " - EP" (the type moves to the line under it, as
     * YouTube Music draws it), and the line under it is "Single • 2025" on the
     * artist's own shelf ([ownArtist] is that artist) or "Single • Artista" on a
     * shelf of other artists. The card is built from the record alone, so no
     * request is added; the YouTube Music album is only searched when it is tapped.
     */
    private fun card(record: JsonObject, isAlbum: Boolean, ownArtist: String? = null): ShelfItem? {''',
    ),
    (
        """        val releaseLine = if (isAlbum) listOfNotNull(kind, year).joinToString(" • ") else ""
        targets[key] = AppleShelfTarget(key, name, subtitle, url, isAlbum, releaseLine)
        return ShelfItem(
            title = name,
            subtitle = subtitle,""",
        """        val releaseLine = if (isAlbum) listOfNotNull(kind, year).joinToString(" • ") else ""
        val shownTitle = if (isAlbum) ApplePreRelease.displayTitle(name) else name
        val onOwnShelf = isAlbum && !ownArtist.isNullOrBlank() &&
            subtitle.normalizeForMatch().contains(ownArtist.normalizeForMatch())
        val shownSubtitle = when {
            !isAlbum -> subtitle
            onOwnShelf -> releaseLine
            else -> listOf(kind, subtitle).filter { it.isNotBlank() }.joinToString(" • ")
        }
        targets[key] = AppleShelfTarget(key, shownTitle, subtitle, url, isAlbum, releaseLine)
        return ShelfItem(
            title = shownTitle,
            subtitle = shownSubtitle,""",
    ),
    (
        '''        val views = record["views"] as? JsonObject
        val pageLock = Any()''',
        '''        val views = record["views"] as? JsonObject
        val ownName = (record["attributes"] as? JsonObject)?.text("name")
        val pageLock = Any()''',
    ),
    (
        """            .take(MAX_PAGED_CARDS)
            .mapNotNull { card(it, isAlbum = true) }
        // The three artist views""",
        """            .take(MAX_PAGED_CARDS)
            .mapNotNull { card(it, isAlbum = true, ownArtist = ownName) }
        // The three artist views""",
    ),
    (
        """            .take(MAX_PAGED_CARDS)
            .mapNotNull { card(it, isAlbum = true) }
    }

    private fun viewCards""",
        """            .take(MAX_PAGED_CARDS)
            .mapNotNull { card(it, isAlbum = true, ownArtist = ownName) }
    }

    private fun viewCards""",
    ),
    (
        '''        val artistKey = target.artist.substringBefore(",").substringBefore("&").trim().lowercase()''',
        '''        val artistKey = target.artist.substringBefore(",").substringBefore("&").normalizeForMatch()''',
    ),
    (
        "                artistKey.isNotEmpty() && !item.subtitle.lowercase().contains(artistKey) -> null",
        "                artistKey.isNotEmpty() && !item.subtitle.normalizeForMatch().contains(artistKey) -> null",
    ),
])

patch(PRE, [
    (
        "    private val json = Json {",
        '''    private val TYPE_SUFFIX = Regex("""\\s+-\\s+(?:single|ep)\\s*\\z""", RegexOption.IGNORE_CASE)

    /**
     * An Apple release name as it is shown: only a trailing " - Single" or " - EP"
     * is dropped, since the type is drawn on its own line. Anything else in the
     * name ("The 1st Mini Album", an "EP" in the middle) stays as Apple wrote it.
     */
    fun displayTitle(raw: String): String {
        val trimmed = raw.trim()
        return TYPE_SUFFIX.replace(trimmed, "").trim().ifEmpty { trimmed }
    }

    private val json = Json {''',
    ),
    (
        """            name = collection?.text("collectionName")
                ?: songs.firstOrNull()?.text("collectionName")
                ?: "",""",
        """            name = displayTitle(
                collection?.text("collectionName")
                    ?: songs.firstOrNull()?.text("collectionName")
                    ?: "",
            ),""",
    ),
])
print("patched")
