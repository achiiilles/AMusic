
import os,re,subprocess
out=[]
roots=[r for r in ("app","shared","sharedUi") if os.path.isdir(r)]
files=[]
for r in roots:
    for dp,dn,fn in os.walk(r):
        for f in fn:
            if f.endswith(".kt"): files.append(os.path.join(dp,f))
def grep(pat, ctx=0, maxn=60, only=None):
    rx=re.compile(pat)
    n=0
    for p in sorted(files):
        if only and not re.search(only,p): continue
        L=open(p,encoding="utf-8",errors="replace").read().split("\n")
        for i,l in enumerate(L):
            if rx.search(l):
                out.append(f"## {p}:{i+1}")
                for j in range(max(0,i-ctx),min(len(L),i+ctx+1)):
                    out.append(f"{j+1}: {L[j][:220]}")
                n+=1
                if n>=maxn: return
out.append("=== class ShelfItem")
grep(r"class ShelfItem\b",ctx=25)
out.append("=== subtitle used as artist")
grep(r"artist\s*=.*subtitle|subtitle.*artist",ctx=6,maxn=40)
open("tmp-polish/out.txt","w").write("\n".join(out)[:120000])
