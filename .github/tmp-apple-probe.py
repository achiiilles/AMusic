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
def names(label,sf,path,params):
    st,body,url=call(sf,path,params)
    try:
        j=json.loads(body)
    except Exception:
        print(label,st,body[:200]); return
    if "errors" in j: print(label,st,url.replace(AMP,""),j["errors"][0].get("detail")); return
    if "views" in (j.get("data") or [{}])[0]:
        for k,v in j["data"][0]["views"].items():
            print(label,st,"VIEW",k,"next=",v.get("next"),"attrs=",json.dumps(v.get("attributes")),"n=",len(v.get("data",[])))
            for it in v.get("data",[]):
                a=it.get("attributes",{}); print("   ",it.get("type"),it.get("id"),a.get("name"),"|",a.get("artistName"),"|",bool(a.get("url")),bool(a.get("artwork")))
    else:
        print(label,st,url.replace(AMP,""),"next=",j.get("next"),"n=",len(j.get("data",[])))
        for it in j.get("data",[]):
            a=it.get("attributes",{}); print("   ",it.get("type"),it.get("id"),a.get("name"),"|",a.get("artistName"),"|",bool(a.get("url")),bool(a.get("artwork")))
names("P1 parent combined","br","albums/6774223660",{"views":"appears-on,you-might-also-like","include":"artists","l":"pt-BR"})
names("P2 own view","br","albums/6774223660/view/you-might-also-like",{"l":"pt-BR"})
names("P3 own view limit offset","br","albums/6774223660/view/you-might-also-like",{"offset":"0","limit":"25","l":"pt-BR"})
names("P4 own view offset 10","br","albums/6774223660/view/you-might-also-like",{"offset":"10","limit":"25","l":"pt-BR"})
names("P5 us parent","us","albums/6774223660",{"views":"you-might-also-like","l":"en-US"})
for nm,aid in {"calico":"1676552614","nevermind":"1440783617"}.items():
    st,body,url=call("br","albums/"+aid,{"views":"you-might-also-like","l":"pt-BR"})
    j=json.loads(body); v=j["data"][0].get("views",{}).get("you-might-also-like")
    print("Q",nm,st,"n=",len(v["data"]) if v else None,"next=",v.get("next") if v else None)
