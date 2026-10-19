import re, sys
P = 'app/src/main/java/com/music/amusic/ui/components/FrostedTopBar.kt'
s = open(P, encoding='utf-8').read()
n1 = len(re.findall(r'private const val TOP_BAR_VEIL_FILL_ALPHA = 0\.07f', s))
n2 = len(re.findall(r'veil -> Modifier\s*\.background\(Color\.White\.copy\(alpha = TOP_BAR_VEIL_FILL_ALPHA \* veilAmount\), shape\)', s))
print('matches', n1, n2)
if n1 != 1 or n2 != 1:
    sys.exit(3)
s = re.sub(r'(private const val TOP_BAR_VEIL_FILL_ALPHA = 0\.07f)',
           r'\1\n\n/** Backing of the same circles in the page surface colour, so back, share and the playlist pill stay visible over light and dark artwork. */\nprivate const val TOP_BAR_VEIL_BACKING_ALPHA = 0.72f', s, count=1)
s = re.sub(r'veil -> Modifier(\s*)\.background\(Color\.White\.copy\(alpha = TOP_BAR_VEIL_FILL_ALPHA \* veilAmount\), shape\)',
           lambda m: 'veil -> Modifier' + m.group(1) + '.background(container.copy(alpha = TOP_BAR_VEIL_BACKING_ALPHA * veilAmount), shape)' + m.group(1) + '.background(Color.White.copy(alpha = TOP_BAR_VEIL_FILL_ALPHA * veilAmount), shape)', s, count=1)
open(P, 'w', encoding='utf-8').write(s)
print('patched')
