import re, sys
p = 'sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/screens/HomeScreen.kt'
s = open(p, encoding='utf8').read()
icon = '''        Icon(
            painter = painterResource(Res.drawable.ic_logo),
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onBackground,
            modifier = Modifier
                .padding(bottom = 14.dp)
                .height(logoHeight)
                .aspectRatio(LOGO_ASPECT),
        )
'''
logo_val = '''    val logoHeight = with(LocalDensity.current) { (style.fontSize * LOGO_TO_FONT).toDp() }
'''
old_doc = ''' * Listen now's large heading, with the wordmark stacked above it.
 *
 * Only the home tab carries it \u2014 the top bar no longer shows the logo, so this
 * is where the app's mark lives. Its height is taken from the heading's own
 * font size rather than a fixed dp, so the two keep their proportion under the
 * system font scale.
 */'''
new_doc = ''' * Listen now's large heading. The app's mark no longer sits above it.
 */'''
for name, frag in (('icon', icon), ('logo_val', logo_val), ('doc', old_doc)):
    n = s.count(frag)
    print(name, n)
    if n != 1:
        sys.exit('fragment not unique: ' + name)
s = s.replace(icon, '').replace(logo_val, '').replace(old_doc, new_doc)
open(p, 'w', encoding='utf8').write(s)
print('ok')
