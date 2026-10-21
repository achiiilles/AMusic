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
def walk(o, path, acc):
    if isinstance(o, dict):
        if 'bgColor' in o or 'gradient' in o:
            acc.append((path, {k: o[k] for k in o if k in ('bgColor', 'gradient', 'textGradient', 'textColor1')}))
        for k, v in o.items():
            walk(v, path + '/' + k, acc)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, path + '[' + str(i) + ']', acc)
try:
    q = urllib.parse.urlencode({'term': 'Billie Eilish dont smile at me', 'types': 'albums', 'limit': '6', 'extend': 'editorialVideo'})
    data = json.loads(get('https://amp-api.music.apple.com/v1/catalog/us/search?' + q, H))
    for rec in data['results']['albums']['data']:
        a = rec['attributes']
        p('ALBUM', rec['id'], a.get('name'), '|', a.get('artistName'), '| artwork', json.dumps({k: a['artwork'][k] for k in a['artwork'] if k not in ('url',)}))
        ev = a.get('editorialVideo')
        p('  EDITORIALVIDEO', 'present' if ev else 'absent')
        acc = []
        walk(ev, 'editorialVideo', acc)
        for path, d in acc:
            p('  COLOR', path, json.dumps(d))
except Exception as e:
    p('SEARCH ERROR', type(e).__name__, str(e)[:300])
text = chr(10).join(out)
os.makedirs('.pally', exist_ok=True)
with open('.pally/probe_dsam_out.txt', 'w') as f:
    f.write(text[:60000])
print(text[:3000])
