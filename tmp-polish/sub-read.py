
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
out.append("=== artistFromSubtitle def")
grep(r"fun artistFromSubtitle",before=15,after=45,maxn=3)
out.append("=== type word lists")
grep(r'"M\u00fasica"|"Single"\s*,|"Sencillo"',before=4,after=10,maxn=12)
open("tmp-polish/out.txt","w").write("\n".join(out)[:120000])
