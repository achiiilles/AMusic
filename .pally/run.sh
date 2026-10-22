#!/usr/bin/env bash
set -euo pipefail
OUT=.pally
mkdir -p "$OUT"
F=app/src/main/java/com/music/amusic/ui/screens/DetailScreen.kt

{
  echo "== sectioncard lines =="
  grep -n "SectionCard" "$F" || true
  echo "== PreReleasePage call =="
  grep -n "PreReleasePage" -B 4 -A 26 "$F" || true
} > "$OUT/a_sectioncard.txt"

{
  echo "== callbacks in DetailScreen =="
  grep -n "onSong\|onTrack\|onOpen\|onPlay\|onAlbum\|onArtist\|onItem" "$F" | head -120 || true
} > "$OUT/b_callbacks.txt"

{
  echo "== files =="
  find app/src/main/java/com/music/amusic -name "*.kt" | sort
} > "$OUT/c_files.txt"

{
  echo "== play/search funcs =="
  grep -rn "fun play\|fun open\|fun search\|fun playFromSearch\|fun startPlayback" app/src/main/java/com/music/amusic --include=*.kt | head -160 || true
} > "$OUT/d_funcs.txt"
