import json, urllib.request, urllib.error
def p(tag, obj): print("P|" + tag + "|" + json.dumps(obj, ensure_ascii=False)[:2500], flush=True)
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}), timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, None
st, j = get("https://ess.api.bbci.co.uk/schedules?serviceId=bbc_arabic_tv")
items = j["items"]
p("first", items[0]); p("range", {"n": len(items), "first": items[0].get("published_time"), "last": items[-1].get("published_time")})
for sid in ["bbc_afghan_tv", "bbc_pashto_afghanistan", "bbc_world_service_pashto_tv", "bbc_afghanistan_tv", "bbc_pashto_news_tv", "bbc_news_pashto", "bbc_pashto_tv_afghanistan", "bbc_afghan", "bbc_world_news_pashto", "bbc_dari_tv", "bbc_pashto_radio", "bbc_pashto_service"]:
    st, j2 = get(f"https://ess.api.bbci.co.uk/schedules?serviceId={sid}")
    p("pashto", {"sid": sid, "st": st, "n": len(j2["items"]) if j2 else 0, "name": (j2 or {}).get("service", {}).get("name")})
