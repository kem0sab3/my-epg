import json, urllib.request, urllib.error, datetime
UA = {"User-Agent": "Mozilla/5.0 (my-epg probe)", "Accept": "application/json"}
def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:3000], flush=True)
B = "https://listenapi.planetradio.co.uk/api9.2/"
codes = ["cl1", "fo1", "no1", "ta1", "mf1", "gh0", "hit", "abr", "ab8", "ab9", "ki1", "ki2", "mag", "jaz", "ker", "pln"]
st, body = get(B + "stations/GB?premium=1"); allst = {s["stationCode"]: s for s in json.loads(body)}
for c in codes:
    s = allst.get(c)
    if not s:
        st, body = get(B + f"initweb/{c}")
        try: s = json.loads(body)
        except Exception: s = None
    if not s: p("st", {"code": c, "missing": True}); continue
    streams = [(x.get("streamQuality"), x.get("streamPremium"), x.get("streamUrl")) for x in (s.get("stationStreams") or [])]
    p("st", {"code": c, "name": s.get("stationName"), "premiumOnly": s.get("premiumOnlyStation"), "streams": streams,
             "logo": s.get("stationListenBarLogo"), "sq": s.get("stationSquareLogo")})
today = datetime.date.today(); tom = today + datetime.timedelta(days=1)
for path in ["schedule/cl1/today/tomorrow", f"schedule/cl1/{today}/{tom}", "schedule/cl1/today/+7 days".replace(" ", "%20"),
             "schedule/cl1/tomorrow/+2 days".replace(" ", "%20"), f"schedule/cl1/{today}T00:00:00/{today + datetime.timedelta(days=7)}T00:00:00"]:
    st, body = get(B + path)
    txt = body[:300].decode("utf-8", "replace")
    try:
        j = json.loads(body); days = list(j.keys())[:10] if isinstance(j, dict) else len(j)
    except Exception: days = None
    p("sched", {"path": path, "status": st, "days": days, "head": txt[:200]})
