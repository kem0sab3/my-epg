import json, re, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3000], flush=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept": "text/html,*/*"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40) as r:
            return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, u, e.read(500).decode("utf-8", "replace")
st, final, html = get("https://tbn.uk/tv-guide/")
p("page", {"st": st, "final": final, "len": len(html), "title": (re.search(r"<title>(.*?)</title>", html, re.S) or [0, ""])[1].strip()})
p("scripts", sorted(set(re.findall(r'<script[^>]+src="([^"]+)"', html)))[:30])
p("apis", sorted(set(re.findall(r'https?://[^"\'\s<>]*(?:api|json|schedule|guide|epg|wp-json)[^"\'\s<>]*', html)))[:40])
p("next", bool(re.search("__NEXT_DATA__", html)))
for kw in ["schedule", "tv-guide", "programme", "program", "data-time", "data-start", "time"]:
    i = html.lower().find(kw)
    if i > 0: p("ctx-" + kw, re.sub(r"\s+", " ", html[max(0, i-300):i+700]))
# try WordPress REST api discovery
st2, _, body = get("https://tbn.uk/wp-json/")
p("wpjson", {"st": st2, "head": body[:600]})
