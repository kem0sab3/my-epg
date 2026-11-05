import json, re, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3500], flush=True)
HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def get(u, hdr=None):
    h = dict(HD); h.update(hdr or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(500).decode("utf-8", "replace")
st, html = get("https://watch.islamchannel.tv/live/1025")
for kw in ["ssmp", "SSMP", "data-player", "stream_id", "streamId", "data-id=\"1025\"", "uvid", "player_key", "api_key", "ssmpConfig", "new SSMP"]:
    for m in list(re.finditer(re.escape(kw), html))[:2]:
        i = m.start(); p("ctx-" + kw, re.sub(r"\s+", " ", html[max(0, i-600):i+900]))
st, js = get("https://watch.islamchannel.tv/static/dist/js/app-5ae2ea12.js")
p("appjs-len", len(js))
for kw in ["simplestreamcdn.com/api", "stream", "token", "key="]:
    for m in list(re.finditer(re.escape(kw), js))[:3]:
        i = m.start(); p("js-" + kw, re.sub(r"\s+", " ", js[max(0, i-300):i+400]))
