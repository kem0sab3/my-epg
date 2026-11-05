import json, urllib.request, urllib.error, datetime
UA = {"User-Agent": "Mozilla/5.0 (my-epg probe)", "Accept": "application/json"}
def get(url, hdr=UA):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:2500], flush=True)
B = "https://listenapi.planetradio.co.uk/api9.2/"
st, body = get(B + "stations/cl1"); j = json.loads(body)
p("st-cl1-type", {"n": len(j), "first": j[0] if j else None})
st, body = get(B + "schedule/cl1"); p("sched-plain", {"status": st, "body": body[:400].decode("utf-8", "replace")})
today = datetime.date.today()
for path in [f"schedule/cl1/{today}", f"schedule/cl1?date={today}", f"schedule/cl1/{today:%Y%m%d}", f"schedule/cl1/0", f"schedule/cl1/1",
             f"schedule/cl1/{today.isoweekday()}", f"schedule/cl1/today", "schedule/1"]:
    st, body = get(B + path)
    txt = body[:600].decode("utf-8", "replace")
    p("sched", {"path": path, "status": st, "body": txt})
# station splits for regional GHR (e.g. Glasgow)
st, body = get(B + "stations/GB?premium=1"); stations = json.loads(body)
for s in stations:
    if s.get("stationCode") in ("gh0", "cl1", "abr", "hit", "mag", "ki1", "pln", "jaz", "ki2", "fo1"):
        p("splits", {"code": s["stationCode"], "name": s["stationName"], "premiumOnly": s.get("premiumOnlyStation"),
                     "hasSchedule": s.get("hasSchedule"), "splits": s.get("stationSplits"), "logo": s.get("stationListenBarLogo")})
# Rakuten with valid per_page and paging
now = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0); end = now + datetime.timedelta(days=2)
for per in (100, 50, 24):
    q = (f"classification_id=18&device_identifier=web&locale=en&market_code=uk&per_page={per}&page=1"
         f"&epg_starts_at={now:%Y-%m-%dT%H:%M:%S.000Z}&epg_ends_at={end:%Y-%m-%dT%H:%M:%S.000Z}&epg_duration_minutes=360").replace(":", "%3A")
    st, body = get("https://gizmo.rakuten.tv/v3/live_channels?" + q)
    j = json.loads(body)
    if st != 200:
        p("rak", {"per": per, "status": st, "err": j}); continue
    d = j.get("data") or []
    p("rak", {"per": per, "status": st, "n": len(d), "meta": j.get("meta"), "keys": sorted(d[0].keys()) if d else None})
    if d:
        p("rak-prog-sample", (d[0].get("live_programs") or [])[:1])
        for c in d:
            imgs = c.get("images") or {}
            p("rak-ch", {"id": c.get("id"), "title": c.get("title"), "progs": len(c.get("live_programs") or []),
                         "logo": imgs.get("artwork_negative") or imgs.get("artwork")})
    break
