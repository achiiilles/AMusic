#!/usr/bin/env bash
set -uo pipefail
cd "$GITHUB_WORKSPACE"
git config user.name 'pally'
git config user.email 'pally@local'
git rm -r -q --cached .pally || echo 'git rm .pally failed'
git rm -q --cached .github/workflows/_pally_probe.yml || echo 'git rm workflow failed'
rm -rf .pally
git add -A -- .pally .github/workflows/_pally_probe.yml || true
echo '=== STATUS ==='
git status --short
git commit -m 'chore: remove os arquivos temporários do diagnóstico [skip ci]'
echo '=== PUSH ==='
git push origin HEAD:polish-refresh-transitions || echo 'push failed'
git log --oneline -1
exit 0
