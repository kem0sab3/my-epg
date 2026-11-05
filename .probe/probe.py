import json, urllib.request, urllib.error, urllib.parse
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:1500], flush=True)
def get(u, n=None, ua="Mozilla/5.0"):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": ua}), timeout=25) as r:
            return r.status, r.geturl(), r.headers.get("Content-Type"), (r.read(n) if n else r.read())
    except urllib.error.HTTPError as e:
        return e.code, u, None, e.read(300)
    except Exception as e:
        return None, u, None, str(e).encode()
st, fu, ct, body = get("https://i.mjh.nz/Plex/gb.m3u8")
txt = body.decode("utf-8", "replace"); lines = txt.splitlines()
p("plex-m3u", {"st": st, "n": txt.count("#EXTINF"), "head": "\n".join(lines[:7])})
groups = {}
for l in lines:
    if l.startswith("#EXTINF") and 'group-title="' in l:
        g = l.split('group-title="')[1].split('"')[0]; groups[g] = groups.get(g, 0) + 1
p("plex-groups", groups)
urls = [l for l in lines if l.startswith("http")][:6]
for u in urls:
    st, fu, ct, b = get(u, 3000)
    p("plex-stream", {"u": u[:120], "st": st, "final": fu[:120], "ct": ct, "head": b[:150].decode("utf-8", "replace")})
# RTE radio via radio-browser
for nm in ["RTÉ Radio 1", "RTÉ 2FM", "RTÉ lyric fm", "RTÉ Raidió na Gaeltachta"]:
    st, fu, ct, b = get("https://de1.api.radio-browser.info/json/stations/search?" + urllib.parse.urlencode({"name": nm, "countrycode": "IE", "hidebroken": "true", "order": "votes", "reverse": "true", "limit": 5}))
    try:
        res = [(s["name"], s["url_resolved"], s["codec"], s["bitrate"]) for s in json.loads(b)]
    except Exception:
        res = b[:200].decode("utf-8", "replace")
    p("rte-rb", {"q": nm, "res": res})
for u in ["https://www.rte.ie/manifests/radio1.m3u8", "https://www.rte.ie/manifests/2fm.m3u8", "https://www.rte.ie/manifests/lyric.m3u8", "https://www.rte.ie/manifests/rnag.m3u8",
          "https://icecast.rte.ie/radio1", "https://icecast.rte.ie/2fm", "https://icecast.rte.ie/lyric", "https://icecast.rte.ie/rnag"]:
    st, fu, ct, b = get(u, 1500)
    p("rte", {"u": u, "st": st, "final": fu[:100], "ct": ct, "head": b[:120].decode("latin-1")})
