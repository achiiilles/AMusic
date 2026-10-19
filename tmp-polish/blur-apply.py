import sys
F = 'app/src/main/java/com/music/amusic/data/settings/AppSettings.kt'
s = open(F, encoding='utf-8').read()
DEFAULT = 'android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.S'
reps = [
    (
        '    /** Drops haze blur (status bar, mini player, bottom fade, lyrics focus) for a solid-fill look. */\n    val reduceDynamicBlur = MutableStateFlow(false)\n',
        '    /**\n     * Drops haze blur (status bar, mini player, bottom fade, lyrics focus) for a solid-fill look.\n     * Defaults to on below Android 12 (API 31), where dynamic blur does not exist; a saved choice always wins.\n     */\n    private val reduceDynamicBlurDefault: Boolean =\n        ' + DEFAULT + '\n    val reduceDynamicBlur = MutableStateFlow(reduceDynamicBlurDefault)\n',
    ),
    (
        'reduceDynamicBlur.value = prefs.getBoolean(KEY_REDUCE_BLUR, false)',
        'reduceDynamicBlur.value = prefs.getBoolean(KEY_REDUCE_BLUR, reduceDynamicBlurDefault)',
    ),
]
for old, new in reps:
    n = s.count(old)
    if n != 1:
        print('ABORT: expected 1 match, got', n, 'for', old[:60])
        sys.exit(1)
    s = s.replace(old, new)
open(F, 'w', encoding='utf-8').write(s)
print('patched')
