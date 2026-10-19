import re,sys
P="sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/ui/player/"
def edit(path, old, new, imp=None):
    t=open(path,encoding="utf8").read()
    assert t.count(old)==1, (path, old[:40], t.count(old))
    t=t.replace(old,new)
    if imp and imp not in t:
        i=t.index("\nimport ")+1
        t=t[:i]+imp+"\n"+t[i:]
    open(path,"w",encoding="utf8").write(t)
edit(P+"LandscapePlayer.kt",
"    queuePane: @Composable () -> Unit,\n    modifier: Modifier = Modifier,\n) {\n    Box(modifier = modifier.fillMaxSize()) {\n        background(Modifier.fillMaxSize())",
"    queuePane: @Composable () -> Unit,\n    modifier: Modifier = Modifier,\n    /** Alpha of the drag handle at the top; 0 while Hide Song Status is on. */\n    dismissHandleAlpha: () -> Float = { 1f },\n) {\n    Box(modifier = modifier.fillMaxSize()) {\n        background(Modifier.fillMaxSize())")
edit(P+"LandscapePlayer.kt",
"                    .width(38.dp)\n                    .height(5.dp)\n                    .shadow(2.dp, RoundedCornerShape(3.dp), clip = false)",
"                    .width(38.dp)\n                    .height(5.dp)\n                    .graphicsLayer { alpha = dismissHandleAlpha() }\n                    .shadow(2.dp, RoundedCornerShape(3.dp), clip = false)",
"import androidx.compose.ui.graphics.graphicsLayer")
edit(P+"NowPlayingScreen.kt",
"                LandscapePlayerLayout(\n                    pane = when {",
"                LandscapePlayerLayout(\n                    dismissHandleAlpha = { dismissHandleHideAlpha },\n                    pane = when {")
print("ok")
