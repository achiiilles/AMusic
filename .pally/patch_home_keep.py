import io, sys
P = "app/src/main/java/com/music/amusic/MainActivity.kt"
s = io.open(P, encoding="utf-8").read()
old = ("    LaunchedEffect(currentFeed) {\n"
       "        if (currentFeed == MainViewModel.Feed.HOME) viewModel.onHomeShown()\n")
new = ("    // Home is no longer re-fetched when it comes back into view (from an album, or from another tab): after any play that re-fetch replaced the whole feed under the reader. Pull-to-refresh still re-fetches. Set to true to restore the old behaviour.\n"
       "    val refreshHomeOnShow = false\n"
       "    LaunchedEffect(currentFeed) {\n"
       "        if (refreshHomeOnShow && currentFeed == MainViewModel.Feed.HOME) viewModel.onHomeShown()\n")
if s.count(old) != 1:
    sys.exit("anchor not found exactly once")
s = s.replace(old, new)
io.open(P, "w", encoding="utf-8", newline="").write(s)
print("patched")
