import re
p = 'app/src/main/java/com/music/amusic/ui/components/AccountProfileSelector.kt'
raw = open(p, 'rb').read().decode('utf-8')
print('crlf', '\r\n' in raw)
pat = re.compile(r'^([ \t]*)(item \{ SelectorAction\(Icons\.Rounded\.Settings, stringResource\(R\.string\.settings\), onOpenSettings\) \})', re.M)
ms = pat.findall(raw)
print('matches', len(ms))
if len(ms) == 1:
    nl = '\r\n' if '\r\n' in raw else '\n'
    def rep(m):
        ind = m.group(1)
        return ind + '// Linha "Configuracoes" oculta: tocar na foto agora abre Configuracoes direto. onOpenSettings continua no codigo.' + nl + ind + '// ' + m.group(2)
    new = pat.sub(rep, raw)
    open(p, 'wb').write(new.encode('utf-8'))
    print('patched')
