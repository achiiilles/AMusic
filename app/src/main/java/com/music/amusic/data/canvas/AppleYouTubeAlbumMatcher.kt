package com.music.amusic.data.canvas

/** The fields the album-search result actually gives this resolver. */
internal data class YouTubeAlbumCandidate(
    val browseId: String,
    val title: String,
    val subtitle: String,
)

/**
 * Conservative matching rules for an Apple recommendation and YouTube Music's
 * album-search cards. The browse card has no track list, so this deliberately
 * uses only the title, credited artist and metadata the card actually exposes.
 */
internal object AppleYouTubeAlbumMatcher {
    private val SUBTITLE_SEPARATOR = Regex("""\s*[•·|]\s*""")
    private val RELEASE_YEAR = Regex("""\b(?:19|20)\d{2}\b""")
    private val EDITION_MARK = Regex(
        """\b(?:deluxe|expanded|remaster(?:ed)?|anniversary|bonus|special|complete|explicit|clean|live|acoustic|instrumental|karaoke|remix|version|standard)\b""",
        RegexOption.IGNORE_CASE,
    )
    private val RELEASE_KINDS = setOf("album", "álbum", "single", "ep")

    /** Returns distinct compatible album ids; the caller opens one only if there is exactly one. */
    fun matchingBrowseIds(
        appleDisplayTitle: String,
        appleCatalogTitle: String,
        appleArtist: String,
        appleReleaseLine: String,
        candidates: Iterable<YouTubeAlbumCandidate>,
    ): List<String> {
        val wantedTitle = AppleReleaseMatcher.cleanTitle(appleDisplayTitle)
        if (wantedTitle.isBlank() || appleArtist.isBlank()) return emptyList()
        val wantedArtist = AppleReleaseMatcher.cleanTitle(appleArtist)
        return candidates.asSequence()
            .filter { it.browseId.startsWith("MPRE") }
            .filter { AppleReleaseMatcher.cleanTitle(it.title) == wantedTitle }
            .filter { hasExactArtist(it.subtitle, it.title, wantedArtist) }
            .filter { sameEdition(appleCatalogTitle, it.title) }
            .filter { sameYear(appleReleaseLine, it.subtitle) }
            .filter { sameReleaseKind(appleReleaseLine, it.subtitle) }
            .map { it.browseId }
            .distinct()
            .toList()
    }

    private fun hasExactArtist(subtitle: String, title: String, wanted: String): Boolean =
        subtitle.split(SUBTITLE_SEPARATOR).any { part ->
            val value = part.trim()
            value.isNotEmpty() &&
                !value.equals(title.trim(), ignoreCase = true) &&
                !RELEASE_YEAR.matches(value) &&
                value.lowercase() !in RELEASE_KINDS &&
                AppleReleaseMatcher.cleanTitle(value) == wanted
        }

    /** A marker is checked on the original titles, before display-title cleanup. */
    private fun sameEdition(appleTitle: String, youtubeTitle: String): Boolean =
        editionMarkers(appleTitle) == editionMarkers(youtubeTitle)

    private fun editionMarkers(title: String): Set<String> = EDITION_MARK
        .findAll(title)
        .map { match ->
            when (match.value.lowercase()) {
                "remastered" -> "remaster"
                else -> match.value.lowercase()
            }
        }
        .toSet()

    /** A year is a conflict only when both services include one. */
    private fun sameYear(appleDetails: String, youtubeDetails: String): Boolean {
        val appleYear = RELEASE_YEAR.find(appleDetails)?.value ?: return true
        val youtubeYear = RELEASE_YEAR.find(youtubeDetails)?.value ?: return true
        return appleYear == youtubeYear
    }

    /** Compare album/single/EP only when YouTube includes a matching metadata token. */
    private fun sameReleaseKind(appleDetails: String, youtubeDetails: String): Boolean {
        val appleKind = releaseKind(appleDetails) ?: return true
        val youtubeKind = releaseKind(youtubeDetails) ?: return true
        return appleKind == youtubeKind
    }

    private fun releaseKind(details: String): String? = details
        .split(SUBTITLE_SEPARATOR)
        .asSequence()
        .map { it.trim().lowercase() }
        .firstOrNull { it in RELEASE_KINDS }
        ?.let { if (it == "álbum") "album" else it }

    /** Requires both complete lists to contain the same normalized titles and duplicate counts. */
    fun sameTrackList(appleTitles: List<String>, youtubeTitles: List<String>): Boolean {
        if (appleTitles.isEmpty() || appleTitles.size != youtubeTitles.size) return false
        val appleKeys = appleTitles.map(::trackKey)
        val youtubeKeys = youtubeTitles.map(::trackKey)
        if (appleKeys.any { it.isBlank() } || youtubeKeys.any { it.isBlank() }) return false
        return appleKeys.groupingBy { it }.eachCount() == youtubeKeys.groupingBy { it }.eachCount()
    }

    private fun trackKey(title: String): String =
        java.text.Normalizer.normalize(title, java.text.Normalizer.Form.NFKD)
            .lowercase(java.util.Locale.ROOT)
            .filter { it.isLetterOrDigit() }

}
