import json, urllib.request, urllib.parse, urllib.error, datetime
UA = {"User-Agent": "Mozilla/5.0 (my-epg probe)", "Accept": "application/json"}
def get(url, hdr=UA):
    req = urllib.request.Request(url, headers=hdr)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:2500], flush=True)

# Bauer station list: codes, names, stream URLs, any schedule-ish keys
st, body = get("https://listenapi.planetradio.co.uk/api9.2/stations/GB?premium=1")
stations = json.loads(body)
p("bauer-station-keys", sorted(stations[0].keys()))
want = ("clyde", "greatest hits radio glasgow", "absolute radio", "kiss", "magic", "hits radio", "greatest hits radio",
        "forth", "planet rock", "jazz fm", "scala", "kisstory", "union jack")
for s in stations:
    nm = s.get("stationName", "")
    if any(w in nm.lower() for w in want):
        streams = [(x.get("streamQuality"), x.get("streamUrl")) for x in (s.get("stationStreams") or [])]
        p("bauer-st", {"code": s.get("stationCode"), "id": s.get("stationId"), "name": nm, "logo": s.get("stationListenBarLogo"),
                       "sq": s.get("stationSquareLogo") or s.get("stationLogo"), "streams": streams[:4]})
code = next((s["stationCode"] for s in stations if s.get("stationName", "").lower().startswith("clyde 1")), "cl1")
for path in [f"initweb/{code}", f"stations/{code}", f"schedule/{code}", f"epg/{code}", f"station/{code}/schedule",
             f"schedules/{code}", f"onair/{code}", f"stationschedule/{code}"]:
    st, body = get("https://listenapi.planetradio.co.uk/api9.2/" + path)
    try:
        j = json.loads(body); summary = sorted(j.keys())[:40] if isinstance(j, dict) else f"list len {len(j)}"
    except Exception:
        summary = body[:150].decode("utf-8", "replace")
    p("bauer-path", {"path": path, "status": st, "summary": summary})
    if st == 200 and isinstance(j, dict):
        for k in j:
            if "sched" in k.lower() or "epg" in k.lower() or "show" in k.lower():
                p("bauer-field", {"path": path, "key": k, "val": j[k] if not isinstance(j[k], list) else j[k][:2]})

# Rakuten: show error message, then try simpler requests
now = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
end = now + datetime.timedelta(days=2)
base = "https://gizmo.rakuten.tv/v3/live_channels?"
variants = {
  "minimal": "market_code=uk&locale=en&device_identifier=web&per_page=250",
  "classif": "classification_id=18&market_code=uk&locale=en&device_identifier=web&per_page=250",
  "epg": f"market_code=uk&locale=en&device_identifier=web&per_page=250&epg_starts_at={now:%Y-%m-%dT%H:%M:%S.000Z}&epg_ends_at={end:%Y-%m-%dT%H:%M:%S.000Z}&epg_duration_minutes=360",
  "epg-classif5": f"classification_id=5&market_code=uk&locale=en&device_identifier=web&per_page=250&epg_starts_at={now:%Y-%m-%dT%H:%M:%S.000Z}&epg_ends_at={end:%Y-%m-%dT%H:%M:%S.000Z}&epg_duration_minutes=360",
}
for k, q in variants.items():
    st, body = get(base + q.replace(":", "%3A"))
    try:
        j = json.loads(body)
        if st == 200:
            d = j.get("data") or []
            p("rak", {"v": k, "status": st, "n": len(d), "keys": sorted(d[0].keys()) if d else None,
                      "progs0": len((d[0].get("live_programs") or [])) if d else None})
            for c in d[:200]:
                imgs = c.get("images") or {}
                p("rak-ch", {"v": k, "id": c.get("id"), "title": c.get("title"), "progs": len(c.get("live_programs") or []),
                             "logo": imgs.get("artwork_negative") or imgs.get("artwork")})
            break
        else:
            p("rak", {"v": k, "status": st, "err": j})
    except Exception:
        p("rak", {"v": k, "status": st, "body": body[:300].decode("utf-8", "replace")})
