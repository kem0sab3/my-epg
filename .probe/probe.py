import json, re, urllib.request
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=40) as r:
        return r.read().decode("utf-8", "replace")
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3500], flush=True)
for slug in ("clyde", "greatest-hits"):
    html = get(f"https://www.hellorayo.co.uk/{slug}/schedule")
    ist = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1))["props"]["initialState"]
    s = ist["schedule"]
    def shape(n, d=0):
        if d > 3: return "..."
        if isinstance(n, dict): return {k: shape(v, d + 1) for k, v in list(n.items())[:12]}
        if isinstance(n, list): return [f"list[{len(n)}]", shape(n[0], d + 1) if n else None]
        return type(n).__name__
    p("shape-" + slug, shape(s))
    p("raw-" + slug, s)
    # also look for schedule-like API urls in the page
    p("apis-" + slug, sorted(set(re.findall(r'https?://[a-z0-9.-]+/api[^"\'\s<>]{0,100}', html)))[:20])
