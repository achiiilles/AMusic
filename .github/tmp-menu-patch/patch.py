import os

song_actions_path = "app/src/main/java/com/music/amusic/ui/components/SongActionsSheet.kt"
with open(song_actions_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Hide video and revert options visually, keeping code intact
old_video_check = "if (onRollbackToOriginal != null || onUpgradeQuality != null || onToggleAudioVersion != null) {"
assert old_video_check in content, "old_video_check not found in content"
new_video_check = "// Ocultadas visualmente no momento; logica preservada para futuro player de video\\n        val showVideoAndRollbackOptions = false\\n        if (showVideoAndRollbackOptions && (onRollbackToOriginal != null || onUpgradeQuality != null || onToggleAudioVersion != null)) {"
content = content.replace(old_video_check, new_video_check, 1)

# 2. Increase icon size in ActionRow (20/22dp -> 24/26dp)
old_icon_size = "modifier = Modifier.size(if (menu) 20.dp else 22.dp),"
assert old_icon_size in content, "old_icon_size not found in content"
new_icon_size = "modifier = Modifier.size(if (menu) 24.dp else 26.dp),"
content = content.replace(old_icon_size, new_icon_size, 1)

# 3. Decrease spacing between icon and text in ActionRow
old_sheet_spacer = "        if (!menu) {\\n            iconView()\\n            Spacer(Modifier.width(18.dp))\\n        }"
assert old_sheet_spacer in content, "old_sheet_spacer not found in content"
new_sheet_spacer = "        if (!menu) {\\n            iconView()\\n            Spacer(Modifier.width(12.dp))\\n        }"
content = content.replace(old_sheet_spacer, new_sheet_spacer, 1)

old_menu_spacer = "        if (menu) {\\n            Spacer(Modifier.width(14.dp))\\n            iconView()\\n        }"
assert old_menu_spacer in content, "old_menu_spacer not found in content"
new_menu_spacer = "        if (menu) {\\n            Spacer(Modifier.width(12.dp))\\n            iconView()\\n        }"
content = content.replace(old_menu_spacer, new_menu_spacer, 1)

# 4. Update LoadingActionRow icon size and spacing for consistency
old_loading = """        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = palette.onBackground.copy(alpha = 0.4f),
            modifier = Modifier.size(22.dp),
        )
        Spacer(Modifier.width(18.dp))"""
assert old_loading in content, "old_loading not found in content"
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
