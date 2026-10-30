package com.music.amusic.data.canvas

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AppleYouTubeAlbumMatcherTest {
    private fun match(
        vararg candidates: YouTubeAlbumCandidate,
        appleDisplayTitle: String = "Future Nostalgia",
        appleCatalogTitle: String = "Future Nostalgia (Deluxe Edition)",
        appleArtist: String = "Dua Lipa",
        appleReleaseLine: String = "Álbum • 2020",
    ) = AppleYouTubeAlbumMatcher.matchingBrowseIds(
        appleDisplayTitle = appleDisplayTitle,
        appleCatalogTitle = appleCatalogTitle,
        appleArtist = appleArtist,
        appleReleaseLine = appleReleaseLine,
        candidates = candidates.toList(),
    )

    @Test
    fun `one exact title artist edition and year is accepted`() {
        assertEquals(
            listOf("MPRE-good"),
            match(
                YouTubeAlbumCandidate("MPRE-good", "Future Nostalgia (Deluxe Edition)", "Dua Lipa • Album • 2020"),
                YouTubeAlbumCandidate("MPRE-wrong-year", "Future Nostalgia (Deluxe Edition)", "Dua Lipa • Album • 2021"),
                YouTubeAlbumCandidate("MPRE-wrong-artist", "Future Nostalgia (Deluxe Edition)", "Dua Lipa Tribute • Album • 2020"),
            ),
        )
    }

    @Test
    fun `different edition labels are rejected even when cleaned titles match`() {
        assertTrue(
            match(
                YouTubeAlbumCandidate("MPRE-standard", "Future Nostalgia (Standard Edition)", "Dua Lipa • Album • 2020"),
                appleCatalogTitle = "Future Nostalgia (Deluxe Edition)",
            ).isEmpty(),
        )
    }

    @Test
    fun `year conflict is rejected when both services state a year`() {
        assertTrue(
            match(
                YouTubeAlbumCandidate("MPRE-year", "Future Nostalgia (Deluxe Edition)", "Dua Lipa • Album • 2021"),
            ).isEmpty(),
        )
    }

    @Test
    fun `missing YouTube year is unknown rather than a conflict`() {
        assertEquals(
            listOf("MPRE-no-year"),
            match(
                YouTubeAlbumCandidate("MPRE-no-year", "Future Nostalgia (Deluxe Edition)", "Dua Lipa"),
            ),
        )
    }

    @Test
    fun `different release kind is rejected when both cards state it`() {
        assertTrue(
            match(
                YouTubeAlbumCandidate("MPRE-album", "Future Nostalgia", "Dua Lipa • Album • 2020"),
                appleCatalogTitle = "Future Nostalgia - Single",
                appleReleaseLine = "Single • 2020",
            ).isEmpty(),
        )
    }

    @Test
    fun `two compatible album ids stay ambiguous`() {
        val ids = match(
            YouTubeAlbumCandidate("MPRE-first", "Future Nostalgia (Deluxe Edition)", "Dua Lipa • Album • 2020"),
            YouTubeAlbumCandidate("MPRE-second", "Future Nostalgia (Deluxe Edition)", "Dua Lipa • Album • 2020"),
        )
        assertEquals(2, ids.size)
        assertEquals(null, ids.singleOrNull())
    }

    @Test
    fun `duplicate cards for the same browse id do not create false ambiguity`() {
        assertEquals(
            listOf("MPRE-same"),
            match(
                YouTubeAlbumCandidate("MPRE-same", "Future Nostalgia (Deluxe Edition)", "Dua Lipa • Album • 2020"),
                YouTubeAlbumCandidate("MPRE-same", "Future Nostalgia (Deluxe Edition)", "Dua Lipa • Album • 2020"),
            ),
        )
    }

    @Test
    fun `accent differences in an exact artist name are accepted`() {
        assertEquals(
            listOf("MPRE-beyonce"),
            match(
                YouTubeAlbumCandidate("MPRE-beyonce", "Renaissance", "Beyonce • Album • 2022"),
                appleDisplayTitle = "Renaissance",
                appleCatalogTitle = "Renaissance",
                appleArtist = "Beyoncé",
                appleReleaseLine = "Álbum • 2022",
            ),
        )
    }

    @Test
    fun `complete track lists compare every title and duplicate count`() {
        assertTrue(
            AppleYouTubeAlbumMatcher.sameTrackList(
                listOf("Don't Start Now", "Levitating", "Physical"),
                listOf("Physical", "Don’t Start Now", "Levitating"),
            ),
        )
        assertTrue(
            !AppleYouTubeAlbumMatcher.sameTrackList(
                listOf("Intro", "Song", "Song"),
                listOf("Intro", "Song", "Different Song"),
            ),
        )
        assertTrue(
            !AppleYouTubeAlbumMatcher.sameTrackList(
                listOf("Intro", "Song", "Outro"),
                listOf("Intro", "Song"),
            ),
        )
        assertTrue(!AppleYouTubeAlbumMatcher.sameTrackList(emptyList(), emptyList()))
    }

}
