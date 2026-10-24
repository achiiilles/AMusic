
import re, json, urllib.request, urllib.parse, base64, subprocess
UA_W="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
def req(url, headers=None, ua=UA_W):
    h={"User-Agent":ua}; h.update(headers or {})
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=30)
        return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
    except Exception as e:
        return -1, repr(e)
st, html = req("https://music.apple.com/us/browse")
scripts = list(dict.fromkeys(re.findall(r"/assets/index(?:-legacy)?[~-][A-Za-z0-9_-]+\.js", html)))
print("scripts", scripts)
toks=[]
for p in scripts:
    st2, js = req("https://music.apple.com"+p)
    for jwt in dict.fromkeys(re.findall(r"ey[A-Za-z0-9_-]+\.ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", js)):
        try:
            pl=base64.urlsafe_b64decode(jwt.split(".")[1]+"==").decode()
            hd=base64.urlsafe_b64decode(jwt.split(".")[0]+"==").decode()
        except Exception: continue
        exp=re.search(r'"exp"\s*:\s*(\d+)',pl)
        toks.append((p,jwt,hd,pl,int(exp.group(1)) if exp else None))
print("n tokens", len(toks))
for i,(p,jwt,hd,pl,exp) in enumerate(toks):
    print("TOK",i,p[-20:],"hd=",hd[:80],"pl=",pl[:120],"exp",exp,"webplay", ("WebPlayKid" in hd or "AMPWebPlay" in pl))
AMP="https://amp-api.music.apple.com/v1/catalog/"
def hdr(t): return {"Authorization":"Bearer "+t,"Origin":"https://music.apple.com","Referer":"https://music.apple.com/"}
def summ(st,body):
    try:
        j=json.loads(body); d=j.get("data")
        if d and isinstance(d,list) and isinstance(d[0],dict) and "views" in d[0]:
            return "views="+json.dumps({k:len(x.get("data",[])) for k,x in d[0]["views"].items()})
        if isinstance(d,list): return "n=%d"%len(d)
        return body[:150]
    except Exception: return body[:150]
for i,(p,jwt,hd,pl,exp) in enumerate(toks):
    for alb in ["1676552614","6774223660"]:
        u=AMP+"br/albums/"+alb+"?views=appears-on%2Cyou-might-also-like&include=artists&l=pt-BR"
        st,b=req(u,hdr(jwt)); print("TOKTEST",i,alb,"parent",st,summ(st,b))
        u=AMP+"br/albums/"+alb+"/view/you-might-also-like?offset=0&limit=25&l=pt-BR"
        st,b=req(u,hdr(jwt)); print("TOKTEST",i,alb,"own",st,summ(st,b))
tok=[t for t in toks if ("WebPlayKid" in t[2] or "AMPWebPlay" in t[3])]
tok=tok[0][1] if tok else toks[0][1]
def curl(label,url,extra):
    cmd=["curl","-s","-o","/tmp/o.txt","-w","%{http_code} %{http_version}","-H","Authorization: Bearer "+tok,"-H","Origin: https://music.apple.com","-H","Referer: https://music.apple.com/","-A",UA_W]+extra+[url]
    r=subprocess.run(cmd,capture_output=True,text=True)
    body=open("/tmp/o.txt","rb").read().decode("utf-8","replace")
    print("CURL",label,r.stdout,summ(0,body))
for alb in ["1676552614","6774223660"]:
    pu=AMP+"br/albums/"+alb+"?views=appears-on%2Cyou-might-also-like&include=artists&l=pt-BR"
    ou=AMP+"br/albums/"+alb+"/view/you-might-also-like?offset=0&limit=25&l=pt-BR"
    curl("http2 gzip parent",pu,["--http2","--compressed"])
    curl("http1.1 gzip parent",pu,["--http1.1","--compressed"])
    curl("http2 gzip own",ou,["--http2","--compressed"])
    curl("http1.1 gzip own",ou,["--http1.1","--compressed"])
    curl("http2 gzip Accept-Language pt-BR parent",pu,["--http2","--compressed","-H","Accept-Language: pt-BR,pt;q=0.9"])
    curl("no-l parent",AMP+"br/albums/"+alb+"?views=you-might-also-like",["--http2","--compressed"])
