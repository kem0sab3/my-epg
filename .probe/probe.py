import json, re, urllib.request, urllib.error, datetime
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept": "*/*"}
def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=40) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3800], flush=True)
# Bauer: all slugs (chunked)
st, html = get("https://www.hellorayo.co.uk/clyde/schedule")
ist = json.loads(re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1))["props"]["initialState"]
sl = ist["stationList"]["stationsById"]
items = [(k, v.get("stationCode")) for k, v in sl.items() if isinstance(v, dict)]
for i in range(0, len(items), 60): p("slugs", items[i:i+60])
p("sched-meta", {k: ist["schedule"].get(k) for k in ("day", "stationCode", "timestart", "timeend")})
# try other days
for path in ["clyde/schedule/friday", "clyde/schedule/saturday", "clyde/schedule/tomorrow", "clyde/schedule?day=friday", "clyde/schedule/2026-11-06"]:
    st, html = get("https://www.hellorayo.co.uk/" + path)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if m:
        s = json.loads(m.group(1))["props"]["initialState"]["schedule"]
        p("day", {"path": path, "status": st, "keys": list((s.get("data") or {}).keys()), "day": s.get("day"),
                  "first": [(x["start"], x["title"]) for d in (s.get("data") or {}).values() for x in d][:2]})
    else:
        p("day", {"path": path, "status": st, "nonext": True})
# Rakuten: all channels
now = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0); end = now + datetime.timedelta(days=2)
page = 1
while True:
    q = (f"classification_id=18&device_identifier=web&locale=en&market_code=uk&per_page=50&page={page}"
         f"&epg_starts_at={now:%Y-%m-%dT%H:%M:%S.000Z}&epg_ends_at={end:%Y-%m-%dT%H:%M:%S.000Z}&epg_duration_minutes=360").replace(":", "%3A")
    st, body = get("https://gizmo.rakuten.tv/v3/live_channels?" + q)
    j = json.loads(body); d = j.get("data") or []
    for c in d:
        imgs = c.get("images") or {}
        p("rak-ch", {"id": c.get("id"), "n": c.get("channel_number"), "title": c.get("title"), "progs": len(c.get("live_programs") or []),
                     "logo": imgs.get("artwork_negative") or imgs.get("artwork"),
                     "tags": [t.get("name") for t in ((c.get("labels") or {}).get("tags") or [])][:3]})
    if page >= j["meta"]["pagination"]["total_pages"]: break
    page += 1
