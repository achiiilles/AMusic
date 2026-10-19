import glob
out = []
def dump(path, a, b):
    fs = glob.glob('app/src/main/java/**/' + path, recursive=True)
    out.append('=== ' + path + ' ' + str(a) + '-' + str(b) + ' files=' + str(len(fs)))
    for f in fs[:1]:
        lines = open(f, encoding='utf-8').read().split('\n')
        out.append('total lines ' + str(len(lines)))
        for i in range(a - 1, min(b, len(lines))):
            out.append(str(i + 1) + ': ' + lines[i])
dump('MainActivity.kt', 4745, 4800)
dump('MainActivity.kt', 4890, 4915)
dump('BrowseActionsSheet.kt', 55, 420)
open('tmp-polish/out.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(len(out))
