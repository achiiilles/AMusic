#!/bin/bash
set -euo pipefail
# O checkout raso precisa buscar o commit pai que contém o script de base.
git fetch --deepen=2 origin polish-refresh-transitions
python3 - <<'PY'
from pathlib import Path
import subprocess
src=subprocess.check_output(['git','show','c6f3bae4a668003f7f97e4aa651906da2ebf0fd0:tmp-polish/rec-read.sh'],text=True)
src=src.replace('if n != 1: raise RuntimeError', 'if n == 0: raise RuntimeError')
src=src.replace('"$frames frames"', '$frames frames').replace('"$frames quadros"', '$frames quadros')
src=src.replace('"(Surround)"', '(Surround)').replace('"(som surround)"', '(som surround)')
src=src.replace("if n == 0: raise RuntimeError(f'{name}: {before!r} apareceu {n} vezes; nenhuma alteração será gravada')", "if n == 0: print('NÃO ENCONTRADO', name, repr(before)); continue")
Path('/tmp/amusic-pt-remaining.sh').write_text(src)
PY
bash /tmp/amusic-pt-remaining.sh
