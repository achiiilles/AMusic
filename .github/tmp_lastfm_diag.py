import os, re, json, sys, unicodedata, base64, time, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

KEY = os.environ.get("LASTFM_API_KEY", "").strip()
ARTIST = os.environ.get("ARTIST", "Olivia Rodrigo")
CURRENT_ALBUM = os.environ.get("CURRENT_ALBUM", "GUTS")
SF = os.environ.get("STOREFRONT", "br")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/122.0.0.0 Safari/537.36")
SIMILAR_LIMIT = 50
TOPALBUMS_LIMIT = 12
CANDIDATES = 4
PER_ARTIST = 2
MAX_CARDS = 30
FLOORS = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4]

def n(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()

PAREN = re.compile(r"\s*[(\[][^)\]]*\b(?:pa version|explicit|clean|deluxe|remaster(?:ed)?|expanded|edition|version|bonus|anniversary|edited|special)\b[^)\]]*[)\]]", re.I)
DASH = re.compile(r"\s+-\s+(?:single|ep)\s*\Z", re.I)
def clean(raw):
    st = DASH.sub("", DASH.sub("", PAREN.sub("", raw)))
    st = n(st)
    return st or n(raw)

BAD = [re.compile(p, re.I) for p in [
    r"(?:[(\[:,]\s*|\s-\s+)live(?=$|[\s)\]\-:,!.?/])",
    r"\blive\s+(?:at|from|in|on|with|session|sessions|recording|recorded|album|version|tour|performance)\b",
    r"\bunplugged\b", r"\bin concert\b",
    r"\b(?:greatest|biggest|very best|ultimate|essential|essentials|definitive|platinum|gold)\s+(?:hits|collection|of|recordings|singles)\b",
    r"\bbest of\b", r"\bthe very best\b", r"\bhits\s+(?:vol|volume|\d)", r"^hits$",
    r"\bsingles\s+collection\b", r"\bcollection\b", r"\banthology\b", r"\bcompilation\b",
    r"\bremix(?:es|ed)?\b", r"\brmx\b", r"\bsoundtrack\b", r"\bost\b",
    r"\boriginal (?:motion picture|score|cast|series|television|broadway|film)\b",
    r"\bmusic from\b", r"\binspired by\b", r"\b(?:film|motion picture) score\b",
    r"\btribute\b", r"\btributo\b", r"\bkaraoke\b", r"\binstrumentals?\b",
    r"\bdemos?\b", r"\bb-?sides\b", r"\brarities\b", r"\bbootleg\b",
    r"\bsped up\b", r"\bslowed\b", r"\blullaby renditions\b", r"\bstring quartet\b",
    r"\bmade famous by\b", r"\boriginally performed\b", r"\bin the style of\b",
]]
def bad_name(name):
    return any(p.search(name) for p in BAD)

GENRE_BAD = re.compile(r"soundtrack|trilha|karaok|tribut|cast recording|score", re.I)
EDITION = re.compile(r"\b(?:deluxe|expanded|edition|remaster(?:ed)?|anniversary|version|bonus|special|complete)\b", re.I)

def http(url, headers=None, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(1 + i)
    print("  http fail:", type(last).__name__, getattr(last, "code", ""))
    return None

def lastfm(method, **params):
    q = {"method": method, "api_key": KEY, "format": "json", "autocorrect": "1"}
    q.update(params)
    body = http("https://ws.audioscrobbler.com/2.0/?" + urllib.parse.urlencode(q), {"User-Agent": "AMusic"})
    if not body:
        return None
    d = json.loads(body)
    if "error" in d:
        print("  lastfm error", method, d.get("error"), d.get("message"))
        return None
    return d

def apple_token():
    html = http("https://music.apple.com/us/browse", {"User-Agent": UA}) or ""
    for path in sorted(set(re.findall(r"/assets/index(?:-legacy)?[~-][A-Za-z0-9_-]+\.js", html))):
        js = http("https://music.apple.com" + path, {"User-Agent": UA}) or ""
        for jwt in sorted(set(re.findall(r"ey[A-Za-z0-9_-]+\.ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", js))):
            try:
                pl = json.loads(base64.urlsafe_b64decode(jwt.split(".")[1] + "=="))
            except Exception:
                continue
            if pl.get("exp", 0) > time.time():
                hd = base64.urlsafe_b64decode(jwt.split(".")[0] + "==").decode()
                if "WebPlayKid" in hd or "AMPWebPlay" in json.dumps(pl):
                    return jwt
    return None

TOKEN = apple_token()
print("apple token:", "ok" if TOKEN else "MISSING", "| lastfm key:", "present" if KEY else "MISSING")
if not TOKEN or not KEY:
    sys.exit(1)

def apple(path, **params):
    url = "https://amp-api.music.apple.com/v1/catalog/%s/%s?%s" % (SF, path, urllib.parse.urlencode(params))
    body = http(url, {"Authorization": "Bearer " + TOKEN, "Origin": "https://music.apple.com",
                      "Referer": "https://music.apple.com/", "User-Agent": UA})
    return json.loads(body) if body else None

d = lastfm("artist.getsimilar", artist=ARTIST, limit=SIMILAR_LIMIT)
raw = (d or {}).get("similarartists", {}).get("artist", [])
sim = []
for a in raw:
    try:
        m = float(a.get("match"))
    except Exception:
        continue
    if not (0.0 <= m <= 1.0) or not a.get("name"):
        continue
    if n(a["name"]) == n(ARTIST):
        continue
    sim.append((a["name"].strip(), m))
seen = set(); uniq = []
for nm, m in sim:
    if n(nm) in seen: continue
    seen.add(n(nm)); uniq.append((nm, m))
sim = sorted(uniq, key=lambda x: -x[1])
print("similar artists returned by Last.fm:", len(raw), "valid:", len(sim))
print("match scores, in order:", " ".join("%.3f" % m for _, m in sim))

def top_albums(artist):
    d = lastfm("artist.gettopalbums", artist=artist, limit=TOPALBUMS_LIMIT)
    names = [a.get("name", "").strip() for a in (d or {}).get("topalbums", {}).get("album", [])]
    out, dropped, keys = [], [], set()
    for nm in names:
        if not nm or nm.lower() == "(null)": continue
        if bad_name(nm):
            dropped.append(nm); continue
        k = clean(nm)
        if k in keys: continue
        keys.add(k); out.append(nm)
    return out[:CANDIDATES], dropped, names

def original_release(attr):
    if attr.get("isCompilation") is True: return False
    if bad_name(attr.get("name", "")): return False
    if any(GENRE_BAD.search(g) for g in attr.get("genreNames", [])): return False
    return True

def find_on_apple(artist, albums):
    want_artist = clean(artist)
    resolved = []; log = []
    for album in albums:
        d = apple("search", term="%s %s" % (artist, album), types="albums", limit="8", l="pt-BR")
        hits = (((d or {}).get("results") or {}).get("albums") or {}).get("data", [])
        want = clean(album)
        cands = []
        for h in hits:
            at = h.get("attributes", {})
            if not want_artist or clean(at.get("artistName", "")) != want_artist:
                continue
            if clean(at.get("name", "")) != want:
                continue
            if not original_release(at):
                log.append("rejected %s (compilation/live/soundtrack metadata)" % at.get("name"))
                continue
            cands.append(h)
        cands.sort(key=lambda h: 1 if EDITION.search(h["attributes"].get("name", "")) else 0)
        if not cands:
            log.append("no exact Apple match for '%s'" % album)
            continue
        m = cands[0]
        key = clean(m["attributes"]["artistName"]) + "|" + clean(m["attributes"]["name"])
        if all(r[0] != key for r in resolved):
            resolved.append((key, m))
        if len(resolved) >= PER_ARTIST: break
    return [m for _, m in resolved], log

def work(item):
    nm, mt = item
    albums, dropped, rawnames = top_albums(nm)
    if not albums:
        return (nm, mt, [], [], dropped, rawnames)
    recs, log = find_on_apple(nm, albums)
    return (nm, mt, recs, log, dropped, rawnames)

with ThreadPoolExecutor(6) as ex:
    results = list(ex.map(work, sim))

def select(floor):
    eligible = [r for r in results if r[1] >= floor]
    ordered = []
    for i in range(PER_ARTIST):
        for r in eligible:
            if i < len(r[2]): ordered.append((i, r))
    cards, keys = [], set()
    for i, r in ordered:
        rec = r[2][i]
        at = rec["attributes"]
        k = clean(at["artistName"]) + "|" + clean(at["name"])
        if rec["id"] in keys or k in keys: continue
        keys.add(rec["id"]); keys.add(k)
        cards.append((i + 1, r[0], r[1], at["name"], at.get("releaseDate", "")[:4], at.get("isSingle"), at.get("genreNames", [])[:1]))
        if len(cards) >= MAX_CARDS: break
    return cards

print()
print("RESULT: cards by similarity floor (max %d)" % MAX_CARDS)
for f in FLOORS:
    print("  floor %.2f -> artists above floor %d -> cards %d" % (f, len([r for r in results if r[1] >= f]), len(select(f))))
print()
print("ARTIST DETAIL (match | artist | resolved | dropped by name filter | log)")
for nm, mt, recs, log, dropped, rawnames in results:
    print(" %.3f | %s | resolved=%d | dropped=%s | log=%s" % (mt, nm, len(recs), dropped[:5], log[:3]))
print()
for f in (0.0, float(os.environ.get("SHOW_FLOOR", "0.1") or "0.1")):
    print("CARDS at floor %.2f:" % f)
    for c in select(f):
        print("  pass%d | %.3f | %s | %s | %s | single=%s | %s" % c)
    print()
