import json, re, os, traceback, urllib.parse, urllib.request
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
out = []
def p(*a):
    out.append(' '.join(str(x) for x in a))
def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode('utf-8', 'replace')
QUERIES = [('Short n sweet', 'Sabrina Carpenter', 'shortnsweet'), ('Guts', 'Olivia Rodrigo', 'guts'), ('Espresso single', 'Sabrina Carpenter', 'espresso')]
def norm(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())
def walk2(n, pth, dep):
    if dep > 40:
        return
    if isinstance(n, dict):
        for k, v in n.items():
            if (k in ('backgroundTreatment', 'color') and not isinstance(v, (dict, list))) or k == 'gradient':
                p('KV', pth[-90:] + '/' + k, json.dumps(v)[:300])
            walk2(v, pth + '/' + str(k), dep + 1)
    elif isinstance(n, list):
        for i, v in enumerate(n):
            walk2(v, pth + '[' + str(i) + ']', dep + 1)
for title, artist, key in QUERIES:
    p('=== QUERY', title, '|', artist)
    try:
        term = urllib.parse.quote_plus(title + ' ' + artist)
        s = json.loads(get('https://itunes.apple.com/search?term=' + term + '&entity=album&limit=5'))
        res = s.get('results', [])
        p('ITUNES count', len(res))
        pick = None
        for r in res:
            p('ITUNES', r.get('collectionName'), '|', r.get('artistName'), '|', r.get('collectionId'), '|', r.get('collectionViewUrl'))
            if pick is None and key in norm(r.get('collectionName')) and norm(artist.split()[-1]) in norm(r.get('artistName')):
                pick = r
        if pick is None:
            p('NO PICK')
            continue
        url = str(pick['collectionViewUrl']).split('?')[0]
        html = get(url)
        p('PAGE', url, 'len', len(html), 'bgColor count', html.count('bgColor'))
        marker = html.find('serialized-server-data')
        if marker < 0:
            p('NO SSD')
            continue
        start = html.index('>', marker) + 1
        end = html.index('</script>', start)
        data = json.loads(html[start:end])
        hdr = data['data'][0]['data']['sections'][0]['items'][0]
        p('HEADER keys', sorted(hdr.keys()))
        p('HEADER title', hdr.get('title'), '| bg', hdr.get('backgroundTreatment'), '| color', hdr.get('color'))
        for kk in ['artwork', 'tallArtwork']:
            dd = (hdr.get(kk) or {}).get('dictionary', {})
            p('HEADER', kk, 'bgColor', dd.get('bgColor'), 'textColor1', dd.get('textColor1'))
            for g in ['gradient', 'textGradient', 'hasP3']:
                p('HEADER', kk, g, json.dumps(dd.get(g))[:900])
        walk2(data, '', 0)
    except Exception as e:
        p('ERROR', title, type(e).__name__, str(e)[:300])
        p(traceback.format_exc()[-400:])
text = chr(10).join(out)
os.makedirs('.pally', exist_ok=True)
with open('.pally/probe_out.txt', 'w') as f:
    f.write(text[:60000])
print(text[:2000])
