import json, re, os, base64, time, urllib.parse, urllib.request
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
out = []
def p(*a):
    out.append(' '.join(str(x) for x in a))
def get(url, headers=None):
    h = {'User-Agent': UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode('utf-8', 'replace')
def b64(s):
    s += '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s).decode('utf-8', 'replace')
token = None
try:
    html = get('https://music.apple.com/us/browse')
    scripts = sorted(set(re.findall(r'/assets/index(?:-legacy)?[~-][A-Za-z0-9_-]+\.js', html)))
    now = time.time()
    for path in scripts:
        js = get('https://music.apple.com' + path)
        cands = sorted(set(re.findall(r'ey[A-Za-z0-9_-]+\.ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', js)))
        good = []
        for c in cands:
            try:
                parts = c.split('.')
                hd = b64(parts[0]); pl = b64(parts[1])
                m = re.search(r'"exp"\s*:\s*(\d+)', pl)
                if m and int(m.group(1)) > now:
                    good.append((c, 'WebPlayKid' in hd or 'AMPWebPlay' in pl))
            except Exception:
                pass
        if good:
            token = ([c for c, w in good if w] or [good[0][0]])[0]
            break
except Exception as e:
    p('TOKEN ERROR', type(e).__name__, str(e)[:200])
p('TOKEN', bool(token))
H = {'Authorization': 'Bearer ' + str(token), 'Origin': 'https://music.apple.com', 'Referer': 'https://music.apple.com/'}
IDS = [('Short n Sweet', '1752214909'), ('Guts', '1694767605'), ('Espresso', '1744253545'), ('Man Best Friend', '1819861154')]
def walk(o, path, acc):
    if isinstance(o, dict):
        if 'bgColor' in o or 'gradient' in o:
            acc.append((path, {k: o[k] for k in o if k in ('bgColor', 'gradient', 'textGradient', 'textColor1')}))
        for k, v in o.items():
            walk(v, path + '/' + k, acc)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, path + '[' + str(i) + ']', acc)
for name, aid in IDS:
    p('=== ALBUM BY ID', name, aid)
    try:
        url = 'https://amp-api.music.apple.com/v1/catalog/us/albums/' + aid + '?extend=editorialVideo'
        data = json.loads(get(url, H))
        a = data['data'][0]['attributes']
        p('ATTR KEYS', sorted(a.keys()))
        p('ARTWORK', json.dumps({k: a['artwork'][k] for k in a['artwork'] if k != 'url'}))
        ev = a.get('editorialVideo')
        p('EDITORIALVIDEO', 'present' if ev else 'absent', sorted(ev.keys()) if ev else '')
        acc = []
        walk(ev, 'editorialVideo', acc)
        for path, d in acc:
            p('COLOR', path, json.dumps(d))
    except Exception as e:
        p('ERROR', type(e).__name__, str(e)[:300])
    try:
        page = get('https://music.apple.com/us/album/' + aid)
        m = re.search(r'<script[^>]*id="serialized-server-data"[^>]*>(.*?)</script>', page, re.S)
        ssd = json.loads(m.group(1))
        item = ssd['data'][0]['data']['sections'][0]['items'][0]
        p('WEB HEADER id', item.get('id'))
        for key in ('artwork', 'tallArtwork'):
            d = (item.get(key) or {}).get('dictionary') or {}
            p('WEB', key, 'bg', d.get('bgColor'), 'gradient', json.dumps(d.get('gradient')), 'text1', d.get('textColor1'))
        cont = ssd['data'][0]['data']['sections'][1].get('containerArtwork', {}).get('dictionary', {})
        p('WEB containerArtwork bg', cont.get('bgColor'))
    except Exception as e:
        p('WEB ERROR', type(e).__name__, str(e)[:300])
text = chr(10).join(out)
os.makedirs('.pally', exist_ok=True)
with open('.pally/probe_out.txt', 'w') as f:
    f.write(text[:60000])
print(text[:3000])
