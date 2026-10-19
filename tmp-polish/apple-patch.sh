set -e
python3 - <<'PY'
p='app/src/main/java/com/music/amusic/AMusicApplication.kt'
s=open(p).read()
old1='''        // Apple Music photos for artists in every list; YouTube photo stays until one arrives.
        com.music.amusic.ui.components.ArtistPhotos.provider = com.music.amusic.data.canvas.AppleArtistPhotoProvider
'''
new1='''        // Apple Music photos for artists in every list; YouTube photo stays until one arrives.
        // Switched off: with no provider registered every artist keeps the YouTube photo and
        // no Apple Music lookup is made. Set APPLE_ARTIST_PHOTOS to true to bring it back.
        if (APPLE_ARTIST_PHOTOS) {
            com.music.amusic.ui.components.ArtistPhotos.provider = com.music.amusic.data.canvas.AppleArtistPhotoProvider
        }
'''
old2='''    companion object {
        lateinit var authStore: AuthStore
            private set
'''
new2='''    companion object {
        lateinit var authStore: AuthStore
            private set

        /** Whether artist photos from Apple Music replace the YouTube ones in lists. Off. */
        private val APPLE_ARTIST_PHOTOS = false
'''
assert s.count(old1)==1 and s.count(old2)==1
open(p,'w').write(s.replace(old1,new1).replace(old2,new2))
PY
git config user.name tmp
git config user.email tmp@example.com
git add app/src/main/java/com/music/amusic/AMusicApplication.kt
git commit -m "Foto de artista: so a do YouTube, troca pela do Apple Music desligada [skip ci]"
git push origin HEAD:polish-refresh-transitions
{ git show HEAD; echo ===USES===; grep -rn 'AppleArtistPhotoProvider\|ArtistPhotos\|AppleArtistArtRepository' --include=*.kt app sharedUi shared | grep -v '^app/src/main/java/com/music/amusic/data/canvas/AppleArtist'; } > tmp-polish/out-apple.txt
