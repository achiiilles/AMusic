#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
DS=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
rm -f .pally/*.txt
sed -n '318,405p' "$DS" > .pally/q1_sig.txt
sed -n '1040,1185p' "$DS" > .pally/q2_artistbody.txt
grep -n 'onSectionItemClick' "$DS" > .pally/q3a_click.txt

python3 - <<'PY'
import pathlib

path = pathlib.Path('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt')
src = path.read_text(encoding='utf-8')
BADGE = '"Pré-Lançamento"'

try:
    start = src.index('private fun SectionCard(')
    end = src.index('private fun ArtistShelfGridPage(')
except ValueError as exc:
    print('PATCH ABORTED: anchor not found:', exc)
    raise SystemExit(0)

block = src[start:end]
print('section block chars:', len(block))

# 1. The card's title gets a second line on a pre-release, where the name runs
#    long ("Say what you see - EP") and one line cut it mid-word.
i = block.find('text = item.title,')
if i < 0:
    print('PATCH ABORTED: title Text not found')
    raise SystemExit(0)
j = block.find('maxLines = 1,', i)
if j < 0:
    print('PATCH ABORTED: title maxLines not found')
    raise SystemExit(0)
block = block[:j] + 'maxLines = if (item.subtitle.startsWith(' + BADGE + ')) 2 else 1,' + block[j + len('maxLines = 1,'):]
print('title patched')

# 2. Remember which Apple release a card stands for, and open its page instead
#    of the (empty) YouTube page the card has no id for.
anchor = '    ) {\n        Column('
if block.count(anchor) != 1:
    print('PATCH ABORTED: function head matches', block.count(anchor))
    raise SystemExit(0)
state = (
    '    ) {\n'
    '        val preReleaseId = remember(item.title) {\n'
    '            if (item.subtitle.startsWith(' + BADGE + ')) {\n'
    '                com.music.amusic.data.ApplePreRelease.collectionIdOf(item.title)\n'
    '            } else {\n'
    '                null\n'
    '            }\n'
    '        }\n'
    '        var preReleaseOpen by remember(item.title) { mutableStateOf(false) }\n'
    '        Column('
)
block = block.replace(anchor, state, 1)
print('state added')

click_anchor = '.longPressMenuClickable(onClick = onClick, onLongClick = onLongPress),'
if block.count(click_anchor) != 1:
    print('PATCH ABORTED: click matches', block.count(click_anchor))
    raise SystemExit(0)
block = block.replace(
    click_anchor,
    '.longPressMenuClickable(\n'
    '                onClick = { if (preReleaseId != null) preReleaseOpen = true else onClick() },\n'
    '                onLongClick = onLongPress,\n'
    '            ),',
    1,
)
print('click patched')

# 3. The page itself, drawn over the artist page so closing it changes nothing.
k = block.find('text = item.subtitle,')
if k < 0:
    print('PATCH ABORTED: subtitle Text not found')
    raise SystemExit(0)
m = block.find(')', block.find('overflow = TextOverflow.Ellipsis,', k)) + 1
dialog = (
    '\n        if (preReleaseOpen && preReleaseId != null) {\n'
    '            PreReleasePage(\n'
    '                title = item.title,\n'
    '                artistName = null,\n'
    '                badge = item.subtitle,\n'
    '                coverUrl = item.thumbnailUrl,\n'
    '                collectionId = preReleaseId,\n'
    '                onDismiss = { preReleaseOpen = false },\n'
    '            )\n'
    '        }'
)
block = block[:m] + dialog + block[m:]
print('page call added')

path.write_text(src[:start] + block + src[end:], encoding='utf-8')
print('WROTE DetailScreen.kt')
PY

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
