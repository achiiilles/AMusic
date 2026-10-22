#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
DS=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt
echo "=== FIX ==="
python3 - <<'PY'
import re, pathlib
ds = pathlib.Path('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt')
src = ds.read_text(encoding='utf-8')
BADGE = '"Pré-Lançamento"'
broken = 'text = item.title,maxLines = if (item.subtitle?.startsWith(' + BADGE + ') == true) 2 else 11,'
if broken not in src:
    print('FIX: broken title line not found')
    
else:
    i = src.index(broken)
    tail = src[i:]
    m = re.search(r'\n([ \t]*)overflow = TextOverflow\.Ellipsis,', tail)
    if not m:
        print('FIX ABORTED: overflow anchor not found')
        raise SystemExit(0)
    ind = m.group(1)
    fixed = (
        'text = item.title,\n'
        + ind + 'style = MaterialTheme.typography.titleMedium,\n'
        + ind + 'color = palette.onBackground,\n'
        + ind + 'maxLines = if (item.subtitle?.startsWith(' + BADGE + ') == true) 2 else 1,'
    )
    src = src[:i] + fixed + src[i + len(broken):]
    ds.write_text(src, encoding='utf-8')
    print('FIX applied, indent =', repr(ind))
echo_marker = 0
PY
echo "=== VERIFY BLOCK ==="
python3 - <<'PY'
import pathlib
src = pathlib.Path('app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt').read_text(encoding='utf-8')
start = src.index('private fun SectionCard(')
end = src.index('private fun ArtistShelfGridPage(')
print(src[start:end])
PY
if grep -q 'else 11,' "$DS"; then
  echo 'STILL BROKEN: not committing'
exit 0
fi
if grep -q 'PreReleasePage(' "$DS"; then
  git config user.name 'pally'
  git config user.email 'pally@local'
  git add -- "$DS"
  if git diff --cached --quiet; then
    echo 'NOTHING STAGED'
  else
    git commit -m 'fix: título do card de pré-lançamento em duas linhas com o estilo original [skip ci]'
    git log --oneline -1
  fi
fi
exit 0
