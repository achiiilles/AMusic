from pathlib import Path

def edit(path, old, new):
    p = Path(path)
    s = p.read_text()
    if new in s:
        return
    assert s.count(old) == 1, (path, s.count(old), old[:100])
    p.write_text(s.replace(old, new))

base = 'shared/src/'
edit(base+'commonMain/kotlin/com/music/amusic/data/model/Models.kt',
    '    val playbackSourceId: String? = null,\n  ) {', '') if False else None
edit(base+'commonMain/kotlin/com/music/amusic/data/model/Models.kt',
    '    val playbackSourceId: String? = null,\n) {',
    '    val playbackSourceId: String? = null,\n    /** Public YouTube Music plays, never this device\'s listening count. */\n    val playCount: Long? = null,\n) {')
p = base+'jvmSharedMain/kotlin/com/music/amusic/data/innertube/InnertubeParser.kt'
edit(p, '            isExplicit = renderer.hasExplicitBadge(),\n        )',
    '            isExplicit = renderer.hasExplicitBadge(),\n            playCount = columns.drop(1).firstNotNullOfOrNull { column ->\n                playCountOf(column.o("musicResponsiveListItemFlexColumnRenderer").o("text").runs())\n            },\n        )')
# Keep the existing tally test and add the localised play-count test.
old = '!it.matches(DURATION) && it.lowercase(Locale.ROOT) !in TYPE_WORDS && !it.matches(TALLY)'
s = Path(p).read_text()
new = old+' && playCountOf(it) == null'
if new not in s:
    assert s.count(old) == 2
    Path(p).write_text(s.replace(old, new))
helper = '''    /** Parses public per-track labels, including "Tocou 763 mi vezes". */
    fun playCountOf(text: String): Long? {
        val value = text.replace('\u00a0', ' ').replace('\u202f', ' ').trim()
        val match = PUBLIC_PLAYS.matchEntire(value) ?: return null
        val raw = match.groupValues[1].replace(" ", "")
        val suffix = match.groupValues[2].lowercase(Locale.ROOT)
        val multiplier = when (suffix) {
            "k", "mil", "thousand" -> 1_000.0
            "m", "mi", "million", "millions", "milhão", "milhões", "milhao", "milhoes" -> 1_000_000.0
            "b", "bi", "billion", "billions", "bilhão", "bilhões", "bilhao", "bilhoes" -> 1_000_000_000.0
            else -> 1.0
        }
        val numeric = if (suffix.isNotEmpty()) {
            val split = maxOf(raw.lastIndexOf(','), raw.lastIndexOf('.'))
            if (split >= 0) raw.take(split).filter(Char::isDigit) + "." + raw.drop(split + 1)
            else raw
        } else {
            if (!raw.matches(Regex("""\\d{1,3}(?:[.,]\\d{3})+|\\d+"""))) return null
            raw.filter(Char::isDigit)
        }
        val count = (numeric.toDoubleOrNull() ?: return null) * multiplier
        return count.takeIf { it.isFinite() && it >= 0 && it < Long.MAX_VALUE.toDouble() }?.toLong()
    }

    private val PUBLIC_PLAYS = Regex(
        """(?:tocou\\s+)?([\\d][\\d., ]*?)\\s*(k|m|b|mi|mil|bi|thousand|millions?|billions?|milh(?:ão|ões|ao|oes)|bilh(?:ão|ões|ao|oes))?\\s*(?:plays?|views?|vezes|reproduç(?:ão|ões)|reproduc(?:ao|oes)|visualizaç(?:ão|ões)|visualizac(?:ao|oes))""",
        RegexOption.IGNORE_CASE,
    )

'''
edit(p, '    private val DURATION = Regex', helper+'    private val DURATION = Regex')
p = base+'jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt'
edit(p, '        return pageOf(playlist).copy(\n            library = metadata.library,',
    '        val counts = metadata.songs.associate { it.videoId to it.playCount }\n        val listing = pageOf(playlist)\n        return listing.copy(\n            songs = listing.songs.map { song -> song.copy(playCount = counts[song.videoId] ?: song.playCount) },\n            library = metadata.library,')
