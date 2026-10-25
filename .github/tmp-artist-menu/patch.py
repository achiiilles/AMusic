import sys

BASE = "app/src/main/java/com/music/amusic/"
SHEET = BASE + "ui/components/BrowseActionsSheet.kt"
DETAIL = BASE + "ui/screens/DetailScreen.kt"
MAIN = BASE + "MainActivity.kt"


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write(p, t):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)


def sub(text, old, new, name):
    if text.count(old) != 1:
        sys.exit("anchor not found exactly once: " + name)
    return text.replace(old, new)


sheet = read(SHEET)
detail = read(DETAIL)
main = read(MAIN)

if "BrowseCredit" in sheet:
    sys.exit("already applied")

# ---- BrowseActionsSheet.kt ----
sheet = sub(sheet, "import androidx.compose.foundation.background\n",
            "import androidx.compose.foundation.background\nimport androidx.compose.foundation.clickable\n", "import clickable")
sheet = sub(sheet, "import androidx.compose.ui.text.style.TextOverflow\n",
            "import androidx.compose.ui.text.font.FontWeight\nimport androidx.compose.ui.text.style.TextOverflow\n", "import FontWeight")
sheet = sub(sheet, "    val downloadId: String? = null,\n)\n", """    val downloadId: String? = null,
    /**
     * The artist part of [subtitle] and the artists it names, set only by the release
     * page's own overflow so that artist can be tapped there. Null everywhere else:
     * a card keeps its subtitle as plain text.
     */
    val credit: BrowseCredit? = null,
)

/**
 * [text] is the exact piece of the subtitle that names the artist (what gets the tap),
 * and [artists] are the artists it opens: one with a channel id, or the several of a
 * shared credit, which are offered in [ArtistChoiceSheet].
 */
data class BrowseCredit(
    val text: String,
    val artists: List<CreditArtist>,
)
""", "BrowseTarget credit")
sheet = sub(sheet, "    onSort: (() -> Unit)? = null,\n) {\n", """    onSort: (() -> Unit)? = null,
    /**
     * Release page only: opens an artist's public page by channel id. The caller closes
     * the sheet and navigates; the header's artist name is tappable only when this is set.
     */
    onOpenArtist: ((String, String) -> Unit)? = null,
) {
""", "onOpenArtist param")
sheet = sub(sheet, "    var confirmingDeleteDownload by remember { mutableStateOf(false) }\n", """    var confirmingDeleteDownload by remember { mutableStateOf(false) }
    var choosingArtist by remember { mutableStateOf(false) }
""", "choosingArtist state")
sheet = sub(sheet, "                BrowseSheetHeader(target)\n", """                // One artist with a channel id opens straight away, several ask which one.
                // With no id there is nothing to open by, so the name stays plain text.
                val creditArtists = target.credit?.artists.orEmpty()
                val onlyArtist = creditArtists.singleOrNull()
                val onlyArtistId = onlyArtist?.browseId
                val artistTap: (() -> Unit)? = onOpenArtist?.let { open ->
                    when {
                        creditArtists.size > 1 -> ({ choosingArtist = true })
                        onlyArtist != null && onlyArtistId != null -> ({ open(onlyArtistId, onlyArtist.name) })
                        else -> null
                    }
                }
                BrowseSheetHeader(target, onArtistClick = artistTap)
""", "header call")
sheet = sub(sheet, "            if (!menu) Spacer(Modifier.height(24.dp))\n        }\n    }\n}\n", """            if (!menu) Spacer(Modifier.height(24.dp))
        }
        val sharedCredit = target.credit
        if (choosingArtist && sharedCredit != null && onOpenArtist != null) {
            ArtistChoiceSheet(
                artists = sharedCredit.artists,
                onPick = onOpenArtist,
                onDismiss = { choosingArtist = false },
            )
        }
    }
}
""", "choice sheet")
i0 = sheet.index("private fun BrowseSheetHeader(target: BrowseTarget) {\n")
i1 = sheet.index("            Text(\n                // A card frequently has no subtitle at all", i0)
end_marker = "                maxLines = 1,\n                overflow = TextOverflow.Ellipsis,\n            )\n        }\n    }\n}\n"
i2 = sheet.index(end_marker, i1) + len(end_marker)
new_block = """            // A card frequently has no subtitle at all, and the kind of
            // thing it is beats a blank line under the title. A card of
            // unknown kind has neither, and gets the track count instead —
            // which by then is the one thing actually known about it.
            val subtitleText = target.subtitle.ifBlank {
                target.type.localizedNoun().replaceFirstChar { it.uppercase(Locale.getDefault()) }.ifBlank {
                    target.songs.size.takeIf { it > 0 }
                        ?.let { pluralStringResource(R.plurals.song_count_plural, it, it) }
                        .orEmpty()
                }
            }
            val credit = target.credit?.takeIf { onArtistClick != null && it.text.isNotBlank() }
            val at = if (credit != null) target.subtitle.indexOf(credit.text) else -1
            if (credit != null && onArtistClick != null && at >= 0) {
                // The artist is the one tappable stretch of the same line. It sits a shade
                // heavier and brighter than the type and year beside it, and presses with
                // the usual ripple, so the line keeps its place and its length.
                Row(verticalAlignment = Alignment.CenterVertically) {
                    if (at > 0) SheetSubtitle(target.subtitle.substring(0, at))
                    Text(
                        text = credit.text,
                        style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.W500),
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier
                            .weight(1f, fill = false)
                            .clip(RoundedCornerShape(4.dp))
                            .clickable(onClick = onArtistClick),
                    )
                    val after = target.subtitle.substring(at + credit.text.length)
                    if (after.isNotEmpty()) SheetSubtitle(after)
                }
            } else {
                SheetSubtitle(subtitleText)
            }
        }
    }
}

@Composable
private fun SheetSubtitle(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        maxLines = 1,
        overflow = TextOverflow.Ellipsis,
    )
}
"""
sheet = sheet[:i1] + new_block + sheet[i2:]
sheet = sub(sheet, "private fun BrowseSheetHeader(target: BrowseTarget) {\n",
            "private fun BrowseSheetHeader(target: BrowseTarget, onArtistClick: (() -> Unit)? = null) {\n", "header signature")

# ---- DetailScreen.kt ----
detail = sub(detail, "import com.music.amusic.ui.components.CreditArtist\n",
             "import com.music.amusic.ui.components.BrowseCredit\nimport com.music.amusic.ui.components.CreditArtist\n", "import BrowseCredit")
detail = sub(detail, "\n/**\n * Album / artist / playlist page. Rendered inside the main content area", """
/**
 * The artist line of a release page's three-dots menu: the part of the subtitle that names
 * the artist, found the way [headerLines] finds the page's own credit (everything that is
 * neither the year nor the kind), and the artists it opens. Several artists in the credit
 * come from [creditArtistsOf]; a single one is the first track's artist and channel, the same
 * one a tap on the name on the page opens. Null without a channel id to open by.
 */
internal fun releaseMenuCredit(subtitle: String, songs: List<Song>): BrowseCredit? {
    val parts = subtitle.split("•", "·").map { it.trim() }.filter { it.isNotEmpty() }
    val year = parts.lastOrNull { it.length == 4 && it.all(Char::isDigit) }
    val kind = parts.firstOrNull { it.lowercase(Locale.ROOT) in KIND_WORDS }
    val creditParts = parts.filter { it != year && it != kind }
    val text = creditParts.firstOrNull() ?: return null
    val shared = creditArtistsOf(songs, creditParts.joinToString(", "))
    if (shared.size > 1) return BrowseCredit(text, shared)
    val lead = songs.firstOrNull() ?: return null
    val id = lead.artistId ?: return null
    return BrowseCredit(text, listOf(CreditArtist(name = lead.artist, browseId = id)))
}

/**
 * Album / artist / playlist page. Rendered inside the main content area""", "releaseMenuCredit")
# ---- MainActivity.kt ----
main = sub(main, "import com.music.amusic.ui.screens.sortedForDetail\n",
           "import com.music.amusic.ui.screens.sortedForDetail\nimport com.music.amusic.ui.screens.releaseMenuCredit\n", "import releaseMenuCredit")
main = sub(main, "                                                fromCard = false,\n                                                downloadId = downloadIdFor(detail.browseId),\n",
           "                                                credit = if (detailIsLibraryArtist) null else releaseMenuCredit(detail.subtitle, releaseSongs),\n                                                fromCard = false,\n                                                downloadId = downloadIdFor(detail.browseId),\n", "target credit")
main = sub(main, "                onSort = if (target.type == BrowseType.ALBUM && !target.fromCard) ({\n                    browseActions = null\n                    songSortMenuOpen = true\n                }) else null,\n",
           """                onSort = if (target.type == BrowseType.ALBUM && !target.fromCard) ({
                    browseActions = null
                    songSortMenuOpen = true
                }) else null,
                // The artist's name in the header, opened by the id that came with the
                // release. Closes the sheet first, as every other row here does.
                onOpenArtist = target.credit?.let {
                    { id: String, name: String ->
                        browseActions = null
                        viewModel.openDetail(id, name, "Artist", null, BrowseType.ARTIST)
                    }
                },
""", "onOpenArtist call")

write(SHEET, sheet)
write(DETAIL, detail)
write(MAIN, main)
print("patched")
