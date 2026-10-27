import os
import sys

print("--- Starting patch ---")
song_actions_path = "app/src/main/java/com/music/amusic/ui/components/SongActionsSheet.kt"
assert os.path.exists(song_actions_path), f"File not found: {song_actions_path}"

with open(song_actions_path, "r", encoding="utf-8") as f:
    content = f.read().replace("\r\n", "\n")

# 1. Hide video and rollback/revert options visually
print("Applying step 1: hide video/revert options...")
old_video_check = "        if (onRollbackToOriginal != null || onUpgradeQuality != null || onToggleAudioVersion != null) {"
assert old_video_check in content, "old_video_check not found"
new_video_check = """        // Ocultadas visualmente no momento; logica preservada para futuro player de video
        val showVideoAndRollbackOptions = false
        if (showVideoAndRollbackOptions && (onRollbackToOriginal != null || onUpgradeQuality != null || onToggleAudioVersion != null)) {"""
content = content.replace(old_video_check, new_video_check, 1)

# 2. Increase icon size in ActionRow
print("Applying step 2: increase icon size...")
old_icon_size = "modifier = Modifier.size(if (menu) 20.dp else 22.dp),"
assert old_icon_size in content, "old_icon_size not found"
new_icon_size = "modifier = Modifier.size(if (menu) 24.dp else 26.dp),"
content = content.replace(old_icon_size, new_icon_size, 1)

# 3. Decrease spacing between icon and text in ActionRow
print("Applying step 3: adjust spacing...")
old_sheet_spacer = """        if (!menu) {
            iconView()
            Spacer(Modifier.width(18.dp))
        }"""
assert old_sheet_spacer in content, "old_sheet_spacer not found"
new_sheet_spacer = """        if (!menu) {
            iconView()
            Spacer(Modifier.width(12.dp))
        }"""
content = content.replace(old_sheet_spacer, new_sheet_spacer, 1)

old_menu_spacer = """        if (menu) {
            Spacer(Modifier.width(14.dp))
            iconView()
        }"""
assert old_menu_spacer in content, "old_menu_spacer not found"
new_menu_spacer = """        if (menu) {
            Spacer(Modifier.width(12.dp))
            iconView()
        }"""
content = content.replace(old_menu_spacer, new_menu_spacer, 1)

# 4. LoadingActionRow icon size and spacing
print("Applying step 4: adjust LoadingActionRow...")
old_loading = """        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = palette.onBackground.copy(alpha = 0.4f),
            modifier = Modifier.size(22.dp),
        )
        Spacer(Modifier.width(18.dp))"""
assert old_loading in content, "old_loading not found"
new_loading = """        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = palette.onBackground.copy(alpha = 0.4f),
            modifier = Modifier.size(if (menu) 24.dp else 26.dp),
        )
        Spacer(Modifier.width(12.dp))"""
content = content.replace(old_loading, new_loading, 1)

with open(song_actions_path, "w", encoding="utf-8") as f:
    f.write(content)

print("SongActionsSheet.kt patched successfully!")
