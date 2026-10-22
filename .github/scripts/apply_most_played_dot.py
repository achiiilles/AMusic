"""Apply the most-played dot to Common.kt on this branch, once.

Temporary helper: the GitHub file API only takes a whole file and Common.kt is
43 KB, so this makes the four small edits in place on the checked-out copy and
fails loudly if any anchor is missing or ambiguous.
"""
import io
import sys

PATH = "sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/components/Common.kt"

with io.open(PATH, encoding="utf-8") as fh:
    source = fh.read()


def apply(source, old, new, label):
    count = source.count(old)
    if count != 1:
        sys.exit("anchor %s matched %d times, expected 1" % (label, count))
    return source.replace(old, new)


old_imports = "import androidx.compose.animation.core.animateFloatAsState\n"
new_imports = (
    old_imports
    + "import androidx.compose.animation.core.tween\n"
    + "import androidx.compose.foundation.layout.offset\n"
)
source = apply(source, old_imports, new_imports, "imports")

old_width = "val TRACK_NUMBER_WIDTH = 24.dp\n"
new_width = old_width + """
/**
 * The dot Apple Music puts beside the number of a release's most-played track.
 *
 * Small, in the number's own colour, and hung just outside the number column:
 * the row is marked without the digit or the title moving.
 */
val MOST_PLAYED_DOT_SIZE = 6.dp

/** How far the dot hangs left of the number column, out into the row's gutter. */
val MOST_PLAYED_DOT_OUTSET = 8.dp

/** Length of the dot's fade: short and quiet, the mark settling as the row arrives. */
private const val MOST_PLAYED_DOT_FADE_MS = 180
"""
source = apply(source, old_width, new_width, "number width")

old_unavailable = "    val unavailable = song.isMatchMissing\n"
new_unavailable = old_unavailable + """    // Apple Music dots the release's most-played track. Only a numbered release
    // row asks the host, so the flat feeds pay nothing for the question.
    val mostPlayedIds = if (trackNumber != null) AppUi.host.mostPlayedTrackIds() else emptySet()
    val mostPlayed = song.videoId in mostPlayedIds
    val mostPlayedAlpha by animateFloatAsState(
        targetValue = if (mostPlayed) 1f else 0f,
        animationSpec = tween(MOST_PLAYED_DOT_FADE_MS),
        label = "most played dot",
    )
"""
source = apply(source, old_unavailable, new_unavailable, "unavailable")

old_number = '''                    Text(
                        text = "$trackNumber",
                        style = trackNumberStyle,
                        color = subtitleColor,
                        maxLines = 1,
                    )
'''
new_number = old_number + '''                    if (mostPlayed) {
                        // The dot hangs into the row's gutter instead of taking
                        // width, so the number and the title stay put.
                        Box(
                            Modifier
                                .align(Alignment.CenterStart)
                                .offset(x = -MOST_PLAYED_DOT_OUTSET)
                                .size(MOST_PLAYED_DOT_SIZE)
                                .alpha(mostPlayedAlpha)
                                .clip(CircleShape)
                                .background(subtitleColor),
                        )
                    }
'''
source = apply(source, old_number, new_number, "track number")

with io.open(PATH, "w", encoding="utf-8") as fh:
    fh.write(source)

print("applied 4 edits")
