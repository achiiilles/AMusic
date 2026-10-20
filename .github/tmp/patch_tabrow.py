import sys
p = "app/src/main/java/com/music/amusic/ui/components/floatingtabbar/FloatingTabBar.kt"
old = b".layerBackdrop(tabRow)"
new = b".then(if (glassPill) Modifier.layerBackdrop(tabRow) else Modifier)"
d = open(p, "rb").read()
assert d.count(old) == 1, d.count(old)
open(p, "wb").write(d.replace(old, new))
print("patched")
