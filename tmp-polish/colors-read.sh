#!/bin/bash
cd app/src/main
{
echo "=== files with artistColours"
grep -rlE "artistColours|ArtistColours" .
echo "=== lines"
grep -rnE "artistColours|ArtistColours" . | cut -c1-220 | head -150
echo "=== screens"
find . -name "*.kt" | grep -iE "Detail|AlbumScreen|PlaylistScreen|ArtistScreen|FrostedTopBar|MainActivity|Glass"
} > ../../../tmp-polish/out-colors-a.txt 2>&1
