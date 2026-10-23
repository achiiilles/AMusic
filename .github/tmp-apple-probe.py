import re, json, urllib.request, urllib.parse, base64, sys
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
print("browse", st, "scripts", len(scripts))
tok=None
for p in scripts:
    st2, js = req("https://music.apple.com"+p)
    for jwt in set(re.findall(r"ey[A-Za-z0-9_-]+\.ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", js)):
        try:
            pl=base64.urlsafe_b64decode(jwt.split(".")[1]+"==").decode()
            hd=base64.urlsafe_b64decode(jwt.split(".")[0]+"==").decode()
        except Exception: continue
        if "WebPlayKid" in hd or "AMPWebPlay" in pl:
            tok=jwt
    if tok: break
print("token found", bool(tok))
H={"Authorization":"Bearer "+tok,"Origin":"https://music.apple.com","Referer":"https://music.apple.com/"}
AMP="https://amp-api.music.apple.com/v1/catalog/"
ALB="6774223660"
def show(label, sf, path, params):
    url=AMP+sf+"/"+path+("?"+urllib.parse.urlencode(params, safe=",[]") if params else "")
    st,body=req(url,H)
    info=""
    try:
        j=json.loads(body)
        if "data" in j and j["data"] and isinstance(j["data"],list) and "views" in (j["data"][0] if isinstance(j["data"][0],dict) else {}):
            v=j["data"][0]["views"]
            info=" views="+json.dumps({k:len(x.get("data",[])) for k,x in v.items()})
        elif "data" in j:
            info=" data_len=%d next=%s"%(len(j["data"]), j.get("next"))
        if "errors" in j: info+=" errors="+json.dumps(j["errors"])[:300]
    except Exception:
        info=" body="+body[:200]
    print(label, st, url.replace(AMP,""), info)
for sf in ["br","us"]:
    l="pt-BR" if sf=="br" else "en-US"
    show("A app-parent",sf,"albums/"+ALB,{"views":"appears-on,related-albums","include":"artists","l":l})
    show("B +platform web",sf,"albums/"+ALB,{"views":"appears-on,related-albums","include":"artists","l":l,"platform":"web"})
    show("C all views web",sf,"albums/"+ALB,{"views":"appears-on,other-versions,related-albums,related-videos","include":"artists,tracks","platform":"web","l":l})
    show("C2 all views no l",sf,"albums/"+ALB,{"views":"appears-on,other-versions,related-albums,related-videos"})
    show("C3 related only",sf,"albums/"+ALB,{"views":"related-albums"})
    show("D1 view l",sf,"albums/"+ALB+"/view/related-albums",{"l":l})
    show("D2 view none",sf,"albums/"+ALB+"/view/related-albums",{})
    show("D3 view web",sf,"albums/"+ALB+"/view/related-albums",{"platform":"web","l":l})
    show("D4 view limit",sf,"albums/"+ALB+"/view/related-albums",{"limit":"10"})
    show("D5 view offset",sf,"albums/"+ALB+"/view/related-albums",{"offset":"0","limit":"25","l":l})
    show("D6 appears-on view",sf,"albums/"+ALB+"/view/appears-on",{"l":l})
    show("D7 appears-on view paged",sf,"albums/"+ALB+"/view/appears-on",{"offset":"10","limit":"25","l":l})
    show("D8 other-versions view",sf,"albums/"+ALB+"/view/other-versions",{})
show("E related relationship","br","albums/"+ALB+"/related-albums",{})
show("F artist views","br","artists/483234172",{"views":"full-albums,singles","l":"pt-BR"})
show("G album plain","br","albums/"+ALB,{})
