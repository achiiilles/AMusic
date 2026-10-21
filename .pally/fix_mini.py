import subprocess
P1 = 'app/src/main/java/com/music/amusic/ui/components/MiniPlayer.kt'
P2 = 'app/src/main/java/com/music/amusic/ui/components/GlassNavBar.kt'
BASE = '27cb9958399698457fdeb7cc6fbc08c524b86058'
subprocess.check_call(['git', 'checkout', BASE, '--', P1, P2])

def rep(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new)

mp = open(P1, encoding='utf-8').read()
mp = rep(mp, "    val sleeveTint = rememberArtworkBarColor(rememberRemoteArtworkUrl(song), ROW_ART_PX)\n",
"    // The sleeve's colour no longer tints the bar: the mini player now draws the\n    // same surface as the bottom navigation bar, light or dark with the theme.\n    // [rememberArtworkBarColor] and [artworkBarTint] are kept, just not used here.\n")
mp = rep(mp, "                        style = HazeMaterials.thin(MaterialTheme.colorScheme.surface),\n",
"                        style = HazeMaterials.regular(MaterialTheme.colorScheme.surface),\n")
mp = rep(mp, "            .artworkBarTint(sleeveTint)\n            .border(0.5.dp, Color.White.copy(alpha = 0.10f), shape)\n",
"            .border(GLASS_EDGE_WIDTH, GLASS_EDGE_COLOR, shape)\n")
open(P1, 'w', encoding='utf-8').write(mp)

gn = open(P2, encoding='utf-8').read()
gn = rep(gn, """    // The sleeve's colour under the now playing bar of the standard surface.
    // Text and symbols keep their colours; liquid glass is left as it is.
    val sleeveTint = if (plainSurface) {
        rememberArtworkBarColor(song?.let { rememberRemoteArtworkUrl(it) }, ROW_ART_PX)
    } else {
        null
    }
""", """    // No sleeve colour under the now playing bar any more: it draws the same
    // surface as the tab pill, following the theme. Kept as a null tint so the
    // colour path can be switched back on without rewriting the surface.
    val sleeveTint: androidx.compose.runtime.State<Color>? = null
""")
gn = rep(gn, "plainBarSurface(hazeState = hazeState, shape = pillShape, thin = true, tint = sleeveTint)",
"plainBarSurface(hazeState = hazeState, shape = pillShape, thin = false, tint = sleeveTint)")
gn = rep(gn, """    // The now playing pill: the plain mini player's thin frost over the tab
    // pill's regular one, as in the standard bars.""", """    // The now playing pill: the same regular frost as the tab pill, so the
    // two read as one colour in both themes.""")
open(P2, 'w', encoding='utf-8').write(gn)
