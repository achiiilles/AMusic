#!/bin/bash
set -euo pipefail
O=tmp-polish/out-rec.txt
: > "$O"
python3 - <<'PY' >> "$O" 2>&1
from pathlib import Path
p='app/src/main/java/com/music/amusic/'
replacements={
 p+'ui/components/AudioPipelineDialog.kt':[
 ('"No — DSD converted to PCM"','"Não — DSD convertido para PCM"'),
 ('"No — loudness normalization"','"Não — normalização de volume"'),
 ('"No — equalizer"','"Não — equalizador"'),
 ('"No — spatial audio"','"Não — áudio espacial"'),
 ('"Yes${outputExactDetail','"Sim${outputExactDetail'),
 ('"No — ${outputExactDetail ?: "converted downstream"}"','"Não — ${outputExactDetail ?: "convertido após a decodificação"}"'),
 ('"DSD to PCM (native FIR decimator)"','"DSD para PCM (decimador FIR nativo)"'),
 ('"FIR decimation ×','"Decimação FIR ×'),
 ('"None"','"Nenhum"'),
 ('"Resampler"','"Reamostrador"'),
 ('"DSD to PCM, full band below the cutoff"','"DSD para PCM, faixa inteira abaixo do corte"'),
 ('"Passthrough"','"Passagem direta"'),
 ('"Resampled"','"Reamostrado"'),
 ('"DSD to PCM"','"DSD para PCM"'),
 ('"Flat"','"Plano"'),
 ('"$frames frames"','"$frames quadros"'),
 ('"(Surround)"','"(som surround)"'),
 ('"AudioFlinger Mixer $mixerRate','"Mixer AudioFlinger $mixerRate'),
 ('PipelineRow("Fallback", fallbackText)','PipelineRow("Alternativa", fallbackText)'),
 ],
 p+'download/DownloadService.kt':[
 ('"Downloading ${runningStates.size} songs"','"Baixando ${runningStates.size} músicas"'),
 ('"Downloading"','"Baixando"'),
 ('"$waiting more queued"','"Mais $waiting na fila"'),
 ('"Starting"','"Iniciando"'),
 ('"${song.artist} · $waiting more queued"','"${song.artist} · mais $waiting na fila"'),
 ('"Cancel"','"Cancelar"'),
 ('"Downloads",','"Downloads",'),
 ('"Songs being saved to your Music folder"','"Músicas sendo salvas na sua pasta de músicas"'),
 ],
 p+'playback/audio/DirectAudioProbe.kt':[
 ('"Direct playback not supported or API < 33"','"Reprodução direta incompatível ou Android anterior à API 33"'),
 ('"Direct PCM supported: "','"PCM direto compatível: "'),
 ('"Direct PCM not exposed for $sampleRateHz Hz (AudioFlinger mixer route)"','"PCM direto indisponível a $sampleRateHz Hz (rota do mixer AudioFlinger)"'),
 ],
 p+'data/sources/SourceKind.kt':[
 ('label = "Addon"','label = "Complemento"'),
 ('"An addon server you host or were given a link to. Searched and streamed over "','"Servidor de complemento seu ou recebido por link. Pesquisa e transmissão por "'),
 ('"plain HTTP — no code is downloaded or run."','"HTTP comum — nenhum código é baixado ou executado."'),
 ('label = "Custom module"','label = "Módulo personalizado"'),
 ('"Your own compatible module index. Tried before the built-in one."','"Seu índice de módulos compatíveis. É consultado antes do integrado."'),
 ('label = "Module source"','label = "Fonte de módulos"'),
 ('"A URL to a compatible module index. Modules are JS plugins that "','"URL de um índice de módulos compatíveis. Os módulos são extensões JS que "'),
 ('"can search and stream from services like Tidal, Qobuz, Apple Music and more."','"pesquisam e transmitem de serviços como Tidal, Qobuz e Apple Music."'),
 ('"Optional JioSaavn streams up to 320kbps AAC/MP4. Catalogue matching can select the wrong song."','"Transmissão opcional do JioSaavn em até 320 kbps AAC/MP4. A correspondência do catálogo pode escolher a música errada."'),
 ('"High Quality"','"Alta qualidade"'),
 ('"The full catalogue, at Opus up to about 171 kbps. Lossy — there is no "','"Catálogo completo, em Opus até cerca de 171 kbps. Com perdas — não há "'),
 ('"lossless rendition to ask for."','"versão sem perdas disponível."'),
 ('"Lossy", "Full catalogue", "Radio"','"Com perdas", "Catálogo completo", "Rádio"'),
 ],
 'shared/src/jvmSharedMain/kotlin/com/music/amusic/data/lyrics/LyricsSource.kt':[
 ('"Apple timings by recording, syllable by syllable"','"Sincronia do Apple Music por gravação, sílaba por sílaba"'),
 ('"The same Apple timings, matched on the recording itself"','"Mesma sincronia do Apple Music, associada à gravação"'),
 ('"Apple Music timings, word by word"','"Sincronia do Apple Music, palavra por palavra"'),
 ('"QQ Music karaoke timings through BetterLyrics"','"Sincronia de karaokê do QQ Music via BetterLyrics"'),
 ('"Apple Music timings through the original keyless provider"','"Sincronia do Apple Music via provedor original sem chave"'),
 ('"Spotify lyrics with PaxSenix fallback; API key required"','"Letras do Spotify com alternativa PaxSenix; requer chave de API"'),
 ('"Musixmatch timings with PaxSenix fallback; API key required"','"Sincronia do Musixmatch com alternativa PaxSenix; requer chave de API"'),
 ('"Syllable by syllable, on community mirrors"','"Sílaba por sílaba, em servidores da comunidade"'),
 ('"Matched on the video, so never the wrong edit"','"Associado ao vídeo, evitando versões diferentes"'),
 ('"Contributed by listeners, so it has what nobody licensed"','"Contribuições de ouvintes, incluindo letras sem licença comercial"'),
 ('label = "YouTube captions"','label = "Legendas do YouTube"'),
 ('"Timed captions matched to the exact playing video"','"Legendas sincronizadas com o vídeo em reprodução"'),
 ('"Plain lyrics from the playing video\'s Lyrics tab"','"Letras simples da aba Letras do vídeo em reprodução"'),
 ('"Community-made, whole-line LRC"','"LRC comunitário sincronizado por linha"'),
 ('"Whole lines, strong outside the English catalogue"','"Sincronia por linha, boa cobertura fora do catálogo inglês"'),
 ('"Whole lines only, and always up"','"Apenas linhas inteiras, com alta disponibilidade"'),
 ('"Whole lines, from the biggest lyrics database there is"','"Sincronia por linha de um grande catálogo de letras"'),
 ('"Plain text fallback, massive web catalogue"','"Alternativa em texto simples, com amplo catálogo na web"'),
 ],
}
original={}; edited={}
for name, changes in replacements.items():
    path=Path(name); text=path.read_text(); original[name]=text
    for before,after in changes:
        if before==after: continue
        n=text.count(before)
        if n != 1: raise RuntimeError(f'{name}: {before!r} apareceu {n} vezes; nenhuma alteração será gravada')
        text=text.replace(before,after)
    edited[name]=text
for name,text in edited.items():
    Path(name).write_text(text)
    print('ALTERADO',name)
PY
git config user.name 'AMusic translations'
git config user.email 'translations@users.noreply.github.com'
git add app/src/main/java/com/music/amusic/ui/components/AudioPipelineDialog.kt app/src/main/java/com/music/amusic/download/DownloadService.kt app/src/main/java/com/music/amusic/playback/audio/DirectAudioProbe.kt app/src/main/java/com/music/amusic/data/sources/SourceKind.kt shared/src/jvmSharedMain/kotlin/com/music/amusic/data/lyrics/LyricsSource.kt
git commit -m 'Traduzir textos restantes de áudio, fontes e notificações [skip ci]' >> "$O" 2>&1
git push origin HEAD:polish-refresh-transitions >> "$O" 2>&1
