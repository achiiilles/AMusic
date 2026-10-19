import sys

APP = "app/src/main/java/com/music/amusic/data/settings/AppSettings.kt"
VM = "app/src/main/java/com/music/amusic/ui/MainViewModel.kt"


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        print("FAIL", label, "matches:", n)
        sys.exit(1)
    return text.replace(old, new)


with open(APP, encoding="utf-8") as f:
    app = f.read()

app = replace_once(
    app,
    "    fun setLyricsSourceOrder(value: List<LyricsSource>) {",
    """    /**
     * The lyrics source the listener picked by hand for one particular track,
     * or null when they never did. Kept per track id so the choice is still
     * there the next time that song plays; a name that no longer exists, or a
     * source that is now hidden, reads back as no choice at all.
     */
    fun lyricsSourceForTrack(videoId: String): LyricsSource? {
        if (videoId.isBlank()) return null
        val name = prefs.getString(KEY_LYRICS_SOURCE_TRACK_PREFIX + videoId, null) ?: return null
        return LyricsSource.entries.firstOrNull { it.name == name && !it.hidden }
    }

    fun setLyricsSourceForTrack(videoId: String, source: LyricsSource) {
        if (videoId.isBlank()) return
        prefs.edit().putString(KEY_LYRICS_SOURCE_TRACK_PREFIX + videoId, source.name).apply()
    }

    fun setLyricsSourceOrder(value: List<LyricsSource>) {""",
    "app-fun",
)
app = replace_once(
    app,
    '    private const val KEY_LYRICS_SOURCE_ORDER = "lyrics_source_order"\n',
    '    private const val KEY_LYRICS_SOURCE_ORDER = "lyrics_source_order"\n'
    '    private const val KEY_LYRICS_SOURCE_TRACK_PREFIX = "lyrics_source_track_"\n',
    "app-key",
)
with open(APP, "w", encoding="utf-8") as f:
    f.write(app)

with open(VM, encoding="utf-8") as f:
    vm = f.read()

vm = replace_once(
    vm,
    "        selectedLyricsSource = null\n        manualLyricsJobs.values.forEach(Job::cancel)",
    """        // The source the listener picked for this exact track the last time it
        // played. It is asked first below, and shown as soon as it answers; when
        // it is switched off in Settings or finds nothing, the usual order and
        // the usual winner apply.
        val rememberedSource = AppSettings.lyricsSourceForTrack(videoId)?.takeIf { it in sources }
        selectedLyricsSource = rememberedSource
        manualLyricsJobs.values.forEach(Job::cancel)""",
    "vm-load",
)
vm = replace_once(
    vm,
    "                AppSettings.lyricsSourceOrder.value, AppSettings.prioritizeSyllableSync.value,",
    """                rememberedSource
                    ?.let { first -> listOf(first) + AppSettings.lyricsSourceOrder.value.filter { it != first } }
                    ?: AppSettings.lyricsSourceOrder.value,
                AppSettings.prioritizeSyllableSync.value,""",
    "vm-order",
)
vm = replace_once(
    vm,
    "        val request = currentLyricsRequest ?: return\n        when (_lyricsProviderStates.value[source]) {",
    """        val request = currentLyricsRequest ?: return
        // A manual pick is remembered for this track. A provider already known
        // to have nothing is inert, so it is not saved either.
        if (_lyricsProviderStates.value[source] != LyricsProviderState.NOT_FOUND) {
            AppSettings.setLyricsSourceForTrack(request.videoId, source)
        }
        when (_lyricsProviderStates.value[source]) {""",
    "vm-select",
)
with open(VM, "w", encoding="utf-8") as f:
    f.write(vm)
print("OK")
