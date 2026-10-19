import glob, re

def find(name):
    fs = glob.glob('app/src/main/java/**/' + name, recursive=True)
    assert len(fs) == 1, (name, fs)
    return fs[0]

def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        s = f.read()
    assert '\r\n' not in s, p
    return s

def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(s)

def sub1(text, pattern, fn):
    new, n = re.subn(pattern, fn, text, flags=re.M)
    assert n == 1, (pattern, n)
    return new

main_p = find('MainActivity.kt')
sheet_p = find('BrowseActionsSheet.kt')
m = read(main_p)
s = read(sheet_p)

# 1. top bar: the search button is left off an album page
m = sub1(
    m,
    r'^([ \t]*)(val releaseSongs = \(detail\.songs as\? UiState\.Success\)\?\.data\.orEmpty\(\))\n([ \t]*)if \(releaseSongs\.isNotEmpty\(\)\) \{\n([ \t]*)IconButton\(onClick = \{ detailSearching = !detailSearching \}\) \{',
    lambda x: (
        x.group(1) + x.group(2) + '\n'
        + x.group(1) + '// On an album page the search and the sort live in the "..." menu.\n'
        + x.group(1) + 'val isAlbumPage = detail.type == BrowseType.ALBUM && !isLocalDetail\n'
        + x.group(3) + 'if (releaseSongs.isNotEmpty() && !isAlbumPage) {\n'
        + x.group(4) + 'IconButton(onClick = { detailSearching = !detailSearching }) {'
    ),
)

# 2. top bar: the sort button is left off an album page
m = sub1(
    m,
    r'^([ \t]*)IconButton\(\n([ \t]*)onClick = \{ if \(isLocalDetail\) folderMenuOpen = true else songSortMenuOpen = true \},',
    lambda x: (
        x.group(1) + 'if (!isAlbumPage) IconButton(\n'
        + x.group(2) + 'onClick = { if (isLocalDetail) folderMenuOpen = true else songSortMenuOpen = true },'
    ),
)

# 3. the "..." sheet gets the two actions, for an album page only
def sheet_args(x):
    i = x.group(1)
    j = i + '    '
    return (
        i + 'presentation = presentation,\n'
        + i + '// Album page only: its search and sort are rows of this menu now.\n'
        + i + 'searchActive = detailSearching,\n'
        + i + 'onSearch = if (target.type == BrowseType.ALBUM && !target.fromCard) ({\n'
        + j + 'browseActions = null\n'
        + j + 'detailSearching = !detailSearching\n'
        + i + '}) else null,\n'
        + i + 'onSort = if (target.type == BrowseType.ALBUM && !target.fromCard) ({\n'
        + j + 'browseActions = null\n'
        + j + 'songSortMenuOpen = true\n'
        + i + '}) else null,\n'
        + x.group(2) + 'onRenameInSheet = {'
    )
m = sub1(m, r'^([ \t]*)presentation = presentation,\n([ \t]*)onRenameInSheet = \{', sheet_args)

# 4. BrowseActionsSheet: import, parameters, rows
assert s.count('import androidx.compose.material.icons.rounded.Share\n') == 1
assert 'icons.rounded.Sort\n' not in s
s = s.replace(
    'import androidx.compose.material.icons.rounded.Share\n',
    'import androidx.compose.material.icons.rounded.Share\nimport androidx.compose.material.icons.rounded.Sort\n',
)
s = sub1(
    s,
    r'^([ \t]*)startRenaming: Boolean = false,\n\) \{\n([ \t]*)val menu = presentation',
    lambda x: (
        x.group(1) + 'startRenaming: Boolean = false,\n'
        + x.group(1) + '/** Album page only: the page\'s own search and sort, as rows of this menu. */\n'
        + x.group(1) + 'searchActive: Boolean = false,\n'
        + x.group(1) + 'onSearch: (() -> Unit)? = null,\n'
        + x.group(1) + 'onSort: (() -> Unit)? = null,\n'
        + ') {\n'
        + x.group(2) + 'val menu = presentation'
    ),
)
s = sub1(
    s,
    r'^([ \t]*)onPlay\?\.let \{ ActionRow\(Icons\.Rounded\.PlayArrow',
    lambda x: (
        x.group(1) + 'onSearch?.let {\n'
        + x.group(1) + '    ActionRow(\n'
        + x.group(1) + '        AMusicIcons.Search,\n'
        + x.group(1) + '        stringResource(if (searchActive) R.string.close_search else R.string.search_this_list),\n'
        + x.group(1) + '        onClick = it,\n'
        + x.group(1) + '    )\n'
        + x.group(1) + '}\n'
        + x.group(1) + 'onSort?.let { ActionRow(Icons.Rounded.Sort, stringResource(R.string.sort_songs), onClick = it) }\n'
        + x.group(1) + 'onPlay?.let { ActionRow(Icons.Rounded.PlayArrow'
    ),
)
write(main_p, m)
write(sheet_p, s)
print('patched', main_p, sheet_p)
