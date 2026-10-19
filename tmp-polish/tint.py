import subprocess
def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout + r.stderr
M = 'app/src/main/java/com/music/amusic/MainActivity.kt'
out = []
out.append('== isLocalDetail / detailPalette in Main ==')
out.append(run("grep -n 'isLocalDetail\\|detailPalette\\|LocalArtist\\|localArtist' " + M + " | cut -c1-230 | head -80"))
out.append('== local artist files ==')
out.append(run("grep -rln 'LocalArtist\\|localArtist\\|LibraryArtist' app/src/main --include=*.kt"))
out.append('== palette defs ==')
out.append(run("grep -rn 'class ArtworkPalette\\|val wash\\|val background' app/src/main --include=*.kt | cut -c1-230 | head -30"))
out.append('== background( in local/library artist screens ==')
out.append(run("grep -rn 'LocalArtist\\|LibraryArtist' app/src/main --include=*.kt | cut -c1-230 | head -40"))
open('tmp-polish/out-tint-c.txt','w').write('\n'.join(out))
