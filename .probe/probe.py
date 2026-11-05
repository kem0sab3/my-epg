import json, urllib.request, urllib.parse, datetime, sys
UA = {"User-Agent": "Mozilla/5.0 (my-epg probe)", "Accept": "application/json"}
def get(url, hdr=UA, n=None):
    req = urllib.request.Request(url, headers=hdr)
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, (r.read(n) if n else r.read())
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3000], flush=True)

# 1) Rakuten UK channels
now = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
end = now + datetime.timedelta(days=3)
q = (f"classification_id=18&device_identifier=web&device_stream_audio_quality=2.0&device_stream_hdr_type=NONE"
     f"&device_stream_video_quality=FHD&epg_duration_minutes=360&epg_ends_at={end:%Y-%m-%dT%H:%M:%S.000Z}"
     f"&epg_ends_at_timestamp={end.timestamp()}&epg_starts_at={now:%Y-%m-%dT%H:%M:%S.000Z}"
     f"&epg_starts_at_timestamp={now.timestamp()}&locale=en&market_code=uk&per_page=250").replace(":", "%3A")
try:
    st, body = get("https://gizmo.rakuten.tv/v3/live_channels?" + q)
    data = json.loads(body)["data"]
    p("rak-count", len(data))
    p("rak-keys", sorted(data[0].keys()))
    for c in data:
        imgs = c.get("images") or {}
        p("rak", {"id": c["id"], "n": c.get("channel_number"), "title": c["title"], "progs": len(c.get("live_programs") or []),
                  "logo": imgs.get("artwork_negative") or imgs.get("artwork"),
                  "cat": [t.get("name") for t in ((c.get("labels") or {}).get("tags") or [])][:3]})
except Exception as e:
    p("rak-error", str(e))

# 2) radio-browser lookups
names = ["Clyde 1", "Greatest Hits Radio Glasgow", "Capital", "Capital XTRA", "Heart", "Heart 80s", "Heart 90s", "Heart Dance",
         "Smooth Radio", "Classic FM", "Radio X", "LBC", "LBC News", "Gold", "talkSPORT", "Virgin Radio UK", "Absolute Radio",
         "KISS", "Planet Rock", "Times Radio", "Greatest Hits Radio", "Hits Radio", "Magic Radio", "Jazz FM", "Scala Radio",
         "Premier Christian Radio", "BFBS", "Forth 1", "Capital Scotland", "Heart Scotland", "Smooth Scotland"]
for nm in names:
    try:
        st, body = get("https://de1.api.radio-browser.info/json/stations/search?" + urllib.parse.urlencode(
            {"name": nm, "countrycode": "GB", "hidebroken": "true", "order": "votes", "reverse": "true", "limit": 6}))
        res = [{"name": s["name"], "url": s["url_resolved"], "codec": s["codec"], "br": s["bitrate"], "ok": s["lastcheckok"],
                "votes": s["votes"], "fav": s["favicon"]} for s in json.loads(body)]
        p("rb", {"q": nm, "res": res})
    except Exception as e:
        p("rb-error", {"q": nm, "e": str(e)})

# 3) Bauer (Rayo) listen API
for u in ["https://listenapi.planetradio.co.uk/api9.2/initweb/clyde1",
          "https://listenapi.planetradio.co.uk/api9.2/stations/GB?premium=1",
          "https://listenapi.planetradio.co.uk/api9.2/schedule/clyde1"]:
    try:
        st, body = get(u)
        j = json.loads(body)
        if isinstance(j, dict):
            p("bauer", {"u": u, "status": st, "keys": sorted(j.keys())[:60]})
            for k in ("stationSchedule", "schedule", "stationOnAir", "stationStreams"):
                if k in j: p("bauer-" + k, j[k] if not isinstance(j[k], list) else j[k][:3])
        else:
            p("bauer", {"u": u, "status": st, "len": len(j), "first": j[0] if j else None})
    except Exception as e:
        p("bauer-error", {"u": u, "e": str(e)})

# 4) Global schedule API guess
for u in ["https://bff-web-guacamole.musicradio.com/globalplayer/brands", "https://bff-web-guacamole.musicradio.com/features/schedule/capital"]:
    try:
        st, body = get(u, n=4000)
        p("global", {"u": u, "status": st, "head": body[:800].decode("utf-8", "replace")})
    except Exception as e:
        p("global-error", {"u": u, "e": str(e)})

# 5) stream reachability (from US runner; UK-only streams may refuse)
for u in ["https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/master.m3u8",
          "https://masterpl.hls.nhkworld.jp/hls/w/live/smarttv.m3u8",
          "https://abc-news-dmd-streams-1.akamaized.net/out/v1/701126012d044971b3fa89406a440133/index.m3u8"]:
    try:
        st, body = get(u, {"User-Agent": "Mozilla/5.0"}, 300)
        p("stream", {"u": u, "status": st, "head": body[:80].decode("utf-8", "replace")})
    except Exception as e:
        p("stream-error", {"u": u, "e": str(e)})
