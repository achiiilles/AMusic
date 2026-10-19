#!/bin/bash
OUT=tmp-polish/acct-out.txt
: > $OUT
{
echo '== files =='
grep -rIl --include=*.kt --include=*.xml -e 'Alternar conta' -e 'switch_account' -e 'SwitchAccount' -e 'AccountSwitch' app/src/main 2>/dev/null
echo
echo '== lines =='
grep -rIn --include=*.kt --include=*.xml -e 'Alternar conta' -e 'switch_account' -e 'SwitchAccount' -e 'AccountSwitch' app/src/main 2>/dev/null | cut -c1-220 | head -60
echo
echo '== Gerenciar contas lines =='
grep -rIn --include=*.kt --include=*.xml -e 'Gerenciar contas' -e 'manage_accounts' -e 'ManageAccounts' app/src/main 2>/dev/null | cut -c1-220 | head -40
} >> $OUT 2>&1
