import json, re, urllib.request, urllib.error, collections
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=40) as r:
        return r.read().decode("utf-8", "replace")
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3500], flush=True)
html = get("https://www.hellorayo.co.uk/clyde/schedule")
data = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1))
ist = data["props"]["initialState"]
p("initialState-keys", sorted(ist.keys()))
lists = collections.defaultdict(int)
def walk(n, path):
    if isinstance(n, dict):
        for k, v in n.items(): walk(v, path + "/" + k)
    elif isinstance(n, list):
        if n and isinstance(n[0], dict) and "episodeStart" in n[0]:
            lists[path] = len(n)
        for i, v in enumerate(n[:400]): walk(v, path + "[]")
walk(ist, "")
p("episode-lists", dict(sorted(lists.items(), key=lambda kv: -kv[1])[:15]))
best = max(lists, key=lists.get) if lists else None
if best:
    node = ist
    # resolve the path (with [] meaning first element) to show the first and last items
    parts = re.findall(r"/([^/\[]+)|(\[\])", best)
    def resolve(n, parts):
        for key, br in parts:
            n = n[0] if br else n[key]
        return n
    lst = resolve(ist, parts)
    p("best-path", best); p("best-first", lst[0]); p("best-last", lst[-1]); p("best-n", len(lst))
sl = ist.get("stationList", {}).get("stationsById", {})
p("slugs", {k: (v.get("stationCode"), v.get("stationName")) for k, v in list(sl.items())[:400] if isinstance(v, dict)})
