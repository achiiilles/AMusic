package com.music.amusic.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.music.amusic.data.settings.AppSettings
import com.music.amusic.data.settings.LibraryViewType
import com.music.amusic.data.stats.MostPlayedTracks
import com.music.amusic.download.Downloads

/** The shared pages' settings and downloads, answered from the phone's own stores. */
object AndroidAppUiHost : AppUiHost {
    override val swipeToPlayNext = AppSettings.swipeToPlayNext
    override val homeRecentsViewType = AppSettings.homeRecentsViewType
    override fun setHomeRecentsViewType(value: LibraryViewType) = AppSettings.setHomeRecentsViewType(value)
    override val pinnedPlaylists = AppSettings.pinnedPlaylists
    override val librarySort = AppSettings.librarySort

    @Composable
    override fun downloadedIds(): Set<String> {
        val saved by Downloads.saved.collectAsStateWithLifecycle()
        return saved.keys
    }

    @Composable
    override fun mostPlayedTrackIds(): Set<String> {
        // A release's numbered rows asking for the dots is also the cue to re-read
        // the history, so a track played after launch can take the mark.
        LaunchedEffect(Unit) { MostPlayedTracks.refreshIfStale() }
        val marks by MostPlayedTracks.ids.collectAsStateWithLifecycle()
        return marks
    }
}
