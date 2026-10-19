import subprocess
def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout + r.stderr
M = 'app/src/main/java/com/music/amusic/MainActivity.kt'
D = 'app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt'
out = []
out.append('== Main 2200-2235 ==')
out.append(run("sed -n '2200,2235p' " + M + " | cut -c1-200"))
out.append('== Main 3076-3086 ==')
out.append(run("sed -n '3076,3086p' " + M + " | cut -c1-200"))
out.append('== Detail 366-378 ==')
out.append(run("sed -n '366,378p' " + D + " | cut -c1-200"))
out.append('== class ArtworkPalette ==')
out.append(run("grep -rn 'ArtworkPalette(' app/src/main --include=*.kt | cut -c1-200 | head -10"))
out.append('== wash defs ==')
out.append(run("grep -rn 'wash' app/src/main --include=*.kt | cut -c1-200 | head -20"))
open('tmp-polish/out-tint-d.txt','w').write('\n'.join(out))
