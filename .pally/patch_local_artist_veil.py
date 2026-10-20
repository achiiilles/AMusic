import io, sys
P = "app/src/main/java/com/music/amusic/MainActivity.kt"
s = io.open(P, encoding="utf-8").read()

old1 = "                    pageVeil = isDetailVisible,\npageColor = chromeButtonColor,\n"
new1 = ("                    pageVeil = isDetailVisible || isLocalArtistPageVisible,\n"
        "pageColor = if (isLocalArtistPageVisible) detailPalette.background else chromeButtonColor,\n")
old2 = "    chromePageColor\n}\n                // This is the bottom floor itself turned upside down"
new2 = ("    chromePageColor\n}\n"
        "// A folder's artist page (Local Music) is drawn in the palette background like an album, so its top circles wear that same page colour.\n"
        "val isLocalArtistPageVisible = detail != null && LocalGroups.isArtist(detail.browseId) &&\n"
        "    !showDiscord && !showHistory && !showSettings &&\n"
        "    !showAccountScrobbling && !showSources && !showListenTogether && !showWearOs && !showEqualizer && !showReplay\n"
        "                // This is the bottom floor itself turned upside down")
for o in (old1, old2):
    if s.count(o) != 1:
        sys.exit("anchor not found exactly once")
s = s.replace(old1, new1).replace(old2, new2)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("patched")
