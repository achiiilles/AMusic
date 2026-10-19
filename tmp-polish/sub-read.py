
import re, difflib
p = "shared/src/jvmSharedMain/kotlin/com/music/amusic/data/innertube/InnertubeParser.kt"
s = open(p, encoding="utf-8").read()
orig = s
log = []
old1 = "it.lowercase() !in TYPE_WORDS && !it.matches(TALLY) && !it.matches(DURATION)"
new1 = "it.lowercase() !in TYPE_WORDS && it.lowercase(Locale.ROOT) !in LOCALIZED_TYPE_WORDS && !it.matches(TALLY) && !it.matches(DURATION)"
log.append("old1 count=%d" % s.count(old1))
rx = re.compile(r"^([ \t]*)private val TYPE_WORDS = setOf\(", re.M)
log.append("type_words matches=%d" % len(rx.findall(s)))
if s.count(old1) == 1 and len(rx.findall(s)) == 1 and "LOCALIZED_TYPE_WORDS" not in s:
    s = s.replace(old1, new1)
    def ins(m):
        i = m.group(1)
        block = [
            "/**",
            " * Type labels YouTube writes in the listener's language (\"Música\", \"Álbum\"). Only",
            " * [artistFromSubtitle] reads this: a shelf card's subtitle leads with the type,",
            " * and outside English that label would be taken for the artist.",
            " */",
            "private val LOCALIZED_TYPE_WORDS = setOf(",
            "    \"música\", \"musica\", \"canção\", \"cancao\", \"canción\", \"cancion\", \"chanson\", \"titre\",",
            "    \"vídeo\", \"álbum\", \"sencillo\", \"artista\", \"artiste\",",
            "    \"lista de reprodução\", \"lista de reproducción\", \"lista de reproduccion\",",
            "    \"episódio\", \"episodio\", \"épisode\",",
            "    \"bài hát\", \"đĩa đơn\", \"danh sách phát\",",
            "    \"曲\", \"シングル\", \"再生リスト\", \"アルバム\", \"アーティスト\", \"動画\",",
            ")",
        ]
        return "\n".join(i + b for b in block) + "\n" + i + "private val TYPE_WORDS = setOf("
    s = rx.sub(ins, s, count=1)
    open(p, "w", encoding="utf-8").write(s)
    log.append("PATCHED")
else:
    log.append("NOT PATCHED")
d = "".join(difflib.unified_diff(orig.splitlines(True), s.splitlines(True), "before", "after", n=2))
open("tmp-polish/out.txt", "w", encoding="utf-8").write("\n".join(log) + "\n" + d)
