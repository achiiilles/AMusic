#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
p = Path('sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt')
s = p.read_text()
old = 'RecentSectionHeader(\n            title = shelf.title,'
new = 'RecentSectionHeader(\n            title = localizeShelfTitle(shelf.title),'
assert s.count(old) == 1, f'expected one exact Recents header, got {s.count(old)}'
p.write_text(s.replace(old, new, 1))
PY
git diff --check -- sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt
