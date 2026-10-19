import subprocess
p = 'app/src/main/java/com/music/amusic/ui/components/AccountProfileSelector.kt'
s = open(p, encoding='utf-8').read()
old = '                  item { SelectorAction(Icons.Rounded.Settings, stringResource(R.string.settings), onOpenSettings) }\n'
new = '                  // Linha "Configuracoes" oculta: tocar na foto agora abre Configuracoes direto. onOpenSettings continua no codigo.\n                  // item { SelectorAction(Icons.Rounded.Settings, stringResource(R.string.settings), onOpenSettings) }\n'
print('matches', s.count(old))
if s.count(old) == 1:
    open(p, 'w', encoding='utf-8').write(s.replace(old, new))
    print('patched')
print('== usages ==')
r = subprocess.run(['grep', '-rIn', '--include=*.kt', '-e', 'AccountProfileSelector(', '-e', 'onOpenSettings', 'app/src/main'], capture_output=True, text=True)
for l in r.stdout.splitlines()[:40]:
    print(l[:230])
