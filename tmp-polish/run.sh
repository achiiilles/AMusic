#!/bin/bash
mkdir -p tmp-polish
python3 tmp-polish/apply.py
cat tmp-polish/out-apply.txt
