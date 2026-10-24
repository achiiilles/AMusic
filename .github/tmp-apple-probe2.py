
import re, json, urllib.request, urllib.parse, base64
UA_W="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
def req(url, headers=None):
    h={"User-Agent":UA_W}; h.update(headers or {})
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=30)
        return r.status, r.read().decode("utf-8","replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8","replace")
    except Exception as e:
        return -1, repr(e)
st, html = req("https://music.apple.com/us/browse")
scripts = sorted(set(re.findall(r"/assets/index(?:-legacy)?[~-][A-Za-z0-9_-]+\.js", html)))
tok=None
for p in scripts:
    st2, js = req("https://music.apple.com"+p)
    for jwt in dict.fromkeys(re.findall(r"ey[A-Za-z0-9_-]+\.ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", js)):
        try:
            hd=base64.urlsafe_b64decode(jwt.split(".")[0]+"==").decode()
        except Exception: continue
        if "WebPlayKid" in hd and not tok: tok=jwt
print("token", bool(tok))
AMP="https://amp-api.music.apple.com/v1/catalog"
APPH={"Authorization":"Bearer "+tok,"Origin":"https://music.apple.com","Referer":"https://music.apple.com/"}
BARE={"Authorization":"Bearer "+tok}
def cnt(body, name):
    try:
        v=json.loads(body)["data"][0]["views"].get(name)
        return None if v is None else len(v.get("data",[]))
    except Exception as e:
        return "x"
def probe(sf, aid, hdr):
    q=urllib.parse.urlencode({"views":"appears-on,you-might-also-like","include":"artists","l":"pt-BR"}, quote_via=urllib.parse.quote)
    s1,b1=req(f"{AMP}/{sf}/albums/{aid}?{q}", hdr)
    s2,b2=req(f"{AMP}/{sf}/albums/{aid}/view/you-might-also-like?offset=0&limit=25&l=pt-BR", hdr)
    return s1, cnt(b1,"you-might-also-like"), s2
names=["Ryan Beatty","Bad Bunny","Tame Impala","Billie Eilish","Anitta","Djavan"]
for nm in names:
    s,b=req("https://itunes.apple.com/search?term="+urllib.parse.quote(nm)+"&entity=musicArtist&limit=1&country=br")
    try: aid=json.loads(b)["results"][0]["artistId"]
    except Exception: print("noartist",nm); continue
    s,b=req(f"https://itunes.apple.com/lookup?id={aid}&entity=album&limit=200&country=br")
    cols=[x for x in json.loads(b).get("results",[]) if x.get("wrapperType")=="collection"][:6]
    print("=====",nm,aid,len(cols))
    for c in cols:
        cid=c["collectionId"]
        a=probe("br",cid,APPH); b_=probe("br",cid,BARE); u=probe("us",cid,APPH)
        print(cid,c["collectionName"][:30],"| br app-headers",a,"| br bare",b_,"| us app-headers",u)
