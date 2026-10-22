#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
DS=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
AP=shared/src/jvmSharedMain/kotlin/com/music/amusic/data/ApplePreRelease.kt
echo "=== APPLE API ==="
grep -n 'collectionIdOf\|collectionIds\|fun album\|lowercase\|trim()' "$AP" | head -40
echo "=== PATCH ==="
python3 - <<'PY'
import re, pathlib
ds = pathlib.Path('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt')
ap = pathlib.Path('shared/src/jvmSharedMain/kotlin/com/music/amusic/data/ApplePreRelease.kt')
src = ds.read_text(encoding='utf-8')
BADGE = '"Pré-Lançamento"'
if 'fun collectionIdOf' not in ap.read_text(encoding='utf-8'):
    print('SKIP: ApplePreRelease.collectionIdOf not found')
    raise SystemExit(0)
if 'preReleaseId' in src:
    print('ALREADY PATCHED')
    raise SystemExit(0)
try:
    start = src.index('private fun SectionCard(')
    end = src.index('private fun ArtistShelfGridPage(')
except ValueError as exc:
    print('PATCH ABORTED: anchor not found:', exc)
    raise SystemExit(0)
block = src[start:end]
print('section block chars:', len(block))
m = re.search(r'text = item\.title,(?P<mid>.{0,400}?maxLines = )1', block, re.S)
if not m:
    print('PATCH ABORTED: title maxLines not found')
    raise SystemExit(0)
block = block[:m.start('mid')] + 'maxLines = if (item.subtitle?.startsWith(' + BADGE + ') == true) 2 else 1' + block[m.end('mid'):]
print('title patched')
h = re.search(r'(\)\s*\{\n)([ \t]*)(Column\()', block)
if not h:
    print('PATCH ABORTED: function head not found')
    raise SystemExit(0)
ind = h.group(2)
state = (
    ind + 'val preReleaseId = androidx.compose.runtime.remember(item.title) {\n'
    + ind + '    if (item.subtitle?.startsWith(' + BADGE + ') == true) com.music.amusic.data.ApplePreRelease.collectionIdOf(item.title) else null\n'
    + ind + '}\n'
    + ind + 'val preReleaseOpen = androidx.compose.runtime.remember(item.title) { androidx.compose.runtime.mutableStateOf(false) }\n'
)
block = block[:h.start(0)] + h.group(1) + state + h.group(2) + h.group(3) + block[h.end(0):]
print('state added')
CLICK = '.longPressMenuClickable(onClick = onClick, onLongClick = onLongPress),'
if block.count(CLICK) != 1:
    print('PATCH ABORTED: click matches', block.count(CLICK))
    raise SystemExit(0)
block = block.replace(CLICK,
    '.longPressMenuClickable(\n'
    + ind + '    onClick = { if (preReleaseId != null) preReleaseOpen.value = true else onClick() },\n'
    + ind + '    onLongClick = onLongPress,\n'
    + ind + '),')
print('click patched')
m2 = re.search(r'\n([ \t]*)text = item\.subtitle,', block)
if not m2:
    print('PATCH ABORTED: subtitle Text not found')
    raise SystemExit(0)
child = m2.group(1)
inner = child + '    '
i = block.index('text = item.subtitle,')
j = block.index('overflow = TextOverflow.Ellipsis,', i)
k = block.index(')', j)
dialog = (
    '\n' + child + 'if (preReleaseOpen.value && preReleaseId != null) {\n'
    + inner + 'PreReleasePage(\n'
    + inner + '    title = item.title,\n'
    + inner + '    artistName = null,\n'
    + inner + '    badge = item.subtitle,\n'
    + inner + '    coverUrl = item.thumbnailUrl,\n'
    + inner + '    collectionId = preReleaseId,\n'
    + inner + '    onDismiss = { preReleaseOpen.value = false },\n'
    + inner + ')\n'
    + child + '}')
block = block[:k + 1] + dialog + block[k + 1:]
print('page call added')
ds.write_text(src[:start] + block + src[end:], encoding='utf-8')
print('WROTE DetailScreen.kt')
PY
echo "=== VERIFY ==="
grep -n 'preReleaseId\|PreReleasePage(\|maxLines = if' "$DS" | head -20
if grep -q 'PreReleasePage(' "$DS"; then
  git config user.name 'pally'
  git config user.email 'pally@local'
  git add -- "$DS"
  if git diff --cached --quiet; then
    echo 'NOTHING STAGED'
  else
    git commit -m 'feat: card de pré-lançamento abre a página do lançamento e o título cabe em 2 linhas [skip ci]'
    git log --oneline -1
  fi
else
  echo 'PATCH DID NOT APPLY'
fi
exit 0
