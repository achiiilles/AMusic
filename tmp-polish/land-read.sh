#!/bin/bash
O=tmp-polish
for c in 88730d5 2f12e3c 166b48d fee5b92 c054388 d93e8d2; do git show --stat=200 --format='== %h %s' $c; done | cut -c1-230 > $O/out-land-a.txt
git show 88730d5 -U3 --format='== %h' | cut -c1-200 > $O/out-land-b.txt
