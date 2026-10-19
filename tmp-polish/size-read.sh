#!/bin/bash
set -u
OUT=tmp-polish/out-size.txt
ROOT=app/src/main/java
{
echo '== files that mention TopBarAccountButton'
grep -rln 'TopBarAccountButton' $ROOT
echo '== definition'
DEF=$(grep -rl 'fun TopBarAccountButton' $ROOT | head -1)
echo "file: $DEF"
L=$(grep -n 'fun TopBarAccountButton' "$DEF" | head -1 | cut -d: -f1)
sed -n "$((L-3)),$((L+120))p" "$DEF"
echo '== call sites with context'
grep -rn -B3 -A8 'TopBarAccountButton(' $ROOT | head -150
echo '== library pill lines'
grep -rn -E -i 'pill|capsule|hist' $ROOT/ui/screens/LibraryScreen.kt | head -40
} > $OUT
