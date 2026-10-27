import os
import re

file_path = "app/src/main/java/com/music/amusic/ui/components/SongActionsSheet.kt"
assert os.path.exists(file_path), f"File {file_path} not found"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """        when {
            song.albumId != null || !song.albumName.isNullOrBlank() || song.title.isNotBlank() -> ActionRow(
                Icons.Rounded.Album,
                stringResource(R.string.open_album),
                accent = palette.accent,
                onClick = onOpenAlbum,
            )
            resolvingLinks -> LoadingActionRow(Icons.Rounded.Album, stringResource(R.string.open_album), palette)
        }
        when {
            song.artistId != null || song.artists.isNotEmpty() || song.artist.isNotBlank() -> ActionRow(
                Icons.Rounded.Person,
                stringResource(R.string.open_artist),
                accent = palette.accent,
                onClick = onOpenArtist,
            )
            resolvingLinks -> LoadingActionRow(Icons.Rounded.Person, stringResource(R.string.open_artist), palette)
        }
"""

if target in content:
    new_content = content.replace(target, "", 1)
elif target.replace("\n", "\r\n") in content:
    new_content = content.replace(target.replace("\n", "\r\n"), "", 1)
else:
    pattern = re.compile(
        r"[ \t]*when\s*\{\s*song\.albumId\s*!=.*?LoadingActionRow\(Icons\.Rounded\.Album.*?\}[ \t]*\r?\n"
        r"[ \t]*when\s*\{\s*song\.artistId\s*!=.*?LoadingActionRow\(Icons\.Rounded\.Person.*?\}[ \t]*\r?\n",
        re.DOTALL
    )
    match = pattern.search(content)
    assert match is not None, "Target when blocks not found in SongActionsSheet.kt"
    new_content = content[:match.start()] + content[match.end():]

assert "Icons.Rounded.Album" not in new_content, "Icons.Rounded.Album still present in SongActionsSheet.kt"
assert "Icons.Rounded.Person" not in new_content, "Icons.Rounded.Person still present in SongActionsSheet.kt"
assert "SheetTrackHeader(song" in new_content, "SheetTrackHeader missing in SongActionsSheet.kt"
assert "onOpenAlbum = onOpenAlbum" in new_content, "onOpenAlbum missing in SheetTrackHeader"
assert "onOpenArtist = onOpenArtist" in new_content, "onOpenArtist missing in SheetTrackHeader"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully removed album and artist ActionRow from SongActionsSheet.kt")
