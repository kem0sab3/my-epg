import json, re, urllib.request, urllib.error, urllib.parse, html as H
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:2500], flush=True)
HD = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Origin": "https://watch.islamchannel.tv", "Referer": "https://watch.islamchannel.tv/"}
def get(u, hdr=None, n=None):
    h = dict(HD); h.update(hdr or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=40) as r:
            return r.status, r.geturl(), (r.read(n) if n else r.read()).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, u, e.read(400).decode("utf-8", "replace")
st, _, page = get("https://watch.islamchannel.tv/live/1025")
attrs = dict(re.findall(r'data-(id|key|userid|uvid|expiry|token|env)="([^"]*)"', page.split('data-env="production"', 1)[1][:1500].join(['data-env="production"', ''])) )
p("attrs", {k: (v if k not in ("token", "key") else v[:6] + "…") for k, v in attrs.items()})
st, _, js = get("https://ssmp.simplestreamcdn.com/dist/builds/bitmovin/v1.1.32/ssmp.bundle.js?plugins=youbora,ima")
urls = sorted(set(re.findall(r'https?://[a-z0-9.\-]*simplestream[a-z0-9.\-]*/[^"\'`\s]{0,120}', js)))
p("ssmp-urls", urls[:40])
for kw in ["/api/live", "live/stream", "stream/", "expiry"]:
    for m in list(re.finditer(re.escape(kw), js))[:2]:
        i = m.start(); p("js-" + kw, re.sub(r"\s+", " ", js[max(0, i-400):i+500]))
# try the usual Simplestream live stream API
sid, key, tok, exp, uid = attrs.get("id"), attrs.get("key"), attrs.get("token"), attrs.get("expiry"), attrs.get("userid")
for base in ["https://v2-streams-elb.simplestreamcdn.com/api/live/stream/", "https://v2-streams.simplestreamcdn.com/api/live/stream/"]:
    q = urllib.parse.urlencode({"key": key, "platform": "chrome", "user": uid, "token": tok, "expiry": exp, "uvid": attrs.get("uvid")})
    st, fu, body = get(base + sid + "?" + q, {"Accept": "application/json"})
    p("api", {"base": base, "st": st, "body": body[:700]})
