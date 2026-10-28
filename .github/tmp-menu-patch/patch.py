import os
import sys

print("--- Starting heart-to-star patch ---")

p1 = "app/src/main/res/drawable/ic_sf_heart.xml"
assert os.path.exists(p1), f"File not found: {p1}"
sf_heart_content = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:pathData="M12,3.4L14.4,8.9L20.4,9.5L15.9,13.5L17.2,19.3L12,16.3L6.8,19.3L8.1,13.5L3.6,9.5L9.6,8.9Z"
        android:strokeColor="#FFFFFFFF"
        android:strokeLineCap="round"
        android:strokeLineJoin="round"
        android:strokeWidth="2.2" />
</vector>
"""
with open(p1, "w", encoding="utf-8") as f:
    f.write(sf_heart_content)
print("Updated ic_sf_heart.xml")

p2 = "app/src/main/res/drawable/ic_sf_heart_fill.xml"
assert os.path.exists(p2), f"File not found: {p2}"
sf_heart_fill_content = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="M12,3.4L14.4,8.9L20.4,9.5L15.9,13.5L17.2,19.3L12,16.3L6.8,19.3L8.1,13.5L3.6,9.5L9.6,8.9Z"
        android:strokeColor="#FFFFFFFF"
        android:strokeLineCap="round"
        android:strokeLineJoin="round"
        android:strokeWidth="2.2" />
</vector>
"""
with open(p2, "w", encoding="utf-8") as f:
    f.write(sf_heart_fill_content)
print("Updated ic_sf_heart_fill.xml")

p3 = "app/src/main/res/drawable/ic_widget_heart.xml"
assert os.path.exists(p3), f"File not found: {p3}"
widget_heart_content = """<?xml version="1.0" encoding="utf-8"?>
<!--
  Like, unset. The same star AMusicIcons.Heart draws in the player, carried
  over as a drawable because a widget can't render an ImageVector. Stroked at
  the transport's 2.4 rather than the app's 2.2 so it matches its neighbours.
-->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:pathData="M12,3.4L14.4,8.9L20.4,9.5L15.9,13.5L17.2,19.3L12,16.3L6.8,19.3L8.1,13.5L3.6,9.5L9.6,8.9Z"
        android:strokeColor="#FFFFFFFF"
        android:strokeLineCap="round"
        android:strokeLineJoin="round"
        android:strokeWidth="2.4" />
</vector>
"""
with open(p3, "w", encoding="utf-8") as f:
    f.write(widget_heart_content)
print("Updated ic_widget_heart.xml")

p4 = "app/src/main/res/drawable/ic_widget_heart_filled.xml"
assert os.path.exists(p4), f"File not found: {p4}"
widget_heart_filled_content = """<?xml version="1.0" encoding="utf-8"?>
<!-- Like, set. Filled rather than tinted, as AMusicIcons.HeartFilled explains. -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="M12,3.4L14.4,8.9L20.4,9.5L15.9,13.5L17.2,19.3L12,16.3L6.8,19.3L8.1,13.5L3.6,9.5L9.6,8.9Z"
        android:strokeColor="#FFFFFFFF"
        android:strokeLineCap="round"
        android:strokeLineJoin="round"
        android:strokeWidth="2.4" />
</vector>
"""
with open(p4, "w", encoding="utf-8") as f:
    f.write(widget_heart_filled_content)
print("Updated ic_widget_heart_filled.xml")

p5 = "sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/icons/AMusicIcons.kt"
assert os.path.exists(p5), f"File not found: {p5}"
with open(p5, "r", encoding="utf-8") as f:
    icons_content = f.read().replace("\r\n", "\n")

old_heart_fn = """    private fun heart(name: String, filled: Boolean): ImageVector =
        ImageVector.Builder(
            name = name,
            defaultWidth = 24.dp, defaultHeight = 24.dp,
            viewportWidth = 24f, viewportHeight = 24f,
        ).apply {
            path(
                stroke = stroke,
                strokeLineWidth = STROKE,
                strokeLineCap = StrokeCap.Round,
                strokeLineJoin = StrokeJoin.Round,
                fill = if (filled) stroke else null,
            ) {
                // Two lobes meeting at the top notch, falling to a single point.
                moveTo(12f, 20f)
                curveTo(12f, 20f, 3.2f, 14.6f, 3.2f, 8.9f)
                arcToRelative(4.5f, 4.5f, 0f, isMoreThanHalf = false, isPositiveArc = true, 8.8f, -1.5f)
                arcToRelative(4.5f, 4.5f, 0f, isMoreThanHalf = false, isPositiveArc = true, 8.8f, 1.5f)
                curveTo(20.8f, 14.6f, 12f, 20f, 12f, 20f)
                close()
            }
        }.build()"""

assert old_heart_fn in icons_content, "old_heart_fn not found in AMusicIcons.kt"

new_heart_fn = """    private fun heart(name: String, filled: Boolean): ImageVector =
        ImageVector.Builder(
            name = name,
            defaultWidth = 24.dp, defaultHeight = 24.dp,
            viewportWidth = 24f, viewportHeight = 24f,
        ).apply {
            path(
                stroke = stroke,
                strokeLineWidth = STROKE,
                strokeLineCap = StrokeCap.Round,
                strokeLineJoin = StrokeJoin.Round,
                fill = if (filled) stroke else null,
            ) {
                moveTo(12f, 3.4f)
                lineTo(14.4f, 8.9f)
                lineTo(20.4f, 9.5f)
                lineTo(15.9f, 13.5f)
                lineTo(17.2f, 19.3f)
                lineTo(12f, 16.3f)
                lineTo(6.8f, 19.3f)
                lineTo(8.1f, 13.5f)
                lineTo(3.6f, 9.5f)
                lineTo(9.6f, 8.9f)
                close()
            }
        }.build()"""

icons_content = icons_content.replace(old_heart_fn, new_heart_fn, 1)

with open(p5, "w", encoding="utf-8") as f:
    f.write(icons_content)
print("Updated AMusicIcons.kt")
print("--- Patch complete successfully ---")
