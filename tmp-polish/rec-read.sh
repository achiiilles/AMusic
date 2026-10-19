#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import re
A=Path('app/src/main/java/com/music/amusic')
shared=Path('sharedUi/src/commonMain/composeResources/values-pt/strings.xml')
app=Path('app/src/main/res/values-pt/strings.xml')
def xml(p,changes,adds={}):
 s=p.read_text()
 for key,value in changes.items():
  pattern=r'(<string name="'+re.escape(key)+r'"[^>]*>)(.*?)(</string>)'
  s,n=re.subn(pattern,lambda m:m.group(1)+value+m.group(3),s,count=1,flags=re.S)
  if n!=1: print('MISSING',p,key)
 for key,value in adds.items():
  if not re.search(r'<string name="'+re.escape(key)+r'"',s):
   s=s.replace('</resources>',f'    <string name="{key}">{value}</string>\n</resources>')
 p.write_text(s)
xml(shared,{
 'audio_output':'Saída de áudio','audio_output_playing':'Reproduzindo aqui','audio_pipeline':'Caminho do áudio',
 'cast':'Transmitir','cast_casting':'Transmitindo','cast_connecting':'Conectando…','cast_row_subtitle':'Alto-falantes Chromecast e Google Cast',
 'data_saver':'Economia de dados','decrease_lyrics_offset':'Diminuir atraso da letra','increase_lyrics_offset':'Aumentar atraso da letra',
 'lyrics_offset':'Sincronização da letra','lyrics_offset_description':'Valores positivos exibem a letra mais tarde','lyrics_offset_reset':'Redefinir',
 'medium_quality':'Qualidade média','open_lyrics':'Letra','played_by':'Reproduzido por %1$s','playing_from':'Reproduzindo de %1$s',
 'wired_headphones':'Fones de ouvido com fio','usb_audio':'Áudio USB','personal_phone':'Celular de %1$s','this_phone':'Este celular',
 'instrumental':'Instrumental','playlist':'playlist','playlist_action':'Playlist','playlists':'Playlists',
 'shelf_single':'Single','search_filter_playlists':'Playlists','search_section_playlists':'Playlists'
 },{
 'watch_output':'Relógio','watch_output_subtitle':'Reproduzir no alto-falante ou nos fones do relógio',
 'previously_played':'Reproduzido anteriormente','search_addons_hint':'Buscar nos complementos',
 'search_addons_empty':'Buscar em todos os complementos ativados. As faixas tocam diretamente do complemento.',
 'search_addons_no_results':'Nenhum complemento encontrou “%1$s”.','sign_in_with_google':'Entrar com Google'
 })
xml(app,{
 'downloads':'Downloads','search_source_addons':'Complementos','playlists':'Playlists','lyrics_offset':'Sincronização da letra',
 'settings_search_hint':'Buscar nas configurações','settings_search_empty':'Nenhuma configuração corresponde a “%1$s”',
 'prefer_music_only':'Preferir versão só de áudio','prefer_music_only_subtitle':'Para vídeos musicais, mostrar os detalhes do vídeo enquanto busca e carrega a versão em áudio do catálogo.',
 'equalizer_footer':'Ajusta o som dentro do AMusic antes de chegar ao sistema.',
 'equalizer_dynamic':'Dinâmico','equalizer_manual':'Manual','equalizer_tone':'Tom','equalizer_tilt':'Inclinação','equalizer_contour':'Contorno',
 'equalizer_broad':'Amplo','equalizer_focused':'Focado',
 'equalizer_broad_footer':'Arraste para a esquerda para um som mais quente e para a direita para um som mais brilhante; para baixo reduz os médios, para cima os realça.',
 'equalizer_focused_footer':'Arraste para a esquerda para um som mais quente e para a direita para um som mais brilhante; para baixo reduz os médios, para cima os realça.',
 'equalizer_preset':'Predefinição','equalizer_bands':'Bandas','equalizer_bands_footer':'Mover uma banda substitui a predefinição por uma curva personalizada.',
 'equalizer_reset':'Redefinir todas as bandas','equalizer_balance':'Balanço','equalizer_balance_footer':'Desloca o som para um ouvido reduzindo o volume do outro.',
 'system_equalizer':'Equalizador do sistema','system_equalizer_subtitle':'Painel de áudio do dispositivo',
 'system_equalizer_footer':'É aplicado depois do equalizador do AMusic, em toda a sessão de áudio. Usar os dois aplica os dois efeitos.',
 'eq_preset_flat':'Neutro','eq_preset_acoustic':'Acústico','eq_preset_bass_boost':'Reforço de graves','eq_preset_bass_cut':'Redução de graves',
 'eq_preset_vocal':'Voz','eq_preset_treble_boost':'Reforço de agudos','eq_preset_treble_cut':'Redução de agudos',
 'eq_preset_loudness':'Intensidade','eq_preset_spoken_word':'Voz falada','eq_preset_electronic':'Eletrônico',
 'eq_preset_rock':'Rock','eq_preset_hip_hop':'Hip-hop','eq_preset_jazz':'Jazz','eq_preset_classical':'Clássica',
 'eq_preset_small_speakers':'Alto-falantes pequenos','eq_preset_late_night':'Madrugada','eq_preset_custom':'Personalizado',
 'translation_language':'Idioma da tradução','translation_language_description':'Idioma para o qual o botão de tradução converte a letra.',
 'translation_language_app_default':'Idioma do app','translation_language_subtitle':'Segue o idioma do app',
 'search_languages':'Buscar idiomas','no_languages_match':'Nenhum idioma encontrado',
 'audio_pipeline':'Caminho do áudio','cast_dialog_title':'Transmitir','cast_dialog_subtitle':'Reproduzir em um alto-falante Chromecast ou Google Cast',
 'cast_searching':'Procurando dispositivos…','cast_searching_hint':'O celular e o receptor precisam estar na mesma rede Wi-Fi.',
 'cast_device_connecting':'Conectando…','cast_device_connected':'Transmitindo','cast_stop':'Parar transmissão',
 'cast_track_unsupported':'Esta faixa não pode ser transmitida','cast_connect_failed':'Não foi possível conectar ao receptor',
 'pipeline_track_info':'Informações da faixa','pipeline_decoder':'Decodificador','pipeline_resampler':'Reamostrador',
 'pipeline_output_device':'Dispositivo de saída','pipeline_source':'Origem','pipeline_format':'Formato',
 'pipeline_bit_depth':'Profundidade de bits','pipeline_sample_rate':'Taxa de amostragem','pipeline_bitrate':'Taxa de bits',
 'pipeline_channels':'Canais','pipeline_decoder_name':'Nome do decodificador','pipeline_io_rate':'Taxa de entrada/saída'
 },{'pipeline_pcm_data_rate':'Taxa de dados PCM','replay_in_music':'na música'})
xml(Path('app/src/main/res/values/strings.xml'),{}, {'replay_in_music':'in music'})
def change(path,replacements):
 p=A/path;s=p.read_text();old=s
 for a,b in replacements:
  if a not in s: print('NO MATCH',p,a[:70]);continue
  s=s.replace(a,b)
 if s!=old:p.write_text(s)
change(Path('ui/replay/ReplayModel.kt'),[( '"This week"','context.getString(R.string.replay_this_week)'),('" in music."','" " + context.getString(R.string.replay_in_music) + "."')])
change(Path('ui/components/AccountChannelDialog.kt'),[( '"Listen as"','"Ouvir como"'),('"Looking up your channels…"','"Procurando seus canais…"'),('"Couldn\'t list this account\'s channels. You can still pick " +\n                    "one in YouTube Music itself."','"Não foi possível listar os canais desta conta. Você ainda pode escolher " +\n                    "um no próprio YouTube Music."'),('"Choose in YouTube Music"','"Escolher no YouTube Music"'),('"Brand channel"','"Canal de marca"'),('"Your channel"','"Seu canal"'),('"Close"','"Fechar"')])
change(Path('ui/screens/DiscordScreen.kt'),[( '"Online"','"Disponível"'),('"Idle"','"Ausente"'),('"Do not disturb"','"Não perturbe"'),('"Green dot"','"Ponto verde"'),('"Amber crescent — as if away"','"Lua âmbar — indica ausência"'),('"Red dash — suppresses their notifications too"','"Traço vermelho — também silencia notificações"'),('"Listening to"','"Ouvindo"'),('"Listening"','"Ouvindo"'),('"Playing"','"Jogando"'),('"Watching"','"Assistindo"'),('"Competing in"','"Competindo em"'),('"Competing"','"Competindo"')])
change(Path('MainActivity.kt'),[('"Sign in to Discord"','"Entrar no Discord"')])
change(Path('ui/MainViewModel.kt'),[('"No downloaded tracks"','"Nenhuma faixa baixada"')])
change(Path('ui/components/AudioPipelineDialog.kt'),[('val deviceName = outputStatus.deviceName.ifBlank { "System default" }','val deviceName = outputStatus.deviceName.takeUnless { it.isBlank() || it == "System default" } ?: "Padrão do sistema"'),('PipelineRow("USB Device Capability",','PipelineRow("Recursos do dispositivo USB",'),('PipelineRow("Route",','PipelineRow("Rota",'),('PipelineRow("Transport",','PipelineRow("Transporte",'),('PipelineRow("Direct",','PipelineRow("Direto",'),('PipelineRow("System",','PipelineRow("Sistema",'),('PipelineRow("Codec Bits",','PipelineRow("Bits do codec",'),('PipelineRow("Codec Sample Rate",','PipelineRow("Taxa de amostragem do codec",'),('PipelineRow("Codec Bitrate",','PipelineRow("Taxa de bits do codec",'),('PipelineRow("Codec Mode",','PipelineRow("Modo do codec",'),('"System Managed"','"Gerenciado pelo sistema"'),('"Reported by Android for the connected USB device. This describes device capabilities and may differ from the active playback format."','"Informado pelo Android para o dispositivo USB conectado. Esses recursos podem diferir do formato de reprodução ativo."'),('"Active (Direct Userspace USB)"','"Ativo (USB direto em espaço do usuário)"'),('"Active (Direct AudioTrack, Bypasses Mixer)"','"Ativo (AudioTrack direto, sem passar pelo mixer)"'),('"Rejected"','"Rejeitado"'),('"Supported (Framework Mixed)"','"Compatível (mixagem do sistema)"'),('"Not Supported (Mixed Path)"','"Incompatível (caminho com mixagem)"'),('"Direct (Bypasses System Mixer)"','"Direto (sem passar pelo mixer do sistema)"'),('"Direct path active; endpoint format not independently verified"','"Caminho direto ativo; formato de saída não verificado de forma independente"')])
PY
git config user.name "AMusic translations"
git config user.email "translations@users.noreply.github.com"
git add app/src/main/res/values/strings.xml app/src/main/res/values-pt/strings.xml sharedUi/src/commonMain/composeResources/values-pt/strings.xml app/src/main/java/com/music/amusic/ui/replay/ReplayModel.kt app/src/main/java/com/music/amusic/ui/components/AccountChannelDialog.kt app/src/main/java/com/music/amusic/ui/screens/DiscordScreen.kt app/src/main/java/com/music/amusic/MainActivity.kt app/src/main/java/com/music/amusic/ui/MainViewModel.kt app/src/main/java/com/music/amusic/ui/components/AudioPipelineDialog.kt
git commit -m 'Traduzir textos do app Android para pt-BR [skip ci]'
git push origin HEAD:polish-refresh-transitions
