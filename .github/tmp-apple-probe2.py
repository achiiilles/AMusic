import re, json, urllib.request, urllib.parse, base64
UA_W="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
UA_A="Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
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
scripts = sorted(set(re.findall(r"/assets/index(?:-legacy)?[~-][A-Za-z0-9_-]+\.js", html)))
tok=None
for p in scripts:
    st2, js = req("https://music.apple.com"+p)
    for jwt in set(re.findall(r"ey[A-Za-z0-9_-]+\.ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", js)):
        try:
            pl=base64.urlsafe_b64decode(jwt.split(".")[1]+"==").decode()
            hd=base64.urlsafe_b64decode(jwt.split(".")[0]+"==").decode()
        except Exception: continue
        if "WebPlayKid" in hd or "AMPWebPlay" in pl: tok=jwt
    if tok: break
print("token", bool(tok))
H={"Authorization":"Bearer "+tok,"Origin":"https://music.apple.com","Referer":"https://music.apple.com/"}
AMP="https://amp-api.music.apple.com/v1/catalog/"
def call(label, sf, path, params, ua=UA_W, raw=False):
    q = urllib.parse.urlencode(params, safe=",[]") if raw else urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    url=AMP+sf+"/"+path+("?"+q if q else "")
    st,body=req(url,H,ua)
    info=""
    try:
        j=json.loads(body)
        d=j.get("data")
        if d and isinstance(d,list) and isinstance(d[0],dict) and "views" in d[0]:
            info=" views="+json.dumps({k:len(x.get("data",[])) for k,x in d[0]["views"].items()})
        elif isinstance(d,list):
            info=" n=%d"%len(d)
        if "errors" in j: info+=" err="+json.dumps(j["errors"])[:200]
    except Exception: info=" body="+body[:150]
    print(label, st, url.replace(AMP,"")[:140], info)
    return st
YML="you-might-also-like"
st,b=req("https://itunes.apple.com/search?term=Ryan%20Beatty&entity=musicArtist&limit=3&country=br")
aid=json.loads(b)["results"][0]["artistId"]; print("artist", aid)
st,b=req("https://itunes.apple.com/lookup?id=%s&entity=album&limit=200&country=br"%aid)
rel=[(r["collectionId"],r["collectionName"]) for r in json.loads(b)["results"] if r.get("collectionId")]
print("itunes releases", rel[:8])
albums=[("calico","1676552614"),("sweetfortune","6774223660"),("nevermind","1440783617")]+[("ryan_"+n[:20],str(i)) for i,n in rel[:4]]
for name,aid_ in albums:
    print("=====",name,aid_)
    call("V1 probe-style br android raw parent","br","albums/"+aid_,{"views":"appears-on,"+YML,"include":"artists","l":"pt-BR"},UA_A,True)
    call("V2 app-style br windows %2C parent","br","albums/"+aid_,{"views":"appears-on,"+YML,"include":"artists","l":"pt-BR"},UA_W,False)
    call("V3 app-style br windows %2C parent single view","br","albums/"+aid_,{"views":YML,"l":"pt-BR"},UA_W,False)
    call("V4 own view br windows offset/limit","br","albums/"+aid_+"/view/"+YML,{"offset":"0","limit":"25","l":"pt-BR"},UA_W,False)
    call("V5 own view br android","br","albums/"+aid_+"/view/"+YML,{"offset":"0","limit":"25","l":"pt-BR"},UA_A,False)
    call("V6 own view us windows pt-BR","us","albums/"+aid_+"/view/"+YML,{"offset":"0","limit":"25","l":"pt-BR"},UA_W,False)
    call("V7 own view us en-US","us","albums/"+aid_+"/view/"+YML,{"l":"en-US"},UA_W,False)
    call("V8 own view pt windows","pt","albums/"+aid_+"/view/"+YML,{"l":"pt-BR"},UA_W,False)
    call("V9 parent us windows","us","albums/"+aid_,{"views":"appears-on,"+YML,"include":"artists","l":"pt-BR"},UA_W,False)
