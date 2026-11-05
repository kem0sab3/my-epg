import json, re, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3000], flush=True)
HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept": "text/html,*/*"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=HD), timeout=40) as r:
            return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, u, e.read(500).decode("utf-8", "replace")
st, final, html = get("https://islamchannel.tv/tv-guide/")
p("page", {"st": st, "final": final, "len": len(html), "title": (re.search(r"<title>(.*?)</title>", html, re.S) or [0, ""])[1].strip()})
p("scripts", sorted(set(re.findall(r'<script[^>]+src="([^"]+)"', html)))[:40])
p("apis", sorted(set(re.findall(r'https?://[^"\'\s<>]*(?:api|json|schedule|guide|epg|ajax)[^"\'\s<>]*', html)))[:40])
p("inline-vars", re.findall(r'var\s+\w+\s*=\s*\{[^<]{0,400}', html)[:8])
for kw in ["schedule", "data-start", "datetime=", "programme", "time-slot", "tv-guide-", "class=\"time", "am</", "pm</"]:
    i = html.find(kw)
    if i > 0: p("ctx-" + kw, re.sub(r"\s+", " ", html[max(0, i-400):i+900]))
st2, _, body = get("https://islamchannel.tv/wp-json/")
p("wpjson", {"st": st2, "head": body[:800]})
