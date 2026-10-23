import sys

path = 'app/src/main/java/com/music/amusic/playback/PlaybackService.kt'
with open(path, encoding='utf8', newline='') as f:
    s = f.read()

old = (
    '        setMediaNotificationProvider(\n'
    '            DefaultMediaNotificationProvider.Builder(this)\n'
    '                .setChannelId(CHANNEL_ID)\n'
    '                .setChannelName(R.string.playback_channel_name)\n'
    '                .build()\n'
    '                .apply { setSmallIcon(R.drawable.ic_notification_logo) },\n'
    '        )\n'
)
new = (
    '        setMediaNotificationProvider(\n'
    '            AMusicNotificationProvider(this, CHANNEL_ID, R.string.playback_channel_name)\n'
    '                .apply { setSmallIcon(R.drawable.ic_notification_logo) },\n'
    '        )\n'
)

n = s.count(old)
if n != 1:
    print('anchor count', n)
    sys.exit(1)

s = s.replace(old, new)
with open(path, 'w', encoding='utf8', newline='') as f:
    f.write(s)
print('ok')
