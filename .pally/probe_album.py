import json, re, os, traceback, urllib.parse, urllib.request
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
out = []
def p(*a):
    out.append(' '.join(str(x) for x in a))
def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode('utf-8', 'replace')
QUERIES = [('Short n sweet', 'Sabrina Carpenter', 'shortnsweet'), ('Guts', 'Olivia Rodrigo', 'guts')]
def norm(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())
KEYHITS = {}
def walk(node, path, depth, hits):
    if depth > 60:
        return
    if isinstance(node, dict):
        for k in node.keys():
            if re.search(r'olor|radient|ackground', str(k)):
                KEYHITS[str(k)] = KEYHITS.get(str(k), 0) + 1
        art = node.get('artwork')
        if isinstance(art, dict):
            d = art.get('dictionary', art)
            if isinstance(d, dict) and 'bgColor' in d:
                hits.append((path, node, d))
        elif 'bgColor' in node:
            hits.append((path, node, node))
        for k, v in node.items():
            walk(v, path + '/' + str(k), depth + 1, hits)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + '[' + str(i) + ']', depth + 1, hits)
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
        p('PAGE', url, 'len', len(html), 'ssd', 'serialized-server-data' in html, 'bgColor count', html.count('bgColor'))
        marker = html.find('serialized-server-data')
        if marker >= 0:
            start = html.index('>', marker) + 1
            end = html.index('</script>', start)
            raw = html[start:end]
            p('SSD chars', len(raw))
            data = json.loads(raw)
            hits = []
            walk(data, '', 0, hits)
            p('HITS', len(hits))
            for path, node, d in hits[:14]:
                strs = [(str(k), str(v)[:70]) for k, v in node.items() if isinstance(v, str)]
                p('HIT path', path[-110:])
                p('  node keys', sorted(str(k) for k in node.keys())[:24])
                p('  node strings', strs[:10])
                p('  art', {k: d.get(k) for k in ['bgColor', 'textColor1', 'textColor2', 'textColor3', 'textColor4', 'width', 'height']})
            p('KEY NAMES', sorted(KEYHITS.items())[:50])
        else:
            for m in list(re.finditer('bgColor', html))[:3]:
                p('HTML CTX', html[max(0, m.start() - 150): m.start() + 150].replace(chr(10), ' '))
    except Exception as e:
        p('ERROR', title, type(e).__name__, str(e)[:300])
        p(traceback.format_exc()[-400:])
text = chr(10).join(out)
os.makedirs('.pally', exist_ok=True)
with open('.pally/probe_out.txt', 'w') as f:
    f.write(text[:60000])
print(text[:2000])
