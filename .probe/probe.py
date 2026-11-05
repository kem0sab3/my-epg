import json, re, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3000], flush=True)
HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def get(u, hdr=None):
    h = dict(HD); h.update(hdr or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=40) as r:
            return r.status, r.geturl(), r.headers.get("Content-Type"), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, u, None, e.read(500).decode("utf-8", "replace")
st, final, ct, html = get("https://watch.islamchannel.tv/live/1025")
p("page", {"st": st, "final": final, "len": len(html), "title": (re.search(r"<title>(.*?)</title>", html, re.S) or [0, ""])[1].strip()})
p("m3u8", sorted(set(re.findall(r'https?://[^"\'\s<>\\]+\.m3u8[^"\'\s<>\\]*', html)))[:20])
p("scripts", sorted(set(re.findall(r'<script[^>]+src="([^"]+)"', html)))[:25])
p("apis", sorted(set(re.findall(r'https?://[^"\'\s<>\\]*(?:api|stream|live|player|vimeo|jw|brightcove|cdn)[^"\'\s<>\\]*', html)))[:40])
p("next", bool(re.search("__NEXT_DATA__|__NUXT__", html)))
for kw in ["1025", "hls", "drm", "widevine", "token", "login", "subscribe"]:
    i = html.lower().find(kw)
    if i > 0: p("ctx-" + kw, re.sub(r"\s+", " ", html[max(0, i-300):i+500]))
