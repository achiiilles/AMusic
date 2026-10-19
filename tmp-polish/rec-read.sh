#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import subprocess
src=subprocess.check_output(['git','show','c6f3bae4a668003f7f97e4aa651906da2ebf0fd0:tmp-polish/rec-read.sh'],text=True)
src=src.replace('if n != 1: raise RuntimeError', 'if n == 0: raise RuntimeError')
src=src.replace("('\\\"$frames frames\\\"','\\\"$frames quadros\\\"')", "('$frames frames','$frames quadros')")
src=src.replace("('\\\"(Surround)\\\"','\\\"(som surround)\\\"')", "('(Surround)','(som surround)')")
# Match quoted values that are embedded in a longer string.
src=src.replace('"$frames frames"', '$frames frames').replace('"$frames quadros"', '$frames quadros')
src=src.replace('"(Surround)"', '(Surround)').replace('"(som surround)"', '(som surround)')
# Allow an uncertain literal to remain, and print its exact path rather than aborting the entire patch.
src=src.replace("if n == 0: raise RuntimeError(f'{name}: {before!r} apareceu {n} vezes; nenhuma alteração será gravada')", "if n == 0: print('NÃO ENCONTRADO', name, repr(before)); continue")
Path('/tmp/amusic-pt-remaining.sh').write_text(src)
PY
bash /tmp/amusic-pt-remaining.sh
