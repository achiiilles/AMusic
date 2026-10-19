import subprocess
def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout + r.stderr
M = 'app/src/main/java/com/music/amusic/MainActivity.kt'
out = []
out.append('== Main 3600-3735 ==')
out.append(run("sed -n '3600,3735p' " + M + " | cut -c1-220"))
out.append('== Main 4095-4112 ==')
out.append(run("sed -n '4095,4112p' " + M + " | cut -c1-220"))
out.append('== Detail 550-562 ==')
out.append(run("sed -n '545,562p' app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt | cut -c1-220"))
open('tmp-polish/out-tint-b.txt','w').write('\n'.join(out))
