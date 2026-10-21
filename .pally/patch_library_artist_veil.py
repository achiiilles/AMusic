import io, sys
P = "app/src/main/java/com/music/amusic/MainActivity.kt"
s = io.open(P, encoding="utf-8", newline="").read()

old1 = "                    pageVeil = isDetailVisible || isLocalArtistPageVisible,\npageColor = if (isLocalArtistPageVisible) detailPalette.background else chromeButtonColor,\n"
new1 = ("                    pageVeil = isDetailVisible || isLocalArtistPageVisible || isLibraryArtistPageVisible,\n"
        "pageColor = when {\n"
        "    isLocalArtistPageVisible -> detailPalette.background\n"
        "    isLibraryArtistPageVisible -> detailPalette.wash\n"
        "    else -> chromeButtonColor\n"
        "},\n")
old2 = "!showAccountScrobbling && !showSources && !showListenTogether && !showWearOs && !showEqualizer && !showReplay\n                // This is the bottom floor itself turned upside down"
new2 = ("!showAccountScrobbling && !showSources && !showListenTogether && !showWearOs && !showEqualizer && !showReplay\n"
        "// The library's own artist page (opened from Na sua biblioteca) has a browse type that is neither album, playlist nor artist, so isDetailVisible is false for it. It is drawn in the flat wash like a public artist page, so its back button and top pill wear that wash.\n"
        "val isLibraryArtistPageVisible = detail != null && detailIsLibraryArtist && !isLocalDetail &&\n"
        "    !showDiscord && !showHistory && !showSettings &&\n"
        "    !showAccountScrobbling && !showSources && !showListenTogether && !showWearOs && !showEqualizer && !showReplay\n"
        "                // This is the bottom floor itself turned upside down")
for o in (old1, old2):
    if s.count(o) != 1:
        sys.exit("anchor not found exactly once")
s = s.replace(old1, new1).replace(old2, new2)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("patched")
