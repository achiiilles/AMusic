package com.music.amusic.data.canvas

import android.content.Context
import org.json.JSONObject
import java.io.File
import java.security.MessageDigest

/**
 * A small on-disk memory for the Apple lookups, so an album or an artist that was
 * already looked up shows at once the next time, even after the app was closed.
 *
 * It lives in the cache folder: Android may empty it when the phone needs room, and
 * the lookups then simply run again. Every read and write is best effort and never
 * throws; without [init] it does nothing and the callers behave as they did before.
 * Entries older than a month are removed when the app starts.
 */
object AppleLookupStore {

    private const val DAY_MS = 24L * 60 * 60 * 1000
    private const val PRUNE_AFTER_MS = 30L * DAY_MS

    /** An artist's list of releases can gain a new one, so it is kept for a short while. */
    const val DISCOGRAPHY_MAX_AGE_MS = 3L * DAY_MS

    /** Artist ids and the song names of a release do not change. */
    const val STABLE_MAX_AGE_MS = 30L * DAY_MS

    const val ALBUM_MAX_AGE_MS = 14L * DAY_MS

    /** "Apple has no colours for it" is only trusted for a few hours. */
    const val ALBUM_NO_COLOURS_MAX_AGE_MS = 6L * 60 * 60 * 1000

    const val ARTIST_ART_MAX_AGE_MS = 7L * DAY_MS

    @Volatile
    private var dir: File? = null

    /** Called once from [CanvasCache.init], which already runs when the app starts. */
    fun init(context: Context) {
        runCatching {
            val folder = File(context.cacheDir, "apple-lookups")
            folder.mkdirs()
            dir = folder
            val pruneThread = Thread {
                runCatching {
                    val limit = System.currentTimeMillis() - PRUNE_AFTER_MS
                    folder.listFiles()?.forEach { file ->
                        if (file.lastModified() < limit) file.delete()
                    }
                }
            }
            pruneThread.isDaemon = true
            pruneThread.start()
        }
    }

    private fun fileFor(folder: File, key: String): File {
        val digest = MessageDigest.getInstance("SHA-1").digest(key.toByteArray(Charsets.UTF_8))
        val name = digest.joinToString("") { byte -> "%02x".format(byte) }
        return File(folder, name)
    }

    /** The text saved under [key] if it is younger than [maxAgeMs], else null. */
    fun read(key: String, maxAgeMs: Long): String? {
        val folder = dir ?: return null
        return runCatching {
            val file = fileFor(folder, key)
            if (!file.isFile) return@runCatching null
            if (System.currentTimeMillis() - file.lastModified() > maxAgeMs) return@runCatching null
            file.readText()
        }.getOrNull()
    }

    fun write(key: String, value: String) {
        val folder = dir ?: return
        runCatching {
            val file = fileFor(folder, key)
            val temp = File(folder, file.name + "." + System.nanoTime() + ".tmp")
            temp.writeText(value)
            if (!temp.renameTo(file)) {
                file.delete()
                if (!temp.renameTo(file)) temp.delete()
            }
        }
    }

    // ---- Album and single colours --------------------------------------

    fun readAlbum(browseId: String): AppleAlbumColorsResult? {
        val text = read("album:$browseId", ALBUM_MAX_AGE_MS) ?: return null
        return runCatching {
            val json = JSONObject(text)
            val colors = if (json.has("bg")) {
                AppleAlbumColors(json.getInt("bg"), json.getInt("accent"))
            } else {
                null
            }
            val savedAt = json.optLong("at", 0L)
            // An empty answer saved before "v" existed may come from a credit with several
            // artists that was read as one name; it is asked again.
            if (colors == null && json.optInt("v", 0) < 3) return@runCatching null
            if (colors == null && System.currentTimeMillis() - savedAt > ALBUM_NO_COLOURS_MAX_AGE_MS) {
                return@runCatching null
            }
            AppleAlbumColorsResult(
                colors = colors,
                genre = json.optString("genre").ifBlank { null },
                releaseYear = json.optString("year").ifBlank { null },
                releaseDate = json.optString("date").ifBlank { null },
                copyright = json.optString("copyright").ifBlank { null },
                recordLabel = json.optString("label").ifBlank { null },
            )
        }.getOrNull()
    }

    fun writeAlbum(browseId: String, result: AppleAlbumColorsResult) {
        runCatching {
            val json = JSONObject()
            json.put("at", System.currentTimeMillis())
            json.put("v", 3)
            result.colors?.let { colors ->
                json.put("bg", colors.background)
                json.put("accent", colors.accent)
            }
            result.genre?.let { json.put("genre", it) }
            result.releaseYear?.let { json.put("year", it) }
            result.releaseDate?.let { json.put("date", it) }
            result.copyright?.let { json.put("copyright", it) }
            result.recordLabel?.let { json.put("label", it) }
            write("album:$browseId", json.toString())
        }
    }

    // ---- Artist page header --------------------------------------------

    fun readArtist(key: String): AppleArtistArt? {
        val text = read("artist-art:$key", ARTIST_ART_MAX_AGE_MS) ?: return null
        return runCatching {
            val json = JSONObject(text)
            AppleArtistArt(
                heroUrl = json.getString("hero"),
                logoUrl = json.optString("logo").ifBlank { null },
                logoAspect = json.optDouble("aspect", 1.0).toFloat(),
                videoUrl = json.optString("video").ifBlank { null },
                background = json.getInt("bg"),
                accent = json.getInt("accent"),
                keyColor = if (json.has("key")) json.getInt("key") else null,
            )
        }.getOrNull()
    }

    fun writeArtist(key: String, art: AppleArtistArt) {
        runCatching {
            val json = JSONObject()
            json.put("hero", art.heroUrl)
            art.logoUrl?.let { json.put("logo", it) }
            json.put("aspect", art.logoAspect.toDouble())
            art.videoUrl?.let { json.put("video", it) }
            json.put("bg", art.background)
            json.put("accent", art.accent)
            art.keyColor?.let { json.put("key", it) }
            write("artist-art:$key", json.toString())
        }
    }
}
