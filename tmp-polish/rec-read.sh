#!/bin/bash
O=tmp-polish/out-rec.txt
: > $O
g() { echo "=== $1" >> $O; shift; grep -rnE --include=*.kt "$@" . 2>/dev/null | grep -vE '/(desktop|tv|wear)[A-Za-z]*/|/build/' | cut -c1-230 | head -40 >> $O; }
g "replay" 'This week| in music\.'
g "channel" 'Looking up your channels|Brand channel|Your channel'
g "discord" 'Sign in to Discord|"Online"|"Idle"|"Listening"|Playing…|Playing\.\.\.'
g "pipeline" 'System default|USB Device Capability'
g "downloaded" 'No downloaded tracks'
g "eq" -i 'footer|preamp|Reset to flat|Bass boost'
g "artistalbum" '"Artist"|"Album"|"Song"|"Video"|"Playlist"|"Podcast"'
g "hlgl" '"hl"|"gl"|hl *=|gl *=|"clientName"|Locale\.|"en"|"en-US"|"US"'
echo "=== files" >> $O
find . -name 'InnertubeParser*.kt' -o -name 'Innertube*.kt' | grep -v build | head -20 >> $O
echo "=== Text literals" >> $O
grep -rnE --include=*.kt 'Text\("[A-Z][a-z]+' app sharedUi 2>/dev/null | grep -vE '/(desktop|tv|wear)' | cut -c1-200 | head -80 >> $O
echo "=== named literals" >> $O
grep -rnE --include=*.kt '(contentDescription|label|title|subtitle|placeholder|text) *= *"[A-Z][a-z]+' app sharedUi 2>/dev/null | grep -vE '/(desktop|tv|wear)' | cut -c1-200 | head -80 >> $O
