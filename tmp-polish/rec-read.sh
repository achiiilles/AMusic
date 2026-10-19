#!/bin/bash
O=tmp-polish/out-rec.txt
: > $O
FILES=$( (find app/src/main/java -name '*.kt'; find sharedUi/src -name '*.kt' -path '*Main*'; find shared/src -name '*.kt' -path '*Main*') | grep -vE '/(desktop|tv|wear|test|debug|jvmTest|androidTest)|Test\.kt|Preview' )
echo "=== counts per file (candidate literals)" >> $O
for f in $FILES; do
  n=$(grep -E '^\s*[^/*].*' "$f" | grep -vE 'Log\.|TAG|throw |require|check\(|error\(|println|^\s*(//|\*)|import |@(SerialName|Json)|stringResource|getString|R\.string' | grep -oE '(label|title|subtitle|text|placeholder|contentDescription|hint|description|message|Text|PipelineRow|PipelineNote|PipelineSection|AlertAction|Toast\.makeText\([^"]*)[ (=]*"[A-Z][^"$\\]{2,}"' | wc -l)
  [ "$n" -gt 0 ] && echo "$n $f" >> $O
done
echo "=== literals" >> $O
for f in $FILES; do
  grep -nE '^\s*[^/*].*' "$f" | grep -vE 'Log\.|TAG|throw |require|check\(|error\(|println|import |@(SerialName|Json)|stringResource|getString|R\.string' | grep -oE '^[0-9]+:|(label|title|subtitle|text|placeholder|contentDescription|hint|description|message|Text|PipelineRow|PipelineNote|PipelineSection|AlertAction)[ (=]*"[A-Z][^"$\\]{2,}"' | awk -v f="$f" '/^[0-9]+:$/{ln=$0; next} {print f":"ln" "$0}' 
done | sed 's#app/src/main/java/com/music/amusic/#A/#; s#sharedUi/src/jvmSharedMain/kotlin/com/music/amusic/#SU/#; s#shared/src/jvmSharedMain/kotlin/com/music/amusic/#S/#' | cut -c1-170 | head -450 >> $O
