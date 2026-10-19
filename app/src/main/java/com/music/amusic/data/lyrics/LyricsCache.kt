package com.music.amusic.data.lyrics

import android.content.Context
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * Lyrics that were found once, kept on the device so that coming back to a
 * track opens them at once instead of asking the databases again.
 *
 * One small JSON file per track under the app's files directory, so it
 * survives closing the app. Each entry records the lyrics, the [LyricsSource]
 * that answered, and [Entry.pick]: the source the listener had chosen by hand
 * for that track when the entry was written, or empty when the lookup ran
 * on its own (automatic, by the order of the list).
 *
 * The caller only trusts an entry whose pick equals the track's current manual
 * choice. So a hand-picked source always wins over an automatic result: picking
 * another source makes the old entry stale, the new source is fetched, and its
 * answer overwrites the entry.
 *
 * Bounded: past [MAX_ENTRIES] tracks the least recently opened files are
 * removed. Never throws; an unreadable file is dropped and counts as a miss.
 * A translation overlay (timingSource) is display-only and is not stored.
 */
object LyricsCache {

    class Entry(val source: LyricsSource, val pick: String, val lines: List<LyricLine>)

    const val MAX_ENTRIES = 200
    private const val DIR = "lyrics_cache"
    private const val VERSION = 1
    private val lock = Any()

    private fun directory(context: Context) = File(context.filesDir, DIR)

    private fun fileFor(context: Context, videoId: String): File {
        val safe = videoId.replace(Regex("[^A-Za-z0-9_-]"), "_").take(64)
        return File(directory(context), safe + "_" + Integer.toHexString(videoId.hashCode()) + ".json")
    }

    suspend fun read(context: Context, videoId: String): Entry? = withContext(Dispatchers.IO) {
        if (videoId.isEmpty()) return@withContext null
        val file = fileFor(context, videoId)
        synchronized(lock) {
            if (!file.isFile) return@synchronized null
            try {
                val entry = decode(file.readText(), videoId)
                if (entry == null) file.delete() else file.setLastModified(System.currentTimeMillis())
                entry
            } catch (_: Exception) {
                file.delete()
                null
            }
        }
    }

    suspend fun write(
        context: Context,
        videoId: String,
        source: LyricsSource,
        pick: String,
        lines: List<LyricLine>,
    ) {
        if (videoId.isEmpty() || lines.isEmpty()) return
        withContext(Dispatchers.IO) {
            try {
                val json = encode(videoId, source, pick, lines)
                synchronized(lock) {
                    val dir = directory(context)
                    dir.mkdirs()
                    val file = fileFor(context, videoId)
                    val temp = File(dir, file.name + ".tmp")
                    temp.writeText(json)
                    if (!temp.renameTo(file)) {
                        file.delete()
                        temp.renameTo(file)
                    }
                    trim(dir)
                }
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
            }
        }
    }

    private fun trim(dir: File) {
        val all = dir.listFiles() ?: return
        all.filter { it.name.endsWith(".tmp") }.forEach { it.delete() }
        val saved = all.filter { it.name.endsWith(".json") }
        if (saved.size <= MAX_ENTRIES) return
        saved.sortedBy { it.lastModified() }.take(saved.size - MAX_ENTRIES).forEach { it.delete() }
    }

    private fun encode(videoId: String, source: LyricsSource, pick: String, lines: List<LyricLine>): String =
        JSONObject()
            .put("v", VERSION)
            .put("id", videoId)
            .put("source", source.name)
            .put("pick", pick)
            .put("lines", JSONArray(lines.map { encodeLine(it) }))
            .toString()

    private fun encodeLine(line: LyricLine): JSONObject {
        val o = JSONObject()
        o.put("t", line.timeMs)
        o.put("x", line.text)
        if (line.words.isNotEmpty()) o.put("w", JSONArray(line.words.map { encodeWord(it) }))
        line.sungUntilMs?.let { o.put("u", it) }
        line.background?.let { o.put("b", encodeLine(it)) }
        if (line.alignment != LyricAlignment.Start) o.put("a", line.alignment.name)
        return o
    }

    private fun encodeWord(word: LyricWord): JSONObject {
        val o = JSONObject()
        o.put("s", word.startMs)
        o.put("e", word.endMs)
        o.put("x", word.text)
        if (word.syllables.isNotEmpty()) {
            o.put(
                "y",
                JSONArray(
                    word.syllables.map {
                        JSONArray(listOf(it.startMs, it.endMs, it.startChar.toLong(), it.endChar.toLong()))
                    },
                ),
            )
        }
        return o
    }

    private fun decode(text: String, videoId: String): Entry? {
        val root = JSONObject(text)
        if (root.optInt("v") != VERSION || root.optString("id") != videoId) return null
        val name = root.optString("source")
        val source = LyricsSource.entries.firstOrNull { it.name == name && !it.hidden } ?: return null
        val array = root.getJSONArray("lines")
        val lines = List(array.length()) { decodeLine(array.getJSONObject(it)) }
        if (lines.isEmpty()) return null
        return Entry(source, root.optString("pick"), lines)
    }

    private fun decodeLine(o: JSONObject): LyricLine {
        val wordsJson = o.optJSONArray("w")
        val words = if (wordsJson == null) {
            emptyList()
        } else {
            List(wordsJson.length()) { decodeWord(wordsJson.getJSONObject(it)) }
        }
        return LyricLine(
            timeMs = o.getLong("t"),
            text = o.getString("x"),
            words = words,
            sungUntilMs = if (o.has("u")) o.getLong("u") else null,
            background = o.optJSONObject("b")?.let { decodeLine(it) },
            alignment = if (o.optString("a") == LyricAlignment.End.name) LyricAlignment.End else LyricAlignment.Start,
        )
    }

    private fun decodeWord(o: JSONObject): LyricWord {
        val parts = o.optJSONArray("y")
        val syllables = if (parts == null) {
            emptyList()
        } else {
            List(parts.length()) {
                val p = parts.getJSONArray(it)
                LyricSyllable(p.getLong(0), p.getLong(1), p.getInt(2), p.getInt(3))
            }
        }
        return LyricWord(
            startMs = o.getLong("s"),
            endMs = o.getLong("e"),
            text = o.getString("x"),
            syllables = syllables,
        )
    }
}
