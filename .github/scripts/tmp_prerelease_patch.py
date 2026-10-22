import re
import subprocess
import sys

PATH = 'shared/src/jvmSharedMain/kotlin/com/music/amusic/data/YtMusicRepository.kt'
PATTERN = re.compile(
    r'^([ \t]*)page\.copy\(songs = resolvedSongs, sections = fullShelves\)[ \t]*$',
    re.MULTILINE,
)


def run(*args):
    done = subprocess.run(args, capture_output=True, text=True)
    print('$', ' '.join(args))
    print(done.stdout)
    print(done.stderr)
    print('exit', done.returncode)
    return done.returncode


with open(PATH, encoding='utf-8') as handle:
    text = handle.read()

found = PATTERN.findall(text)
print('anchor occurrences', len(found))
if len(found) != 1:
    print('ABORT: the anchor must appear exactly once; nothing was written')
    sys.exit(2)

indent = found[0]
replacement = (
    indent + 'val preRelease = ApplePreRelease.shelf(page.name)\n'
    + indent + 'page.copy(\n'
    + indent + '    songs = resolvedSongs,\n'
    + indent + '    sections = listOfNotNull(preRelease) + fullShelves,\n'
    + indent + ')\n'
)

patched = PATTERN.sub(lambda _match: replacement, text, count=1)
if patched == text:
    print('ABORT: nothing changed')
    sys.exit(2)

with open(PATH, 'w', encoding='utf-8') as handle:
    handle.write(patched)
print('patched', PATH)

run('git', 'diff', '--stat')
run('git', 'diff', '--', PATH)
run('git', 'config', 'user.name', 'achiiilles')
run('git', 'config', 'user.email', 'achillesh74@gmail.com')
run('git', 'add', PATH)
run('git', 'commit', '-m', 'Pagina do artista lista os pre-lancamentos do Apple Music [skip ci]')
if run('git', 'push', 'origin', 'HEAD:polish-refresh-transitions') != 0:
    print('ABORT: push failed')
    sys.exit(3)
print('pushed')
