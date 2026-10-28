import os
import sys

print("--- Starting notification star and shuffle icons patch ---")

# 1. Create app/src/main/res/drawable/ic_notif_shuffle_on.xml
p_on = "app/src/main/res/drawable/ic_notif_shuffle_on.xml"
shuffle_on_content = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:pathData="M3.4,7.4L7,7.4L16.6,16.6L20.6,16.6M18.1,14.1L20.6,16.6L18.1,19.1M3.4,16.6L7,16.6L9.8,13.9M13.9,10.1L16.6,7.4L20.6,7.4M18.1,4.9L20.6,7.4L18.1,9.9"
        android:strokeColor="#FFFFFFFF"
        android:strokeLineCap="round"
        android:strokeLineJoin="round"
        android:strokeWidth="2.2" />
</vector>
"""
with open(p_on, "w", encoding="utf-8") as f:
    f.write(shuffle_on_content)
print("Created ic_notif_shuffle_on.xml")

# 2. Create app/src/main/res/drawable/ic_notif_shuffle_off.xml
p_off = "app/src/main/res/drawable/ic_notif_shuffle_off.xml"
shuffle_off_content = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:pathData="M3.4,7.4L7,7.4L16.6,16.6L20.6,16.6M18.1,14.1L20.6,16.6L18.1,19.1M3.4,16.6L7,16.6L9.8,13.9M13.9,10.1L16.6,7.4L20.6,7.4M18.1,4.9L20.6,7.4L18.1,9.9"
        android:strokeColor="#80FFFFFF"
        android:strokeLineCap="round"
        android:strokeLineJoin="round"
        android:strokeWidth="2.2" />
</vector>
"""
with open(p_off, "w", encoding="utf-8") as f:
    f.write(shuffle_off_content)
print("Created ic_notif_shuffle_off.xml")

# 3. Patch AMusicNotificationProvider.kt
p_provider = "app/src/main/java/com/music/amusic/playback/AMusicNotificationProvider.kt"
assert os.path.exists(p_provider), f"File not found: {p_provider}"
with open(p_provider, "r", encoding="utf-8") as f:
    provider_content = f.read().replace("\r\n", "\n")

old_provider_block = """        for (button in base) {
            when {
                button.playerCommand != Player.COMMAND_INVALID ->
                    transport.add(restyle(button, showPauseButton))
                button.sessionCommand?.customAction == ACTION_TOGGLE_FAVORITE ->
                    favorite.add(button)
                else -> others.add(button)
            }
        }"""

new_provider_block = """        for (button in base) {
            when {
                button.playerCommand != Player.COMMAND_INVALID ->
                    transport.add(restyle(button, showPauseButton))
                button.sessionCommand?.customAction == ACTION_TOGGLE_FAVORITE ->
                    favorite.add(restyleFavorite(button))
                button.sessionCommand?.customAction == ACTION_TOGGLE_SHUFFLE ->
                    others.add(restyleShuffle(button))
                else -> others.add(button)
            }
        }"""

assert old_provider_block in provider_content, "old_provider_block not found in AMusicNotificationProvider.kt"
provider_content = provider_content.replace(old_provider_block, new_provider_block, 1)

provider_helper_methods = """    private fun restyleFavorite(button: CommandButton): CommandButton {
        val drawable = if (button.icon == CommandButton.ICON_HEART_FILLED) {
            R.drawable.ic_sf_heart_fill
        } else {
            R.drawable.ic_sf_heart
        }
        val builder = CommandButton.Builder(button.icon)
            .setDisplayName(button.displayName)
            .setCustomIconResId(drawable)
        button.sessionCommand?.let { builder.setSessionCommand(it) }
        return builder.build()
    }

    private fun restyleShuffle(button: CommandButton): CommandButton {
        val drawable = if (button.icon == CommandButton.ICON_SHUFFLE_ON) {
            R.drawable.ic_notif_shuffle_on
        } else {
            R.drawable.ic_notif_shuffle_off
        }
        val builder = CommandButton.Builder(button.icon)
            .setDisplayName(button.displayName)
            .setCustomIconResId(drawable)
        button.sessionCommand?.let { builder.setSessionCommand(it) }
        return builder.build()
    }

    private fun restyle(button: CommandButton, showPauseButton: Boolean): CommandButton {"""

assert "    private fun restyle(button: CommandButton, showPauseButton: Boolean): CommandButton {" in provider_content, "restyle function not found"
provider_content = provider_content.replace(
    "    private fun restyle(button: CommandButton, showPauseButton: Boolean): CommandButton {",
    provider_helper_methods,
    1
)

with open(p_provider, "w", encoding="utf-8") as f:
    f.write(provider_content)
print("Updated AMusicNotificationProvider.kt")

# 4. Patch PlaybackService.kt
p_service = "app/src/main/java/com/music/amusic/playback/PlaybackService.kt"
assert os.path.exists(p_service), f"File not found: {p_service}"
with open(p_service, "r", encoding="utf-8") as f:
    service_content = f.read().replace("\r\n", "\n")

old_service_block = """    /** Favorite and Shuffle: the only actions shown on the phone notification. */
    private fun notificationButtons(): List<CommandButton> {
        val favorite = if (!canLike(player?.currentMediaItem)) null else CommandButton.Builder(
            if (LikeState.overrides.value[player?.currentMediaItem?.mediaId] == LikeStatus.LIKE) {
                CommandButton.ICON_HEART_FILLED
            } else {
                CommandButton.ICON_HEART_UNFILLED
            },
        )
            .setSessionCommand(favoriteCommand)
            .setDisplayName("Favorite")
            .build()
        val shuffleEnabled = QueueShuffle.enabled.value
        val shuffle = CommandButton.Builder(
            if (shuffleEnabled) {
                CommandButton.ICON_SHUFFLE_ON
            } else {
                CommandButton.ICON_SHUFFLE_OFF
            },
        )
            .setSessionCommand(shuffleCommand)
            .setDisplayName(if (shuffleEnabled) "Shuffle off" else "Shuffle on")
            .build()
        return listOfNotNull(favorite, shuffle)
    }"""

new_service_block = """    /** Favorite and Shuffle: the only actions shown on the phone notification. */
    private fun notificationButtons(): List<CommandButton> {
        val isLiked = LikeState.overrides.value[player?.currentMediaItem?.mediaId] == LikeStatus.LIKE
        val favorite = if (!canLike(player?.currentMediaItem)) null else CommandButton.Builder(
            if (isLiked) {
                CommandButton.ICON_HEART_FILLED
            } else {
                CommandButton.ICON_HEART_UNFILLED
            },
        )
            .setSessionCommand(favoriteCommand)
            .setDisplayName("Favorite")
            .setCustomIconResId(if (isLiked) R.drawable.ic_sf_heart_fill else R.drawable.ic_sf_heart)
            .build()
        val shuffleEnabled = QueueShuffle.enabled.value
        val shuffle = CommandButton.Builder(
            if (shuffleEnabled) {
                CommandButton.ICON_SHUFFLE_ON
            } else {
                CommandButton.ICON_SHUFFLE_OFF
            },
        )
            .setSessionCommand(shuffleCommand)
            .setDisplayName(if (shuffleEnabled) "Shuffle off" else "Shuffle on")
            .setCustomIconResId(if (shuffleEnabled) R.drawable.ic_notif_shuffle_on else R.drawable.ic_notif_shuffle_off)
            .build()
        return listOfNotNull(favorite, shuffle)
    }"""

assert old_service_block in service_content, "old_service_block not found in PlaybackService.kt"
service_content = service_content.replace(old_service_block, new_service_block, 1)

with open(p_service, "w", encoding="utf-8") as f:
    f.write(service_content)
print("Updated PlaybackService.kt")
print("--- Patch complete successfully ---")
