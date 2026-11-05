import json, re, urllib.request, urllib.error, urllib.parse
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
blk = page[page.find('data-env="production"'):][:1500]
a = dict(re.findall(r'data-([a-z\-]+)="([^"]*)"', blk))
st, _, body = get("https://mm-v2.simplestream.com/ssmp/api.php?id=" + a["id"] + "&env=production")
p("player-api", {"st": st, "body": body[:800]})
try:
    pa = json.loads(body); pa = pa.get("response", pa)
except Exception:
    pa = {}
host, comp = pa.get("api_hostname"), pa.get("company_uuid")
p("host", {"host": host, "company": comp})
if host:
    if "https://api" in host:
        url = f"{host}/streams/v2/{comp}/live/{a['uvid']}"
    else:
        url = f"{host}/streams/api/live/stream/{a['uvid']}"
    url += "?" + urllib.parse.urlencode({"key": a["key"], "cc": "GB", "platform": "chrome", "url": "https://watch.islamchannel.tv/live/1025", "gdpr": "0", "gdpr_consent": ""})
    hdr = {"Accept": "application/json", "Token": a["token"], "Token-Expiry": a["expiry"], "Userid": a.get("userid", "123456"), "Uvid": a["uvid"]}
    st, _, body = get(url, hdr)
    p("streams", {"st": st, "url": url.split("?")[0], "body": body[:1500]})
    m = re.findall(r'https?:\\?/\\?/[^"]+\.m3u8[^"]*', body)
    for u in m[:3]:
        u = u.replace("\\/", "/")
        st2, fu, b2 = get(u, {}, 2000)
        p("hls", {"u": u[:200], "st": st2, "head": b2[:300]})
        # does it work without the page's referer/origin?
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                p("hls-plain", {"st": r.status})
        except urllib.error.HTTPError as e:
            p("hls-plain", {"st": e.code})
