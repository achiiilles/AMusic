package com.music.amusic.playback

import android.content.Context
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.session.CommandButton
import androidx.media3.session.DefaultMediaNotificationProvider
import androidx.media3.session.MediaSession
import com.google.common.collect.ImmutableList
import com.music.amusic.R

/**
 * Notificacao de midia com os botoes no estilo do player do Spotify: anterior e proximo
 * pequenos, play/pause grande no centro, e o Favoritar antes dos controles (como o botao de
 * adicionar do Spotify). Os slots padrao do Media3 continuam escolhendo anterior, play/pause
 * e proximo na versao compacta.
 */
@UnstableApi
class AMusicNotificationProvider(
    context: Context,
    channelId: String,
    channelNameResourceId: Int,
) : DefaultMediaNotificationProvider(
    context,
    DefaultMediaNotificationProvider.NotificationIdProvider {
        DefaultMediaNotificationProvider.DEFAULT_NOTIFICATION_ID
    },
    channelId,
    channelNameResourceId,
) {

    override fun getMediaButtons(
        session: MediaSession,
        playerCommands: Player.Commands,
        mediaButtonPreferences: ImmutableList<CommandButton>,
        showPauseButton: Boolean,
    ): ImmutableList<CommandButton> {
        val base = super.getMediaButtons(
            session,
            playerCommands,
            mediaButtonPreferences,
            showPauseButton,
        )
        val transport = ArrayList<CommandButton>()
        val favorite = ArrayList<CommandButton>()
        val others = ArrayList<CommandButton>()
        for (button in base) {
            when {
                button.playerCommand != Player.COMMAND_INVALID ->
                    transport.add(restyle(button, showPauseButton))
                button.sessionCommand?.customAction == ACTION_TOGGLE_FAVORITE ->
                    favorite.add(button)
                else -> others.add(button)
            }
        }
        return ImmutableList.builder<CommandButton>()
            .addAll(favorite)
            .addAll(transport)
            .addAll(others)
            .build()
    }

    private fun restyle(button: CommandButton, showPauseButton: Boolean): CommandButton {
        val icon: Int
        val drawable: Int
        when (button.playerCommand) {
            Player.COMMAND_SEEK_TO_PREVIOUS,
            Player.COMMAND_SEEK_TO_PREVIOUS_MEDIA_ITEM -> {
                icon = CommandButton.ICON_PREVIOUS
                drawable = R.drawable.ic_notif_previous
            }
            Player.COMMAND_SEEK_TO_NEXT,
            Player.COMMAND_SEEK_TO_NEXT_MEDIA_ITEM -> {
                icon = CommandButton.ICON_NEXT
                drawable = R.drawable.ic_notif_next
            }
            Player.COMMAND_PLAY_PAUSE -> {
                if (showPauseButton) {
                    icon = CommandButton.ICON_PAUSE
                    drawable = R.drawable.ic_notif_pause
                } else {
                    icon = CommandButton.ICON_PLAY
                    drawable = R.drawable.ic_notif_play
                }
            }
            else -> return button
        }
        return CommandButton.Builder(icon)
            .setPlayerCommand(button.playerCommand)
            .setDisplayName(button.displayName)
            .setCustomIconResId(drawable)
            .build()
    }
}
