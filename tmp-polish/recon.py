import glob, re
out = []
def dump(path, a, b):
    fs = glob.glob('app/src/main/java/**/' + path, recursive=True)
    out.append('=== ' + path + ' ' + str(a) + '-' + str(b) + ' files=' + str(len(fs)))
    for f in fs[:1]:
        lines = open(f, encoding='utf-8').read().split('\n')
        for i in range(a - 1, min(b, len(lines))):
            out.append(str(i + 1) + ': ' + lines[i])
dump('MainActivity.kt', 4725, 4744)
dump('MainActivity.kt', 4800, 4892)
dump('BrowseActionsSheet.kt', 1, 54)
dump('BrowseActionsSheet.kt', 232, 262)
out.append('=== grep')
for f in glob.glob('app/src/main/java/**/*.kt', recursive=True):
    for i, l in enumerate(open(f, encoding='utf-8').read().split('\n'), 1):
        if re.search(r'var detailSearching|browseMenuBody\s*=|fun ActionRow\(|val browseMenuBody|name="(search_this_list|close_search|sort_songs)"', l):
            out.append(f.split('/')[-1] + ':' + str(i) + ': ' + l.strip()[:170])
for f in glob.glob('app/src/main/res/values/strings.xml'):
    for i, l in enumerate(open(f, encoding='utf-8').read().split('\n'), 1):
        if re.search(r'name="(search_this_list|close_search|sort_songs)"', l):
            out.append('strings.xml:' + str(i) + ': ' + l.strip())
open('tmp-polish/out.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(len(out))
