
import re, json, urllib.request, urllib.parse, base64
UA="Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
def req(url, headers=None):
    h={"User-Agent":UA}; h.update(headers or {})
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
            pl=base64.urlsafe_b64decode(jwt.split(".")[1]+"==").decode(); hd=base64.urlsafe_b64decode(jwt.split(".")[0]+"==").decode()
        except Exception: continue
        if "WebPlayKid" in hd or "AMPWebPlay" in pl: tok=jwt
    if tok: break
print("token", bool(tok))
H={"Authorization":"Bearer "+tok,"Origin":"https://music.apple.com","Referer":"https://music.apple.com/"}
AMP="https://amp-api.music.apple.com/v1/catalog/"
def call(sf,path,params):
    url=AMP+sf+"/"+path+("?"+urllib.parse.urlencode(params, safe=",[]") if params else "")
    st,body=req(url,H); return st,body,url
def summ(label,sf,path,params):
    st,body,url=call(sf,path,params)
    info=""
    try:
        j=json.loads(body)
        d=j.get("data")
        if d and isinstance(d,list) and isinstance(d[0],dict):
            e=d[0]
            if "views" in e: info+=" views="+json.dumps({k:len(x.get("data",[])) for k,x in e["views"].items()})
            if "relationships" in e: info+=" rels="+json.dumps({k:len(x.get("data",[])) for k,x in e["relationships"].items()})
            if "views" not in e and "relationships" not in e: info+=" data_len=%d first=%s"%(len(d),json.dumps(e.get("attributes",{}).get("name")))
        if "errors" in j: info+=" err="+j["errors"][0].get("detail","")[:120]
    except Exception: info=" body="+body[:150]
    print(label,st,url.replace(AMP,"")[:150],info)
albums={"sweetfortune":"6774223660","calico":"1676552614","boyinjeans":"1417379686","nevermind":"1440783617","folklore":"1528112358"}
for name,aid in albums.items():
    summ("related-albums "+name,"br","albums/"+aid,{"views":"related-albums,appears-on","l":"pt-BR"})
for v in ["you-might-also-like","more-by-artist","similar-albums","recommended","related","also-like","related-artists","similar","fans-also-like","other-by-artist","editorial-notes","top-listeners","essentials"]:
    summ("view "+v,"br","albums/6774223660",{"views":v})
for rel in ["related-albums","similar-albums","recommendations"]:
    summ("rel "+rel,"br","albums/6774223660",{"include":rel})
summ("relate albums","br","albums/6774223660",{"relate[albums]":"artists"})
summ("artist views","br","artists/483234172",{"views":"similar-artists,featured-albums,full-albums,latest-release,top-songs,singles,appears-on-albums,live-albums,compilation-albums"})
for v in ["related-albums"]:
    summ("artist-album-rel "+v,"br","albums/6774223660/related-albums",{})
summ("ext url","br","albums/6774223660",{"extend":"artistUrl,editorialArtwork,editorialVideo","views":"related-albums","platform":"web","with":"attributes"})
summ("fields","br","albums/6774223660",{"views":"related-albums","fields[albums]":"name,artistName","platform":"web"})
st,body,url=call("br","albums/6774223660",{"views":"related-albums,appears-on"})
j=json.loads(body); e=j["data"][0]
print("keys", list(e.keys()), "view keys", list(e.get("views",{}).keys()))
print("appears-on view sample keys", list(e["views"]["appears-on"].keys()))
