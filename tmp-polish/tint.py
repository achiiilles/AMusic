import re, os, subprocess
def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout + r.stderr
out = []
out.append('== pageVeil ==')
out.append(run("grep -rn 'pageVeil' app/src/main --include=*.kt | cut -c1-260"))
out.append('== veil 0.07 ==')
out.append(run("grep -rn '0\\.07f\\|TOP_BAR_VEIL' app/src/main --include=*.kt | cut -c1-260"))
out.append('== tint names ==')
out.append(run("grep -rniE 'pageTint|pageInk|artworkTint|pageColor|dominantColor|paletteColor|pageBackground|artworkColor|surfaceTint' app/src/main --include=*.kt | cut -c1-260 | head -150"))
open('tmp-polish/out-tint-a.txt','w').write('\n'.join(out))
