#!/usr/bin/env python3
# Temporary, applied once by the pally workflow: anchored edits only.
import pathlib, sys

NL = chr(10)
DETAIL = pathlib.Path("app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt")

BLOCK = '''    // "Videoclipes": the album's music videos, found one track at a time by a
    // YouTube search (YouTube Music does not send them with the album). Empty
    // until (and unless) a clip is found, so the page reads as before; the
    // section fades in when it arrives. A section YouTube itself sent wins.
    val clipsEligible = page.type == BrowseType.ALBUM && !artistColours && folder == null && !isPreRelease &&
        page.browseId.orEmpty().let { it.startsWith("MPRE") || it.startsWith("OLAK") || it.startsWith("VLOLAK") } &&
        page.sections.none { it.title.trim().equals(AlbumMusicVideos.TITLE, ignoreCase = true) }
    var albumClips by remember(page.browseId) {
        mutableStateOf(
            if (clipsEligible) AlbumMusicVideos.cached(page.browseId.orEmpty()) else emptyList<HomeShelf>(),
        )
    }
    LaunchedEffect(page.browseId, appleAlbumCredit, clipsEligible, rawSongs.size) {
        if (!clipsEligible || rawSongs.isEmpty()) return@LaunchedEffect
        albumClips = AlbumMusicVideos.clipsFor(page.browseId.orEmpty(), appleAlbumCredit, rawSongs) ?: albumClips
    }
    val clipsAlpha by animateFloatAsState(
        targetValue = if (albumClips.isNotEmpty()) 1f else 0f,
        animationSpec = tween(durationMillis = 350, easing = FastOutSlowInEasing),
    )
'''


def once(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit("anchor for " + what + " found " + str(n) + " times")
    return text.replace(old, new)


text = DETAIL.read_text(encoding="utf-8")
imp = "import com.music.amusic.data.canvas.AppleAlbumShelves" + NL
text = once(text, imp, "import com.music.amusic.data.canvas.AlbumMusicVideos" + NL + imp, "import")
anchor = "    val appleAlbum = appleAlbumResult?.colors" + NL
text = once(text, anchor, BLOCK + anchor, "state block")
text = once(text, "items(visibleSections + appleShelves) { shelf ->",
            "items(visibleSections + albumClips + appleShelves) { shelf ->", "items")
i = text.index("items(visibleSections + albumClips + appleShelves) { shelf ->")
col = "Column(Modifier.padding(top = 22.dp)) {"
j = text.index(col, i)
if j - i > 600 or text.count(col) != 1:
    sys.exit("shelf column anchor moved")
pad = " " * 16
fade = (
    "val isClipShelf = albumClips.contains(shelf)" + NL
    + pad + "Column(" + NL
    + pad + "    Modifier" + NL
    + pad + "        .padding(top = 22.dp)" + NL
    + pad + "        .graphicsLayer { this.alpha = if (isClipShelf) clipsAlpha else 1f }," + NL
    + pad + ") {"
)
text = text[:j] + fade + text[j + len(col):]
DETAIL.write_text(text, encoding="utf-8")
print("ok")
