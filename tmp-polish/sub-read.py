
import os,re
out=[]
files=[]
for r in ("app","shared","sharedUi"):
    for dp,dn,fn in os.walk(r):
        for f in fn:
            if f.endswith(".kt"): files.append(os.path.join(dp,f))
def grep(pat, before=0, after=0, maxn=30):
    rx=re.compile(pat); n=0
    for p in sorted(files):
        L=open(p,encoding="utf-8",errors="replace").read().split("\n")
        for i,l in enumerate(L):
            if rx.search(l):
                out.append(f"## {p}:{i+1}")
                for j in range(max(0,i-before),min(len(L),i+after+1)):
                    out.append(f"{j+1}: {L[j][:200]}")
                n+=1
                if n>=maxn: return
out.append("=== TYPE_WORDS def")
grep(r"val TYPE_WORDS",before=8,after=40,maxn=3)
out.append("=== TYPE_WORDS uses")
grep(r"TYPE_WORDS",before=0,after=0,maxn=30)
out.append("=== other localized type lists")
grep(r'(?i)"(m\u00fasica|\u00e1lbum|sencillo|canci\u00f3n|lagu)"',before=3,after=8,maxn=8)
open("tmp-polish/out.txt","w").write("\n".join(out)[:120000])
