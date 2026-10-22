"""Adds the "Outras versões" carousel to the album page, once.

Temporary helper: the files are far too big to upload whole through the GitHub
file API, so the edits are made in place on the checked-out copy. Every anchor
must match exactly once, otherwise nothing is written and the job fails.
"""
import io
import sys

MODELS = "shared/src/commonMain/kotlin/com/music/amusic/data/model/Models.kt"
PARSER = "shared/src/jvmSharedMain/kotlin/com/music/amusic/data/innertube/InnertubeParser.kt"
REPO = "shared/src/jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt"
VIEWMODEL = "app/src/main/java/com/music/amusic/ui/MainViewModel.kt"
DETAIL = "app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt"


def read(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def apply(source, old, new, label):
    count = source.count(old)
    if count != 1:
        sys.exit("anchor %s matched %d times, expected 1" % (label, count))
    return source.replace(old, new)


# 1. ShelfItem learns whether the card is explicit.
models = read(MODELS)
models = apply(
    models,
    "    val videoId: String?,\n    val browseId: String?,\n)\n",
    "    val videoId: String?,\n    val browseId: String?,\n"
    "    /** Whether YouTube marks the card with its explicit badge (the \"E\" on an album). */\n"
    "    val explicit: Boolean = false,\n)\n",
    "ShelfItem",
)

# 2. The parser reads the "Other versions" carousel off an album response.
parser = read(PARSER)
parser = apply(
    parser,
    "    private fun parseTwoRowItem(renderer: JsonObject?): ShelfItem? {\n",
    '''    /**
     * The "Other versions" carousel on an album page: the other releases the
     * artist has linked to this one (the video version, the deluxe, the
     * explicit or clean cut). Null when the page has no such carousel, so an
     * album without linked versions reads exactly as before.
     *
     * Found by its heading, because an album response carries other carousels
     * too ("More from the artist", "You might also like") that must not be
     * shown under this title. Only album cards are kept.
     */
    fun parseOtherVersions(root: JsonElement): HomeShelf? {
        val shelf = collectRenderers(root, "musicCarouselShelfRenderer").firstOrNull { carousel ->
            OTHER_VERSIONS_TITLE.containsMatchIn(
                carousel.o("header").o("musicCarouselShelfBasicHeaderRenderer").o("title").runs(),
            )
        } ?: return null
        val items = shelf.a("contents").orEmpty().mapNotNull { entry ->
            val renderer = entry.o("musicTwoRowItemRenderer")
            parseTwoRowItem(renderer)?.let { item ->
                item.copy(explicit = renderer?.get("subtitleBadges").hasExplicitBadge() == true)
            }
        }.filter { it.browseId?.startsWith("MPRE") == true }
        if (items.isEmpty()) return null
        return HomeShelf(title = "Outras versões", items = items)
    }

    /** The heading YouTube gives that carousel, in the languages the app is likely to be asked in. */
    private val OTHER_VERSIONS_TITLE = Regex(
        "other versions|outras vers|otras versiones|autres versions|andere versionen|altre versioni",
        RegexOption.IGNORE_CASE,
    )

    private fun parseTwoRowItem(renderer: JsonObject?): ShelfItem? {
''',
    "parseTwoRowItem",
)

# 3. The album's SongPage carries them.
repo = read(REPO)
repo = apply(
    repo,
    "        val description: String? = null,\n    )\n\n    /**\n     * The first page of an album/playlist's tracks, and nothing more.",
    "        val description: String? = null,\n"
    "        /**\n"
    "         * The album page's \"Other versions\" carousel, see\n"
    "         * [InnertubeParser.parseOtherVersions]. Null for anything but an album,\n"
    "         * and for an album with no linked versions.\n"
    "         */\n"
    "        val otherVersions: com.music.amusic.data.model.HomeShelf? = null,\n"
    "    )\n\n    /**\n     * The first page of an album/playlist's tracks, and nothing more.",
    "SongPage",
)
repo = apply(
    repo,
    "        if (!browseId.startsWith(\"VL\")) page\n        else page.copy(owned = InnertubeParser.parsePlaylistOwned(response))\n",
    "        if (!browseId.startsWith(\"VL\")) {\n"
    "            // Read off the album's own response: the playlist that supplies\n"
    "            // its tracks (albumPageOf) does not carry the carousel.\n"
    "            if (browseId.startsWith(\"MPREb\")) {\n"
    "                page.copy(otherVersions = InnertubeParser.parseOtherVersions(response))\n"
    "            } else {\n"
    "                page\n"
    "            }\n"
    "        } else {\n"
    "            page.copy(owned = InnertubeParser.parsePlaylistOwned(response))\n"
    "        }\n",
    "browseSongs",
)

# 4. openDetail hands them to the page as its only section.
vm = read(VIEWMODEL)
vm = apply(
    vm,
    "                            description = page.description\n                            if (page.songs.isEmpty()) {",
    "                            description = page.description\n"
    "                            // An album's \"Outras versões\" carousel; the page draws a\n"
    "                            // section the same way it does an artist's albums.\n"
    "                            page.otherVersions?.let { sections = listOf(it) }\n"
    "                            if (page.songs.isEmpty()) {",
    "openDetail",
)

# 5. The card shows the explicit badge after the title, only when set.
detail = read(DETAIL)
old_title = """        Text(
            text = item.title,
            style = MaterialTheme.typography.titleMedium,
            color = palette.onBackground,
            maxLines = if (item.subtitle?.startsWith("Pré-Lançamento") == true) 2 else 1,
            overflow = TextOverflow.Ellipsis,
        )
"""
new_title = """        if (item.explicit) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = item.title,
                    style = MaterialTheme.typography.titleMedium,
                    color = palette.onBackground,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f, fill = false),
                )
                Text(
                    text = "E",
                    style = MaterialTheme.typography.labelSmall,
                    color = palette.onBackgroundVariant,
                    modifier = Modifier
                        .padding(start = 5.dp)
                        .clip(RoundedCornerShape(2.dp))
                        .background(palette.elevated)
                        .padding(horizontal = 3.dp),
                )
            }
        } else {
""" + "\n".join(("    " + l) if l else l for l in old_title.rstrip("\n").split("\n")) + "\n        }\n"
detail = apply(detail, old_title, new_title, "SectionCard title")

write(MODELS, models)
write(PARSER, parser)
write(REPO, repo)
write(VIEWMODEL, vm)
write(DETAIL, detail)
print("ok: 5 files edited")
