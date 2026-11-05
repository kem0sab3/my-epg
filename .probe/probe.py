import json, re, urllib.request, urllib.error, datetime
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3500], flush=True)
def get(url, hdr=None, n=None):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept": "*/*"}
    h.update(hdr or {})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
            return r.status, r.geturl(), r.read(n) if n else r.read()
    except urllib.error.HTTPError as e:
        return e.code, url, e.read(400)
    except Exception as e:
        return None, url, str(e).encode()

# A) Bauer: every free station with a schedule
st, _, body = get("https://listenapi.planetradio.co.uk/api9.2/stations/GB?premium=1")
for s in json.loads(body):
    streams = [x.get("streamUrl") for x in (s.get("stationStreams") or []) if not x.get("streamPremium")]
    direct = next((u for u in streams if re.search(r'\.(aac|mp3)\?', u or "") and "hls" not in u), None)
    p("bauer", {"code": s["stationCode"], "name": s["stationName"], "prem": s.get("premiumOnlyStation"), "sched": s.get("hasSchedule"),
                "direct": direct, "logo": s.get("stationListenBarLogo")})

# B) Global: brands/stations + find a schedule endpoint
st, _, body = get("https://bff-web-guacamole.musicradio.com/globalplayer/brands")
brands = json.loads(body)
p("global-brand-keys", sorted(brands[0].keys()))
for b in brands:
    p("gbrand", {k: b.get(k) for k in ("id", "slug", "name", "heraldId", "brandSlug", "legacyStationPrefix", "brandLogo", "brandId")})
for u in ["https://bff-web-guacamole.musicradio.com/stations/2mwx3", "https://bff-web-guacamole.musicradio.com/globalplayer/stations/2mwx3",
          "https://bff-web-guacamole.musicradio.com/globalplayer/stations/2mwx3/schedule", "https://bff-web-guacamole.musicradio.com/stations/2mwx3/schedule",
          "https://bff-web-guacamole.musicradio.com/globalplayer/schedules/2mwx3", "https://www.globalplayer.com/live/capitaldance/uk/"]:
    st, final, body = get(u, n=600000)
    txt = body.decode("utf-8", "replace")
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', txt, re.S)
    if m:
        d = json.loads(m.group(1))
        found = []
        def walk(n, path):
            if isinstance(n, dict):
                ks = set(n.keys())
                if ({"start_time", "end_time"} <= ks or {"startTime", "endTime"} <= ks or {"start", "end"} <= ks) and len(found) < 3:
                    found.append({"path": path, "item": {k: n[k] for k in list(n)[:12]}})
                for k, v in n.items(): walk(v, path + "/" + k)
            elif isinstance(n, list):
                for i, v in enumerate(n[:100]): walk(v, path + "[]")
        walk(d, "")
        p("gpage", {"u": u, "st": st, "found": found, "apis": sorted(set(re.findall(r'https://[a-z0-9.-]*musicradio\.com/[a-zA-Z0-9/_\-{}.]{3,80}', txt)))[:25]})
    else:
        p("gapi", {"u": u, "st": st, "head": txt[:700]})

# C) Times Radio / Boom Radio
for u in ["https://www.thetimes.com/radio/schedule", "https://timesradio.wireless.radio/schedule", "https://www.timesradio.co.uk/schedule",
          "https://www.boomradiouk.com/schedule/", "https://boomradiouk.com/schedule"]:
    st, final, body = get(u, n=400000)
    txt = body.decode("utf-8", "replace")
    p("tb", {"u": u, "st": st, "final": final, "len": len(txt), "next": bool(re.search('__NEXT_DATA__', txt)),
             "jsonld": len(re.findall('application/ld\\+json', txt)), "apis": sorted(set(re.findall(r'https://[a-z0-9.-]+/(?:api|wp-json)[^"\'\s<>]{0,80}', txt)))[:15],
             "title": (re.search(r'<title>(.*?)</title>', txt, re.S) or [None, None])[1]})

# D) LG Channels UK
for u, hdr in [("https://api.lgchannels.com/api/v1.0/schedulelist", {"x-device-country": "GB", "x-device-language": "en"}),
               ("https://api.lgchannels.com/api/v1.0/channellist", {"x-device-country": "GB", "x-device-language": "en"})]:
    st, final, body = get(u, hdr)
    try:
        j = json.loads(body)
        def shape(n, d=0):
            if d > 3: return "..."
            if isinstance(n, dict): return {k: shape(v, d+1) for k, v in list(n.items())[:15]}
            if isinstance(n, list): return [f"list[{len(n)}]", shape(n[0], d+1) if n else None]
            return type(n).__name__
        p("lg", {"u": u, "st": st, "shape": shape(j)})
        cats = j.get("categories") or []
        for c in cats[:40]:
            for ch in (c.get("schedules") or c.get("channels") or [])[:200]:
                p("lgch", {"cat": c.get("categoryName"), "id": ch.get("channelId"), "name": ch.get("channelName"),
                           "url": ch.get("mediaStaticUrl"), "logo": ch.get("channelLogoUrl"), "progs": len(ch.get("programs") or [])})
        break
    except Exception as e:
        p("lg", {"u": u, "st": st, "err": str(e)[:100], "head": body[:300].decode("utf-8", "replace")})
