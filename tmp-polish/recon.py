import glob, base64
out = []
def dump(path, a, b):
    fs = glob.glob('app/src/main/java/**/' + path, recursive=True)
    out.append('=== ' + path + ' ' + str(a) + '-' + str(b) + ' files=' + str(len(fs)))
    for f in fs[:1]:
        lines = open(f, encoding='utf-8').read().split('\n')
        for i in range(a - 1, min(b, len(lines))):
            out.append(str(i + 1) + ': ' + lines[i])
dump('MainActivity.kt', 3720, 3990)
dump('MainActivity.kt', 5115, 5150)
dump('MainActivity.kt', 5545, 5560)
open('tmp-polish/out.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(len(out))
