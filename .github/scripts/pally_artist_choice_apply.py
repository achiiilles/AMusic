import sys

PATH = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'

EDITS = []

EDITS.append((r'''import com.music.amusic.ui.components.liquidGlassRim
''', r'''import com.music.amusic.ui.components.liquidGlassRim
import com.music.amusic.ui.components.ArtistChoiceSheet
import com.music.amusic.ui.components.CreditArtist
'''))

EDITS.append((r'''private fun String.looksLikeCredit() = CREDIT_SEPARATOR.containsMatchIn(this)
''', r'''private fun String.looksLikeCredit() = CREDIT_SEPARATOR.containsMatchIn(this)

/**
 * The same split as [CREDIT_SEPARATOR] plus the "and" of the other languages YouTube
 * writes a shared credit in ("Olivia Rodrigo e Chappell Roan"), used only to list the
 * artists a credit names.
 */
private val CREDIT_CHOICE_SEPARATOR = Regex(
    """,\s*|\s&\s|\s(?:x|e|and|y|und|et|feat\.?|ft\.?|with)\s""",
    RegexOption.IGNORE_CASE,
)

/**
 * Each artist of a shared credit, with their own channel where the page's tracks said
 * which one it is. Empty when the credit names one artist, including a single name that
 * itself contains a separator ("Tyler, The Creator"), so a one-artist page keeps its
 * plain tap. The lead's channel is the first track's [Song.artistId].
 */
private fun creditArtistsOf(songs: List<Song>, credit: String): List<CreditArtist> {
    val first = songs.firstOrNull() ?: return emptyList()
    val known = songs.flatMap { it.artists }
    if (known.any { it.name.equals(credit.trim(), ignoreCase = true) }) return emptyList()
    val names = credit.split(CREDIT_CHOICE_SEPARATOR)
        .map { it.trim() }
        .filter { it.isNotEmpty() }
        .distinctBy { it.lowercase() }
    if (names.size < 2) return emptyList()
    return names.mapIndexed { index, name ->
        val id = known.firstOrNull { it.name.equals(name, ignoreCase = true) && it.browseId != null }
            ?.browseId
            ?: if (index == 0) first.artistId else null
        CreditArtist(name = name, browseId = id)
    }
}
'''))

EDITS.append((r'''    val artist = songs.firstOrNull()

    Column(''', r'''    val artist = songs.firstOrNull()
    // More than one name in the credit: tapping it asks which artist to open.
    val creditArtists = remember(songs, credit, albumText) {
        if (albumText) creditArtistsOf(songs, credit) else emptyList()
    }
    var choosingArtist by remember { mutableStateOf(false) }

    Column('''))

EDITS.append((r'''                        val id = artist?.artistId
                        if (id == null || onArtistClick == null) {
                            m
                        } else {
                            m.clip(RoundedCornerShape(6.dp))
                                .clickable { onArtistClick(id, artist.artist) }
                        }
                    },
            )
        }
''', r'''                        val id = artist?.artistId
                        if (creditArtists.size > 1 && onArtistClick != null) {
                            m.clip(RoundedCornerShape(6.dp))
                                .clickable { choosingArtist = true }
                        } else if (id == null || onArtistClick == null) {
                            m
                        } else {
                            m.clip(RoundedCornerShape(6.dp))
                                .clickable { onArtistClick(id, artist.artist) }
                        }
                    },
            )
            if (choosingArtist && onArtistClick != null) {
                ArtistChoiceSheet(
                    artists = creditArtists,
                    onPick = onArtistClick,
                    onDismiss = { choosingArtist = false },
                )
            }
        }
'''))

with open(PATH, encoding='utf-8', newline='') as f:
    text = f.read()

for index, (old, new) in enumerate(EDITS, start=1):
    found = text.count(old)
    if found != 1:
        print('edit', index, 'matched', found, 'times, expected 1')
        sys.exit(1)
    text = text.replace(old, new)
    print('edit', index, 'applied')

with open(PATH, 'w', encoding='utf-8', newline='') as f:
    f.write(text)
print('DetailScreen.kt written')
